//! Async compliance scanning
//!
//! Provides async parallel scanning capabilities for compliance checks.

use crate::{ComplianceError, Finding, Rule, ScanResult, ScanSummary, Severity};
use chrono::Utc;
use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;
use tokio::fs;
use tokio::sync::{mpsc, Semaphore};
use tokio::task::JoinHandle;
use tracing::{debug, info, warn};

/// Maximum concurrent scans
const MAX_CONCURRENT_SCANS: usize = 10;

/// Async compliance scanner
#[derive(Debug)]
pub struct AsyncComplianceScanner {
    rules: Vec<Rule>,
    enabled_rules: Vec<String>,
    max_concurrent: usize,
}

impl Default for AsyncComplianceScanner {
    fn default() -> Self {
        let rules = crate::standard_rules();
        let enabled_rules = rules.iter().map(|r| r.id.clone()).collect();

        Self {
            rules,
            enabled_rules,
            max_concurrent: MAX_CONCURRENT_SCANS,
        }
    }
}

impl AsyncComplianceScanner {
    /// Create a new async scanner with default rules
    pub fn new() -> Self {
        Self::default()
    }

    /// Set the maximum number of concurrent scans
    pub fn with_concurrency(mut self, max: usize) -> Self {
        self.max_concurrent = max;
        self
    }

    /// Disable a specific rule
    pub fn disable_rule(&mut self, rule_id: &str) {
        self.enabled_rules.retain(|id| id != rule_id);
    }

    /// Enable a specific rule
    pub fn enable_rule(&mut self, rule_id: &str) {
        if !self.enabled_rules.contains(&rule_id.to_string()) {
            if self.rules.iter().any(|r| r.id == rule_id) {
                self.enabled_rules.push(rule_id.to_string());
            }
        }
    }

    /// Scan a project asynchronously
    pub async fn scan_async(
        &self,
        project_path: impl AsRef<Path>,
    ) -> Result<ScanResult, ComplianceError> {
        let path = project_path.as_ref();
        let project_name = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown")
            .to_string();

        info!("Starting async compliance scan for: {}", project_name);

        let scan_started = Utc::now();
        let mut findings = Vec::new();
        let mut rules_checked = Vec::new();
        let mut rules_skipped = Vec::new();

        // Process rules concurrently with semaphore
        let semaphore = Arc::new(Semaphore::new(self.max_concurrent));
        let (tx, mut rx) = mpsc::channel::<(String, Option<Finding>)>(self.rules.len());

        let mut handles = Vec::new();

        for rule in &self.rules {
            if !self.enabled_rules.contains(&rule.id) {
                rules_skipped.push(rule.id.clone());
                continue;
            }

            rules_checked.push(rule.id.clone());

            let permit = semaphore.clone().acquire_owned().await.unwrap();
            let rule = rule.clone();
            let path = path.to_path_buf();
            let tx = tx.clone();

            let handle: JoinHandle<()> = tokio::spawn(async move {
                let _permit = permit;
                let result = check_rule_async(&rule, &path).await;
                let _ = tx.send((rule.id.clone(), result)).await;
            });

            handles.push(handle);
        }

        // Drop the original tx so rx closes when all tasks complete
        drop(tx);

        // Collect results
        for handle in handles {
            if let Err(e) = handle.await {
                warn!("Rule check task failed: {}", e);
            }
        }

        while let Some((rule_id, finding)) = rx.recv().await {
            if let Some(f) = finding {
                info!("Rule {} failed", rule_id);
                findings.push(f);
            } else {
                debug!("Rule {} passed", rule_id);
            }
        }

        let scan_completed = Utc::now();

        // Build summary
        let mut summary = ScanSummary {
            total_rules: rules_checked.len(),
            passed: rules_checked.len() - findings.len(),
            failed: findings.len(),
            skipped: rules_skipped.len(),
            by_severity: HashMap::new(),
        };

        for finding in &findings {
            let key = finding.severity.to_string();
            *summary.by_severity.entry(key).or_insert(0) += 1;
        }

        let result = ScanResult {
            project_name,
            project_path: path.to_path_buf(),
            scan_started,
            scan_completed,
            findings,
            rules_checked,
            rules_skipped,
            summary,
        };

        info!(
            "Async scan completed for {}: {} passed, {} failed",
            result.project_name, result.summary.passed, result.summary.failed
        );

        Ok(result)
    }

