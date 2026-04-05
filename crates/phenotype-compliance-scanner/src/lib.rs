//! Phenotype Compliance Scanner
//!
//! Scans projects for documentation and governance compliance.
//!
//! # Features
//!
//! - `async-scan`: Async parallel scanning capabilities
//! - `health-integration`: Integration with phenotype-health for health monitoring

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use thiserror::Error;
use tracing::{debug, info, warn};

#[cfg(feature = "async-scan")]
pub mod async_scan;

#[cfg(feature = "health-integration")]
pub mod health_integration;

/// Compliance scanning errors
#[derive(Debug, Error)]
pub enum ComplianceError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Scan failed: {0}")]
    ScanFailed(String),
}

/// Severity levels for compliance findings
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum Severity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

impl std::fmt::Display for Severity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Severity::Critical => write!(f, "CRITICAL"),
            Severity::High => write!(f, "HIGH"),
            Severity::Medium => write!(f, "MEDIUM"),
            Severity::Low => write!(f, "LOW"),
            Severity::Info => write!(f, "INFO"),
        }
    }
}

/// Compliance rule categories
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RuleCategory {
    Documentation,
    Governance,
    Security,
    Quality,
    Legal,
}

impl std::fmt::Display for RuleCategory {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RuleCategory::Documentation => write!(f, "documentation"),
            RuleCategory::Governance => write!(f, "governance"),
            RuleCategory::Security => write!(f, "security"),
            RuleCategory::Quality => write!(f, "quality"),
            RuleCategory::Legal => write!(f, "legal"),
        }
    }
}

/// A compliance rule definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Rule {
    /// Unique rule identifier
    pub id: String,
    /// Short rule name
    pub name: String,
    /// Full rule description
    pub description: String,
    /// Rule category
    pub category: RuleCategory,
    /// Default severity if violated
    pub severity: Severity,
    /// Whether this rule is required (cannot be disabled)
    pub required: bool,
    /// Files/patterns this rule applies to
    pub applies_to: Vec<String>,
    /// Help text for fixing violations
    pub remediation: String,
}

/// A single compliance finding
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Finding {
    /// Rule that was violated
    pub rule_id: String,
    /// Human-readable message
    pub message: String,
    /// File path where violation was found
    pub file_path: PathBuf,
    /// Line number if applicable
    pub line: Option<usize>,
    /// Severity of this finding
    pub severity: Severity,
    /// When the finding was detected
    pub detected_at: DateTime<Utc>,
    /// Suggested fix
    pub suggestion: Option<String>,
}

/// Compliance scan results for a project
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanResult {
    /// Project name
    pub project_name: String,
    /// Project path
    pub project_path: PathBuf,
    /// When the scan started
    pub scan_started: DateTime<Utc>,
    /// When the scan completed
    pub scan_completed: DateTime<Utc>,
    /// All findings
    pub findings: Vec<Finding>,
    /// Rules that were checked
    pub rules_checked: Vec<String>,
    /// Rules that were skipped
    pub rules_skipped: Vec<String>,
    /// Summary statistics
    pub summary: ScanSummary,
}

/// Scan summary statistics
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ScanSummary {
    /// Total rules checked
    pub total_rules: usize,
    /// Rules that passed
    pub passed: usize,
    /// Rules that failed
    pub failed: usize,
    /// Rules that were skipped
    pub skipped: usize,
    /// Findings by severity
    pub by_severity: HashMap<String, usize>,
}

impl ScanResult {
    /// Check if the scan passed (no critical or high findings)
    pub fn passed(&self) -> bool {
        !self
            .findings
            .iter()
            .any(|f| matches!(f.severity, Severity::Critical | Severity::High))
    }

    /// Get count of findings by severity
    pub fn count_by_severity(&self, severity: Severity) -> usize {
        self.findings
            .iter()
            .filter(|f| f.severity == severity)
            .count()
    }

    /// Get critical findings
    pub fn critical_findings(&self) -> Vec<&Finding> {
        self.findings
            .iter()
            .filter(|f| f.severity == Severity::Critical)
            .collect()
    }

