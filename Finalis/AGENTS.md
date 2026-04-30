# AGENTS.md — Finalis

## Project Overview

- **Name**: Finalis (Workflow Finalization Engine)
- **Description**: Workflow completion and finalization engine for orchestrating complex multi-step processes with deterministic outcomes
- **Location**: `/Users/kooshapari/CodeProjects/Phenotype/repos/Finalis`
- **Language Stack**: Rust (Edition 2024), PostgreSQL, Redis
- **Published**: Private (Phenotype org)

## Quick Start Commands

```bash
# Clone and setup
git clone https://github.com/KooshaPari/Finalis.git
cd Finalis

# Install Rust toolchain
rustup update nightly
rustup default nightly

# Build
cargo build --release

# Run tests
cargo test
cargo nextest run

# Setup database
cargo run --bin finalis -- db setup

# Start server
cargo run --bin finalis -- server
```

## Architecture

### Workflow Finalization Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Workflow Definition Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   DAG Builder     │  │   State Machine │  │   Dependencies  │         │
│  │   (Graph)         │  │   (States)      │  │   (Resolver)    │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
└───────────┼────────────────────┼────────────────────┼────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Execution Engine (Rust)                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Finalis Core                                │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │
│  │  │   Scheduler  │  │   Executor   │  │   Monitor    │            │   │
│  │  │   (Async)    │  │   (Workers)  │  │   (Observ)   │            │   │
│  │  └────────────┘  └────────────┘  └────────────┘            │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │
│  │  │   Retrier    │  │   Timeout    │  │   Circuit    │            │   │
│  │  │   (Backoff)  │  │   (Control)  │  │   (Breaker)  │            │   │
│  │  └────────────┘  └────────────┘  └────────────┘            │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Task Handlers                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   Function        │  │   Container     │  │   External      │         │
│  │   (Rust/Python)   │  │   (Docker)      │  │   (HTTP/gRPC)   │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
└───────────┼────────────────────┼────────────────────┼────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Storage & Persistence Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   PostgreSQL      │  │   Redis         │  │   Event Log     │         │
│  │   (Workflows)     │  │   (Queue/Cache) │  │   (Audit)       │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

### Workflow State Machine

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Workflow State Transitions                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐        │
│   │ PENDING │───▶│ RUNNING │───▶│COMPLETE │───▶│ FINAL   │        │
│   │         │    │         │    │         │    │         │        │
│   └─────────┘    └────┬────┘    └─────────┘    └─────────┘        │
│        │              │                                            │
│        │              │         ┌─────────┐                       │
│        │              └────────▶│ FAILED  │                       │
│        │                         │         │                       │
│        │                         └────┬────┘                       │
│        │                              │                            │
│        └──────────────────────────────┘                            │
│                    (Retry with backoff)                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### DAG Execution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Workflow DAG Execution                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│       ┌─────────┐                                                   │
│       │  Start  │                                                   │
│       └────┬────┘                                                   │
│            │                                                         │
│     ┌──────┴──────┐                                                  │
│     ▼             ▼                                                  │
│ ┌───────┐    ┌───────┐                                              │
│ │Task A │    │Task B │                                              │
│ └───┬───┘    └───┬───┘                                              │
│     │            │                                                   │
│     └──────┬─────┘                                                   │
│            ▼                                                         │
│       ┌─────────┐                                                    │
│       │ Task C  │ (depends on A & B)                                 │
│       └────┬────┘                                                    │
│            │                                                         │
│            ▼                                                         │
│       ┌─────────┐                                                    │
│       │  End    │                                                    │
│       └─────────┘                                                    │
│                                                                      │
│  Parallel: A & B execute simultaneously                              │
│  Sequential: C waits for both A & B to complete                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Quality Standards

### Rust Code Quality

- **Formatter**: `rustfmt` (nightly)
- **Linter**: `clippy --all-targets --all-features -- -D warnings`
- **Type Safety**: `#![deny(unsafe_code)]` where possible
- **Tests**: `cargo nextest run` with coverage >85%
- **Documentation**: `cargo doc --no-deps`

### Workflow Testing

- All workflows must have deterministic outcomes
- State machine transitions fully tested
- Timeout and retry logic validated
- Rollback scenarios covered

### Test Requirements

```bash
# Unit tests
cargo test

# Integration tests
cargo test --test integration

# Workflow tests
cargo test --test workflows

# Nextest (preferred)
cargo nextest run

# Coverage
cargo tarpaulin --out lcov
```

## Git Workflow

### Branch Naming

Format: `<type>/<component>/<description>`

Types: `feat`, `fix`, `docs`, `refactor`, `perf`, `workflow`

Examples:
- `feat/scheduler/add-priority-queues`
- `fix/executor/handle-panics`
- `workflow/ecommerce/add-order-flow`
- `refactor/state/extract-machine`