    /// Scan multiple projects concurrently
    pub async fn scan_projects_async(
        &self,
        project_paths: &[impl AsRef<Path> + Send + Sync],
    ) -> Vec<Result<ScanResult, ComplianceError>> {
        let mut results = Vec::with_capacity(project_paths.len());

        for path in project_paths {
            results.push(self.scan_async(path).await);
        }

        results
    }

    /// Scan multiple projects in parallel (truly concurrent)
    pub async fn scan_projects_parallel(
        &self,
        project_paths: &[impl AsRef<Path> + Send + Sync + Clone],
    ) -> Vec<Result<ScanResult, ComplianceError>> {
        let semaphore = Arc::new(Semaphore::new(self.max_concurrent));
        let mut handles = Vec::with_capacity(project_paths.len());

        for path in project_paths {
            let permit = semaphore.clone().acquire_owned().await.unwrap();
            let scanner = AsyncComplianceScanner {
                rules: self.rules.clone(),
                enabled_rules: self.enabled_rules.clone(),
                max_concurrent: self.max_concurrent,
            };
            let path = path.as_ref().to_path_buf();

            let handle: JoinHandle<Result<ScanResult, ComplianceError>> =
                tokio::spawn(async move {
                    let _permit = permit;
                    scanner.scan_async(path).await
                });

            handles.push(handle);
        }

        let mut results = Vec::with_capacity(handles.len());
        for handle in handles {
            match handle.await {
                Ok(result) => results.push(result),
                Err(e) => {
                    results.push(Err(ComplianceError::ScanFailed(e.to_string())));
                }
            }
        }

        results
    }
}

/// Check a single rule asynchronously
async fn check_rule_async(rule: &Rule, project_path: &Path) -> Option<Finding> {
    match rule.id.as_str() {
        "DOC-001" => check_readme_async(rule, project_path).await,
        "DOC-002" => check_license_async(rule, project_path).await,
        "GOV-001" => check_agents_md_async(rule, project_path).await,
        "GOV-002" => check_claude_md_async(rule, project_path).await,
        "DOC-003" => check_changelog_async(rule, project_path).await,
        "SEC-001" => check_secrets_async(rule, project_path).await,
        _ => None,
    }
}

/// Async check for README.md
async fn check_readme_async(rule: &Rule, path: &Path) -> Option<Finding> {
    let readme_md = path.join("README.md");
    let readme_txt = path.join("README.txt");

    let (md_exists, txt_exists) =
        tokio::join!(fs::try_exists(&readme_md), fs::try_exists(&readme_txt),);

    if !md_exists.unwrap_or(false) && !txt_exists.unwrap_or(false) {
        return Some(Finding {
            rule_id: rule.id.clone(),
            message: "README.md not found".to_string(),
            file_path: path.to_path_buf(),
            line: None,
            severity: rule.severity,
            detected_at: Utc::now(),
            suggestion: Some(rule.remediation.clone()),
        });
    }

    None
}

/// Async check for LICENSE file
async fn check_license_async(rule: &Rule, path: &Path) -> Option<Finding> {
    let license_files = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"];

    // Check all license files concurrently
    let checks: Vec<_> = license_files
        .iter()
        .map(|f| {
            let file_path = path.join(f);
            async move { fs::try_exists(&file_path).await.unwrap_or(false) }
        })
        .collect();

    let results: Vec<bool> = futures_util::future::join_all(checks).await;
    let has_license = results.iter().any(|&exists| exists);

    if !has_license {
        return Some(Finding {
            rule_id: rule.id.clone(),
            message: "LICENSE file not found".to_string(),
            file_path: path.to_path_buf(),
            line: None,
            severity: rule.severity,
            detected_at: Utc::now(),
            suggestion: Some(rule.remediation.clone()),
        });
    }

    None
}

/// Async check for AGENTS.md
async fn check_agents_md_async(rule: &Rule, path: &Path) -> Option<Finding> {
    let agents_md = path.join("AGENTS.md");

    if !fs::try_exists(&agents_md).await.unwrap_or(false) {
        return Some(Finding {
            rule_id: rule.id.clone(),
            message: "AGENTS.md not found".to_string(),
            file_path: path.to_path_buf(),
            line: None,
            severity: rule.severity,
            detected_at: Utc::now(),
            suggestion: Some(rule.remediation.clone()),
        });
    }

    None
}