    /// Get high severity findings
    pub fn high_findings(&self) -> Vec<&Finding> {
        self.findings
            .iter()
            .filter(|f| f.severity == Severity::High)
            .collect()
    }
}

/// Predefined compliance rules
pub fn standard_rules() -> Vec<Rule> {
    vec![
        Rule {
            id: "DOC-001".to_string(),
            name: "README Required".to_string(),
            description: "Project must have a README.md file".to_string(),
            category: RuleCategory::Documentation,
            severity: Severity::High,
            required: true,
            applies_to: vec!["*".to_string()],
            remediation:
                "Create a README.md with project description, usage, and contribution guidelines"
                    .to_string(),
        },
        Rule {
            id: "DOC-002".to_string(),
            name: "LICENSE Required".to_string(),
            description: "Project must have a LICENSE file".to_string(),
            category: RuleCategory::Legal,
            severity: Severity::Critical,
            required: true,
            applies_to: vec!["*".to_string()],
            remediation: "Add a LICENSE file (MIT, Apache-2.0, or other appropriate license)"
                .to_string(),
        },
        Rule {
            id: "GOV-001".to_string(),
            name: "AGENTS.md Required".to_string(),
            description: "Project must have an AGENTS.md file for agent guidance".to_string(),
            category: RuleCategory::Governance,
            severity: Severity::Medium,
            required: false,
            applies_to: vec!["*".to_string()],
            remediation: "Create AGENTS.md with agent-specific instructions and context"
                .to_string(),
        },
        Rule {
            id: "GOV-002".to_string(),
            name: "CLAUDE.md Required".to_string(),
            description: "Project should have a CLAUDE.md file for Claude AI guidance".to_string(),
            category: RuleCategory::Governance,
            severity: Severity::Low,
            required: false,
            applies_to: vec!["*".to_string()],
            remediation: "Create CLAUDE.md with project overview for Claude AI".to_string(),
        },
        Rule {
            id: "DOC-003".to_string(),
            name: "CHANGELOG Recommended".to_string(),
            description: "Project should maintain a CHANGELOG".to_string(),
            category: RuleCategory::Documentation,
            severity: Severity::Low,
            required: false,
            applies_to: vec!["*".to_string()],
            remediation: "Create CHANGELOG.md following Keep a Changelog format".to_string(),
        },
        Rule {
            id: "SEC-001".to_string(),
            name: "No Secrets in Code".to_string(),
            description: "Source code should not contain hardcoded secrets".to_string(),
            category: RuleCategory::Security,
            severity: Severity::Critical,
            required: true,
            applies_to: vec![
                "*.rs".to_string(),
                "*.py".to_string(),
                "*.js".to_string(),
                "*.ts".to_string(),
            ],
            remediation: "Use environment variables or a secrets manager for sensitive data"
                .to_string(),
        },
    ]
}

/// Scanner for compliance checks
#[derive(Debug)]
pub struct ComplianceScanner {
    rules: Vec<Rule>,
    enabled_rules: Vec<String>,
}

impl Default for ComplianceScanner {
    fn default() -> Self {
        let rules = standard_rules();
        let enabled_rules = rules.iter().map(|r| r.id.clone()).collect();

        Self {
            rules,
            enabled_rules,
        }
    }
}

impl ComplianceScanner {
    /// Create a new scanner with default rules
    pub fn new() -> Self {
        Self::default()
    }

