//! Phenotype Project Registry
//!
//! Manages project discovery and metadata across the monorepo.
//!
//! # Features
//!
//! - `async-discovery`: Async project discovery with parallel scanning
//! - `cache`: In-memory caching with TTL
//! - `health-integration`: Integration with phenotype-health for health checks

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use thiserror::Error;
use tracing::{debug, info, warn};

#[cfg(feature = "async-discovery")]
pub mod async_ops;

#[cfg(feature = "cache")]
pub mod cache;

#[cfg(feature = "health-integration")]
pub mod health_integration;

/// Errors that can occur during project discovery
#[derive(Debug, Error)]
pub enum RegistryError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Invalid project structure: {0}")]
    InvalidStructure(String),
    #[error("Project not found: {0}")]
    NotFound(String),
}

/// Types of projects in the monorepo
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProjectType {
    RustLibrary,
    RustBinary,
    RustWorkspace,
    GoModule,
    GoBinary,
    PythonPackage,
    PythonApplication,
    TypeScriptLibrary,
    TypeScriptApplication,
    DotnetLibrary,
    DotnetApplication,
    Documentation,
    Mixed,
    Unknown,
}

impl std::fmt::Display for ProjectType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let name = match self {
            ProjectType::RustLibrary => "rust-lib",
            ProjectType::RustBinary => "rust-bin",
            ProjectType::RustWorkspace => "rust-workspace",
            ProjectType::GoModule => "go-mod",
            ProjectType::GoBinary => "go-bin",
            ProjectType::PythonPackage => "python-pkg",
            ProjectType::PythonApplication => "python-app",
            ProjectType::TypeScriptLibrary => "ts-lib",
            ProjectType::TypeScriptApplication => "ts-app",
            ProjectType::DotnetLibrary => "dotnet-lib",
            ProjectType::DotnetApplication => "dotnet-app",
            ProjectType::Documentation => "docs",
            ProjectType::Mixed => "mixed",
            ProjectType::Unknown => "unknown",
        };
        write!(f, "{}", name)
    }
}

/// Health check configuration for a project
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct HealthConfig {
    /// Whether health checks are enabled for this project
    pub enabled: bool,
    /// Health check endpoint path (if applicable)
    pub endpoint: Option<String>,
    /// Port to use for health checks
    pub port: Option<u16>,
    /// Custom health check command
    pub command: Option<String>,
    /// Expected health check timeout in seconds
    pub timeout_seconds: Option<u64>,
}

/// Metadata about a discovered project
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectMetadata {
    /// Project name (derived from directory)
    pub name: String,
    /// Full path to project root
    pub path: PathBuf,
    /// Detected project type
    pub project_type: ProjectType,
    /// Programming language(s) used
    pub languages: Vec<String>,
    /// Whether the project has a Cargo.toml
    pub has_cargo_toml: bool,
    /// Whether the project has a package.json
    pub has_package_json: bool,
    /// Whether the project has a go.mod
    pub has_go_mod: bool,
    /// Whether the project has a pyproject.toml or setup.py
    pub has_python_setup: bool,
    /// Whether the project has a .csproj file
    pub has_csproj: bool,
    /// Health check configuration
    #[serde(default)]
    pub health_config: HealthConfig,
    /// Additional metadata as key-value pairs
    #[serde(default)]
    pub extra: HashMap<String, String>,
}

impl ProjectMetadata {
    /// Create new project metadata
    pub fn new(name: impl Into<String>, path: impl Into<PathBuf>) -> Self {
        Self {
            name: name.into(),
            path: path.into(),
            project_type: ProjectType::Unknown,
            languages: Vec::new(),
            has_cargo_toml: false,
            has_package_json: false,
            has_go_mod: false,
            has_python_setup: false,
            has_csproj: false,
            health_config: HealthConfig::default(),
            extra: HashMap::new(),
        }
    }

    /// Check if this is a Rust project
    pub fn is_rust(&self) -> bool {
        matches!(
            self.project_type,
            ProjectType::RustLibrary | ProjectType::RustBinary | ProjectType::RustWorkspace
        ) || self.has_cargo_toml
    }

