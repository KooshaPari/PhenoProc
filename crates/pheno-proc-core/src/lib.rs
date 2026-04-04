//! Process management primitives for PhenoProc registry
//!
//! Core process management types and traits used by sharecli.

use anyhow::Result;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

/// Information about a managed process
#[derive(Debug, Clone)]
pub struct ProcessInfo {
    /// Process ID
    pub pid: u32,
    /// Project name
    pub project: String,
    /// Harness type (e.g., "claude", "codex")
    pub harness: String,
    /// When the process started
    pub started_at: Instant,
    /// Current status
    pub status: ProcessStatus,
    /// Memory usage in MB
    pub memory_mb: Option<u64>,
    /// CPU usage percentage
    pub cpu_percent: Option<f32>,
}

/// Process status
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProcessStatus {
    /// Process is running
    Running,
    /// Process is stopped
    Stopped,
    /// Process has exited
    Exited,
    /// Process is in error state
    Error,
}

impl std::fmt::Display for ProcessStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ProcessStatus::Running => write!(f, "running"),
            ProcessStatus::Stopped => write!(f, "stopped"),
            ProcessStatus::Exited => write!(f, "exited"),
            ProcessStatus::Error => write!(f, "error"),
        }
    }
}

/// A managed process with lifecycle control
#[derive(Debug, Clone)]
pub struct ManagedProcess {
    /// Process information
    pub info: ProcessInfo,
    /// Command that was executed
    pub command: String,
    /// Working directory
    pub cwd: String,
}

/// Process pool for managing multiple processes
#[derive(Debug, Clone)]
pub struct ProcessPool {
    /// All managed processes
    processes: Arc<Mutex<HashMap<u32, ManagedProcess>>>,
    /// Maximum memory limit in MB
    pub max_memory_mb: u64,
    /// Maximum number of processes
    pub max_processes: u32,
}

impl ProcessPool {
    /// Create a new process pool
    pub fn new(max_memory_mb: u64, max_processes: u32) -> Self {
        Self {
            processes: Arc::new(Mutex::new(HashMap::new())),
            max_memory_mb,
            max_processes,
        }
    }

    /// Add a process to the pool
    pub fn add(&self, process: ManagedProcess) {
        let mut processes = self.processes.lock().unwrap();
        processes.insert(process.info.pid, process);
    }

    /// Remove a process from the pool
    pub fn remove(&self, pid: u32) -> Option<ManagedProcess> {
        let mut processes = self.processes.lock().unwrap();
        processes.remove(&pid)
    }

    /// Get a process by PID
    pub fn get(&self, pid: u32) -> Option<ManagedProcess> {
        let processes = self.processes.lock().unwrap();
        processes.get(&pid).cloned()
    }

    /// List all processes
    pub fn list(&self) -> Vec<ManagedProcess> {
        let processes = self.processes.lock().unwrap();
        processes.values().cloned().collect()
    }

    /// Get process count
    pub fn count(&self) -> usize {
        let processes = self.processes.lock().unwrap();
        processes.len()
    }

    /// Check if pool is at capacity
    pub fn is_full(&self) -> bool {
        let processes = self.processes.lock().unwrap();
        processes.len() >= self.max_processes as usize
    }

    /// Get total memory usage
    pub fn total_memory_mb(&self) -> u64 {
        let processes = self.processes.lock().unwrap();
        processes.values().filter_map(|p| p.info.memory_mb).sum()
    }

    /// Find processes by project
    pub fn by_project(&self, project: &str) -> Vec<ManagedProcess> {
        let processes = self.processes.lock().unwrap();
        processes
            .values()
            .filter(|p| p.info.project == project)
            .cloned()
            .collect()
    }

    /// Find processes by harness
    pub fn by_harness(&self, harness: &str) -> Vec<ManagedProcess> {
        let processes = self.processes.lock().unwrap();
        processes
            .values()
            .filter(|p| p.info.harness == harness)
            .cloned()
            .collect()
    }

    /// Clear all processes
    pub fn clear(&self) {
        let mut processes = self.processes.lock().unwrap();
        processes.clear();
    }
}

impl Default for ProcessPool {
    fn default() -> Self {
        Self::new(4096, 100)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_process(pid: u32, project: &str, harness: &str) -> ManagedProcess {
        ManagedProcess {
            info: ProcessInfo {
                pid,
                project: project.to_string(),
                harness: harness.to_string(),
                started_at: Instant::now(),
                status: ProcessStatus::Running,
                memory_mb: Some(100),
                cpu_percent: Some(5.0),
            },
            command: "test".to_string(),
            cwd: "/tmp".to_string(),
        }
    }

    #[test]
    fn test_process_pool_add_remove() {
        let pool = ProcessPool::new(4096, 10);

        let process = create_test_process(1234, "project-a", "claude");
        pool.add(process);

        assert_eq!(pool.count(), 1);

        let removed = pool.remove(1234);
        assert!(removed.is_some());
        assert_eq!(pool.count(), 0);
    }

    #[test]
    fn test_process_pool_by_project() {
        let pool = ProcessPool::new(4096, 10);

        pool.add(create_test_process(1000, "project-a", "claude"));
        pool.add(create_test_process(1001, "project-a", "codex"));
        pool.add(create_test_process(1002, "project-b", "claude"));

        let results = pool.by_project("project-a");
        assert_eq!(results.len(), 2);
    }

    #[test]
    fn test_process_pool_by_harness() {
        let pool = ProcessPool::new(4096, 10);

        pool.add(create_test_process(1000, "project-a", "claude"));
        pool.add(create_test_process(1001, "project-b", "claude"));
        pool.add(create_test_process(1002, "project-c", "codex"));

        let results = pool.by_harness("claude");
        assert_eq!(results.len(), 2);
    }

    #[test]
    fn test_process_pool_capacity() {
        let pool = ProcessPool::new(4096, 2);

        assert!(!pool.is_full());

        pool.add(create_test_process(1000, "p1", "claude"));
        pool.add(create_test_process(1001, "p2", "claude"));

        assert!(pool.is_full());
    }

    #[test]
    fn test_total_memory() {
        let pool = ProcessPool::new(4096, 10);

        pool.add(create_test_process(1000, "p1", "claude"));
        pool.add(create_test_process(1001, "p2", "claude"));

        assert_eq!(pool.total_memory_mb(), 200);
    }
}