/// Async check for CLAUDE.md
async fn check_claude_md_async(rule: &Rule, path: &Path) -> Option<Finding> {
    let claude_md = path.join("CLAUDE.md");

    if !fs::try_exists(&claude_md).await.unwrap_or(false) {
        return Some(Finding {
            rule_id: rule.id.clone(),
            message: "CLAUDE.md not found".to_string(),
            file_path: path.to_path_buf(),
            line: None,
            severity: rule.severity,
            detected_at: Utc::now(),
            suggestion: Some(rule.remediation.clone()),
        });
    }

    None
}

/// Async check for CHANGELOG
async fn check_changelog_async(rule: &Rule, path: &Path) -> Option<Finding> {
    let changelog_files = ["CHANGELOG.md", "CHANGELOG.txt", "HISTORY.md", "CHANGES.md"];

    // Check all changelog files concurrently
    let checks: Vec<_> = changelog_files
        .iter()
        .map(|f| {
            let file_path = path.join(f);
            async move { fs::try_exists(&file_path).await.unwrap_or(false) }
        })
        .collect();

    let results: Vec<bool> = futures_util::future::join_all(checks).await;
    let has_changelog = results.iter().any(|&exists| exists);

    if !has_changelog {
        return Some(Finding {
            rule_id: rule.id.clone(),
            message: "CHANGELOG not found".to_string(),
            file_path: path.to_path_buf(),
            line: None,
            severity: rule.severity,
            detected_at: Utc::now(),
            suggestion: Some(rule.remediation.clone()),
        });
    }

    None
}

/// Async basic secret detection
async fn check_secrets_async(_rule: &Rule, path: &Path) -> Option<Finding> {
    // This is a simplified check - in production you'd use proper secret scanning
    let patterns = [
        "password",
        "secret",
        "api_key",
        "apikey",
        "private_key",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ];

    // Try to read src directory
    let src_dir = path.join("src");
    if !fs::try_exists(&src_dir).await.unwrap_or(false) {
        return None;
    }

    let mut entries = match fs::read_dir(&src_dir).await {
        Ok(e) => e,
        Err(_) => return None,
    };

    while let Ok(Some(entry)) = entries.next_entry().await {
        if let Some(ext) = entry.path().extension() {
            if ["rs", "py", "js", "ts", "go"].contains(&ext.to_str().unwrap_or("")) {
                if let Ok(content) = fs::read_to_string(entry.path()).await {
                    for (line_num, line) in content.lines().enumerate() {
                        let lower = line.to_lowercase();
                        for pattern in &patterns {
                            if lower.contains(pattern)
                                && (lower.contains("=")
                                    || lower.contains(":")
                                    || lower.contains("\""))
                            {
                                return Some(Finding {
                                    rule_id: "SEC-001".to_string(),
                                    message: format!(
                                        "Potential secret keyword '{}' found",
                                        pattern
                                    ),
                                    file_path: entry.path(),
                                    line: Some(line_num + 1),
                                    severity: Severity::Medium,
                                    detected_at: Utc::now(),
                                    suggestion: Some(
                                        "Review this line for hardcoded secrets. Use environment variables if this is a secret.".to_string(),
                                    ),
                                });
                            }
                        }
                    }
                }
            }
        }
    }

    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[tokio::test]
    async fn test_async_scanner_new() {
        let scanner = AsyncComplianceScanner::new();
        assert!(!scanner.rules.is_empty());
    }

    #[tokio::test]
    async fn test_scan_async_empty_project() {
        let temp_dir = TempDir::new().unwrap();
        let project_dir = temp_dir.path().join("test-project");
        fs::create_dir(&project_dir).await.unwrap();

        let scanner = AsyncComplianceScanner::new();
        let result = scanner.scan_async(&project_dir).await.unwrap();

        // Should have findings since no required files exist
        assert!(!result.findings.is_empty());
    }

    #[tokio::test]
    async fn test_scan_async_passes() {
        let temp_dir = TempDir::new().unwrap();
        let project_dir = temp_dir.path().join("test-project");
        fs::create_dir(&project_dir).await.unwrap();
        fs::create_dir(project_dir.join("src")).await.unwrap();

        // Create required files
        fs::write(project_dir.join("README.md"), "# Test")
            .await
            .unwrap();
        fs::write(project_dir.join("LICENSE"), "MIT").await.unwrap();

        let scanner = AsyncComplianceScanner::new();
        let result = scanner.scan_async(&project_dir).await.unwrap();

        // Should not have critical findings
        assert!(result.critical_findings().is_empty());
    }
}