    /// Check if this is a Go project
    pub fn is_go(&self) -> bool {
        matches!(
            self.project_type,
            ProjectType::GoModule | ProjectType::GoBinary
        ) || self.has_go_mod
    }

    /// Check if this is a Python project
    pub fn is_python(&self) -> bool {
        matches!(
            self.project_type,
            ProjectType::PythonPackage | ProjectType::PythonApplication
        ) || self.has_python_setup
    }

    /// Check if this is a TypeScript/JavaScript project
    pub fn is_typescript(&self) -> bool {
        matches!(
            self.project_type,
            ProjectType::TypeScriptLibrary | ProjectType::TypeScriptApplication
        ) || self.has_package_json
    }

    /// Check if this is a .NET project
    pub fn is_dotnet(&self) -> bool {
        matches!(
            self.project_type,
            ProjectType::DotnetLibrary | ProjectType::DotnetApplication
        ) || self.has_csproj
    }
}

/// Registry for managing projects
#[derive(Debug, Default)]
pub struct ProjectRegistry {
    projects: HashMap<String, ProjectMetadata>,
}

impl ProjectRegistry {
    /// Create a new empty registry
    pub fn new() -> Self {
        Self {
            projects: HashMap::new(),
        }
    }

    /// Register a project
    pub fn register(&mut self, project: ProjectMetadata) {
        debug!("Registering project: {}", project.name);
        self.projects.insert(project.name.clone(), project);
    }

    /// Get a project by name
    pub fn get(&self, name: &str) -> Option<&ProjectMetadata> {
        self.projects.get(name)
    }

    /// Get all registered projects
    pub fn all(&self) -> Vec<&ProjectMetadata> {
        self.projects.values().collect()
    }

    /// Get projects filtered by type
    pub fn by_type(&self, project_type: ProjectType) -> Vec<&ProjectMetadata> {
        self.projects
            .values()
            .filter(|p| p.project_type == project_type)
            .collect()
    }

    /// Get projects by language
    pub fn by_language(&self, language: &str) -> Vec<&ProjectMetadata> {
        self.projects
            .values()
            .filter(|p| p.languages.contains(&language.to_string()))
            .collect()
    }

    /// Count total projects
    pub fn count(&self) -> usize {
        self.projects.len()
    }

    /// Check if a project is registered
    pub fn contains(&self, name: &str) -> bool {
        self.projects.contains_key(name)
    }
}

/// Discover projects in a directory
pub fn discover_projects(root: impl AsRef<Path>) -> Result<Vec<ProjectMetadata>, RegistryError> {
    let root = root.as_ref();
    info!("Discovering projects in: {}", root.display());

    let mut projects = Vec::new();
    let entries = std::fs::read_dir(root)?;

    for entry in entries {
        let entry = entry?;
        let path = entry.path();

        if !path.is_dir() {
            continue;
        }

        // Skip hidden directories
        if path
            .file_name()
            .and_then(|n| n.to_str())
            .map(|n| n.starts_with('.'))
            .unwrap_or(false)
        {
            continue;
        }

        // Skip excluded directories (common non-project dirs)
        let dir_name = path.file_name().and_then(|n| n.to_str()).unwrap_or("");
        if ["target", "node_modules", "dist", "build", "crates", "docs"].contains(&dir_name) {
            continue;
        }

        match analyze_project(&path) {
            Some(project) => {
                info!("Found project: {} at {:?}", project.name, project.path);
                projects.push(project);
            }
            None => {
                debug!("Skipping non-project directory: {}", path.display());
            }
        }
    }

    info!("Discovered {} projects", projects.len());
    Ok(projects)
}