### Commit Messages

Format: `<type>(<scope>): <description>`

Examples:
- `feat(scheduler): implement priority queue for task scheduling`
- `fix(executor): handle worker panics gracefully with restart`
- `workflow(ecommerce): add complete order processing flow`
- `refactor(state): extract state machine into separate crate`

## File Structure

```
Finalis/
├── src/
│   ├── bin/                # Binary entry points
│   │   └── finalis.rs      # Main server binary
│   ├── lib.rs              # Library root
│   ├── core/               # Core engine
│   │   ├── scheduler.rs      # Task scheduler
│   │   ├── executor.rs       # Task executor
│   │   ├── state_machine.rs  # State management
│   │   └── dag.rs            # DAG operations
│   ├── handlers/           # Task handlers
│   │   ├── function.rs       # Function handler
│   │   ├── container.rs      # Container handler
│   │   └── external.rs       # External API handler
│   ├── storage/            # Data persistence
│   │   ├── postgres.rs       # PostgreSQL adapter
│   │   ├── redis.rs          # Redis adapter
│   │   └── event_log.rs      # Event sourcing
│   └── api/                # API layer
│       ├── routes.rs         # HTTP routes
│       └── models.rs         # API models
├── workflows/              # Workflow definitions
│   └── examples/
├── tests/                  # Integration tests
├── benches/                # Benchmarks
└── docs/                   # Documentation
```

## CLI Commands

### Server Operations

```bash
# Start server
cargo run --bin finalis -- server

# Start with config
cargo run --bin finalis -- server --config ./config.toml

# Start with specific port
cargo run --bin finalis -- server --port 8080

# Start workers only
cargo run --bin finalis -- worker
```

### Database Operations

```bash
# Setup database
cargo run --bin finalis -- db setup

# Run migrations
cargo run --bin finalis -- db migrate

# Rollback migration
cargo run --bin finalis -- db rollback

# Reset database
cargo run --bin finalis -- db reset
```

### Workflow Management

```bash
# Submit workflow
cargo run --bin finalis -- workflow submit --file workflow.yaml

# List workflows
cargo run --bin finalis -- workflow list

# Get status
cargo run --bin finalis -- workflow status --id wf-123

# Cancel workflow
cargo run --bin finalis -- workflow cancel --id wf-123

# Retry failed
cargo run --bin finalis -- workflow retry --id wf-123
```

### Task Operations

```bash
# List tasks
cargo run --bin finalis -- task list --workflow wf-123

# Get task details
cargo run --bin finalis -- task get --id task-456

# Rerun task
cargo run --bin finalis -- task rerun --id task-456
```

## Troubleshooting

### Workflow Stuck

```bash
# Check workflow status
cargo run --bin finalis -- workflow status --id wf-123

# List pending tasks
cargo run --bin finalis -- task list --status pending

# Check workers
cargo run --bin finalis -- worker status

# Restart stuck workflow
cargo run --bin finalis -- workflow kick --id wf-123
```

### Database Connection Issues

```bash
# Check PostgreSQL
pg_isready -h localhost -p 5432

# Check Redis
redis-cli ping

# Verify connection strings
echo $DATABASE_URL
echo $REDIS_URL

# Test connections
cargo run --bin finalis -- db test
```

### Worker Issues

```bash
# Check worker health
cargo run --bin finalis -- worker health

# Restart workers
cargo run --bin finalis -- worker restart

# Scale workers
cargo run --bin finalis -- worker scale --count 10

# View worker logs
cargo run --bin finalis -- worker logs --id worker-1
```

### Build Failures

```bash
# Clean build
cargo clean
cargo build

# Update dependencies
cargo update

# Check toolchain
rustup show

# Fix lockfile
rm Cargo.lock
cargo build
```

## Environment Variables

```bash
# Server
FINALIS_PORT=8080
FINALIS_HOST=0.0.0.0
RUST_LOG=info

# Database
DATABASE_URL=postgresql://finalis:pass@localhost:5432/finalis
DATABASE_POOL_SIZE=10

# Redis
REDIS_URL=redis://localhost:6379/0

# Workers
WORKER_COUNT=5
WORKER_QUEUE=default
WORKER_TIMEOUT=300

# Workflow
MAX_RETRIES=3
RETRY_BACKOFF=exponential
DEFAULT_TIMEOUT=300
```

## Integration Points

| System | Protocol | Purpose |
|--------|----------|---------|
| PhenoMCP | REST | Agent workflows |
| HeliosApp | gRPC | Deployment flows |
| Portage | Events | CI/CD pipelines |
| TheGent | REST | Task execution |

---

Last Updated: 2026-04-05
Version: 1.0.0
