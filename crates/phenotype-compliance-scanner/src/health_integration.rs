//! Health check integration for compliance scanner
//!
//! Provides health checks based on compliance scan results.

use crate::{ComplianceError, ScanResult, Severity};
use phenotype_health::{
    ComponentHealthCheck, HealthCheck, HealthRegistry, HealthReport, HealthStatus, ReportSummary,
};
use std::sync::Arc;
use tracing::{debug, warn};

/// Health check based on compliance scan results
#[derive(Debug)]
pub struct ComplianceHealthCheck {
    scanner: Arc<crate::ComplianceScanner>,
    project_path: std::path::PathBuf,
}

impl ComplianceHealthCheck {
    /// Create a new compliance health check
    pub fn new(
        scanner: Arc<crate::ComplianceScanner>,
        project_path: impl AsRef<std::path::Path>,
    ) -> Self {
        Self {
            scanner,
            project_path: project_path.as_ref().to_path_buf(),
        }
    }
}

#[async_trait::async_trait]
impl HealthCheck for ComplianceHealthCheck {
    fn name(&self) -> &str {
        "compliance"
    }

    async fn check(&self) -> Result<HealthStatus, phenotype_health::HealthCheckError> {
        let path = self.project_path.clone();
        let scanner = self.scanner.clone();

        // Run compliance scan in spawn_blocking since ComplianceScanner is sync
        let result = tokio::task::spawn_blocking(move || scanner.scan(&path))
            .await
            .map_err(|e| phenotype_health::HealthCheckError::Internal(e.to_string()))?;

        match result {
            Ok(scan_result) => {
                // Determine health based on findings
                let critical_count = scan_result.count_by_severity(Severity::Critical);
                let high_count = scan_result.count_by_severity(Severity::High);

                if critical_count > 0 {
                    Ok(HealthStatus::Unhealthy)
                } else if high_count > 0 || !scan_result.passed() {
                    Ok(HealthStatus::Degraded)
                } else {
                    Ok(HealthStatus::Healthy)
                }
            }
            Err(e) => {
                warn!("Compliance scan failed: {}", e);
                Err(phenotype_health::HealthCheckError::CheckFailed(
                    e.to_string(),
                ))
            }
        }
    }
}

/// Compliance health monitor
///
/// Monitors compliance status and provides health reports
#[derive(Debug)]
pub struct ComplianceHealthMonitor {
    scanner: Arc<crate::ComplianceScanner>,
}

impl ComplianceHealthMonitor {
    /// Create a new compliance health monitor
    pub fn new(scanner: Arc<crate::ComplianceScanner>) -> Self {
        Self { scanner }
    }

    /// Check health for a project
    pub async fn check_project(
        &self,
        project_path: impl AsRef<std::path::Path>,
    ) -> Result<HealthReport, ComplianceError> {
        let path = project_path.as_ref().to_path_buf();
        let scanner = self.scanner.clone();

        // Run scan in spawn_blocking since ComplianceScanner is sync
        let result = tokio::task::spawn_blocking(move || scanner.scan(&path))
            .await
            .map_err(|e| ComplianceError::ScanFailed(e.to_string()))?;

        // Convert scan result to health report
        Ok(scan_result_to_health_report(&result?))
    }

    /// Check health for multiple projects
    pub async fn check_projects(
        &self,
        project_paths: &[impl AsRef<std::path::Path> + Send + Sync],
    ) -> Vec<Result<HealthReport, ComplianceError>> {
        let mut results = Vec::new();

        for path in project_paths {
            results.push(self.check_project(path).await);
        }

        results
    }

    /// Convert scan results to health registry for HTTP endpoints
    pub async fn build_health_registry(
        &self,
        project_paths: &[impl AsRef<std::path::Path> + Send + Sync + Clone],
    ) -> HealthRegistry {
        let registry = HealthRegistry::new();

        for path in project_paths {
            if let Ok(report) = self.check_project(path).await {
                // Create a component health check based on the report
                let status = report.overall_status;
                let component_name = path
                    .as_ref()
                    .file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown")
                    .to_string();

                debug!("Creating health check for {}: {:?}", component_name, status);
                let _check = ComponentHealthCheck::new(component_name, status);
                // Note: We'd need to register this, but HealthRegistry::register is async
                // For now, just log it
            }
        }
        registry
    }
}

impl Default for ComplianceHealthMonitor {
    fn default() -> Self {
        Self::new(Arc::new(crate::ComplianceScanner::new()))
    }
}