/// Analyze a directory to determine if it's a project
fn analyze_project(path: &Path) -> Option<ProjectMetadata> {
    let name = path.file_name()?.to_str()?.to_string();

    let mut project = ProjectMetadata::new(&name, path);
    let mut detected_type = None;

    // Check for various project files
    let cargo_toml = path.join("Cargo.toml");
    let package_json = path.join("package.json");
    let go_mod = path.join("go.mod");
    let pyproject = path.join("pyproject.toml");
    let setup_py = path.join("setup.py");
    let requirements = path.join("requirements.txt");

    // Find .csproj files
    let has_csproj = std::fs::read_dir(path)
        .ok()?
        .filter_map(|e| e.ok())
        .any(|e| e.path().extension().map(|e| e == "csproj").unwrap_or(false));

    // Check for Cargo.toml
    if cargo_toml.exists() {
        project.has_cargo_toml = true;
        project.languages.push("rust".to_string());

        // Try to determine if it's a workspace or library/binary
        if let Ok(content) = std::fs::read_to_string(&cargo_toml) {
            if content.contains("[workspace]") {
                detected_type = Some(ProjectType::RustWorkspace);
            } else if content.contains("[[bin]]") {
                detected_type = Some(ProjectType::RustBinary);
            } else {
                detected_type = Some(ProjectType::RustLibrary);
            }
        }
    }

    // Check for package.json
    if package_json.exists() {
        project.has_package_json = true;
        project.languages.push("typescript".to_string());

        if let Ok(content) = std::fs::read_to_string(&package_json) {
            if content.contains("\"main\"") || content.contains("\"module\"") {
                detected_type = Some(ProjectType::TypeScriptLibrary);
            } else if content.contains("\"bin\"") {
                detected_type = Some(ProjectType::TypeScriptApplication);
            }
        }
    }

    // Check for Go module
    if go_mod.exists() {
        project.has_go_mod = true;
        project.languages.push("go".to_string());

        // Check for main package to determine if binary
        let main_go = path.join("main.go");
        if main_go.exists() {
            detected_type = Some(ProjectType::GoBinary);
        } else {
            detected_type = Some(ProjectType::GoModule);
        }
    }

    // Check for Python project
    if pyproject.exists() || setup_py.exists() || requirements.exists() {
        project.has_python_setup = true;
        project.languages.push("python".to_string());

        if pyproject.exists() {
            if let Ok(content) = std::fs::read_to_string(&pyproject) {
                if content.contains("[project.scripts]")
                    || content.contains("[tool.poetry.scripts]")
                {
                    detected_type = Some(ProjectType::PythonApplication);
                } else {
                    detected_type = Some(ProjectType::PythonPackage);
                }
            }
        } else if setup_py.exists() {
            detected_type = Some(ProjectType::PythonPackage);
        }
    }

    // Check for .NET project
    if has_csproj {
        project.has_csproj = true;
        project.languages.push("csharp".to_string());
        detected_type = Some(ProjectType::DotnetLibrary);

        // Try to determine if it's an application
        for entry in std::fs::read_dir(path).ok()? {
            if let Ok(entry) = entry {
                if entry
                    .path()
                    .extension()
                    .map(|e| e == "csproj")
                    .unwrap_or(false)
                {
                    if let Ok(content) = std::fs::read_to_string(entry.path()) {
                        if content.contains("<OutputType>Exe</OutputType>") {
                            detected_type = Some(ProjectType::DotnetApplication);
                            break;
                        }
                    }
                }
            }
        }
    }

    // Check for documentation-only projects
    let readme = path.join("README.md");
    let has_docs_only = readme.exists()
        && !project.has_cargo_toml
        && !project.has_package_json
        && !project.has_go_mod
        && !project.has_python_setup
        && !project.has_csproj;

    if has_docs_only {
        project.languages.push("markdown".to_string());
        detected_type = Some(ProjectType::Documentation);
    }

    // Set the detected type
    if let Some(pt) = detected_type {
        project.project_type = pt;
    } else if project.languages.len() > 1 {
        project.project_type = ProjectType::Mixed;
    }

    // Only return if we found at least one indicator
    if project.languages.is_empty() && project.project_type == ProjectType::Unknown {
        // Check if it has a src directory as last resort
        let src_dir = path.join("src");
        if src_dir.exists() {
            warn!(
                "Directory {} has src/ but no recognized project files",
                name
            );
            return Some(project);
        }
        return None;
    }

    Some(project)
}

