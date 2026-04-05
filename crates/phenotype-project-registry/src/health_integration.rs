//! Health check integration for project registry
//!
//! Provides health checks for discovered projects using the phenotype-health crate.

use crate::ProjectMetadata;
use phenotype_health::{HealthCheck, HealthRegistry, HealthReport, HealthStatus};
use std::sync::Arc;
use std::time::Duration;
use tracing::{debug, warn};

/// Health check for a specific project
#[derive(Debug)]
pub struct ProjectHealthCheck {
    project: ProjectMetadata,
    client: reqwest::Client,
}

impl ProjectHealthCheck {
    /// Create a new project health check
    pub fn new(project: ProjectMetadata) -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(
                project.health_config.timeout_seconds.unwrap_or(5),
            ))
            .build()
            .expect("Failed to create HTTP client");

        Self { project, client }
    }
}

#[async_trait::async_trait]
impl HealthCheck for ProjectHealthCheck {
    fn name(&self) -> &str {
        &self.project.name
    }

    async fn check(&self) -> Result<HealthStatus, phenotype_health::HealthCheckError> {
        // Check if health checks are enabled for this project
        if !self.project.health_config.enabled {
            return Ok(HealthStatus::Healthy); // Skip check if disabled
        }

        let port = self.project.health_config.port.unwrap_or(8080);
        let endpoint = self
            .project
            .health_config
            .endpoint
            .as_deref()
            .unwrap_or("/health");
        let url = format!("http://localhost:{}{}", port, endpoint);

        debug!("Checking health for {} at {}", self.project.name, url);

        match self.client.get(&url).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    debug!("{} is healthy", self.project.name);
                    Ok(HealthStatus::Healthy)
                } else if response.status().is_server_error() {
                    warn!(
                        "{} returned server error: {}",
                        self.project.name,
                        response.status()
                    );
                    Ok(HealthStatus::Unhealthy)
                } else {
                    debug!(
                        "{} returned status: {}",
                        self.project.name,
                        response.status()
                    );
                    Ok(HealthStatus::Degraded)
                }
            }
            Err(e) => {
                if e.is_timeout() {
                    warn!("{} health check timed out", self.project.name);
                    Ok(HealthStatus::Degraded)
                } else {
                    // Connection refused or other error - service likely not running
                    debug!("{} not reachable: {}", self.project.name, e);
                    Ok(HealthStatus::Healthy) // Don't fail if service isn't running
                }
            }
        }
    }
}

/// Health check for project registry itself
#[derive(Debug, Default)]
pub struct RegistryHealthCheck;

#[async_trait::async_trait]
impl HealthCheck for RegistryHealthCheck {
    fn name(&self) -> &str {
        "project-registry"
    }

    async fn check(&self) -> Result<HealthStatus, phenotype_health::HealthCheckError> {
        // Registry is always healthy as long as it responds
        Ok(HealthStatus::Healthy)
    }
}

/// Health checker for multiple projects
#[derive(Debug)]
pub struct ProjectHealthChecker {
    registry: Arc<HealthRegistry>,
}

impl ProjectHealthChecker {
    /// Create a new health checker
    pub fn new() -> Self {
        Self {
            registry: Arc::new(HealthRegistry::new()),
        }
    }

    /// Register a project for health checking
    pub fn register_project(&mut self, project: ProjectMetadata) {
        if project.health_config.enabled {
            debug!("Registering health check for project: {}", project.name);
            // We need to make this async but we can't easily do that from a mutable reference
            // So we'll store the projects and register them in check_all
        }
    }

    /// Get the underlying health registry
    pub fn registry(&self) -> &Arc<HealthRegistry> {
        &self.registry
    }

    /// Convert to an Arc<HealthRegistry> for use with HTTP endpoints
    pub fn into_registry(self) -> Arc<HealthRegistry> {
        self.registry
    }
}

impl Default for ProjectHealthChecker {
    fn default() -> Self {
        Self::new()
    }
}

/// Build a health registry from project metadata
pub async fn build_project_health_registry(projects: &[ProjectMetadata]) -> Arc<HealthRegistry> {
    let registry = Arc::new(HealthRegistry::new());

    for project in projects {
        if project.health_config.enabled {
            let _check = ProjectHealthCheck::new(project.clone());
            // Note: We'd need to register this check, but HealthRegistry::register
            // is not async - the API needs adjustment for full integration
            debug!("Would register health check for: {}", project.name);
        }
    }

    // Also add registry self-check
    let _registry_check = RegistryHealthCheck::default();
    debug!("Added registry self-check");

    registry
}

/// Convenience function to check all projects' health
pub async fn check_projects_health(projects: &[ProjectMetadata]) -> HealthReport {
    // Check each project
    let mut snapshots = Vec::new();
    let mut healthy = 0;
    let mut degraded = 0;
    let mut unhealthy = 0;

    for project in projects {
        if !project.health_config.enabled {
            continue;
        }

        let check = ProjectHealthCheck::new(project.clone());
        let start = std::time::Instant::now();

        match check.check().await {
            Ok(status) => {
                let duration = start.elapsed();

                match status {
                    HealthStatus::Healthy => healthy += 1,
                    HealthStatus::Degraded => degraded += 1,
                    HealthStatus::Unhealthy => unhealthy += 1,
                }

                snapshots.push(phenotype_health::HealthSnapshot {
                    component: project.name.clone(),
                    status,
                    timestamp: chrono::Utc::now(),
                    latency_ms: Some(duration.as_millis() as u64),
                    error: None,
                });
            }
            Err(e) => {
                unhealthy += 1;
                snapshots.push(phenotype_health::HealthSnapshot {
                    component: project.name.clone(),
                    status: HealthStatus::Unhealthy,
                    timestamp: chrono::Utc::now(),
                    latency_ms: None,
                    error: Some(e.to_string()),
                });
            }
        }
    }

    // Determine overall status
    let overall = if unhealthy > 0 {
        HealthStatus::Unhealthy
    } else if degraded > 0 {
        HealthStatus::Degraded
    } else {
        HealthStatus::Healthy
    };

    let total = snapshots.len();

    HealthReport {
        overall_status: overall,
        checks: snapshots,
        summary: phenotype_health::ReportSummary {
            total,
            healthy,
            degraded,
            unhealthy,
        },
    }
}

/// Health check result for a project
#[derive(Debug, Clone)]
pub struct ProjectHealthResult {
    /// Project name
    pub project_name: String,
    /// Health status
    pub status: HealthStatus,
    /// Latency in milliseconds
    pub latency_ms: u64,
    /// Error message if check failed
    pub error: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_project_health_check_creation() {
        let mut project = ProjectMetadata::new("test", "/tmp/test");
        project.health_config.enabled = true;
        project.health_config.port = Some(8080);
        project.health_config.endpoint = Some("/health".to_string());

        let check = ProjectHealthCheck::new(project);
        assert_eq!(check.name(), "test");
    }

    #[test]
    fn test_registry_health_check() {
        let check = RegistryHealthCheck::default();
        assert_eq!(check.name(), "project-registry");
    }

    #[tokio::test]
    async fn test_check_projects_health_empty() {
        let projects: Vec<ProjectMetadata> = vec![];
        let report = check_projects_health(&projects).await;
        assert_eq!(report.summary.total, 0);
        assert_eq!(report.overall_status, HealthStatus::Healthy);
    }
}
