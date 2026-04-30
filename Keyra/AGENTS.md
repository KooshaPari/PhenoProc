# AGENTS.md — Keyra

## Project Overview

- **Name**: Keyra (Key Management Service)
- **Description**: Cryptographic key management service with HSM integration, key rotation, and secure key lifecycle management
- **Location**: `/Users/kooshapari/CodeProjects/Phenotype/repos/Keyra`
- **Language Stack**: Rust (Edition 2024), PostgreSQL, HashiCorp Vault
- **Published**: Private (Phenotype org)

## Quick Start Commands

```bash
# Clone and setup
git clone https://github.com/KooshaPari/Keyra.git
cd Keyra

# Install Rust toolchain
rustup update nightly
rustup default nightly

# Build
cargo build --release

# Run tests
cargo test
cargo nextest run

# Setup
cargo run --bin keyra -- setup
```

## Architecture

### Key Management Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Key Lifecycle Layer                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   Generate        │  │   Store         │  │   Rotate        │         │
│  │   (Create)        │  │   (Encrypt)     │  │   (Renew)       │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
└───────────┼────────────────────┼────────────────────┼────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Keyra Core (Rust)                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Key Management Service                        │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │
│  │  │   Key      │  │   Policy   │  │   Access   │            │   │
│  │  │   Store    │  │   Engine   │  │   Control  │            │   │
│  │  └────────────┘  └────────────┘  └────────────┘            │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │
│  │  │   Audit    │  │   Rotation │  │   Backup   │            │   │
│  │  │   Log      │  │   Scheduler│  │   Manager  │            │   │
│  │  └────────────┘  └────────────┘  └────────────┘            │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Storage Backends                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   HashiCorp       │  │   AWS KMS       │  │   HSM           │         │
│  │   Vault           │  │   (Cloud)       │  │   (Hardware)    │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Key Hierarchy Model                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Master Key (KEK)                            │  │
│  │                    (HSM Protected)                           │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
│                              │                                       │
│              ┌───────────────┼───────────────┐                       │
│              ▼               ▼               ▼                       │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │   Key-Enc    │   │   Data-Enc   │   │   Signing    │            │
│  │   Keys       │   │   Keys       │   │   Keys       │            │
│  │   (DEKs)     │   │   (DEKs)     │   │              │            │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘            │
│         │                  │                  │                      │
│         └──────────────────┴──────────────────┘                      │
│                            │                                         │
│                            ▼                                         │
│                   ┌──────────────┐                                   │
│                   │  Data/Sign   │                                   │
│                   │  Operations  │                                   │
│                   └──────────────┘                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Quality Standards

### Rust Code Quality

- **Formatter**: `rustfmt` (nightly)
- **Linter**: `clippy -- -D warnings`
- **Tests**: `cargo nextest run` with coverage >85%
- **Security**: Regular security audits

### Key Management Standards

- FIPS 140-2 Level 2+ compliance
- Key rotation every 90 days (configurable)
- HSM for root key protection
- Audit logging for all key operations
- Access control via RBAC

### Test Requirements

```bash
# Unit tests
cargo test

# Integration tests
cargo test --test integration

# Security tests
cargo test --features security-tests

# Nextest
cargo nextest run
```

## Git Workflow

### Branch Naming

Format: `<type>/<component>/<description>`

Types: `feat`, `fix`, `security`, `docs`, `refactor`

Examples:
- `feat/rotation/add-automated-rotation`
- `security/hsm/add-pkcs11-support`
- `fix/storage/handle-vault-timeout`
- `refactor/api/extract-grpc-service`

### Commit Messages

Format: `<type>(<scope>): <description>`

Security commits must include `Security:` trailer.

Examples:
- `feat(rotation): implement automated key rotation with notifications`
- `security(hsm): add PKCS#11 HSM integration`
- `fix(storage): handle Vault timeout gracefully`

## File Structure

```
Keyra/
├── src/
│   ├── bin/                # Binary entry points
│   │   └── keyra.rs        # Main server
│   ├── core/               # Core systems
│   │   ├── key_store.rs      # Key storage
│   │   ├── policy.rs         # Policy engine
│   │   └── access.rs         # Access control
│   ├── backends/           # Storage backends
│   │   ├── vault.rs          # HashiCorp Vault
│   │   ├── awskms.rs         # AWS KMS
│   │   └── hsm.rs            # HSM integration
│   ├── crypto/             # Cryptographic operations
│   │   ├── generate.rs       # Key generation
│   │   ├── rotate.rs         # Key rotation
│   │   └── derive.rs         # Key derivation
│   └── api/                # API layer
│       ├── grpc.rs           # gRPC service
│       └── rest.rs           # REST API
├── tests/                  # Integration tests
└── docs/                   # Documentation
```

## CLI Commands

```bash
# Generate key
cargo run --bin keyra -- key generate --type aes-256 --name my-key

# List keys
cargo run --bin keyra -- key list

# Rotate key
cargo run --bin keyra -- key rotate --id key-123

# Encrypt data
cargo run --bin keyra -- encrypt --key key-123 --data "secret"

# Decrypt data
cargo run --bin keyra -- decrypt --key key-123 --ciphertext "..."
```

## Environment Variables

```bash
# Server
KEYRA_PORT=8080
KEYRA_HSM_ENABLED=true

# Vault
VAULT_ADDR=https://vault.example.com:8200
VAULT_TOKEN=s.xxx

# AWS KMS
AWS_REGION=us-east-1
AWS_KMS_KEY_ID=alias/my-key

# Audit
AUDIT_LOG_PATH=/var/log/keyra/audit.log
```

---

Last Updated: 2026-04-05
Version: 1.0.0