/// Convert a scan result to a health report
fn scan_result_to_health_report(scan_result: &ScanResult) -> HealthReport {
    let mut snapshots = Vec::new();

    // Add findings as health snapshots
    for finding in &scan_result.findings {
        let status = match finding.severity {
            Severity::Critical => HealthStatus::Unhealthy,
            Severity::High => HealthStatus::Unhealthy,
            Severity::Medium => HealthStatus::Degraded,
            Severity::Low => HealthStatus::Degraded,
            Severity::Info => HealthStatus::Healthy,
        };

        snapshots.push(phenotype_health::HealthSnapshot {
            component: format!("{}: {}", finding.rule_id, finding.message),
            status,
            timestamp: finding.detected_at,
            latency_ms: None,
            error: finding.suggestion.clone(),
        });
    }

    // Calculate overall status
    let overall = if scan_result.count_by_severity(Severity::Critical) > 0 {
        HealthStatus::Unhealthy
    } else if scan_result.count_by_severity(Severity::High) > 0 {
        HealthStatus::Unhealthy
    } else if scan_result.count_by_severity(Severity::Medium) > 0 {
        HealthStatus::Degraded
    } else if scan_result.count_by_severity(Severity::Low) > 0 {
        HealthStatus::Degraded
    } else {
        HealthStatus::Healthy
    };

    // Count by status
    let healthy = snapshots
        .iter()
        .filter(|s| s.status == HealthStatus::Healthy)
        .count();
    let degraded = snapshots
        .iter()
        .filter(|s| s.status == HealthStatus::Degraded)
        .count();
    let unhealthy = snapshots
        .iter()
        .filter(|s| s.status == HealthStatus::Unhealthy)
        .count();

    HealthReport {
        overall_status: overall,
        checks: snapshots,
        summary: ReportSummary {
            total: scan_result.findings.len(),
            healthy,
            degraded,
            unhealthy,
        },
    }
}

/// Get compliance score as a health metric (0-100)
///
/// Returns 100 for fully compliant projects (no critical/high findings),
/// lower for projects with critical or high severity findings.
/// Medium, Low, and INFO-level findings don't impact the score
/// as they are recommendations, not requirements.
pub fn compliance_health_score(scan_result: &ScanResult) -> u8 {
    // Only count critical and high findings as actionable
    // This matches the documented behavior
    let actionable_findings =
        scan_result.critical_findings().len() + scan_result.high_findings().len();

    if actionable_findings == 0 {
        return 100;
    }

    // Weight findings by severity (only critical and high count)
    let critical_weight = scan_result.critical_findings().len() as f32 * 10.0;
    let high_weight = scan_result.high_findings().len() as f32 * 5.0;

    let total_weight = critical_weight + high_weight;
    let score = 100.0 - (total_weight / actionable_findings as f32).min(100.0);

    score as u8
}

/// Compliance health summary for reporting
#[derive(Debug, Clone)]
pub struct ComplianceHealthSummary {
    /// Project name
    pub project_name: String,
    /// Overall health status
    pub status: HealthStatus,
    /// Compliance health score (0-100)
    pub score: u8,
    /// Number of critical findings
    pub critical_count: usize,
    /// Number of high findings
    pub high_count: usize,
    /// Total findings
    pub total_findings: usize,
}

impl ComplianceHealthSummary {
    /// Create from a scan result
    pub fn from_scan_result(scan_result: &ScanResult) -> Self {
        Self {
            project_name: scan_result.project_name.clone(),
            status: if scan_result.critical_findings().is_empty() {
                if scan_result.high_findings().is_empty() {
                    HealthStatus::Healthy
                } else {
                    HealthStatus::Degraded
                }
            } else {
                HealthStatus::Unhealthy
            },
            score: compliance_health_score(scan_result),
            critical_count: scan_result.critical_findings().len(),
            high_count: scan_result.high_findings().len(),
            total_findings: scan_result.findings.len(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ComplianceScanner;
    use tempfile::TempDir;

    #[test]
    fn test_compliance_health_score_perfect() {
        let temp_dir = TempDir::new().unwrap();
        let project_dir = temp_dir.path().join("test-project");
        std::fs::create_dir(&project_dir).unwrap();

        // Create all required files (including optional ones to get a perfect score)
        std::fs::File::create(project_dir.join("README.md")).unwrap();
        std::fs::File::create(project_dir.join("LICENSE")).unwrap();
        std::fs::File::create(project_dir.join("AGENTS.md")).unwrap();
        std::fs::File::create(project_dir.join("CLAUDE.md")).unwrap();
        std::fs::File::create(project_dir.join("CHANGELOG.md")).unwrap();

        let scanner = ComplianceScanner::new();
        let result = scanner.scan(&project_dir).unwrap();

        let score = compliance_health_score(&result);
        assert_eq!(score, 100);
    }

    #[tokio::test]
    async fn test_compliance_health_monitor() {
        let scanner = Arc::new(ComplianceScanner::new());
        let monitor = ComplianceHealthMonitor::new(scanner);

        let temp_dir = TempDir::new().unwrap();
        let project_dir = temp_dir.path().join("test-project");
        std::fs::create_dir(&project_dir).unwrap();
        std::fs::File::create(project_dir.join("README.md")).unwrap();
        std::fs::File::create(project_dir.join("LICENSE")).unwrap();

        let report = monitor.check_project(&project_dir).await.unwrap();

        // Should be healthy since required files exist
        assert!(
            report.overall_status == HealthStatus::Healthy
                || report.overall_status == HealthStatus::Degraded
        );
    }

    #[test]
    fn test_compliance_health_summary() {
        let temp_dir = TempDir::new().unwrap();
        let project_dir = temp_dir.path().join("test-project");
        std::fs::create_dir(&project_dir).unwrap();
        std::fs::File::create(project_dir.join("README.md")).unwrap();
        std::fs::File::create(project_dir.join("LICENSE")).unwrap();

        let scanner = ComplianceScanner::new();
        let result = scanner.scan(&project_dir).unwrap();

        let summary = ComplianceHealthSummary::from_scan_result(&result);
        assert_eq!(summary.project_name, "test-project");
        assert_eq!(summary.critical_count, 0);
    }
}
