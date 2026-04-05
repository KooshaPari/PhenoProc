//! Async project discovery and operations
//!
//! Provides async variants of discovery functions with parallel scanning.

use crate::{HealthConfig, ProjectMetadata, RegistryError};
use std::path::Path;
use std::sync::Arc;
use tokio::fs;
use tokio::sync::Semaphore;
use tracing::{info, warn};

/// Maximum concurrent directory scans
const MAX_CONCURRENT_SCANS: usize = 10;

/// Discover projects asynchronously with parallel scanning
///
/// This is the async equivalent of `discover_projects` that scans
/// directories concurrently for better performance on large monorepos.
///
/// # Example
///
/// ```rust,no_run
/// use phenotype_project_registry::async_ops::discover_projects_async;
///
/// async fn scan() {
///     let projects = discover_projects_async("/path/to/repos").await.unwrap();
///     println!("Found {} projects", projects.len());
/// }
/// ```
pub async fn discover_projects_async(
    root: impl AsRef<Path>,
) -> Result<Vec<ProjectMetadata>, RegistryError> {
    let root = root.as_ref();
    info!("Starting async project discovery in: {}", root.display());

    let mut projects = Vec::new();
    let mut entries = fs::read_dir(root).await?;

    // Collect all directories first
    let mut dirs = Vec::new();
    while let Some(entry) = entries.next_entry().await? {
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

        // Skip excluded directories
        let dir_name = path.file_name().and_then(|n| n.to_str()).unwrap_or("");
        if ["target", "node_modules", "dist", "build", "crates", "docs"].contains(&dir_name) {
            continue;
        }

        dirs.push(path);
    }

    // Process directories concurrently with semaphore for backpressure
    let semaphore = Arc::new(Semaphore::new(MAX_CONCURRENT_SCANS));
    let mut handles = Vec::new();

    for dir in dirs {
        let permit = semaphore.clone().acquire_owned().await.unwrap();
        let handle = tokio::spawn(async move {
            let _permit = permit; // Hold permit until task completes
            analyze_project_async(&dir).await
        });
        handles.push(handle);
    }

    // Collect results
    for handle in handles {
        match handle.await {
            Ok(Some(project)) => {
                info!("Found project: {} at {:?}", project.name, project.path);
                projects.push(project);
            }
            Ok(None) => {}
            Err(e) => {
                warn!("Task failed: {}", e);
            }
        }
    }

    info!(
        "Async discovery completed: {} projects found",
        projects.len()
    );
    Ok(projects)
}