/// Discover health configurations for projects
pub fn discover_health_configs(projects: &[ProjectMetadata]) -> HashMap<String, HealthConfig> {
    let mut configs = HashMap::new();

    for project in projects {
        let config = detect_health_config(project);
        configs.insert(project.name.clone(), config);
    }

    configs
}

/// Detect health configuration for a single project
fn detect_health_config(project: &ProjectMetadata) -> HealthConfig {
    let mut config = HealthConfig::default();

    // Only enable health checks for certain project types
    config.enabled = match project.project_type {
        ProjectType::RustBinary
        | ProjectType::TypeScriptApplication
        | ProjectType::PythonApplication
        | ProjectType::DotnetApplication
        | ProjectType::GoBinary => true,
        _ => false,
    };

    // Default ports based on project type
    if config.enabled {
        config.port = Some(match project.project_type {
            ProjectType::RustBinary => 8080,
            ProjectType::TypeScriptApplication => 3000,
            ProjectType::PythonApplication => 5000,
            ProjectType::DotnetApplication => 5001,
            ProjectType::GoBinary => 8000,
            _ => 8080,
        });

        config.endpoint = Some("/health".to_string());
        config.timeout_seconds = Some(5);
    }

    // Check for custom health.yaml or .health/config
    let health_yaml = project.path.join("health.yaml");
    let health_yml = project.path.join("health.yml");
    let dothealth = project.path.join(".health").join("config");

    if health_yaml.exists() || health_yml.exists() || dothealth.exists() {
        // Try to parse custom config
        let config_file = if health_yaml.exists() {
            health_yaml
        } else if health_yml.exists() {
            health_yml
        } else {
            dothealth
        };

        if let Ok(content) = std::fs::read_to_string(&config_file) {
            if let Ok(parsed) = serde_yaml::from_str::<HealthConfig>(&content) {
                config = parsed;
            }
        }
    }

    config
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::TempDir;

    #[test]
    fn test_project_type_display() {
        assert_eq!(ProjectType::RustLibrary.to_string(), "rust-lib");
        assert_eq!(ProjectType::GoBinary.to_string(), "go-bin");
        assert_eq!(ProjectType::Documentation.to_string(), "docs");
    }

    #[test]
    fn test_project_metadata_is_rust() {
        let mut project = ProjectMetadata::new("test", "/tmp/test");
        project.has_cargo_toml = true;
        assert!(project.is_rust());
    }

    #[test]
    fn test_registry_register_and_get() {
        let mut registry = ProjectRegistry::new();
        let project = ProjectMetadata::new("test-project", "/tmp/test");

        registry.register(project.clone());
        assert_eq!(registry.count(), 1);
        assert!(registry.contains("test-project"));
        assert!(registry.get("test-project").is_some());
    }

    #[test]
    fn test_registry_by_type() {
        let mut registry = ProjectRegistry::new();

        let mut project1 = ProjectMetadata::new("rust-lib", "/tmp/rust-lib");
        project1.project_type = ProjectType::RustLibrary;

        let mut project2 = ProjectMetadata::new("go-bin", "/tmp/go-bin");
        project2.project_type = ProjectType::GoBinary;

        registry.register(project1);
        registry.register(project2);

        let rust_projects = registry.by_type(ProjectType::RustLibrary);
        assert_eq!(rust_projects.len(), 1);
        assert_eq!(rust_projects[0].name, "rust-lib");
    }

    #[test]
    fn test_analyze_rust_project() {
        let temp_dir = TempDir::new().unwrap();
        let project_dir = temp_dir.path().join("my-rust-project");
        std::fs::create_dir(&project_dir).unwrap();

        // Create a Cargo.toml
        let cargo_toml = project_dir.join("Cargo.toml");
        let mut file = std::fs::File::create(&cargo_toml).unwrap();
        writeln!(file, "[package]").unwrap();
        writeln!(file, "name = \"my-rust-project\"").unwrap();
        writeln!(file, "version = \"0.1.0\"").unwrap();

        let result = analyze_project(&project_dir);
        assert!(result.is_some());

        let project = result.unwrap();
        assert_eq!(project.name, "my-rust-project");
        assert!(project.is_rust());
        assert!(project.has_cargo_toml);
    }
}