    /// Create a scanner with custom rules
    pub fn with_rules(rules: Vec<Rule>) -> Self {
        let enabled_rules = rules.iter().map(|r| r.id.clone()).collect();
        Self {
            rules,
            enabled_rules,
        }
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

    /// Scan a project directory
    pub fn scan(&self, project_path: impl AsRef<Path>) -> Result<ScanResult, ComplianceError> {
        let path = project_path.as_ref();
        let project_name = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown")
            .to_string();

        info!("Starting compliance scan for: {}", project_name);

        let scan_started = Utc::now();
        let mut findings = Vec::new();
        let mut rules_checked = Vec::new();
        let mut rules_skipped = Vec::new();

        for rule in &self.rules {
            if !self.enabled_rules.contains(&rule.id) {
                rules_skipped.push(rule.id.clone());
                continue;
            }

            rules_checked.push(rule.id.clone());

            match check_rule(rule, path) {
                Ok(Some(finding)) => {
                    info!("Rule {} failed for {}", rule.id, project_name);
                    findings.push(finding);
                }
                Ok(None) => {
                    debug!("Rule {} passed for {}", rule.id, project_name);
                }
                Err(e) => {
                    warn!("Error checking rule {}: {}", rule.id, e);
                }
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
            "Scan completed for {}: {} passed, {} failed",
            result.project_name, result.summary.passed, result.summary.failed
        );

        Ok(result)
    }

    /// Scan multiple projects
    pub fn scan_projects(
        &self,
        project_paths: &[impl AsRef<Path>],
    ) -> Vec<Result<ScanResult, ComplianceError>> {
        project_paths.iter().map(|p| self.scan(p)).collect()
    }
}

/// Check a single rule against a project
fn check_rule(rule: &Rule, project_path: &Path) -> Result<Option<Finding>, ComplianceError> {
    match rule.id.as_str() {
        "DOC-001" => check_readme(rule, project_path),
        "DOC-002" => check_license(rule, project_path),
        "GOV-001" => check_agents_md(rule, project_path),
        "GOV-002" => check_claude_md(rule, project_path),
        "DOC-003" => check_changelog(rule, project_path),
        "SEC-001" => check_secrets(rule, project_path),
        _ => Ok(None),
    }
}

/// Check for README.md
fn check_readme(rule: &Rule, path: &Path) -> Result<Option<Finding>, ComplianceError> {
    let readme_md = path.join("README.md");
    let readme_txt = path.join("README.txt");

    if !readme_md.exists() && !readme_txt.exists() {
        return Ok(Some(Finding {
            rule_id: rule.id.clone(),
            message: "README.md not found".to_string(),
            file_path: path.to_path_buf(),
            line: None,
            severity: rule.severity,
            detected_at: Utc::now(),
            suggestion: Some(rule.remediation.clone()),
        }));
    }

    Ok(None)
}

/// Check for LICENSE file
fn check_license(rule: &Rule, path: &Path) -> Result<Option<Finding>, ComplianceError> {
    let license_files = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"];

    let has_license = license_files.iter().any(|f| path.join(f).exists());

    if !has_license {
        return Ok(Some(Finding {
            rule_id: rule.id.clone(),
            message: "LICENSE file not found".to_string(),
            file_path: path.to_path_buf(),
            line: None,
            severity: rule.severity,
            detected_at: Utc::now(),
            suggestion: Some(rule.remediation.clone()),
        }));
    }

    Ok(None)
}

/// Check for AGENTS.md
fn check_agents_md(rule: &Rule, path: &Path) -> Result<Option<Finding>, ComplianceError> {
    let agents_md = path.join("AGENTS.md");

    if !agents_md.exists() {
        return Ok(Some(Finding {
            rule_id: rule.id.clone(),
            message: "AGENTS.md not found".to_string(),
            file_path: path.to_path_buf(),
            line: None,
            severity: rule.severity,
            detected_at: Utc::now(),
            suggestion: Some(rule.remediation.clone()),
        }));
    }

    Ok(None)
}

/// Check for CLAUDE.md
fn check_claude_md(rule: &Rule, path: &Path) -> Result<Option<Finding>, ComplianceError> {
    let claude_md = path.join("CLAUDE.md");

    if !claude_md.exists() {
        return Ok(Some(Finding {
            rule_id: rule.id.clone(),
            message: "CLAUDE.md not found".to_string(),
            file_path: path.to_path_buf(),
            line: None,
            severity: rule.severity,
            detected_at: Utc::now(),
            suggestion: Some(rule.remediation.clone()),
        }));
    }

    Ok(None)
}

/// Check for CHANGELOG
fn check_changelog(rule: &Rule, path: &Path) -> Result<Option<Finding>, ComplianceError> {
    let changelog_files = ["CHANGELOG.md", "CHANGELOG.txt", "HISTORY.md", "CHANGES.md"];

    let has_changelog = changelog_files.iter().any(|f| path.join(f).exists());

    if !has_changelog {
        return Ok(Some(Finding {
            rule_id: rule.id.clone(),
            message: "CHANGELOG not found".to_string(),
            file_path: path.to_path_buf(),
            line: None,
            severity: rule.severity,
            detected_at: Utc::now(),
            suggestion: Some(rule.remediation.clone()),
        }));
    }

    Ok(None)
}

/// Basic secret detection (simplified)
fn check_secrets(_rule: &Rule, path: &Path) -> Result<Option<Finding>, ComplianceError> {
    // This is a simplified check - in production you'd use proper secret scanning
    // like git-secrets, detect-secrets, or trufflehog

    let patterns = [
        "password",
        "secret",
        "api_key",
        "apikey",
        "private_key",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ];

    for pattern in &patterns {
        // Walk the project looking for source files
        if let Ok(entries) = std::fs::read_dir(path.join("src")) {
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ["rs", "py", "js", "ts", "go"].contains(&ext.to_str().unwrap_or("")) {
                        if let Ok(content) = std::fs::read_to_string(entry.path()) {
                            for (line_num, line) in content.lines().enumerate() {
                                let lower = line.to_lowercase();
                                if lower.contains(pattern)
                                    && (lower.contains("=")
                                        || lower.contains(":")
                                        || lower.contains("\""))
                                {
                                    // Potential secret - flag for review
                                    return Ok(Some(Finding {
                                        rule_id: "SEC-001".to_string(),
                                        message: format!(
                                            "Potential secret keyword '{}' found",
                                            pattern
                                        ),
                                        file_path: entry.path(),
                                        line: Some(line_num + 1),
                                        severity: Severity::Medium, // Downgrade from critical for false positives
                                        detected_at: Utc::now(),
                                        suggestion: Some(
                                            "Review this line for hardcoded secrets. Use environment variables if this is a secret.".to_string(),
                                        ),
                                    }));
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Ok(None)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_standard_rules_count() {
        let rules = standard_rules();
        assert!(!rules.is_empty());
    }

    #[test]
    fn test_compliance_scanner_new() {
        let scanner = ComplianceScanner::new();
        assert!(!scanner.rules.is_empty());
    }

    #[test]
    fn test_scan_with_no_readme() {
        let temp_dir = TempDir::new().unwrap();
        let project_dir = temp_dir.path().join("test-project");
        std::fs::create_dir(&project_dir).unwrap();

        // Create only LICENSE, not README
        let license_file = project_dir.join("LICENSE");
        std::fs::File::create(&license_file).unwrap();

        let scanner = ComplianceScanner::new();
        let result = scanner.scan(&project_dir).unwrap();

        // Should have at least one finding (missing README)
        assert!(!result.passed());
        assert!(result.findings.iter().any(|f| f.rule_id == "DOC-001"));
    }

    #[test]
    fn test_scan_passes_with_all_files() {
        let temp_dir = TempDir::new().unwrap();
        let project_dir = temp_dir.path().join("test-project");
        std::fs::create_dir(&project_dir).unwrap();

        // Create all required files
        std::fs::File::create(project_dir.join("README.md")).unwrap();
        std::fs::File::create(project_dir.join("LICENSE")).unwrap();

        let scanner = ComplianceScanner::new();
        let result = scanner.scan(&project_dir).unwrap();

        // Should not have critical or high findings
        assert!(result.critical_findings().is_empty());
        assert!(result.high_findings().is_empty());
    }

    #[test]
    fn test_scan_summary() {
        let summary = ScanSummary {
            total_rules: 5,
            passed: 3,
            failed: 2,
            skipped: 0,
            by_severity: HashMap::new(),
        };

        assert_eq!(summary.total_rules, 5);
        assert_eq!(summary.passed, 3);
        assert_eq!(summary.failed, 2);
    }
}