/// Analyze a directory to determine if it's a project (async version)
async fn analyze_project_async(path: &Path) -> Option<ProjectMetadata> {
    let name = path.file_name()?.to_str()?.to_string();

    let mut project = ProjectMetadata::new(&name, path);
    let mut detected_type = None;

    // Check for various project files asynchronously
    // Check files concurrently where possible
    let cargo_toml = path.join("Cargo.toml");
    let package_json = path.join("package.json");
    let go_mod = path.join("go.mod");
    let pyproject = path.join("pyproject.toml");
    let setup_py = path.join("setup.py");
    let requirements = path.join("requirements.txt");

    // Check files concurrently where possible
    let results = tokio::join!(
        fs::try_exists(&cargo_toml),
        fs::try_exists(&package_json),
        fs::try_exists(&go_mod),
        fs::try_exists(&pyproject),
        fs::try_exists(&setup_py),
        fs::try_exists(&requirements),
    );

    let cargo_exists = results.0.unwrap_or(false);
    let package_exists = results.1.unwrap_or(false);
    let go_exists = results.2.unwrap_or(false);
    let pyproject_exists = results.3.unwrap_or(false);
    let setup_exists = results.4.unwrap_or(false);
    let requirements_exists = results.5.unwrap_or(false);
    // Handle .csproj files
    let has_csproj = if let Ok(mut entries) = fs::read_dir(path).await {
        let mut found = false;
        while let Ok(Some(entry)) = entries.next_entry().await {
            if entry
                .path()
                .extension()
                .map(|e| e == "csproj")
                .unwrap_or(false)
            {
                found = true;
                break;
            }
        }
        found
    } else {
        false
    };

    // Check for Cargo.toml
    if cargo_exists {
        project.has_cargo_toml = true;
        project.languages.push("rust".to_string());

        // Try to determine if it's a workspace or library/binary
        if let Ok(content) = fs::read_to_string(&cargo_toml).await {
            if content.contains("[workspace]") {
                detected_type = Some(crate::ProjectType::RustWorkspace);
            } else if content.contains("[[bin]]") {
                detected_type = Some(crate::ProjectType::RustBinary);
            } else {
                detected_type = Some(crate::ProjectType::RustLibrary);
            }
        }
    }

    // Check for package.json
    if package_exists {
        project.has_package_json = true;
        project.languages.push("typescript".to_string());

        if let Ok(content) = fs::read_to_string(&package_json).await {
            if content.contains("\"main\"") || content.contains("\"module\"") {
                detected_type = Some(crate::ProjectType::TypeScriptLibrary);
            } else if content.contains("\"bin\"") {
                detected_type = Some(crate::ProjectType::TypeScriptApplication);
            }
        }
    }

    // Check for Go module
    if go_exists {
        project.has_go_mod = true;
        project.languages.push("go".to_string());

        // Check for main package
        let main_go = path.join("main.go");
        if fs::try_exists(&main_go).await.unwrap_or(false) {
            detected_type = Some(crate::ProjectType::GoBinary);
        } else {
            detected_type = Some(crate::ProjectType::GoModule);
        }
    }

    // Check for Python project
    let has_pyproject = pyproject_exists;
    let has_setup = setup_exists;
    let has_requirements = requirements_exists;

    if has_pyproject || has_setup || has_requirements {
        project.has_python_setup = true;
        project.languages.push("python".to_string());

        if has_pyproject {
            if let Ok(content) = fs::read_to_string(&pyproject).await {
                if content.contains("[project.scripts]")
                    || content.contains("[tool.poetry.scripts]")
                {
                    detected_type = Some(crate::ProjectType::PythonApplication);
                } else {
                    detected_type = Some(crate::ProjectType::PythonPackage);
                }
            }
        } else if has_setup {
            detected_type = Some(crate::ProjectType::PythonPackage);
        }
    }

    // Check for .NET project
    if has_csproj {
        project.has_csproj = true;
        project.languages.push("csharp".to_string());
        detected_type = Some(crate::ProjectType::DotnetLibrary);

        // Try to determine if it's an application
        if let Ok(mut entries) = fs::read_dir(path).await {
            while let Ok(Some(entry)) = entries.next_entry().await {
                if entry
                    .path()
                    .extension()
                    .map(|e| e == "csproj")
                    .unwrap_or(false)
                {
                    if let Ok(content) = fs::read_to_string(entry.path()).await {
                        if content.contains("<OutputType>Exe</OutputType>") {
                            detected_type = Some(crate::ProjectType::DotnetApplication);
                            break;
                        }
                    }
                }
            }
        }
    }

    // Check for documentation-only projects
    let readme = path.join("README.md");
    let readme_exists = fs::try_exists(&readme).await.unwrap_or(false);
    let has_docs_only = readme_exists
        && !project.has_cargo_toml
        && !project.has_package_json
        && !project.has_go_mod
        && !project.has_python_setup
        && !project.has_csproj;

    if has_docs_only {
        project.languages.push("markdown".to_string());
        detected_type = Some(crate::ProjectType::Documentation);
    }

    // Set the detected type
    if let Some(pt) = detected_type {
        project.project_type = pt;
    } else if project.languages.len() > 1 {
        project.project_type = crate::ProjectType::Mixed;
    }

    // Detect health config
    project.health_config = detect_health_config_async(path, &project).await;

    // Only return if we found at least one indicator
    if project.languages.is_empty() && project.project_type == crate::ProjectType::Unknown {
        // Check if it has a src directory as last resort
        let src_dir = path.join("src");
        if fs::try_exists(&src_dir).await.unwrap_or(false) {
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

/// Detect health configuration asynchronously
async fn detect_health_config_async(path: &Path, project: &ProjectMetadata) -> HealthConfig {
    use crate::ProjectType;

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
    let health_yaml = path.join("health.yaml");
    let health_yml = path.join("health.yml");
    let dothealth = path.join(".health").join("config");

    let (yaml_exists, yml_exists, dot_exists) = tokio::join!(
        fs::try_exists(&health_yaml),
        fs::try_exists(&health_yml),
        fs::try_exists(&dothealth),
    );

    let config_file = if yaml_exists.unwrap_or(false) {
        Some(health_yaml)
    } else if yml_exists.unwrap_or(false) {
        Some(health_yml)
    } else if dot_exists.unwrap_or(false) {
        Some(dothealth)
    } else {
        None
    };

    if let Some(config_file) = config_file {
        if let Ok(content) = fs::read_to_string(&config_file).await {
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
    use tempfile::TempDir;

    #[tokio::test]
    async fn test_discover_projects_async_empty() {
        let temp_dir = TempDir::new().unwrap();
        let projects = discover_projects_async(temp_dir.path()).await.unwrap();
        assert!(projects.is_empty());
    }

    #[tokio::test]
    async fn test_discover_projects_async_finds_rust() {
        let temp_dir = TempDir::new().unwrap();
        let project_dir = temp_dir.path().join("my-rust-project");
        fs::create_dir(&project_dir).await.unwrap();

        // Create a Cargo.toml
        fs::write(
            project_dir.join("Cargo.toml"),
            "[package]\nname = \"test\"\n",
        )
        .await
        .unwrap();

        let projects = discover_projects_async(temp_dir.path()).await.unwrap();
        assert_eq!(projects.len(), 1);
        assert_eq!(projects[0].name, "my-rust-project");
    }
}
