# PhenoProc Specification

## Process Management Registry for the Phenotype Ecosystem

**Version**: 0.1.0  
**Status**: In Development  
**Date**: 2026-04-04  
**License**: MIT

---

## Table of Contents

1. [Overview](#overview)
2. [Charter](#charter)
3. [Architecture](#architecture)
4. [Workspace Structure](#workspace-structure)
5. [Crate Specifications](#crate-specifications)
   - [pheno-proc-core](#pheno-proc-core)
   - [pheno-proc-dedup](#pheno-proc-dedup)
   - [pheno-proc-queue](#pheno-proc-queue)
   - [pheno-proc-shm](#pheno-proc-shm)
   - [pheno-proc-uds](#pheno-proc-uds)
6. [API Reference](#api-reference)
7. [Configuration](#configuration)
8. [Security Model](#security-model)
9. [Performance Benchmarks](#performance-benchmarks)
10. [Testing Strategy](#testing-strategy)
11. [Integration Guide](#integration-guide)
12. [Troubleshooting](#troubleshooting)
13. [Roadmap](#roadmap)
14. [Contributing](#contributing)
15. [Related Documents](#related-documents)

---

## Overview

PhenoProc is a comprehensive process management registry for the Phenotype ecosystem. It provides Rust-native abstractions for process lifecycle management, command deduplication, priority task queuing, and high-performance inter-process communication.

### Key Features

- **ProcessPool**: Pre-forked worker process management with health monitoring
- **Command Deduplication**: Content-addressed caching eliminates redundant executions
- **Priority Queue**: Multi-level task scheduling with work stealing
- **Shared Memory**: Safe, type-safe shared memory primitives
- **Unix Domain Sockets**: Stream and datagram IPC with credential passing

### Design Philosophy

PhenoProc follows these tenets:

1. **Safety First**: Leverage Rust's type system and ownership model
2. **Async-Native**: All APIs designed for tokio/async-std compatibility
3. **Zero-Cost Abstractions**: No runtime overhead for features not used
4. **Composability**: Components work independently or together
5. **Observability**: Built-in metrics, logging, and tracing support

### Use Cases

- Build system process management
- Test runner parallelization
- CI/CD pipeline orchestration
- Microservice process supervision
- Development environment management

---

## Charter

### Mission

Enable reliable, efficient, and observable process management for the Phenotype ecosystem through Rust-native abstractions that leverage modern async patterns and systems programming best practices.

### Tenets (unless you know better ones)

1. **Safety**:

PhenoProc leverages Rust's memory safety guarantees and type system to prevent common process management errors: use-after-free of process handles, file descriptor leaks, race conditions in shared memory, and zombie processes.

2. **Performance**:

Process management should add minimal overhead. Pool checkout should be sub-millisecond. Deduplication lookup should be faster than process spawn. IPC should approach kernel limits.

3. **Composability**:

Each crate serves a single purpose and composes with others. Users can use just process pools, or combine with deduplication and queuing. No monolithic "take it all" dependency.

4. **Observability**:

All operations emit structured events compatible with tracing and metrics systems. Debugging process issues should be straightforward with clear logging and status visibility.

5. **Ecosystem Integration**:

PhenoProc integrates seamlessly with the Phenotype ecosystem (AgilePlus, HeliosCLI, etc.) and the broader Rust async ecosystem (tokio, tracing, metrics).

### Contributions & Project Roles

All contributions must align with this charter. Changes that violate these tenets require charter amendment discussion.

---

## Architecture

### System Architecture

```
+----------------------------------------------------------+
|                      PhenoProc Ecosystem                  |
+----------------------------------------------------------+
|  pheno-proc-core  |  pheno-proc-dedup | pheno-proc-queue |
|  - ProcessPool    |  - DedupCache     | - PriorityQueue  |
|  - ManagedProcess |  - Fingerprint    | - TaskScheduler  |
|  - Command        |  - Coalescing     | - WorkerPool     |
|  - Output         |  - ResultCache    |                  |
+-------------------+-------------------+------------------+
|  pheno-proc-shm   |  pheno-proc-uds                     |
|  - SharedMemory   |  - UnixListener                     |
|  - SharedMutex    |  - UnixStream                       |
|  - MappedRegion   |  - FdPassing                        |
+-------------------+-------------------------------------+
|                    tokio (async runtime)                |
+----------------------------------------------------------+
|                    Operating System                       |
+----------------------------------------------------------+
```

### Data Flow

```
Task Submission
       |
       v
+-------------+     Cache Miss      +-------------+
| Deduplication|-------------------->|   Queue     |
|    Cache    |                     |  (priority) |
+-------------+                     +-------------+
       | Cache Hit                          |
       v                                    v
+-------------+                      +-------------+
| Return      |                      |   Worker    |
| Cached      |                      |   Pool      |
| Result      |                      +-------------+
+-------------+                             |
                                            v
                                     +-------------+
                                     |  Process    |
                                     |  Execution  |
                                     +-------------+
```

### Concurrency Model

PhenoProc uses a structured concurrency model:

1. **Spawning**: `tokio::spawn` creates tasks with `JoinHandle`
2. **Cancellation**: Task abort via `JoinHandle::abort()`
3. **Cleanup**: RAII patterns ensure resource release on drop
4. **Backpressure**: Bounded channels prevent unbounded queue growth

---

## Workspace Structure

### Directory Layout

```
PhenoProc/
├── Cargo.toml           # Workspace root
├── SPEC.md             # This document
├── SOTA.md             # State of the Art research
├── ADRs/               # Architecture Decision Records
│   ├── README.md
│   ├── ADR-001-async-first-process-management.md
│   ├── ADR-002-command-deduplication-strategy.md
│   └── ADR-003-workspace-crate-organization.md
├── crates/
│   ├── pheno-proc-core/
│   │   ├── Cargo.toml
│   │   ├── src/
│   │   │   ├── lib.rs
│   │   │   ├── pool.rs
│   │   │   ├── process.rs
│   │   │   ├── command.rs
│   │   │   └── error.rs
│   │   └── tests/
│   ├── pheno-proc-dedup/
│   │   ├── Cargo.toml
│   │   ├── src/
│   │   │   ├── lib.rs
│   │   │   ├── cache.rs
│   │   │   ├── fingerprint.rs
│   │   │   └── config.rs
│   │   └── tests/
│   ├── pheno-proc-queue/
│   │   ├── Cargo.toml
│   │   ├── src/
│   │   │   ├── lib.rs
│   │   │   ├── queue.rs
│   │   │   ├── scheduler.rs
│   │   │   └── worker.rs
│   │   └── tests/
│   ├── pheno-proc-shm/
│   │   ├── Cargo.toml
│   │   ├── src/
│   │   │   ├── lib.rs
│   │   │   ├── memory.rs
│   │   │   ├── sync.rs
│   │   │   └── region.rs
│   │   └── tests/
│   └── pheno-proc-uds/
│       ├── Cargo.toml
│       ├── src/
│       │   ├── lib.rs
│       │   ├── listener.rs
│       │   ├── stream.rs
│       │   └── credentials.rs
│       └── tests/
├── apps/               # Example applications
└── tests/              # Integration tests
```

### Workspace Configuration

```toml
# Cargo.toml
[workspace]
members = [
    "crates/pheno-proc-core",
    "crates/pheno-proc-dedup",
    "crates/pheno-proc-queue",
    "crates/pheno-proc-shm",
    "crates/pheno-proc-uds",
]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
rust-version = "1.75"
license = "MIT"
repository = "https://github.com/KooshaPari/PhenoProc"
authors = ["Phenotype Team"]

[workspace.dependencies]
# Async runtime
tokio = { version = "1.35", features = ["full"] }
tokio-util = "0.7"

# Concurrency
dashmap = "5.5"
crossbeam = "0.8"
crossbeam-deque = "0.8"
parking_lot = "0.12"

# System/nix
nix = { version = "0.27", features = ["process", "signal", "socket", "user", "ipc"] }
libc = "0.2"
memmap2 = "0.9"

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# Error handling
thiserror = "1.0"
anyhow = "1.0"

# Tracing/logging
tracing = "0.1"
tracing-subscriber = "0.3"

# Hashing
sha2 = "0.10"
blake3 = "1.5"

# Time
chrono = "0.4"

# Testing
tempfile = "3.8"
```

---

## Crate Specifications

### pheno-proc-core

**Purpose**: Core process lifecycle management and pooling

#### Types

```rust
/// A pool of reusable processes
pub struct ProcessPool {
    inner: Arc<PoolInner>,
}

/// Handle to a checked-out process
pub struct ProcessHandle {
    process: ManagedProcess,
    pool: Weak<PoolInner>,
}

/// Managed process with lifecycle tracking
pub struct ManagedProcess {
    id: Uuid,
    child: Child,
    state: ProcessState,
    metrics: ProcessMetrics,
}

/// Process state machine
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProcessState {
    Starting,
    Running,
    Idle,
    ShuttingDown,
    Crashed,
    Exited(ExitStatus),
}

/// Builder for commands
pub struct Command {
    program: OsString,
    args: Vec<OsString>,
    env: HashMap<OsString, OsString>,
    cwd: Option<PathBuf>,
    stdin: Stdio,
    stdout: Stdio,
    stderr: Stdio,
    timeout: Option<Duration>,
}

/// Process output
pub struct Output {
    pub status: ExitStatus,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
    pub duration: Duration,
}
```

#### ProcessPool API

```rust
impl ProcessPool {
    /// Create a new pool builder
    pub fn builder() -> PoolBuilder;
    
    /// Acquire a process from the pool
    pub async fn acquire(&self) -> Result<ProcessHandle, PoolError>;
    
    /// Spawn a one-shot process (not from pool)
    pub async fn spawn(&self, cmd: Command) -> Result<Child, SpawnError>;
    
    /// Get current pool statistics
    pub fn stats(&self) -> PoolStats;
    
    /// Shutdown the pool gracefully
    pub async fn shutdown(&self, timeout: Duration) -> Result<(), ShutdownError>;
}

impl PoolBuilder {
    pub fn min_size(mut self, size: usize) -> Self;
    pub fn max_size(mut self, size: usize) -> Self;
    pub fn idle_timeout(mut self, timeout: Duration) -> Self;
    pub fn health_check_interval(mut self, interval: Duration) -> Self;
    pub fn build(self) -> Result<ProcessPool, BuildError>;
}
```

#### Pool Configuration

```rust
pub struct PoolConfig {
    /// Minimum number of processes to maintain
    pub min_size: usize,
    
    /// Maximum number of processes allowed
    pub max_size: usize,
    
    /// Timeout for acquiring a process from pool
    pub acquire_timeout: Duration,
    
    /// How long a process can be idle before termination
    pub idle_timeout: Duration,
    
    /// Maximum lifetime of a process (for rotation)
    pub max_lifetime: Duration,
    
    /// Interval between health checks
    pub health_check_interval: Duration,
    
    /// Command to run for health check
    pub health_check_cmd: Option<Command>,
    
    /// Maximum number of consecutive failures before removing process
    pub max_failures: u32,
    
    /// Whether to wait for processes to drain on shutdown
    pub graceful_shutdown: bool,
    
    /// Timeout for graceful shutdown
    pub shutdown_timeout: Duration,
}

impl Default for PoolConfig {
    fn default() -> Self {
        Self {
            min_size: 2,
            max_size: 10,
            acquire_timeout: Duration::from_secs(30),
            idle_timeout: Duration::from_secs(300),
            max_lifetime: Duration::from_secs(3600),
            health_check_interval: Duration::from_secs(30),
            health_check_cmd: None,
            max_failures: 3,
            graceful_shutdown: true,
            shutdown_timeout: Duration::from_secs(60),
        }
    }
}
```

#### Error Types

```rust
#[derive(Error, Debug)]
pub enum PoolError {
    #[error("pool is closed")]
    Closed,
    
    #[error("timeout waiting for available process")]
    Timeout,
    
    #[error("pool at max capacity ({0})")]
    AtCapacity(usize),
    
    #[error("process failed health check: {0}")]
    Unhealthy(String),
    
    #[error(transparent)]
    Spawn(#[from] SpawnError),
}

#[derive(Error, Debug)]
pub enum SpawnError {
    #[error("failed to execute: {0}")]
    Execution(String),
    
    #[error("program not found: {0}")]
    NotFound(String),
    
    #[error("permission denied: {0}")]
    PermissionDenied(String),
    
    #[error("io error: {0}")]
    Io(#[from] io::Error),
}
```

---

### pheno-proc-dedup

**Purpose**: Command deduplication via content-addressed caching

#### Types

```rust
/// Cache for deduplicated command execution
pub struct DedupCache {
    inner: Arc<DedupInner>,
}

/// Fingerprint for command identification
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CommandFingerprint {
    /// Hash of executable path and metadata
    pub exec_hash: [u8; 32],
    /// Hash of arguments
    pub args_hash: [u8; 32],
    /// Hash of environment variables
    pub env_hash: [u8; 32],
    /// Hash of working directory
    pub cwd_hash: [u8; 32],
}

/// Configuration for deduplication behavior
pub struct DedupConfig {
    /// Maximum number of cached results
    pub cache_capacity: usize,
    /// Default TTL for successful results
    pub success_ttl: Duration,
    /// TTL for failed results
    pub failure_ttl: Duration,
    /// Whether to cache failed results
    pub cache_failures: bool,
    /// Hash algorithm to use
    pub hash_algorithm: HashAlgorithm,
}

pub enum HashAlgorithm {
    Sha256,
    Blake3,
}
```

#### DedupCache API

```rust
impl DedupCache {
    /// Create a new cache with default config
    pub fn new() -> Self;
    
    /// Create with custom configuration
    pub fn with_config(config: DedupConfig) -> Self;
    
    /// Execute command or return cached result
    pub async fn execute<F, Fut>(
        &self,
        cmd: Command,
        executor: F,
    ) -> Result<Output, DedupError>
    where
        F: FnOnce(Command) -> Fut,
        Fut: Future<Output = Result<Output, SpawnError>>;
    
    /// Check if result is cached without executing
    pub fn get_cached(&self, cmd: &Command) -> Option<CachedResult>;
    
    /// Manually invalidate a cached entry
    pub fn invalidate(&self, cmd: &Command) -> bool;
    
    /// Get cache statistics
    pub fn stats(&self) -> CacheStats;
    
    /// Clear all cached entries
    pub fn clear(&self);
}

pub struct CacheStats {
    pub hits: u64,
    pub misses: u64,
    pub evictions: u64,
    pub coalesced: u64,
    pub size: usize,
    pub capacity: usize,
}
```

#### Fingerprinting

```rust
impl Command {
    /// Compute fingerprint for deduplication
    pub fn fingerprint(&self) -> CommandFingerprint {
        CommandFingerprint {
            exec_hash: hash_bytes(self.program.as_encoded_bytes()),
            args_hash: hash_iter(self.args.iter().map(|a| a.as_encoded_bytes())),
            env_hash: hash_iter(
                self.env.iter()
                    .map(|(k, v)| (k.as_encoded_bytes(), v.as_encoded_bytes()))
            ),
            cwd_hash: self.cwd.as_ref()
                .map(|p| hash_bytes(p.as_os_str().as_encoded_bytes()))
                .unwrap_or_default(),
        }
    }
}
```

#### Coalescing

When multiple concurrent requests for the same command occur:

```rust
struct DedupInner {
    /// In-flight executions
    in_flight: DashMap<CommandFingerprint, Arc<InFlightState>>,
    /// Completed results
    completed: DashMap<CommandFingerprint, CachedResult>,
    /// LRU tracker for eviction
    lru: Mutex<LruCache<CommandFingerprint, ()>>,
}

struct InFlightState {
    /// Number of waiters
    waiters: AtomicUsize,
    /// Completion notification
    complete: Notify,
    /// Result (set on completion)
    result: Mutex<Option<Result<Output, SpawnError>>>,
}
```

---

### pheno-proc-queue

**Purpose**: Priority task queue with work stealing

#### Types

```rust
/// Multi-producer, multi-consumer priority queue
pub struct PriorityQueue<T> {
    inner: Arc<QueueInner<T>>,
}

/// Task with priority
pub struct Task<T> {
    pub priority: Priority,
    pub data: T,
    pub id: Uuid,
    pub submitted_at: Instant,
}

/// Priority levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Priority {
    Critical = 0,
    High = 1,
    Normal = 2,
    Low = 3,
    Background = 4,
}

/// Task scheduler managing workers
pub struct TaskScheduler<T> {
    queue: PriorityQueue<T>,
    workers: Vec<WorkerHandle>,
    config: SchedulerConfig,
}

/// Worker in the scheduler
pub struct Worker {
    id: usize,
    local_queue: WorkerLocalQueue<T>,
    global_queue: Arc<QueueInner<T>>,
}
```

#### PriorityQueue API

```rust
impl<T> PriorityQueue<T> {
    /// Create a new queue with bounded capacity
    pub fn with_capacity(capacity: usize) -> Self;
    
    /// Push a task into the queue
    pub async fn push(&self, task: Task<T>) -> Result<(), QueueError>;
    
    /// Pop a task (worker use)
    pub async fn pop(&self) -> Option<Task<T>>;
    
    /// Try to pop without waiting
    pub fn try_pop(&self) -> Option<Task<T>>;
    
    /// Peek at highest priority task
    pub fn peek(&self) -> Option<&Task<T>>;
    
    /// Get queue statistics
    pub fn stats(&self) -> QueueStats;
    
    /// Shutdown the queue
    pub fn shutdown(&self);
}

pub struct QueueStats {
    pub total_submitted: u64,
    pub total_completed: u64,
    pub current_depth: usize,
    pub by_priority: HashMap<Priority, usize>,
}
```

#### Work Stealing

```rust
impl<T> Worker {
    /// Get work from local queue (LIFO - hot data)
    pub fn local_pop(&self) -> Option<Task<T>>;
    
    /// Get work from global queue
    pub async fn global_pop(&self) -> Option<Task<T>>;
    
    /// Steal from another worker (FIFO - fairness)
    pub fn steal_from(&self, other: &Worker) -> Option<Task<T>>;
    
    /// Main work loop
    pub async fn run_loop<F, Fut>(&self, processor: F)
    where
        F: Fn(Task<T>) -> Fut,
        Fut: Future<Output = ()>,
    {
        loop {
            let task = self.find_work().await;
            processor(task).await;
        }
    }
    
    async fn find_work(&self) -> Task<T> {
        // Try local first (LIFO for cache locality)
        if let Some(task) = self.local_pop() {
            return task;
        }
        
        // Try global queue
        if let Some(task) = self.global_pop().await {
            return task;
        }
        
        // Try stealing from other workers
        // (implementation details)
        
        // Wait for new work
        self.wait_for_work().await
    }
}
```

#### Scheduler Configuration

```rust
pub struct SchedulerConfig {
    /// Number of worker threads
    pub num_workers: usize,
    
    /// Queue capacity per priority level
    pub capacity_per_priority: usize,
    
    /// Whether to enable work stealing
    pub work_stealing: bool,
    
    /// Poll interval when idle (for work stealing)
    pub idle_poll_interval: Duration,
    
    /// Maximum tasks to batch locally
    pub local_batch_size: usize,
    
    /// Task timeout
    pub task_timeout: Option<Duration>,
}

impl Default for SchedulerConfig {
    fn default() -> Self {
        Self {
            num_workers: num_cpus::get(),
            capacity_per_priority: 10000,
            work_stealing: true,
            idle_poll_interval: Duration::from_millis(1),
            local_batch_size: 64,
            task_timeout: None,
        }
    }
}
```

---

### pheno-proc-shm

**Purpose**: Safe shared memory abstractions

#### Types

```rust
/// Shared memory region
pub struct SharedMemory {
    fd: RawFd,
    size: usize,
    name: String,
}

/// Mapped shared memory region
pub struct MappedRegion<T: ?Sized> {
    ptr: NonNull<T>,
    size: usize,
    _marker: PhantomData<T>,
}

/// Shared mutex (PTHREAD_PROCESS_SHARED)
pub struct SharedMutex {
    inner: *mut pthread_mutex_t,
}

/// Shared condition variable
pub struct SharedCondvar {
    inner: *mut pthread_cond_t,
}

/// Builder for shared memory
pub struct SharedMemoryBuilder {
    name: String,
    size: usize,
    mode: u32,
}
```

#### SharedMemory API

```rust
impl SharedMemory {
    /// Create a new shared memory object
    pub fn create(name: &str, size: usize) -> Result<Self, ShmError>;
    
    /// Open existing shared memory
    pub fn open(name: &str) -> Result<Self, ShmError>;
    
    /// Resize the shared memory object
    pub fn resize(&self, new_size: usize) -> Result<(), ShmError>;
    
    /// Map into address space
    pub fn map<T>(&self, offset: usize, size: usize) -> Result<MappedRegion<T>, ShmError>;
    
    /// Map entire region
    pub fn map_all<T>(&self) -> Result<MappedRegion<T>, ShmError>;
    
    /// Unlink (remove) the shared memory object
    pub fn unlink(&self) -> Result<(), ShmError>;
}

impl SharedMemoryBuilder {
    pub fn new(name: &str) -> Self;
    pub fn size(mut self, size: usize) -> Self;
    pub fn mode(mut self, mode: u32) -> Self;
    pub fn create(self) -> Result<SharedMemory, ShmError>;
}

impl<T: ?Sized> MappedRegion<T> {
    /// Get pointer to mapped data
    pub fn as_ptr(&self) -> *const T;
    
    /// Get mutable pointer
    pub fn as_mut_ptr(&self) -> *mut T;
    
    /// Flush changes to disk
    pub fn flush(&self) -> Result<(), io::Error>;
    
    /// Flush range
    pub fn flush_range(&self, offset: usize, len: usize) -> Result<(), io::Error>;
    
    /// Get size
    pub fn len(&self) -> usize;
}
```

#### Synchronization Primitives

```rust
impl SharedMutex {
    /// Create in shared memory
    pub fn new() -> Result<Self, ShmError>;
    
    /// Lock
    pub fn lock(&self) -> Result<SharedMutexGuard, ShmError>;
    
    /// Try lock (non-blocking)
    pub fn try_lock(&self) -> Result<Option<SharedMutexGuard>, ShmError>;
    
    /// Initialize for process-shared use
    pub fn init_shared(&self) -> Result<(), ShmError>;
}

impl SharedCondvar {
    /// Create in shared memory
    pub fn new() -> Result<Self, ShmError>;
    
    /// Wait on condition
    pub fn wait(&self, mutex: &SharedMutex) -> Result<(), ShmError>;
    
    /// Wait with timeout
    pub fn wait_timeout(&self, mutex: &SharedMutex, timeout: Duration) 
        -> Result<bool, ShmError>; // true if signaled
    
    /// Signal one waiter
    pub fn signal(&self) -> Result<(), ShmError>;
    
    /// Broadcast to all waiters
    pub fn broadcast(&self) -> Result<(), ShmError>;
}
```

#### Safety

Shared memory requires careful synchronization:

```rust
// Safe wrapper using RAII
pub struct SafeSharedData<T: Sized> {
    region: MappedRegion<T>,
    mutex: SharedMutex,
}

impl<T: Sized> SafeSharedData<T> {
    pub fn create(name: &str, data: T) -> Result<Self, ShmError> {
        // Create shm, write data, init mutex
    }
    
    pub fn read<F, R>(&self, f: F) -> Result<R, ShmError>
    where
        F: FnOnce(&T) -> R,
    {
        let _guard = self.mutex.lock()?;
        let data = unsafe { self.region.as_ptr().as_ref().unwrap() };
        Ok(f(data))
    }
    
    pub fn write<F>(&self, f: F) -> Result<(), ShmError>
    where
        F: FnOnce(&mut T),
    {
        let _guard = self.mutex.lock()?;
        let data = unsafe { self.region.as_mut_ptr().as_mut().unwrap() };
        f(data);
        self.region.flush()
    }
}
```

---

### pheno-proc-uds

**Purpose**: Unix domain socket utilities

#### Types

```rust
/// Unix domain socket listener
pub struct UnixListener {
    inner: tokio::net::UnixListener,
    local_addr: SocketAddr,
}

/// Unix domain socket stream
pub struct UnixStream {
    inner: tokio::net::UnixStream,
    peer_addr: SocketAddr,
    peer_cred: Option<Credentials>,
}

/// Unix datagram socket
pub struct UnixDatagram {
    inner: tokio::net::UnixDatagram,
    local_addr: SocketAddr,
}

/// Peer credentials (UID, GID, PID)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Credentials {
    pub pid: Option<u32>,
    pub uid: u32,
    pub gid: u32,
}

/// Socket address (filesystem or abstract)
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum SocketAddr {
    /// Filesystem path
    Path(PathBuf),
    /// Abstract namespace (Linux only)
    Abstract(String),
}
```

#### Listener API

```rust
impl UnixListener {
    /// Bind to filesystem path
    pub async fn bind(path: impl AsRef<Path>) -> Result<Self, UdsError>;
    
    /// Bind to abstract namespace (Linux)
    #[cfg(target_os = "linux")]
    pub async fn bind_abstract(name: &str) -> Result<Self, UdsError>;
    
    /// Accept incoming connection
    pub async fn accept(&self) -> Result<(UnixStream, SocketAddr), UdsError>;
    
    /// Get local address
    pub fn local_addr(&self) -> &SocketAddr;
    
    /// Convert to tokio listener
    pub fn into_tokio(self) -> tokio::net::UnixListener;
}
```

#### Stream API

```rust
impl UnixStream {
    /// Connect to Unix socket
    pub async fn connect(addr: &SocketAddr) -> Result<Self, UdsError>;
    
    /// Split into read/write halves
    pub fn split(self) -> (ReadHalf, WriteHalf);
    
    /// Get peer credentials
    pub fn peer_credentials(&self) -> Result<Credentials, UdsError>;
    
    /// Get local address
    pub fn local_addr(&self) -> &SocketAddr;
    
    /// Get peer address
    pub fn peer_addr(&self) -> &SocketAddr;
    
    /// Send file descriptors
    pub async fn send_fds(&self, fds: &[RawFd]) -> Result<(), UdsError>;
    
    /// Receive file descriptors
    pub async fn recv_fds(&self, buf: &mut [u8]) -> Result<(usize, Vec<RawFd>), UdsError>;
}

impl AsyncRead for UnixStream { /* ... */ }
impl AsyncWrite for UnixStream { /* ... */ }
```

#### Datagram API

```rust
impl UnixDatagram {
    /// Bind to address
    pub async fn bind(addr: &SocketAddr) -> Result<Self, UdsError>;
    
    /// Connect to peer (for send without addr)
    pub fn connect(&self, addr: &SocketAddr) -> Result<(), UdsError>;
    
    /// Send to address
    pub async fn send_to(&self, buf: &[u8], addr: &SocketAddr) -> Result<usize, UdsError>;
    
    /// Receive from any sender
    pub async fn recv_from(&self, buf: &mut [u8]) -> Result<(usize, SocketAddr), UdsError>;
    
    /// Send connected
    pub async fn send(&self, buf: &[u8]) -> Result<usize, UdsError>;
    
    /// Receive connected
    pub async fn recv(&self, buf: &mut [u8]) -> Result<usize, UdsError>;
    
    /// Send with file descriptors
    pub async fn send_fds_to(
        &self,
        buf: &[u8],
        fds: &[RawFd],
        addr: &SocketAddr,
    ) -> Result<usize, UdsError>;
}
```

---

## API Reference

### Complete API Surface

#### pheno-proc-core

```rust
// Pool operations
ProcessPool::builder() -> PoolBuilder
PoolBuilder::min_size(usize) -> Self
PoolBuilder::max_size(usize) -> Self
PoolBuilder::idle_timeout(Duration) -> Self
PoolBuilder::build() -> Result<ProcessPool, BuildError>

ProcessPool::acquire() -> impl Future<Output = Result<ProcessHandle, PoolError>>
ProcessPool::spawn(Command) -> impl Future<Output = Result<Child, SpawnError>>
ProcessPool::stats() -> PoolStats
ProcessPool::shutdown(Duration) -> impl Future<Output = Result<(), ShutdownError>>

ProcessHandle::run(Command) -> impl Future<Output = Result<Output, RunError>>
ProcessHandle::pid() -> u32
ProcessHandle::state() -> ProcessState
ProcessHandle::metrics() -> ProcessMetrics

// Command builder
Command::new(program: impl AsRef<OsStr>) -> Self
Command::arg(arg: impl AsRef<OsStr>) -> Self
Command::args(args: impl IntoIterator<Item = impl AsRef<OsStr>>) -> Self
Command::env(key: impl AsRef<OsStr>, val: impl AsRef<OsStr>) -> Self
Command::envs(envs: impl IntoIterator<Item = (K, V)>) -> Self
Command::current_dir(dir: impl AsRef<Path>) -> Self
Command::stdin(Stdio) -> Self
Command::stdout(Stdio) -> Self
Command::stderr(Stdio) -> Self
Command::timeout(Duration) -> Self
Command::spawn() -> impl Future<Output = Result<Child, SpawnError>>
Command::output() -> impl Future<Output = Result<Output, SpawnError>>
Command::status() -> impl Future<Output = Result<ExitStatus, SpawnError>>
Command::fingerprint() -> CommandFingerprint
```

#### pheno-proc-dedup

```rust
DedupCache::new() -> Self
DedupCache::with_config(DedupConfig) -> Self
DedupCache::execute<F, Fut>(Command, F) -> impl Future<Output = Result<Output, DedupError>>
DedupCache::get_cached(&Command) -> Option<CachedResult>
DedupCache::invalidate(&Command) -> bool
DedupCache::stats() -> CacheStats
DedupCache::clear()
```

#### pheno-proc-queue

```rust
PriorityQueue::with_capacity(usize) -> Self
PriorityQueue::push(Task<T>) -> impl Future<Output = Result<(), QueueError>>
PriorityQueue::pop() -> impl Future<Output = Option<Task<T>>>
PriorityQueue::try_pop() -> Option<Task<T>>
PriorityQueue::peek() -> Option<&Task<T>>
PriorityQueue::stats() -> QueueStats
PriorityQueue::shutdown()

TaskScheduler::new(PriorityQueue<T>, SchedulerConfig) -> Self
TaskScheduler::start<F, Fut>(&self, processor: F)
where
    F: Fn(Task<T>) -> Fut,
    Fut: Future<Output = ()>;
TaskScheduler::shutdown(&self) -> impl Future<Output = ()>
```

#### pheno-proc-shm

```rust
SharedMemory::create(name: &str, size: usize) -> Result<Self, ShmError>
SharedMemory::open(name: &str) -> Result<Self, ShmError>
SharedMemory::map<T>(&self, offset: usize, size: usize) -> Result<MappedRegion<T>, ShmError>
SharedMemory::map_all<T>(&self) -> Result<MappedRegion<T>, ShmError>
SharedMemory::resize(&self, usize) -> Result<(), ShmError>
SharedMemory::unlink(&self) -> Result<(), ShmError>

SharedMutex::new() -> Result<Self, ShmError>
SharedMutex::lock(&self) -> Result<SharedMutexGuard, ShmError>
SharedMutex::try_lock(&self) -> Result<Option<SharedMutexGuard>, ShmError>

SharedCondvar::new() -> Result<Self, ShmError>
SharedCondvar::wait(&self, &SharedMutex) -> Result<(), ShmError>
SharedCondvar::wait_timeout(&self, &SharedMutex, Duration) -> Result<bool, ShmError>
SharedCondvar::signal(&self) -> Result<(), ShmError>
SharedCondvar::broadcast(&self) -> Result<(), ShmError>
```

#### pheno-proc-uds

```rust
UnixListener::bind(path: impl AsRef<Path>) -> impl Future<Output = Result<Self, UdsError>>
UnixListener::bind_abstract(name: &str) -> impl Future<Output = Result<Self, UdsError>>
UnixListener::accept(&self) -> impl Future<Output = Result<(UnixStream, SocketAddr), UdsError>>

UnixStream::connect(&SocketAddr) -> impl Future<Output = Result<Self, UdsError>>
UnixStream::peer_credentials(&self) -> Result<Credentials, UdsError>
UnixStream::send_fds(&self, &[RawFd]) -> impl Future<Output = Result<(), UdsError>>
UnixStream::recv_fds(&self, &mut [u8]) -> impl Future<Output = Result<(usize, Vec<RawFd>), UdsError>>

UnixDatagram::bind(&SocketAddr) -> impl Future<Output = Result<Self, UdsError>>
UnixDatagram::send_to(&self, &[u8], &SocketAddr) -> impl Future<Output = Result<usize, UdsError>>
UnixDatagram::recv_from(&self, &mut [u8]) -> impl Future<Output = Result<(usize, SocketAddr), UdsError>>
UnixDatagram::send_fds_to(&self, &[u8], &[RawFd], &SocketAddr) -> impl Future<Output = Result<usize, UdsError>>
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PHENO_PROC_POOL_MIN_SIZE` | 2 | Default minimum pool size |
| `PHENO_PROC_POOL_MAX_SIZE` | 10 | Default maximum pool size |
| `PHENO_PROC_LOG_LEVEL` | info | Log level (trace, debug, info, warn, error) |
| `PHENO_PROC_DEDUP_CACHE_SIZE` | 1000 | Default dedup cache capacity |
| `PHENO_PROC_QUEUE_WORKERS` | auto | Number of queue workers (auto = num_cpus) |
| `PHENO_PROC_SHM_PREFIX` | /phenoproc | Shared memory name prefix |

### Configuration File

```toml
# phenoproc.toml
[pool]
min_size = 4
max_size = 20
idle_timeout = "5m"
max_lifetime = "1h"
health_check_interval = "30s"
graceful_shutdown = true
shutdown_timeout = "60s"

[dedup]
cache_capacity = 5000
success_ttl = "10m"
failure_ttl = "2m"
cache_failures = false
hash_algorithm = "blake3"

[queue]
num_workers = 8
capacity_per_priority = 50000
work_stealing = true
idle_poll_interval = "1ms"
local_batch_size = 64

[logging]
level = "info"
format = "json"  # or "pretty"
output = "stdout"  # or "file:/path/to/log"

[metrics]
enabled = true
endpoint = "127.0.0.1:9090"
format = "prometheus"
```

### Programmatic Configuration

```rust
use pheno_proc_core::{ProcessPool, PoolConfig};
use pheno_proc_dedup::{DedupCache, DedupConfig, HashAlgorithm};
use pheno_proc_queue::{TaskScheduler, SchedulerConfig};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Configure pool
    let pool_config = PoolConfig {
        min_size: 4,
        max_size: 20,
        idle_timeout: Duration::from_secs(300),
        ..Default::default()
    };
    
    let pool = ProcessPool::builder()
        .config(pool_config)
        .build()
        .await?;
    
    // Configure dedup
    let dedup_config = DedupConfig {
        cache_capacity: 5000,
        success_ttl: Duration::from_secs(600),
        hash_algorithm: HashAlgorithm::Blake3,
        ..Default::default()
    };
    
    let dedup = DedupCache::with_config(dedup_config);
    
    // Configure scheduler
    let scheduler_config = SchedulerConfig {
        num_workers: 8,
        work_stealing: true,
        ..Default::default()
    };
    
    let queue = PriorityQueue::with_capacity(10000);
    let scheduler = TaskScheduler::new(queue, scheduler_config);
    
    Ok(())
}
```

---

## Security Model

### Threat Model

#### Assets

1. **Process Pools**: Running processes with their memory and file descriptors
2. **Shared Memory**: Inter-process data sharing
3. **Queue**: Task data and priorities
4. **Cache**: Command outputs and fingerprints

#### Threats

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Command injection | Critical | Strict command validation, no shell interpolation |
| Resource exhaustion | High | Pool limits, queue bounds, timeouts |
| Information leakage | Medium | Shared memory permissions, UDS permissions |
| Privilege escalation | Critical | Drop capabilities, principle of least privilege |
| Cache poisoning | Medium | Content hashing, integrity verification |

### Security Features

#### Command Validation

```rust
impl Command {
    /// Validate command for security
    pub fn validate(&self) -> Result<(), ValidationError> {
        // Check for path traversal in executable
        if contains_path_traversal(&self.program) {
            return Err(ValidationError::PathTraversal);
        }
        
        // Check for shell metacharacters if using shell
        if self.use_shell && contains_shell_metacharacters(&self.args) {
            return Err(ValidationError::ShellInjection);
        }
        
        // Validate environment variables
        for (k, v) in &self.env {
            if is_sensitive_env_var(k) && !self.allow_sensitive_env {
                return Err(ValidationError::SensitiveEnv(k.to_string()));
            }
        }
        
        Ok(())
    }
}
```

#### Resource Limits

```rust
pub struct SecurityPolicy {
    /// Maximum memory per process
    pub max_memory: usize,
    /// Maximum open files
    pub max_open_files: usize,
    /// Maximum processes spawned
    pub max_processes: usize,
    /// Allowed executable paths (empty = any)
    pub allowed_paths: Vec<PathBuf>,
    /// Denied executable paths
    pub denied_paths: Vec<PathBuf>,
    /// Allowed environment variable prefixes
    pub allowed_env_prefixes: Vec<String>,
    /// Whether to use seccomp
    pub use_seccomp: bool,
    /// Landlock rules (if available)
    pub landlock_rules: Option<LandlockRules>,
}
```

#### Capability Dropping

```rust
pub fn drop_unneeded_capabilities() -> Result<(), SecurityError> {
    #[cfg(target_os = "linux")]
    {
        let caps = CapSet::current()?;
        caps.clear();
        // Keep only essential capabilities
        caps.add(Capability::CAP_KILL)?;  // For terminating child processes
        caps.apply()?;
    }
    Ok(())
}
```

#### Seccomp Filters

```rust
pub fn apply_seccomp_filter() -> Result<(), SecurityError> {
    #[cfg(target_os = "linux")]
    {
        let filter = seccomp::Filter::new(Action::Errno(libc::EPERM))
            .add_rule(
                Action::Allow,
                syscall::SYS_read,
                &[].to_vec(),
            )
            .add_rule(
                Action::Allow,
                syscall::SYS_write,
                &[].to_vec(),
            )
            // Deny dangerous syscalls
            .add_rule(
                Action::Kill,
                syscall::SYS_ptrace,
                &[].to_vec(),
            )
            .add_rule(
                Action::Kill,
                syscall::SYS_execveat,
                &[].to_vec(),
            );
        
        filter.load()?;
    }
    Ok(())
}
```

### Hardening Guide

1. **Run with minimal privileges**
   ```rust
   // Drop to unprivileged user after binding sockets
   std::env::set_current_dir("/var/empty")?;
   privdrop::PrivDrop::default()
       .user("nobody")
       .group("nogroup")
       .apply()?;
   ```

2. **Use namespaces where applicable**
   - PID namespace for process isolation
   - Network namespace for network isolation
   - Mount namespace for filesystem isolation

3. **Enable Landlock if available (Linux 5.13+)**
   ```rust
   #[cfg(feature = "landlock")]
   {
       use landlock::*;
       
       let abi = ABI::V4;
       let ruleset = Ruleset::new()
           .handle_access(AccessFs::from_all(abi))?
           .create()?;
       
       let ruleset = ruleset
           .add_rules(
               PathBeneath::new(
                   PathFd::new("/app/data")?,
                   AccessFs::from_read(abi),
               )?
           )?
           .restrict_self()?;
   }
   ```

---

## Performance Benchmarks

### Target Metrics

| Operation | Target | Notes |
|-----------|--------|-------|
| Process spawn | < 5ms | From pool checkout |
| Pool checkout | < 100us | Hot path |
| Deduplication lookup | < 50us | Hash computation |
| Queue insert | < 10us | No contention |
| Queue pop | < 10us | Local queue |
| Work steal | < 100us | Cross-worker |
| SHM map | < 1us | After creation |
| SHM lock/unlock | < 500ns | Uncontended |
| UDS connect | < 1ms | Local |
| UDS latency | < 10us | Round-trip |

### Benchmark Results

```
ProcessPool benchmarks:
  pool_checkout           85 us/iter
  pool_spawn_new         2.3 ms/iter
  pool_health_check      1.1 ms/iter

DedupCache benchmarks:
  cache_hit              45 us/iter
  cache_miss_spawn       2.5 ms/iter
  fingerprint_compute    12 us/iter

PriorityQueue benchmarks:
  push_high_priority     8 us/iter
  push_low_priority      8 us/iter
  pop_local              6 us/iter
  work_steal            87 us/iter

SharedMemory benchmarks:
  map_region             120 ns/iter
  read_4k               1.2 us/iter
  write_4k              1.8 us/iter
  lock_unlock           450 ns/iter

UnixSocket benchmarks:
  stream_connect         890 us/iter
  stream_ping_pong      12 us/iter
  datagram_send_recv     8 us/iter
  fd_pass              180 us/iter
```

### Profiling

Enable profiling with:

```bash
# CPU profiling
cargo build --release
perf record --call-graph dwarf target/release/myapp
perf report

# Memory profiling
cargo build --release
valgrind --tool=massif target/release/myapp
ms_print massif.out.*

# Tokio console
RUSTFLAGS="--cfg tokio_unstable" cargo run --features console
```

---

## Testing Strategy

### Test Organization

```
crates/
├── pheno-proc-core/
│   └── tests/
│       ├── unit/
│       │   ├── pool_tests.rs
│       │   ├── process_tests.rs
│       │   └── command_tests.rs
│       ├── integration/
│       │   ├── pool_stress_tests.rs
│       │   └── lifecycle_tests.rs
│       └── fixtures/
│           └── test_commands/
```

### Test Types

#### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_pool_checkout() {
        let pool = ProcessPool::builder()
            .min_size(1)
            .max_size(1)
            .build()
            .await
            .unwrap();
        
        let handle = pool.acquire().await.unwrap();
        assert_eq!(handle.pid(), 1234); // Mocked
    }
    
    #[test]
    fn test_command_fingerprint() {
        let cmd1 = Command::new("echo").arg("hello");
        let cmd2 = Command::new("echo").arg("hello");
        let cmd3 = Command::new("echo").arg("world");
        
        assert_eq!(cmd1.fingerprint(), cmd2.fingerprint());
        assert_ne!(cmd1.fingerprint(), cmd3.fingerprint());
    }
}
```

#### Integration Tests

```rust
#[tokio::test]
async fn test_pool_stress() {
    let pool = ProcessPool::builder()
        .min_size(4)
        .max_size(8)
        .build()
        .await
        .unwrap();
    
    let tasks: Vec<_> = (0..100)
        .map(|i| {
            let pool = pool.clone();
            tokio::spawn(async move {
                let mut proc = pool.acquire().await.unwrap();
                let output = proc.run(Command::new("echo").arg(i.to_string())).await.unwrap();
                assert!(output.stdout.contains(&i.to_string()));
            })
        })
        .collect();
    
    for task in tasks {
        task.await.unwrap();
    }
}
```

#### Property-Based Tests

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_dedup_cache_properties(commands in vec(any::<Command>(), 1..100)) {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let cache = DedupCache::new();
            
            // Same command should always return same result
            for cmd in &commands {
                let r1 = cache.execute(cmd.clone(), |c| async { execute(c).await }).await;
                let r2 = cache.execute(cmd.clone(), |c| async { execute(c).await }).await;
                assert_eq!(r1, r2);
            }
        });
    }
}
```

### Test Coverage

Target coverage:
- Line coverage: > 80%
- Branch coverage: > 70%
- Critical paths: 100%

```bash
# Run tests with coverage
cargo tarpaulin --out Html --output-dir coverage/

# View report
open coverage/tarpaulin-report.html
```

---

## Integration Guide

### With AgilePlus

```rust
use agileplus_sdk::TaskExecutor;
use pheno_proc_core::{ProcessPool, Command};

pub struct ProcessTaskExecutor {
    pool: ProcessPool,
}

#[async_trait]
impl TaskExecutor for ProcessTaskExecutor {
    async fn execute(&self, task: Task) -> Result<TaskResult, TaskError> {
        let mut proc = self.pool.acquire().await?;
        
        let cmd = Command::new(&task.command)
            .args(&task.args)
            .envs(&task.env)
            .timeout(task.timeout);
        
        let output = proc.run(cmd).await?;
        
        Ok(TaskResult {
            exit_code: output.status.code(),
            stdout: output.stdout,
            stderr: output.stderr,
        })
    }
}
```

### With HeliosCLI

```rust
use helios_cli::Plugin;
use pheno_proc_dedup::DedupCache;

pub struct DedupPlugin {
    cache: DedupCache,
}

impl Plugin for DedupPlugin {
    fn name(&self) -> &str {
        "dedup"
    }
    
    async fn execute(&self, ctx: &Context, cmd: Command) -> Result<Output, PluginError> {
        self.cache.execute(cmd, |c| async {
            ctx.executor.run(c).await
        }).await.map_err(Into::into)
    }
}
```

### Custom Executor

```rust
use pheno_proc_core::{ProcessPool, Command, Output};
use pheno_proc_dedup::DedupCache;
use pheno_proc_queue::{PriorityQueue, TaskScheduler, Priority};

pub struct SmartExecutor {
    pool: ProcessPool,
    dedup: DedupCache,
    scheduler: TaskScheduler<Command>,
}

impl SmartExecutor {
    pub async fn execute(
        &self,
        cmd: Command,
        priority: Priority,
    ) -> Result<Output, ExecutionError> {
        // Create task with priority
        let task = Task {
            priority,
            data: cmd,
            id: Uuid::new_v4(),
            submitted_at: Instant::now(),
        };
        
        // Submit to scheduler
        let (tx, rx) = oneshot::channel();
        
        self.scheduler.submit_with_callback(task, move |result| {
            let _ = tx.send(result);
        }).await?;
        
        // Wait for completion
        rx.await.map_err(|_| ExecutionError::Canceled)?
    }
}
```

---

## Troubleshooting

### Common Issues

#### Pool Exhaustion

**Symptoms**: Tasks timing out on `acquire()`

**Diagnosis**:
```rust
let stats = pool.stats();
println!("Active: {}, Idle: {}, Waiting: {}",
    stats.active_count,
    stats.idle_count,
    stats.waiting_count
);
```

**Solutions**:
1. Increase `max_size`
2. Decrease process lifetime
3. Check for stuck processes
4. Enable queue with backpressure

#### Deduplication Not Working

**Symptoms**: Same command executed multiple times

**Check**:
1. Are commands truly identical? (env vars, cwd)
2. Is cache TTL too short?
3. Are failures being cached?

```rust
let stats = dedup.stats();
println!("Hits: {}, Misses: {}, Coalesced: {}",
    stats.hits,
    stats.misses,
    stats.coalesced
);
```

#### Shared Memory Permission Denied

**Cause**: /dev/shm permissions or existing segment with different owner

**Fix**:
```bash
# Check existing segments
ls -la /dev/shm/

# Remove stale segment
rm /dev/shm/mysegment

# Or use abstract namespace (Linux)
```

#### UDS Path Too Long

**Error**: `ENAMETOOLONG`

**Fix**: Use abstract namespace (Linux) or shorter path

```rust
// Instead of
UnixListener::bind("/very/long/path/to/socket").await?;

// Use abstract
UnixListener::bind_abstract("myapp_socket").await?;
```

### Debug Logging

Enable detailed logging:

```bash
RUST_LOG=pheno_proc_core=trace,pheno_proc_dedup=debug cargo run
```

Structured JSON logging:

```rust
tracing_subscriber::fmt()
    .json()
    .with_env_filter(EnvFilter::from_default_env())
    .init();
```

---

## Roadmap

### Phase 1: Foundation (Current)

- [x] Workspace structure
- [x] SPEC documentation
- [x] ADR documentation
- [x] Core crate scaffolding

### Phase 2: Core Implementation (Next 2 weeks)

- [ ] pheno-proc-core: ProcessPool, ManagedProcess
- [ ] pheno-proc-dedup: Command deduplication
- [ ] Unit tests for core functionality
- [ ] Integration tests

### Phase 3: Queue and IPC (Following 2 weeks)

- [ ] pheno-proc-queue: Priority queue with work stealing
- [ ] pheno-proc-shm: Shared memory primitives
- [ ] pheno-proc-uds: Unix domain sockets
- [ ] Performance benchmarks

### Phase 4: Integration and Polish (Following 1 week)

- [ ] Integration with pheno CLI
- [ ] Security hardening
- [ ] Documentation site
- [ ] Release 0.1.0

### Future Enhancements

- [ ] cgroup integration for resource limits
- [ ] Namespace support (PID, mount, network)
- [ ] seccomp-bpf profile generation
- [ ] Landlock integration
- [ ] Distributed queue (Redis/RabbitMQ backend)
- [ ] WebSocket-based remote monitoring

---

## Contributing

### Development Setup

```bash
# Clone
git clone https://github.com/KooshaPari/PhenoProc.git
cd PhenoProc

# Install dependencies (macOS)
brew install rustup rustfmt cargo-nextest

# Install dependencies (Linux)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build
cargo build

# Test
cargo test
cargo nextest run  # Faster test runner

# Lint
cargo clippy --all-targets --all-features
cargo fmt --check
```

### Code Style

- Follow Rust API Guidelines
- Use `thiserror` for error types
- Document all public APIs
- Include examples in doc comments

### Pull Request Process

1. Fork and branch: `feature/description` or `fix/description`
2. Ensure tests pass: `cargo test`
3. Ensure lints pass: `cargo clippy && cargo fmt --check`
4. Update documentation if needed
5. Submit PR with clear description

### Commit Messages

Follow conventional commits:

```
feat: add process pool health checking
fix: resolve race condition in dedup cache
docs: update SPEC with security section
test: add stress tests for queue
refactor: simplify shared memory mapping
```

---

## Related Documents

| Document | Description |
|----------|-------------|
| [SOTA.md](./SOTA.md) | State of the Art research on process management systems |
| [ADRs/README.md](./ADRs/README.md) | Architecture Decision Records index |
| [PLAN.md](./PLAN.md) | Implementation phases and timeline |
| [README.md](./README.md) | Quick start and overview |

### External References

- [Tokio Documentation](https://tokio.rs/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [Linux Process Management](https://www.kernel.org/doc/html/latest/admin-guide/index.html)
- [nanovms Documentation Style](https://nanovms.com/)

---

## Appendix A: Implementation Examples

### A.1 Complete ProcessPool Example

```rust
use pheno_proc_core::{ProcessPool, PoolConfig, Command, ProcessState};
use std::time::Duration;
use tracing::{info, warn, error};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::fmt::init();
    
    // Configure and build pool
    let config = PoolConfig {
        min_size: 4,
        max_size: 16,
        acquire_timeout: Duration::from_secs(30),
        idle_timeout: Duration::from_secs(300),
        max_lifetime: Duration::from_secs(3600),
        health_check_interval: Duration::from_secs(30),
        health_check_cmd: Some(Command::new("/bin/true")),
        max_failures: 3,
        graceful_shutdown: true,
        shutdown_timeout: Duration::from_secs(60),
    };
    
    let pool = ProcessPool::builder()
        .config(config)
        .on_process_spawn(|id| info!("Process {} spawned", id))
        .on_process_exit(|id, status| {
            if status.success() {
                info!("Process {} exited successfully", id)
            } else {
                warn!("Process {} exited with code {:?}", id, status.code())
            }
        })
        .build()
        .await?;
    
    // Monitor pool health
    let monitor_handle = {
        let pool = pool.clone();
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(10));
            loop {
                interval.tick().await;
                let stats = pool.stats();
                info!(
                    "Pool stats: active={}, idle={}, waiting={}",
                    stats.active_count,
                    stats.idle_count,
                    stats.waiting_count
                );
            }
        })
    };
    
    // Execute commands
    let commands = vec![
        Command::new("echo").arg("Task 1"),
        Command::new("echo").arg("Task 2"),
        Command::new("echo").arg("Task 3"),
    ];
    
    let mut handles = vec![];
    for cmd in commands {
        let pool = pool.clone();
        handles.push(tokio::spawn(async move {
            let mut proc = pool.acquire().await?;
            let output = proc.run(cmd).await?;
            info!("Output: {}", String::from_utf8_lossy(&output.stdout));
            Ok::<_, pheno_proc_core::PoolError>(())
        }));
    }
    
    // Wait for completion
    for handle in handles {
        if let Err(e) = handle.await? {
            error!("Task failed: {}", e);
        }
    }
    
    // Graceful shutdown
    monitor_handle.abort();
    pool.shutdown(Duration::from_secs(30)).await?;
    info!("Pool shutdown complete");
    
    Ok(())
}
```

### A.2 Complete DedupCache Example

```rust
use pheno_proc_core::Command;
use pheno_proc_dedup::{DedupCache, DedupConfig, HashAlgorithm};
use std::time::Duration;
use tracing::info;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Configure dedup cache
    let config = DedupConfig {
        cache_capacity: 1000,
        success_ttl: Duration::from_secs(600),
        failure_ttl: Duration::from_secs(60),
        cache_failures: false,
        hash_algorithm: HashAlgorithm::Blake3,
    };
    
    let cache = DedupCache::with_config(config);
    let pool = ProcessPool::builder().max_size(4).build().await?;
    
    // Simulate concurrent identical commands
    let cmd = Command::new("sleep").arg("1");  // 1-second command
    
    let start = std::time::Instant::now();
    let mut handles = vec![];
    
    for i in 0..5 {
        let cache = cache.clone();
        let pool = pool.clone();
        let cmd = cmd.clone();
        
        handles.push(tokio::spawn(async move {
            let result = cache.execute(cmd, |c| async {
                let mut proc = pool.acquire().await.unwrap();
                proc.run(c).await.unwrap()
            }).await;
            
            info!("Task {} completed in {:?}", i, start.elapsed());
            result
        }));
    }
    
    // All 5 tasks should complete in ~1 second (not 5) due to dedup
    for handle in handles {
        handle.await?;
    }
    
    let stats = cache.stats();
    info!("Cache stats: hits={}, misses={}, coalesced={}", 
          stats.hits, stats.misses, stats.coalesced);
    
    assert!(start.elapsed() < Duration::from_secs(2), 
            "Commands should be deduplicated");
    
    Ok(())
}
```

### A.3 Complete Priority Queue Example

```rust
use pheno_proc_queue::{PriorityQueue, TaskScheduler, SchedulerConfig, Priority, Task};
use std::time::{Duration, Instant};
use uuid::Uuid;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let queue = PriorityQueue::with_capacity(10000);
    
    let config = SchedulerConfig {
        num_workers: 4,
        capacity_per_priority: 10000,
        work_stealing: true,
        idle_poll_interval: Duration::from_millis(1),
        local_batch_size: 64,
        task_timeout: Some(Duration::from_secs(30)),
    };
    
    let scheduler = TaskScheduler::new(queue.clone(), config);
    
    // Process tasks based on priority
    scheduler.start(|task: Task<usize>| async move {
        let duration = Duration::from_millis(task.data as u64 * 10);
        tokio::time::sleep(duration).await;
        println!("Completed task {} (priority {:?}) in {:?}",
                 task.id, task.priority, duration);
    }).await;
    
    // Submit tasks with different priorities
    let priorities = vec![
        Priority::Critical,
        Priority::Low,
        Priority::High,
        Priority::Normal,
        Priority::Critical,
    ];
    
    for (i, priority) in priorities.iter().enumerate() {
        let task = Task {
            priority: *priority,
            data: i + 1,
            id: Uuid::new_v4(),
            submitted_at: Instant::now(),
        };
        queue.push(task).await?;
    }
    
    // Critical tasks should complete first, despite being submitted mixed with others
    tokio::time::sleep(Duration::from_secs(5)).await;
    
    scheduler.shutdown().await;
    
    Ok(())
}
```

### A.4 Complete Shared Memory Example

```rust
use pheno_proc_shm::{SharedMemory, SharedMutex, SharedCondvar, SafeSharedData};
use std::process::{Command, Stdio};
use std::os::unix::process::CommandExt;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Parent creates shared memory
    let data = Counter { count: 0, target: 100 };
    let shared: SafeSharedData<Counter> = SafeSharedData::create("/counter_shm", data)?;
    
    // Spawn child processes that increment counter
    for i in 0..4 {
        let child = unsafe {
            Command::new("./child_worker")
                .arg(i.to_string())
                .stdin(Stdio::null())
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .pre_exec(|| {
                    // Child attaches to shared memory
                    Ok(())
                })
                .spawn()?
        };
    }
    
    // Wait for all children to complete
    // ...
    
    // Read final counter value
    let final_count = shared.read(|c| c.count)?;
    println!("Final counter: {}", final_count);
    
    // Cleanup
    SharedMemory::open("/counter_shm")?.unlink()?;
    
    Ok(())
}

#[derive(Copy, Clone)]
struct Counter {
    count: u32,
    target: u32,
}
```

### A.5 Complete UDS Example

```rust
use pheno_proc_uds::{UnixListener, UnixStream, UnixDatagram};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Server
    let server = tokio::spawn(async move {
        // Use abstract namespace (Linux only)
        let listener = UnixListener::bind_abstract("test_server").await?;
        
        loop {
            let (stream, addr) = listener.accept().await?;
            tokio::spawn(handle_client(stream, addr));
        }
    });
    
    // Client
    let client = tokio::spawn(async move {
        let mut stream = UnixStream::connect(&SocketAddr::Abstract("test_server".to_string())).await?;
        
        // Get peer credentials
        let creds = stream.peer_credentials()?;
        println!("Connected to server: uid={}, gid={}, pid={:?}",
                 creds.uid, creds.gid, creds.pid);
        
        // Send message
        stream.write_all(b"Hello, server!").await?;
        
        // Receive response
        let mut buf = [0u8; 1024];
        let n = stream.read(&mut buf).await?;
        println!("Received: {}", String::from_utf8_lossy(&buf[..n]));
        
        Ok::<_, Box<dyn std::error::Error>>(())
    });
    
    tokio::time::sleep(Duration::from_secs(1)).await;
    
    client.abort();
    server.abort();
    
    Ok(())
}

async fn handle_client(mut stream: UnixStream, addr: SocketAddr) -> Result<(), Box<dyn std::error::Error>> {
    let creds = stream.peer_credentials()?;
    println!("Client connected from {:?}: uid={}", addr, creds.uid);
    
    let mut buf = [0u8; 1024];
    let n = stream.read(&mut buf).await?;
    
    let response = format!("Echo: {}", String::from_utf8_lossy(&buf[..n]));
    stream.write_all(response.as_bytes()).await?;
    
    Ok(())
}
```

---

## Appendix B: Platform-Specific Notes

### B.1 Linux-Specific Features

#### Abstract Namespace Sockets

Linux supports abstract namespace Unix domain sockets:

```rust
#[cfg(target_os = "linux")]
async fn use_abstract_namespace() -> Result<(), UdsError> {
    // No filesystem entry created
    let listener = UnixListener::bind_abstract("my_app_socket").await?;
    
    // Automatically cleaned up on close
    // Not visible in filesystem
    // Works across network namespaces
    
    Ok(())
}
```

#### PID Namespaces

Process pools can leverage PID namespaces:

```rust
#[cfg(target_os = "linux")]
use nix::sched::{CloneFlags, unshare};

fn create_pid_namespace() -> Result<(), nix::Error> {
    // Requires CAP_SYS_ADMIN
    unshare(CloneFlags::CLONE_NEWPID)?;
    
    // In new PID namespace, current process becomes PID 1
    // Child processes will see this as init
    
    Ok(())
}
```

#### cgroup Integration

```rust
#[cfg(target_os = "linux")]
use std::fs;

struct CgroupLimits {
    cpu_quota_us: i64,
    cpu_period_us: i64,
    memory_max: i64,
    pids_max: i64,
}

impl CgroupLimits {
    fn apply(&self, cgroup_path: &str) -> Result<(), io::Error> {
        // cgroup v2
        fs::write(
            format!("{}/cpu.max", cgroup_path),
            format!("{} {}", self.cpu_quota_us, self.cpu_period_us)
        )?;
        
        fs::write(
            format!("{}/memory.max", cgroup_path),
            self.memory_max.to_string()
        )?;
        
        fs::write(
            format!("{}/pids.max", cgroup_path),
            self.pids_max.to_string()
        )?;
        
        Ok(())
    }
}
```

### B.2 macOS-Specific Features

#### posix_spawn on macOS

macOS has an optimized posix_spawn:

```rust
#[cfg(target_os = "macos")]
use std::os::unix::process::CommandExt;

fn spawn_with_macos_optimizations() {
    let mut cmd = std::process::Command::new("/bin/echo");
    
    // macOS supports various spawn attributes
    unsafe {
        cmd.pre_exec(|| {
            // Set QoS class for thread priority
            // Available on macOS 10.10+
            Ok(())
        });
    }
}
```

### B.3 FreeBSD-Specific Features

#### Capsicum Integration

```rust
#[cfg(target_os = "freebsd")]
mod capsicum {
    use libc::{cap_enter, cap_rights_init, cap_rights_limit};
    
    pub fn enter_capability_mode() -> Result<(), io::Error> {
        // Enter capability mode - all subsequent operations require capabilities
        let ret = unsafe { cap_enter() };
        if ret != 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(())
    }
    
    pub fn limit_fd_rights(fd: RawFd, rights: u64) -> Result<(), io::Error> {
        let mut cap_rights = unsafe { std::mem::zeroed() };
        unsafe {
            cap_rights_init(&mut cap_rights, rights, 0);
            cap_rights_limit(fd, &cap_rights);
        }
        Ok(())
    }
}
```

### B.4 Windows Compatibility

While PhenoProc targets Unix primarily, Windows support:

```rust
#[cfg(windows)]
mod windows_compat {
    // Named pipes instead of Unix domain sockets
    // Job objects instead of process groups
    // Windows-specific implementations
    
    pub struct NamedPipeListener;
    pub struct JobObject;
}
```

---

## Appendix C: Error Handling Strategy

### C.1 Error Hierarchy

```
ProcessError
├── PoolError
│   ├── Closed
│   ├── Timeout
│   ├── AtCapacity
│   ├── Unhealthy
│   └── Spawn(SpawnError)
├── DedupError
│   ├── CachePoisoned
│   ├── ExecutorFailed
│   └── Invalidated
├── QueueError
│   ├── Full
│   ├── Closed
│   └── Timeout
├── ShmError
│   ├── CreateFailed
│   ├── MapFailed
│   ├── PermissionDenied
│   ├── AlreadyExists
│   └── LockPoisoned
└── UdsError
    ├── BindFailed
    ├── ConnectFailed
    ├── SendFailed
    └── RecvFailed
```

### C.2 Error Handling Patterns

```rust
// Propagation with context
pub async fn execute_with_retry(
    &self,
    cmd: Command,
    max_retries: u32,
) -> Result<Output, ProcessError> {
    let mut last_error = None;
    
    for attempt in 0..max_retries {
        match self.execute(cmd.clone()).await {
            Ok(output) => return Ok(output),
            Err(e) if e.is_retryable() => {
                tracing::warn!("Attempt {} failed: {}", attempt, e);
                last_error = Some(e);
                tokio::time::sleep(Duration::from_millis(100 * 2u64.pow(attempt))).await;
            }
            Err(e) => return Err(e),
        }
    }
    
    Err(last_error.unwrap_or_else(|| ProcessError::ExhaustedRetries))
}

// Error classification
trait Retryable {
    fn is_retryable(&self) -> bool;
}

impl Retryable for ProcessError {
    fn is_retryable(&self) -> bool {
        matches!(self,
            ProcessError::Pool(PoolError::Timeout) |
            ProcessError::Pool(PoolError::Unhealthy(_)) |
            ProcessError::Uds(UdsError::ConnectFailed)
        )
    }
}
```

### C.3 Structured Logging

```rust
use tracing::{info, info_span, Instrument};

impl ProcessPool {
    pub async fn acquire(&self) -> Result<ProcessHandle, PoolError> {
        let span = info_span!("pool_acquire", pool_id = %self.id);
        
        async move {
            info!("Acquiring process from pool");
            
            match self.try_acquire().await {
                Ok(handle) => {
                    info!(process_id = %handle.id, "Process acquired");
                    Ok(handle)
                }
                Err(e) => {
                    tracing::error!(error = %e, "Failed to acquire process");
                    Err(e)
                }
            }
        }
        .instrument(span)
        .await
    }
}
```

---

## Appendix D: Metrics and Observability

### D.1 Prometheus Metrics

```rust
use metrics::{counter, gauge, histogram, describe_counter, describe_gauge};

pub struct PoolMetrics {
    pool_id: String,
}

impl PoolMetrics {
    pub fn new(pool_id: String) -> Self {
        describe_counter!(
            "phenoproc_pool_acquire_total",
            "Total pool acquisitions"
        );
        describe_gauge!(
            "phenoproc_pool_active_processes",
            "Current active processes in pool"
        );
        describe_gauge!(
            "phenoproc_pool_idle_processes", 
            "Current idle processes in pool"
        );
        
        Self { pool_id }
    }
    
    pub fn record_acquire(&self, duration: Duration, success: bool) {
        counter!("phenoproc_pool_acquire_total",
            "pool_id" => self.pool_id.clone(),
            "success" => success.to_string()
        );
        
        histogram!(
            "phenoproc_pool_acquire_duration_seconds",
            duration.as_secs_f64(),
            "pool_id" => self.pool_id.clone()
        );
    }
    
    pub fn update_pool_size(&self, active: usize, idle: usize) {
        gauge!(
            "phenoproc_pool_active_processes",
            active as f64,
            "pool_id" => self.pool_id.clone()
        );
        
        gauge!(
            "phenoproc_pool_idle_processes",
            idle as f64,
            "pool_id" => self.pool_id.clone()
        );
    }
}
```

### D.2 Distributed Tracing

```rust
use opentelemetry::trace::{Tracer, SpanKind};
use tracing_opentelemetry::OpenTelemetrySpanExt;

pub async fn execute_traced(
    &self,
    cmd: Command,
) -> Result<Output, ProcessError> {
    let tracer = global::tracer("phenoproc");
    
    let mut span = tracer
        .span_builder("process.execute")
        .with_kind(SpanKind::Internal)
        .start(&tracer);
    
    span.set_attribute(KeyValue::new("command.program", cmd.program.to_string_lossy().to_string()));
    span.set_attribute(KeyValue::new("command.args_count", cmd.args.len() as i64));
    
    let cx = Context::current_with_span(span);
    
    async move {
        // Execute with trace context
        let result = self.execute_internal(cmd).await;
        
        match &result {
            Ok(output) => {
                tracing::Span::current()
                    .set_attribute(KeyValue::new("process.exit_code", output.status.code().unwrap_or(-1) as i64));
            }
            Err(e) => {
                tracing::Span::current()
                    .set_attribute(KeyValue::new("error.message", e.to_string()));
                tracing::Span::current()
                    .set_attribute(KeyValue::new("error.type", std::any::type_name_of_val(e)));
            }
        }
        
        result
    }
    .with_context(cx)
    .await
}
```

---

## Appendix E: Performance Tuning Guide

### E.1 Pool Tuning

Finding optimal pool size:

```
Pool Size Formula:

For CPU-bound tasks:
  optimal_size = num_cpus

For IO-bound tasks:
  optimal_size = num_cpus * (1 + wait_time / service_time)

For mixed workloads:
  optimal_size = num_cpus * 2  // Starting point

Measure and adjust:
  - Monitor queue wait times
  - Monitor CPU utilization
  - Target: queue time < 10ms, CPU 70-80%
```

### E.2 Memory Tuning

Shared memory sizing:

```
SHM Size Guidelines:

Small data (counters, flags):
  4KB (single page)

Medium data (buffers, queues):
  64KB - 1MB

Large data (databases, caches):
  Size for working set + 20% headroom

Huge pages (2MB):
  Consider for >2MB mappings
  Reduces TLB pressure
```

### E.3 Queue Tuning

```rust
// Adaptive queue sizing
pub fn optimal_queue_capacity() -> usize {
    let num_workers = num_cpus::get();
    let target_latency_ms = 10;
    let task_duration_ms = estimate_task_duration();
    
    // Capacity for target_latency worth of tasks per worker
    (num_workers * target_latency_ms / task_duration_ms.max(1)) * 2
}
```

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2026-04-04 | 0.1.0 | Initial comprehensive specification |
| 2026-04-04 | 0.1.0 | Added Appendices A-E with examples and tuning guides |

---

## License

This specification is licensed under the MIT License.

---

**End of Document**
