# State-of-the-Art Research: Credentials Management Systems

**Document ID:** PHENOTYPE_CREDENTIALS_SOTA_001  
**Status:** Active Research  
**Last Updated:** 2026-04-03  
**Author:** Phenotype Architecture Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Space Definition](#2-problem-space-definition)
3. [Technology Landscape Analysis](#3-technology-landscape-analysis)
4. [Secret Storage Backends](#4-secret-storage-backends)
5. [Key Management Systems](#5-key-management-systems)
6. [Encryption Models](#6-encryption-models)
7. [Credential Rotation Strategies](#7-credential-rotation-strategies)
8. [Hierarchical Scoping Models](#8-hierarchical-scoping-models)
9. [OAuth and Token Management](#9-oauth-and-token-management)
10. [Audit and Compliance](#10-audit-and-compliance)
11. [Comparison Matrices](#11-comparison-matrices)
12. [Code Examples and Patterns](#12-code-examples-and-patterns)
13. [Security Considerations](#13-security-considerations)
14. [Emerging Trends](#14-emerging-trends)
15. [References](#15-references)

---

## 1. Executive Summary

### 1.1 Overview

This document presents a comprehensive state-of-the-art (SOTA) analysis of credential management systems, secret storage technologies, key management systems, and related security infrastructure. The research is conducted to inform the architecture and design decisions for `pheno-credentials`, a credential management system within the Phenotype ecosystem.

### 1.2 Key Findings

- **Multi-backend storage** is the industry standard, with OS keyring integration combined with encrypted file storage providing the best balance of security and portability
- **Fernet encryption** (AES-128-CBC with HMAC-SHA256) is widely adopted for application-level encryption, though modern systems are migrating to AES-256-GCM
- **PBKDF2 with 100,000+ iterations** remains the standard for key derivation, with Argon2id emerging as the preferred alternative
- **Hierarchical credential scoping** is increasingly adopted by enterprise systems, with tree-based resolution providing predictable override semantics
- **Automated credential rotation** is becoming table-stakes, with scheduled rotation, event-driven rotation, and policy-based rotation being the three dominant patterns
- **Zero-trust credential access** requires audit logging, least-privilege scoping, and temporal access controls

### 1.3 Recommendations

Based on this research, the following architectural decisions are recommended for pheno-credentials:

1. Maintain the composite storage pattern (KeyringStore + EncryptedFileStore)
2. Upgrade encryption from Fernet to AES-256-GCM for new deployments
3. Implement Argon2id as an alternative key derivation function
4. Expand hierarchical scoping to support dynamic depth
5. Add automated credential rotation with configurable policies
6. Implement structured audit logging with tamper-evident chains

---

## 2. Problem Space Definition

### 2.1 Core Challenges

Credential management systems must solve several interconnected challenges:

| Challenge | Description | Impact |
|-----------|-------------|--------|
| **Secure Storage** | Protecting credentials at rest and in transit | Critical |
| **Access Control** | Ensuring only authorized entities can access credentials | Critical |
| **Credential Lifecycle** | Managing creation, rotation, and revocation | High |
| **Multi-tenant Isolation** | Separating credentials across projects/environments | High |
| **Auditability** | Tracking all credential access and modifications | High |
| **Developer Experience** | Making secure practices the easy path | Medium |
| **Portability** | Working across different OS and deployment environments | Medium |
| **Scalability** | Handling growing numbers of credentials efficiently | Medium |

### 2.2 Threat Model

The threat model for pheno-credentials includes:

```
┌─────────────────────────────────────────────────────────────┐
│                     THREAT MODEL                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │  Attacker    │     │  Insider     │     │  Compromised │ │
│  │  (External)  │     │  Threat      │     │  Dependency  │ │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘ │
│         │                    │                     │         │
│         ▼                    ▼                     ▼         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Attack Surfaces                         │   │
│  │  • File system access to credential store            │   │
│  │  • Memory scraping of decrypted values               │   │
│  │  • Keyring compromise (OS-level)                     │   │
│  │  • Master password brute-force                       │   │
│  │  • Supply chain attack via dependencies              │   │
│  │  • Side-channel attacks on encryption                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Defensive Measures                      │   │
│  │  • Encryption at rest (AES-256-GCM)                  │   │
│  │  • OS keyring integration                            │   │
│  │  • PBKDF2/Argon2id key derivation                    │   │
│  │  • Audit logging with tamper detection               │   │
│  │  • Credential expiration and rotation                │   │
│  │  • Hierarchical access control                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Requirements Analysis

Based on the threat model and core challenges, the system requirements are:

**Functional Requirements:**
- FR-001: Store and retrieve credentials securely
- FR-002: Support multiple credential types (API keys, OAuth tokens, passwords, certificates, SSH keys)
- FR-003: Provide hierarchical scoping for credential resolution
- FR-004: Support credential rotation and expiration
- FR-005: Maintain audit logs of all credential operations
- FR-006: Integrate with OS-level credential stores
- FR-007: Provide CLI and programmatic interfaces
- FR-008: Support OAuth flow automation

**Non-Functional Requirements:**
- NFR-001: Encryption must use industry-standard algorithms
- NFR-002: Credential retrieval must complete within 50ms
- NFR-003: System must work on macOS, Linux, and Windows
- NFR-004: Audit logs must be tamper-evident
- NFR-005: Master password must never be stored on disk

---

## 3. Technology Landscape Analysis

### 3.1 Credential Management Ecosystem

The credential management landscape spans several categories:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CREDENTIAL MANAGEMENT LANDSCAPE                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │  Secret Managers │  │  Key Management │  │  Identity &     │     │
│  │  (Cloud)         │  │  Systems (KMS)  │  │  Access Mgmt    │     │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤     │
│  │ AWS Secrets Mgr │  │ AWS KMS         │  │ HashiCorp Vault │     │
│  │ GCP Secret Mgr  │  │ GCP KMS         │  │ Keycloak        │     │
│  │ Azure Key Vault │  │ Azure Key Vault │  │ Okta            │     │
│  │ Doppler         │  │ Thales KMS      │  │ Auth0           │     │
│  │ Akeyless        │  │ Entrust KMS     │  │ Ping Identity   │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │  Local Secret    │  │  Config Mgmt    │  │  Dev Tools      │     │
│  │  Storage         │  │  & Env Vars     │  │  & CLIs         │     │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤     │
│  │ OS Keyring      │  │ dotenv          │  │ 1Password CLI   │     │
│  │ Encrypted Files │  │ python-decouple │  │ Bitwarden CLI   │     │
│  │ GNOME Keyring   │  │ environs        │  │ pass            │     │
│  │ macOS Keychain  │  │ dynaconf        │  │ gopass          │     │
│  │ Windows CredMgr │  │ configobj       │  │ sops            │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              pheno-credentials (This Project)               │   │
│  │  • Composite storage (Keyring + Encrypted Files)            │   │
│  │  • Hierarchical scoping                                     │   │
│  │  • OAuth automation                                         │   │
│  │  • Audit logging                                            │   │
│  │  • CLI + TUI + Programmatic API                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Open Source Credential Management Tools

#### 3.2.1 `pass` (Standard Unix Password Manager)

**Architecture:** GPG-encrypted files in a directory tree, managed via Git.

```
~/.password-store/
├── work/
│   ├── aws/
│   │   ├── access_key.gpg
│   │   └── secret_key.gpg
│   └── github/
│       └── token.gpg
└── personal/
    └── email/
        └── password.gpg
```

**Strengths:**
- Simple, auditable design
- Git integration for version control
- Extensible via shell scripts
- No central server required

**Weaknesses:**
- Requires GPG key management
- No built-in rotation
- Limited metadata support
- No hierarchical resolution

#### 3.2.2 `sops` (Secrets OPerationS)

**Architecture:** Encrypts values within YAML/JSON/ENV/BINI files using AWS KMS, GCP KMS, Azure Key Vault, PGP, or age.

```yaml
# config.enc.yaml
database:
  host: db.example.com
  password: ENC[AES256_GCM,data:xyz,iv:abc,tag:def,type:str]
api_key: ENC[AES256_GCM,data:uvw,iv:rst,tag:opq,type:str]
```

**Strengths:**
- Encrypts in-place within config files
- Multiple KMS backends
- Supports structured data
- Git-friendly (only encrypted values change)

**Weaknesses:**
- Requires external KMS for production use
- No credential lifecycle management
- No audit logging
- Not designed for runtime credential resolution

#### 3.2.3 `gopass`

**Architecture:** Go rewrite of `pass` with additional features including team sharing, OTP support, and secret server integration.

**Strengths:**
- Team sharing via Git
- OTP (one-time password) support
- Multiple stores
- Browser extension

**Weaknesses:**
- Complex configuration
- GPG dependency
- No hierarchical credential resolution
- No automated rotation

#### 3.2.4 `1Password CLI` (`op`)

**Architecture:** Commercial password manager with CLI access, using Secret Reference format.

```bash
# Secret Reference format
export DB_PASSWORD="$(op read op://vault/item/field)"
```

**Strengths:**
- Excellent UX
- Cross-platform sync
- Secret references in config files
- Biometric authentication

**Weaknesses:**
- Commercial (not open source)
- Requires 1Password subscription
- Cloud-dependent
- Not embeddable in applications

### 3.3 Cloud-Native Secret Managers

#### 3.3.1 AWS Secrets Manager

**Key Features:**
- Automatic rotation (Lambda-based)
- Cross-region replication
- Integration with RDS, Redshift, DocumentDB
- Fine-grained IAM policies
- Encryption via AWS KMS

**Rotation Architecture:**
```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  Secrets    │    │  Rotation    │    │  Database    │
│  Manager    │───▶│  Lambda      │───▶│  Service     │
│             │    │  Function    │    │              │
└──────┬──────┘    └──────────────┘    └──────────────┘
       │                                      │
       │         ┌──────────────┐             │
       └────────▶│  SNS/SQS     │◀────────────┘
                 │  Events      │
                 └──────────────┘
```

**Cost:** $0.40/secret/month + $0.05/10,000 API calls

#### 3.3.2 HashiCorp Vault

**Key Features:**
- Dynamic secrets (generate credentials on-demand)
- Leases and automatic revocation
- Multiple auth methods (AppRole, Kubernetes, JWT, etc.)
- Transit encryption engine
- PKI certificate management
- Audit logging with multiple backends

**Architecture:**
```
┌──────────────────────────────────────────────────────────┐
│                      Vault Server                        │
├──────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  KV v2   │  │  Transit │  │   PKI    │  │  SSH     │ │
│  │  Engine  │  │  Engine  │  │  Engine  │  │  Engine  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │              │             │              │       │
│  ┌────┴──────────────┴─────────────┴──────────────┴─────┐│
│  │                    Storage Backend                    ││
│  │         (Raft, Consul, S3, DynamoDB, etc.)           ││
│  └──────────────────────────────────────────────────────┘│
│                                                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │                  Auth Methods                        ││
│  │  Token  AppRole  Kubernetes  JWT  LDAP  OIDC  AWS    ││
│  └──────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

**Strengths:**
- Dynamic secret generation
- Comprehensive audit logging
- Multi-datacenter replication
- Extensible via secret engines

**Weaknesses:**
- Complex operational overhead
- Steep learning curve
- Resource-intensive
- Overkill for local development

---

## 4. Secret Storage Backends

### 4.1 OS-Level Keyring Systems

#### 4.1.1 macOS Keychain

**Architecture:**
- Encrypted SQLite database (`~/Library/Keychains/`)
- Secured by login password
- Access controlled via ACLs
- Supports generic passwords, certificates, keys, and notes

**Python Access:** `keyring` library via `keyring.backends.macOS.Keyring`

**Security Properties:**
- Data encrypted with AES-256
- Key protected by user's login password
- Access requires user consent (first time)
- Supports hardware security modules (Secure Enclave on Apple Silicon)

#### 4.1.2 Windows Credential Manager

**Architecture:**
- DPAPI (Data Protection API) encryption
- Stored in `%LOCALAPPDATA%\Microsoft\Credentials\`
- Tied to user's Windows account
- Supports generic credentials and domain credentials

**Python Access:** `keyring` library via `keyring.backends.Windows.WinVaultKeyring`

**Security Properties:**
- Encryption key derived from user's login credentials
- Automatic protection (no explicit encryption needed)
- Roaming credentials via domain accounts

#### 4.1.3 Linux Secret Service (GNOME Keyring / KDE Wallet)

**Architecture:**
- D-Bus based Secret Service API
- GNOME Keyring: libsecret backend
- KDE Wallet: kwallet backend
- Collection-based organization

**Python Access:** `keyring` library via `keyring.backends.SecretService.Keyring`

**Security Properties:**
- Encrypted with user's login password
- Unlock on login (PAM integration)
- Network storage support (for roaming profiles)

### 4.2 Encrypted File Storage

#### 4.2.1 File-Based Encryption Patterns

**Pattern 1: Per-Credential Encryption**
```
~/.pheno/credentials/
├── cache.json          # Encrypted credential cache
├── keys/
│   └── default.key     # Encrypted key material
└── metadata/
    └── index.json      # Non-sensitive metadata
```

**Pattern 2: Single Encrypted Blob**
```
~/.pheno/credentials/
└── vault.enc           # Single encrypted file containing all credentials
```

**Pattern 3: Directory-Based (like pass)**
```
~/.pheno/credentials/
├── OPENAI_API_KEY.enc
├── GITHUB_TOKEN.enc
└── DATABASE_URL.enc
```

#### 4.2.2 Encryption Algorithm Comparison

| Algorithm | Key Size | Mode | Authenticated | Performance | Recommendation |
|-----------|----------|------|---------------|-------------|----------------|
| AES-128-CBC + HMAC | 128-bit | CBC | Yes (via HMAC) | Good | Current (Fernet) |
| AES-256-GCM | 256-bit | GCM | Yes (built-in) | Excellent | **Recommended** |
| ChaCha20-Poly1305 | 256-bit | Stream | Yes (built-in) | Excellent | **Recommended** |
| AES-256-CBC + HMAC | 256-bit | CBC | Yes (via HMAC) | Good | Acceptable |
| XChaCha20-Poly1305 | 256-bit | Stream | Yes (built-in) | Excellent | **Future-proof** |

**Recommendation:** Migrate from Fernet (AES-128-CBC + HMAC) to AES-256-GCM or ChaCha20-Poly1305 for new deployments. Fernet remains acceptable for backward compatibility.

### 4.3 Hybrid Storage Architecture

The composite store pattern used by pheno-credentials is the recommended approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    Composite Store                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │   KeyringStore  │         │ EncryptedFileStore│          │
│  │  (High-value    │         │  (Bulk storage,  │          │
│  │   credentials)  │         │   search, list)  │          │
│  └────────┬────────┘         └────────┬────────┘           │
│           │                           │                     │
│           ▼                           ▼                     │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │  OS Keyring     │         │  ~/.pheno/      │          │
│  │  • macOS:       │         │  credentials/   │          │
│  │    Keychain     │         │  cache.json     │          │
│  │  • Windows:     │         │                 │          │
│  │    CredMgr      │         │  AES-256-GCM    │          │
│  │  • Linux:       │         │  PBKDF2/Argon2  │          │
│  │    SecretSvc    │         │                 │          │
│  └─────────────────┘         └─────────────────┘           │
│                                                             │
│  Resolution Order:                                          │
│  1. KeyringStore (most secure, limited search)             │
│  2. EncryptedFileStore (searchable, bulk operations)       │
│  3. Environment variables (runtime override)               │
│  4. .env files (development convenience)                   │
│  5. Interactive prompt (last resort)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Key Management Systems

### 5.1 Key Derivation Functions (KDF)

#### 5.1.1 PBKDF2 (Password-Based Key Derivation Function 2)

**Current Implementation in pheno-credentials:**
```python
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
)
```

**Analysis:**
- **Iterations:** 100,000 is the OWASP recommended minimum (2023)
- **Salt:** 16 bytes (128 bits) - adequate
- **Output:** 32 bytes (256 bits) - matches AES-256 key size
- **Hash:** SHA-256 - secure

**Recommendations:**
- Increase iterations to 600,000 (OWASP 2024 recommendation for PBKDF2-HMAC-SHA256)
- Consider migrating to Argon2id for new deployments

#### 5.1.2 Argon2id

**Analysis:**
- Winner of the Password Hashing Competition (2015)
- Memory-hard function (resistant to GPU/ASIC attacks)
- Three variants: Argon2d, Argon2i, Argon2id
- **Argon2id** is recommended (hybrid of d and i variants)

**Recommended Parameters:**
```python
import argon2

ph = argon2.PasswordHasher(
    time_cost=3,        # Number of iterations
    memory_cost=65536,  # 64 MiB
    parallelism=4,      # Number of parallel threads
    hash_len=32,        # Output length (bytes)
    salt_len=16,        # Salt length (bytes)
    type=argon2.Type.ID # Argon2id variant
)
```

**Comparison:**

| Parameter | PBKDF2-SHA256 | Argon2id | scrypt |
|-----------|---------------|----------|--------|
| Memory-hard | No | Yes | Yes |
| GPU-resistant | No | Yes | Partial |
| ASIC-resistant | No | Yes | Partial |
| Standardization | NIST SP 800-132 | RFC 9106 | RFC 7914 |
| Python Support | cryptography | argon2-cffi | hashlib |
| Performance | Fast | Moderate | Moderate |
| Recommendation | Legacy | **Primary** | Alternative |

### 5.2 Key Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Key Hierarchy                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Master Password (User Input)                               │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────┐                                       │
│  │  KDF (Argon2id) │                                       │
│  │  + Salt         │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                       │
│  │  Master Key     │  ← Never stored on disk               │
│  │  (256-bit)      │                                       │
│  └────────┬────────┘                                       │
│           │                                                 │
│     ┌─────┴─────┐                                         │
│     ▼           ▼                                           │
│  ┌──────┐  ┌──────────┐                                   │
│  │ KEK  │  │  DEK     │                                   │
│  │(Key  │  │(Data     │                                   │
│  │Encr. │  │Encr.     │                                   │
│  │ Key) │  │ Key)     │                                   │
│  └──┬───┘  └────┬─────┘                                   │
│     │            │                                          │
│     ▼            ▼                                          │
│  Encrypts    Encrypts                                       │
│  other keys  credential                                     │
│              values                                         │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Key Rotation Strategies

**Strategy 1: Master Password Change**
- Re-encrypt all credentials with new master key
- Requires access to all credentials during migration
- Atomic operation (all-or-nothing)

**Strategy 2: Key Versioning**
- Maintain multiple key versions
- New credentials encrypted with latest key
- Old credentials decrypted with their original key
- Gradual migration on access

**Strategy 3: Key Wrapping**
- Wrap data encryption keys with master key
- Rotate master key by re-wrapping DEKs
- No need to re-encrypt credential values

**Recommendation:** Implement Key Versioning for pheno-credentials, as it provides the best balance of security and operational simplicity.

---

## 6. Encryption Models

### 6.1 Encryption at Rest

#### 6.1.1 Current Model: Fernet

**Implementation:**
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Key derivation
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
)
key = base64.urlsafe_b64encode(kdf.derive(master_password))

# Encryption
fernet = Fernet(key)
encrypted = fernet.encrypt(plaintext.encode())
```

**Properties:**
- AES-128-CBC encryption
- HMAC-SHA256 authentication
- Base64-encoded output
- Includes timestamp in token
- 128-bit key (derived from 256-bit PBKDF2 output, truncated)

**Limitations:**
- AES-128 (not AES-256)
- CBC mode (not authenticated encryption)
- No associated data support
- Timestamp-based replay protection only

#### 6.1.2 Recommended Model: AES-256-GCM

**Implementation:**
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

# Key derivation (Argon2id recommended)
key = derive_key(master_password, salt)  # 256-bit key

# Encryption
aesgcm = AESGCM(key)
nonce = os.urandom(12)  # 96-bit nonce
aad = b"pheno-credentials:v1"  # Associated data
ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), aad)

# Store: nonce + ciphertext
encrypted_blob = nonce + ciphertext
```

**Properties:**
- AES-256 encryption
- GCM mode (authenticated encryption)
- 96-bit nonce (random)
- Supports associated data (AAD)
- 128-bit authentication tag

**Advantages over Fernet:**
- 256-bit key (vs 128-bit)
- Authenticated encryption (built-in, not separate HMAC)
- Associated data support (can bind metadata to ciphertext)
- Better performance (hardware AES-NI acceleration)

### 6.2 Encryption in Transit

**Recommendations:**
- Use TLS 1.3 for all network communication
- Certificate pinning for OAuth token exchanges
- Mutual TLS for service-to-service communication

### 6.3 Memory Security

**Best Practices:**
- Zeroize decrypted credentials after use
- Minimize time credentials spend in memory
- Use `mlock()` to prevent swapping (Linux/macOS)
- Avoid logging credential values

**Python Implementation:**
```python
import ctypes
import ctypes.util

def secure_zero(buffer: bytes):
    """Zero out a buffer in memory."""
    libc_name = ctypes.util.find_library("c")
    libc = ctypes.CDLL(libc_name)
    libc.memset(buffer, 0, len(buffer))
```

---

## 7. Credential Rotation Strategies

### 7.1 Rotation Patterns

#### 7.1.1 Scheduled Rotation

**Description:** Rotate credentials on a fixed schedule (e.g., every 90 days).

```
┌─────────────────────────────────────────────────────────────┐
│              Scheduled Rotation Timeline                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Day 0          Day 30         Day 60         Day 90       │
│  │              │              │              │             │
│  ▼              ▼              ▼              ▼             │
│  ┌────┐    ┌────┐    ┌────┐    ┌────┐                       │
│  │Key1│    │    │    │    │    │Key2│                       │
│  │    │    │Warn│    │Warn│    │    │                       │
│  │    │    │(60d│    │(30d│    │    │                       │
│  │    │    │left)│   │left)│   │    │                       │
│  └────┘    └────┘    └────┘    └────┘                       │
│                                                             │
│  Status:      Monitor       Prepare      Rotate             │
│               & Alert       New Key      & Deactivate       │
└─────────────────────────────────────────────────────────────┘
```

**Implementation in pheno-credentials:**
```python
from datetime import datetime, timedelta

class RotationPolicy:
    def __init__(self, max_age_days: int = 90, warn_days: int = 30):
        self.max_age = timedelta(days=max_age_days)
        self.warn_threshold = timedelta(days=warn_days)

    def is_due_for_rotation(self, credential) -> bool:
        age = datetime.utcnow() - credential.created_at
        return age >= self.max_age

    def is_approaching_expiry(self, credential) -> bool:
        if not credential.expires_at:
            return False
        remaining = credential.expires_at - datetime.utcnow()
        return remaining <= self.warn_threshold
```

#### 7.1.2 Event-Driven Rotation

**Description:** Rotate credentials in response to specific events.

**Trigger Events:**
- Security incident detected
- Team member departure
- Credential exposed in logs
- Compliance audit requirement
- Suspicious access pattern detected

**Implementation:**
```python
class EventDrivenRotation:
    TRIGGER_EVENTS = [
        "security_incident",
        "team_member_departure",
        "credential_exposure",
        "compliance_audit",
        "suspicious_access",
    ]

    async def handle_event(self, event_type: str, credential_id: str):
        if event_type in self.TRIGGER_EVENTS:
            await self.rotate_credential(credential_id)
            await self.notify_stakeholders(credential_id, event_type)
```

#### 7.1.3 Policy-Based Rotation

**Description:** Rotate credentials based on configurable policies.

**Policy Definition:**
```python
class RotationPolicy:
    name: str
    credential_types: list[CredentialType]
    max_age: timedelta
    rotation_method: str  # "automatic" | "manual" | "semi-automatic"
    notification_channels: list[str]
    approval_required: bool
    rollback_window: timedelta
```

### 7.2 Rotation Strategies by Credential Type

| Credential Type | Rotation Frequency | Method | Automation Level |
|-----------------|-------------------|--------|-----------------|
| API Keys | 90 days | Generate new, revoke old | Semi-automatic |
| OAuth Tokens | Per expiry (1-24h) | Refresh token flow | Automatic |
| Passwords | 90 days | User-initiated | Manual |
| Database URLs | 30 days | Connection pool drain | Semi-automatic |
| SSH Keys | 180 days | Generate new keypair | Automatic |
| Certificates | Per expiry | ACME/Let's Encrypt | Automatic |

### 7.3 Zero-Downtime Rotation

**Pattern: Dual-Key Rotation**
```
┌─────────────────────────────────────────────────────────────┐
│              Zero-Downtime Rotation Pattern                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 1: Add New Key                                       │
│  ┌──────────┐    ┌──────────┐                              │
│  │  Key A   │    │  Key B   │  ← New key added             │
│  │ (Active) │    │(Pending) │                               │
│  └──────────┘    └──────────┘                              │
│                                                             │
│  Phase 2: Activate New Key                                  │
│  ┌──────────┐    ┌──────────┐                              │
│  │  Key A   │    │  Key B   │  ← Both keys active          │
│  │(Draining)│    │ (Active) │                               │
│  └──────────┘    └──────────┘                              │
│                                                             │
│  Phase 3: Remove Old Key                                    │
│  ┌──────────┐    ┌──────────┐                              │
│  │  Key A   │    │  Key B   │  ← Old key removed           │
│  │(Removed) │    │ (Active) │                               │
│  └──────────┘    └──────────┘                              │
│                                                             │
│  Grace Period: 24-72 hours between phases                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Hierarchical Scoping Models

### 8.1 Scope Resolution Order

The hierarchical scoping system in pheno-credentials follows a tree-based resolution model:

```
┌─────────────────────────────────────────────────────────────┐
│              Hierarchical Scope Resolution                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Resolution Order (most specific to most general):          │
│                                                             │
│  1. Environment/Project-Specific                            │
│     └─ org.group.project.env.CREDENTIAL_NAME                │
│                                                             │
│  2. Project-Specific                                        │
│     └─ org.group.project.CREDENTIAL_NAME                    │
│                                                             │
│  3. Group-Specific                                          │
│     └─ org.group.CREDENTIAL_NAME                            │
│                                                             │
│  4. Organization-Specific                                   │
│     └─ org.CREDENTIAL_NAME                                  │
│                                                             │
│  5. Global                                                  │
│     └─ CREDENTIAL_NAME                                      │
│                                                             │
│  Example Resolution Path:                                   │
│  atoms.infrastructure.platform.pheno-sdk.prod.OPENAI_API_KEY│
│  atoms.infrastructure.platform.pheno-sdk.OPENAI_API_KEY     │
│  atoms.infrastructure.platform.OPENAI_API_KEY               │
│  atoms.infrastructure.OPENAI_API_KEY                        │
│  atoms.OPENAI_API_KEY                                       │
│  OPENAI_API_KEY                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Scope Tree Structure

```
global
└── atoms (org)
    ├── infrastructure (group)
    │   └── platform (program)
    │       └── core-services (portfolio)
    │           ├── pheno-sdk (project)
    │           │   ├── dev (environment)
    │           │   ├── staging (environment)
    │           │   └── prod (environment)
    │           ├── krouter (project)
    │           └── zen-mcp-server (project)
    └── research (group)
        └── phenotype (program)
            └── analysis (project)
```

### 8.3 Comparison with Other Scoping Models

| System | Scoping Model | Resolution | Max Depth | Dynamic |
|--------|--------------|------------|-----------|---------|
| pheno-credentials | Tree-based | Bottom-up | Unlimited | Yes |
| AWS Secrets Manager | Path-based | Exact match | 10 levels | No |
| HashiCorp Vault | Path-based | Exact match | Unlimited | No |
| Kubernetes Secrets | Namespace-based | Namespace | 2 levels | No |
| Doppler | Project/Environment | Config-based | 3 levels | No |
| 1Password | Vault/Item | Manual | 2 levels | No |

---

## 9. OAuth and Token Management

### 9.1 OAuth 2.0 Grant Types

| Grant Type | Use Case | Security Level | Pheno Support |
|-----------|----------|----------------|---------------|
| Authorization Code | Web applications | High | Yes |
| Authorization Code + PKCE | SPA/Mobile | High | Planned |
| Client Credentials | Service-to-service | Medium | Planned |
| Refresh Token | Token renewal | High | Yes |
| Device Code | Headless devices | Medium | Planned |

### 9.2 Token Refresh Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Token Refresh Scheduler                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │  Token      │     │  Refresh     │     │  Credential  │ │
│  │  Manager    │────▶│  Scheduler   │────▶│  Store       │ │
│  │             │     │              │     │              │ │
│  │ • Track     │     │ • Cron-based │     │ • Update     │ │
│  │   expiry    │     │   checks     │     │   tokens     │ │
│  │ • Calculate │     │ • Pre-expiry │     │ • Log access │ │
│  │   refresh   │     │   refresh    │     │ • Notify on  │ │
│  │   time      │     │ • Retry on   │     │   failure    │ │
│  │             │     │   failure    │     │              │ │
│  └─────────────┘     └──────────────┘     └──────────────┘ │
│                                                             │
│  Refresh Timeline:                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Token Issued ──▶ Warning ──▶ Refresh ──▶ Expired   │  │
│  │  (t=0)           (t=expiry-300s)  (t=expiry-60s)    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 9.3 Provider-Specific Implementations

**Supported Providers:**
- GitHub OAuth
- Google OAuth
- Microsoft OAuth
- OpenAI OAuth
- Generic OAuth (configurable endpoints)

---

## 10. Audit and Compliance

### 10.1 Audit Log Structure

```json
{
  "id": "uuid",
  "credential_id": "uuid",
  "action": "read|write|delete",
  "timestamp": "2026-04-03T10:00:00Z",
  "user": "kooshapari",
  "project_id": "pheno-sdk",
  "ip_address": "192.168.1.1",
  "user_agent": "pheno-credentials/3.11",
  "success": true,
  "error_message": null
}
```

### 10.2 Security Alert Detection

| Alert Type | Threshold | Severity | Response |
|-----------|-----------|----------|----------|
| High failure rate | >10 failed attempts | High | Lock credentials |
| Unusual activity | >100 accesses/hour | Medium | Investigate |
| Off-hours access | Outside business hours | Low | Log and monitor |
| Cross-project access | Access outside project scope | Medium | Alert admin |
| Bulk export | Export of >10 credentials | High | Require approval |

### 10.3 Compliance Frameworks

- **SOC 2 Type II:** Audit logging, access controls, encryption
- **ISO 27001:** Information security management
- **GDPR:** Data protection and privacy
- **HIPAA:** Healthcare data protection (if applicable)

---

## 11. Comparison Matrices

### 11.1 Storage Backend Comparison

| Feature | KeyringStore | EncryptedFileStore | CompositeStore |
|---------|-------------|-------------------|----------------|
| Security | OS-level | Application-level | Best of both |
| Search | No | Yes | Yes |
| List Keys | No | Yes | Yes |
| Cross-platform | Yes | Yes | Yes |
| Performance | Fast | Moderate | Fast |
| Backup | OS-managed | Manual | Manual |
| Sync | OS-managed | Git-friendly | Git-friendly |
| Recommendation | High-value creds | Bulk storage | **Primary** |

### 11.2 Encryption Algorithm Comparison

| Feature | Fernet | AES-256-GCM | ChaCha20-Poly1305 |
|---------|--------|-------------|-------------------|
| Key Size | 128-bit | 256-bit | 256-bit |
| Authentication | HMAC-SHA256 | Built-in | Built-in |
| Associated Data | No | Yes | Yes |
| Hardware Acceleration | AES-NI | AES-NI | None (software) |
| Python Support | cryptography | cryptography | cryptography |
| Recommendation | Legacy | **Primary** | ARM/No AES-NI |

### 11.3 KDF Comparison

| Feature | PBKDF2 | Argon2id | scrypt |
|---------|--------|----------|--------|
| Memory-hard | No | Yes | Yes |
| GPU-resistant | No | Yes | Partial |
| Standard | NIST | RFC 9106 | RFC 7914 |
| Python Support | Built-in | argon2-cffi | Built-in |
| Speed | Fast | Moderate | Moderate |
| Recommendation | Legacy | **Primary** | Alternative |

---

## 12. Code Examples and Patterns

### 12.1 Credential Resolution Chain

```python
async def resolve_credential(name: str, context: ResolutionContext) -> str:
    """Resolve credential through the full resolution chain."""
    # 1. Hierarchical scope resolution
    for scope_path in context.scope_paths:
        credential = await store.retrieve(f"{scope_path}_{name}")
        if credential and credential.is_valid:
            return decrypt(credential.value)

    # 2. Environment variables
    value = os.getenv(name)
    if value:
        return value

    # 3. .env files
    value = load_from_env_files(name)
    if value:
        return value

    # 4. Default value
    if context.default is not None:
        return context.default

    # 5. Interactive prompt
    if context.prompt:
        return prompt_user(name)

    raise CredentialNotFoundError(f"Cannot resolve {name}")
```

### 12.2 Secure Credential Storage

```python
class SecureCredentialStore:
    def __init__(self, key_derivation: str = "argon2id"):
        self.kdf = self._init_kdf(key_derivation)
        self.cipher = AESGCM(os.urandom(32))  # 256-bit key

    def store(self, credential: Credential) -> bool:
        # Encrypt value
        nonce = os.urandom(12)
        aad = f"{credential.id}:{credential.type}".encode()
        ciphertext = self.cipher.encrypt(nonce, credential.value.encode(), aad)

        # Store encrypted value with metadata
        stored = {
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "aad": base64.b64encode(aad).decode(),
            "metadata": credential.metadata,
        }

        return self._persist(stored)
```

### 12.3 Audit Log with Tamper Detection

```python
class TamperEvidentAuditLog:
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self._last_hash = self._load_last_hash()

    def log(self, entry: AuditEntry) -> None:
        # Create hash chain
        entry.previous_hash = self._last_hash
        entry_hash = self._hash_entry(entry)
        entry.entry_hash = entry_hash

        # Append to log
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

        self._last_hash = entry_hash

    def verify_integrity(self) -> bool:
        """Verify the entire log chain."""
        entries = self._load_entries()
        current_hash = None

        for entry in entries:
            if entry.previous_hash != current_hash:
                return False
            if entry.entry_hash != self._hash_entry(entry):
                return False
            current_hash = entry.entry_hash

        return True
```

---

## 13. Security Considerations

### 13.1 Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│              Defense in Depth Layers                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: Physical Security                                 │
│  └─ Disk encryption (FileVault, BitLocker, LUKS)           │
│                                                             │
│  Layer 2: OS Security                                       │
│  └─ OS Keyring (Keychain, Credential Manager, Secret Svc)  │
│                                                             │
│  Layer 3: Application Security                              │
│  └─ Fernet/AES-256-GCM encryption                          │
│  └─ PBKDF2/Argon2id key derivation                         │
│                                                             │
│  Layer 4: Access Control                                    │
│  └─ Hierarchical scoping                                   │
│  └─ Project isolation                                      │
│                                                             │
│  Layer 5: Audit & Monitoring                                │
│  └─ Tamper-evident audit logs                              │
│  └─ Security alert detection                               │
│                                                             │
│  Layer 6: Credential Lifecycle                              │
│  └─ Expiration and rotation                                │
│  └─ Automated cleanup                                      │
└─────────────────────────────────────────────────────────────┘
```

### 13.2 Common Vulnerabilities and Mitigations

| Vulnerability | Impact | Mitigation |
|--------------|--------|------------|
| Credential leakage in logs | High | Never log credential values |
| Memory scraping | Medium | Zeroize after use, mlock |
| Weak master password | High | Enforce complexity, Argon2id |
| Replay attacks | Medium | Nonces, timestamps, AAD |
| Side-channel attacks | Low | Constant-time operations |
| Supply chain attacks | High | Pin dependencies, verify signatures |
| File permission issues | Medium | Restrict file permissions (0600) |
| Race conditions | Low | Atomic file operations |

---

## 14. Emerging Trends

### 14.1 Confidential Computing

- Hardware-based encryption (Intel SGX, AMD SEV, ARM TrustZone)
- Enclave-based credential processing
- Memory encryption at the hardware level

### 14.2 Post-Quantum Cryptography

- NIST PQC standardization (CRYSTALS-Kyber, CRYSTALS-Dilithium)
- Hybrid classical/PQC key exchange
- Preparation for quantum-resistant credential storage

### 14.3 Zero-Trust Architecture

- Continuous credential validation
- Just-in-time credential access
- Ephemeral credentials for temporary access
- Identity-based access controls

### 14.4 AI-Assisted Credential Management

- Anomaly detection in access patterns
- Automated credential classification
- Intelligent rotation scheduling
- Predictive credential expiry management

### 14.5 Confidential Computing Integration

- Hardware-based trusted execution environments (TEEs)
- Intel SGX enclaves for credential processing
- AMD SEV-SNP for VM-level memory encryption
- ARM TrustZone for mobile credential storage
- AWS Nitro Enclaves for isolated credential operations

### 14.6 Decentralized Identity and Credentials

- W3C Verifiable Credentials standard
- Decentralized Identifiers (DIDs)
- Self-sovereign identity models
- Blockchain-based credential verification
- Zero-knowledge proof authentication

---

## 15. Detailed Implementation Patterns

### 15.1 Credential Ingestion Patterns

#### 15.1.1 Manual Entry Pattern

```python
def ingest_manual_credential(broker: CredentialBroker) -> bool:
    """Guide user through manual credential entry."""
    name = input("Credential name: ").strip().upper()
    value = getpass.getpass("Credential value: ")
    cred_type = input("Type (api_key/oauth_token/password/secret): ").strip()
    scope = input("Scope (global/project/environment): ").strip()
    service = input("Service (optional): ").strip()
    description = input("Description (optional): ").strip()

    return broker.store_credential(
        name=name,
        value=value,
        credential_type=cred_type,
        scope=scope,
        service=service,
        description=description,
    )
```

#### 15.1.2 Bulk Import Pattern

```python
def bulk_import_credentials(broker: CredentialBroker, file_path: Path) -> dict:
    """Import credentials from CSV/JSON file."""
    results = {"success": 0, "failed": 0, "errors": []}

    if file_path.suffix == ".json":
        with open(file_path) as f:
            credentials = json.load(f)
    elif file_path.suffix == ".csv":
        with open(file_path) as f:
            credentials = list(csv.DictReader(f))
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    for cred_data in credentials:
        try:
            success = broker.store_credential(
                name=cred_data["name"],
                value=cred_data["value"],
                credential_type=cred_data.get("type", "secret"),
                scope=cred_data.get("scope", "global"),
                service=cred_data.get("service"),
                description=cred_data.get("description"),
                tags=cred_data.get("tags", []),
            )
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Failed to store: {cred_data['name']}")
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Error storing {cred_data.get('name', 'unknown')}: {e}")

    return results
```

#### 15.1.3 Environment Variable Migration Pattern

```python
def migrate_env_to_credentials(broker: CredentialBroker, prefix: str = "") -> int:
    """Migrate environment variables to credential store."""
    migrated = 0
    env_manager = broker.environment_manager

    for key, value in os.environ.items():
        if prefix and not key.startswith(prefix):
            continue

        # Skip non-credential variables
        if not _looks_like_credential(key):
            continue

        # Check if already in store
        existing = broker.get_credential_info(key)
        if existing:
            continue

        # Store in credential store
        cred_type = env_manager._infer_credential_type(key)
        service = env_manager._infer_service(key)

        success = broker.store_credential(
            name=key,
            value=value,
            credential_type=cred_type,
            scope="global",
            service=service,
            description=f"Migrated from environment variable",
        )

        if success:
            migrated += 1

    return migrated


def _looks_like_credential(key: str) -> bool:
    """Heuristic to detect credential-like environment variables."""
    credential_indicators = [
        "KEY", "SECRET", "TOKEN", "PASSWORD", "PASSWD", "CREDENTIAL",
        "AUTH", "API", "ACCESS_KEY", "PRIVATE", "CERT",
    ]
    return any(indicator in key.upper() for indicator in credential_indicators)
```

### 15.2 Credential Validation Patterns

#### 15.2.1 API Key Validation

```python
async def validate_api_key(service: str, key: str) -> bool:
    """Validate an API key by making a test request."""
    validators = {
        "openai": _validate_openai_key,
        "github": _validate_github_token,
        "aws": _validate_aws_key,
        "google": _validate_google_key,
    }

    validator = validators.get(service)
    if not validator:
        return True  # Cannot validate unknown service

    return await validator(key)


async def _validate_openai_key(key: str) -> bool:
    """Validate OpenAI API key."""
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
        ) as response:
            return response.status == 200


async def _validate_github_token(token: str) -> bool:
    """Validate GitHub personal access token."""
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"},
        ) as response:
            return response.status == 200
```

#### 15.2.2 Database Connection Validation

```python
async def validate_database_url(url: str) -> bool:
    """Validate a database connection URL."""
    try:
        import asyncpg
        conn = await asyncpg.connect(url, timeout=5)
        await conn.close()
        return True
    except Exception:
        return False
```

### 15.3 Secure Credential Sharing Patterns

#### 15.3.1 Encrypted Export for Team Sharing

```python
def export_for_sharing(broker: CredentialBroker, recipients: list[str]) -> bytes:
    """Export credentials encrypted for specific recipients."""
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization, hashes

    credentials = broker.list_credentials()
    export_data = []

    for cred in credentials:
        export_data.append({
            "name": cred.name,
            "type": cred.type.value,
            "scope": cred.scope.value,
            "service": cred.service,
            "description": cred.description,
            "value": cred.value,  # Already encrypted with master key
        })

    # Encrypt export data with recipient public keys
    # This would use hybrid encryption (symmetric + asymmetric)
    return json.dumps(export_data).encode()
```

#### 15.3.2 Time-Limited Access Tokens

```python
def generate_access_token(credential_id: str, expires_in: int = 3600) -> str:
    """Generate a time-limited access token for a credential."""
    import jwt
    import secrets

    payload = {
        "credential_id": str(credential_id),
        "exp": datetime.utcnow() + timedelta(seconds=expires_in),
        "jti": secrets.token_urlsafe(16),  # Unique token ID
        "scope": "read",
    }

    return jwt.encode(payload, "secret-key", algorithm="HS256")
```

### 15.4 Credential Discovery Patterns

#### 15.4.1 Codebase Scanning

```python
import re
from pathlib import Path

CREDENTIAL_PATTERNS = [
    r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([A-Za-z0-9_\-]{16,})["\']',
    r'(?i)(secret[_-]?key|secret)\s*[=:]\s*["\']([A-Za-z0-9_\-]{16,})["\']',
    r'(?i)(token)\s*[=:]\s*["\']([A-Za-z0-9_\-]{16,})["\']',
    r'(?i)(password|passwd)\s*[=:]\s*["\'](.+?)["\']',
    r'(?i)(database[_-]?url|db[_-]?url)\s*[=:]\s*["\'](.+?)["\']',
]


def scan_for_credentials(directory: Path) -> list[dict]:
    """Scan codebase for hardcoded credentials."""
    findings = []

    for file_path in directory.rglob("*"):
        if file_path.suffix not in (".py", ".js", ".ts", ".yaml", ".yml", ".json", ".env", ".toml"):
            continue

        try:
            content = file_path.read_text()
            for pattern in CREDENTIAL_PATTERNS:
                for match in re.finditer(pattern, content):
                    findings.append({
                        "file": str(file_path),
                        "line": content[:match.start()].count("\n") + 1,
                        "pattern": match.group(1),
                        "value_preview": match.group(2)[:8] + "...",
                    })
        except Exception:
            continue

    return findings
```

### 15.5 Credential Lifecycle Management

#### 15.5.1 Full Lifecycle State Machine

```
┌─────────────────────────────────────────────────────────────────────┐
│              Credential Lifecycle State Machine                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │ PENDING  │───▶│  ACTIVE  │───▶│ WARNING  │───▶│ EXPIRING │     │
│  │          │    │          │    │          │    │          │     │
│  │ New cred │    │ In use   │    │ Approaching│   │ Rotation │     │
│  │ awaiting │    │ normally │    │ expiry   │    │ initiated│     │
│  │ validation│   │          │    │          │    │          │     │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘     │
│       │               │               │                │           │
│       │               │               │          ┌─────┴─────┐    │
│       │               │               │          │           │    │
│       ▼               ▼               ▼          ▼           ▼    │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐ ┌────────┐ ┌────────┐│
│  │INVALID   │   │ REVOKED  │   │ EXPIRED  │ │ACTIVE  │ │ FAILED ││
│  │          │   │          │   │          │ │(new)   │ │        ││
│  │ Validation│  │ Manually │   │ Past     │ │Rotation│ │Rotation││
│  │ failed   │   │ revoked  │   │ expiry   │ │complete│ │failed  ││
│  └──────────┘   └──────────┘   └──────────┘ └────────┘ └────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

#### 15.5.2 Lifecycle Event Handlers

```python
class CredentialLifecycleHandler:
    """Handles credential lifecycle events."""

    def __init__(self, broker: CredentialBroker):
        self.broker = broker

    def on_credential_created(self, credential: Credential):
        """Handle credential creation."""
        # Log creation event
        self.broker.audit_logger.log_access(
            credential_id=str(credential.id),
            action="create",
            success=True,
        )

        # Set expiration if not set
        if not credential.expires_at:
            policy = self._get_rotation_policy(credential.type)
            if policy:
                credential.expires_at = datetime.utcnow() + policy.max_age

    def on_credential_accessed(self, credential: Credential):
        """Handle credential access."""
        # Update last_used timestamp
        credential.last_used = datetime.utcnow()

        # Check for suspicious access patterns
        self._check_access_patterns(credential)

    def on_credential_expired(self, credential: Credential):
        """Handle credential expiration."""
        # Log expiration event
        self.broker.audit_logger.log_access(
            credential_id=str(credential.id),
            action="expire",
            success=True,
        )

        # Trigger rotation if auto-refresh enabled
        if credential.auto_refresh:
            self._trigger_rotation(credential)

    def on_credential_revoked(self, credential: Credential):
        """Handle credential revocation."""
        # Log revocation event
        self.broker.audit_logger.log_access(
            credential_id=str(credential.id),
            action="revoke",
            success=True,
        )

        # Delete from store
        self.broker.delete_credential(credential.name)

    def _check_access_patterns(self, credential: Credential):
        """Check for suspicious access patterns."""
        accesses = self.broker.audit_logger.get_access_log(
            credential_id=str(credential.id),
            limit=50,
        )

        # Check for rapid successive access
        if len(accesses) > 10:
            recent = accesses[-10:]
            time_span = recent[-1].timestamp - recent[0].timestamp
            if time_span.total_seconds() < 60:
                # More than 10 accesses in 60 seconds
                self.broker.audit_logger.log_access(
                    credential_id=str(credential.id),
                    action="suspicious_access",
                    success=False,
                    error_message="Rapid successive access detected",
                )
```

---

## 16. Performance Optimization Strategies

### 16.1 Caching Strategies

#### 16.1.1 Multi-Level Caching

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Multi-Level Caching Architecture                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Level 1: In-Memory Cache (L1)                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • Python dict with credential objects                      │   │
│  │  • TTL-based expiration (configurable)                      │   │
│  │  • LRU eviction policy                                      │   │
│  │  • Hit rate: ~95% for repeated accesses                     │   │
│  │  • Latency: <1ms                                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Level 2: File Cache (L2)                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • Encrypted JSON file (cache.json)                         │   │
│  │  • Loaded at startup, saved on every write                  │   │
│  │  • Hit rate: ~99% (after L1 miss)                          │   │
│  │  • Latency: <10ms (file I/O + decryption)                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Level 3: OS Keyring (L3)                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • OS-level credential storage                              │   │
│  │  • Used as fallback for L2 miss                             │   │
│  │  • Hit rate: ~100% (for stored credentials)                │   │
│  │  • Latency: <50ms (OS API call)                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Cache Invalidation:                                                │
│  ──────────────────                                                 │
│  • Write-through: L1 → L2 → L3 on every store/delete               │
│  • TTL-based: L1 entries expire after configurable timeout         │
│  • Event-based: External modifications trigger cache refresh       │
│  • Manual: Explicit cache.clear() method                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 16.2 Batch Operations

```python
async def batch_store_credentials(
    broker: CredentialBroker,
    credentials: list[Credential],
) -> dict:
    """Store multiple credentials efficiently."""
    results = {"success": 0, "failed": 0, "errors": []}

    # Group by storage backend for efficiency
    for credential in credentials:
        try:
            success = broker.credential_store.store(credential)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Failed to store: {credential.name}")
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Error storing {credential.name}: {e}")

    # Single audit log write for batch
    broker.audit_logger.log_access(
        credential_id="batch",
        action="batch_write",
        success=results["failed"] == 0,
        error_message=f"{results['failed']} failures in batch of {len(credentials)}",
    )

    return results
```

### 16.3 Connection Pooling for OAuth

```python
class OAuthConnectionPool:
    """Connection pool for OAuth token exchanges."""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._sessions: dict[str, aiohttp.ClientSession] = {}
        self._semaphore = asyncio.Semaphore(max_connections)

    async def get_session(self, provider: str) -> aiohttp.ClientSession:
        """Get or create HTTP session for provider."""
        if provider not in self._sessions:
            self._sessions[provider] = aiohttp.ClientSession()
        return self._sessions[provider]

    async def exchange_token(self, provider: str, url: str, data: dict) -> dict:
        """Exchange authorization code for token with connection pooling."""
        async with self._semaphore:
            session = await self.get_session(provider)
            async with session.post(url, data=data) as response:
                return await response.json()

    async def close_all(self):
        """Close all sessions."""
        for session in self._sessions.values():
            await session.close()
        self._sessions.clear()
```

---

## 17. Compliance and Regulatory Requirements

### 17.1 SOC 2 Type II Requirements

| Control | Requirement | pheno-credentials Implementation |
|---------|-------------|----------------------------------|
| CC6.1 | Logical access security | Hierarchical scoping, project isolation |
| CC6.2 | User authentication | Master password, OS keyring integration |
| CC6.3 | Role-based access | Scope-based access control |
| CC6.6 | Security event logging | AuditLogger with JSONL format |
| CC6.7 | Transmission security | TLS for OAuth, encrypted storage |
| CC6.8 | Data at rest encryption | Fernet encryption, PBKDF2 key derivation |
| CC7.1 | Monitoring | Security alert detection |
| CC7.2 | Incident response | Audit log analysis, credential revocation |

### 17.2 ISO 27001 Requirements

| Control | Requirement | pheno-credentials Implementation |
|---------|-------------|----------------------------------|
| A.9.2.1 | User registration | Project-based user context |
| A.9.2.3 | Password management | Master password, PBKDF2 derivation |
| A.9.4.1 | Information access restriction | Hierarchical scoping |
| A.10.1.1 | Cryptographic policy | Fernet encryption, configurable KDF |
| A.12.4.1 | Event logging | Comprehensive audit logging |
| A.12.4.3 | Administrator logs | User attribution in audit entries |
| A.18.1.4 | Privacy and PII protection | No PII stored, only credential metadata |

### 17.3 GDPR Considerations

- **Data Minimization:** Only credential metadata is stored, no personal data
- **Purpose Limitation:** Credentials are stored only for authentication purposes
- **Storage Limitation:** Audit logs have configurable retention periods
- **Integrity and Confidentiality:** Encryption at rest, access controls
- **Accountability:** Comprehensive audit trail of all operations

### 17.4 NIST SP 800-53 Requirements

| Control | Requirement | pheno-credentials Implementation |
|---------|-------------|----------------------------------|
| IA-5 | Authenticator management | Credential lifecycle, rotation policies |
| IA-5(1) | Password-based authentication | PBKDF2 key derivation, complexity |
| IA-5(2) | PKI-based authentication | Certificate credential type support |
| IA-5(13) | Expiration of cached credentials | Credential expiration, auto-cleanup |
| AC-2 | Account management | Project-based access control |
| AC-3 | Access enforcement | Hierarchical scope resolution |
| AC-6 | Least privilege | Scope-based credential access |
| AU-2 | Audit events | All credential operations logged |
| AU-3 | Content of audit records | Comprehensive log entry fields |
| AU-12 | Audit generation | Automatic audit log generation |

---

## 18. Integration Patterns

### 18.1 FastAPI Integration

```python
from fastapi import FastAPI, Depends, HTTPException
from pheno_credentials import get_credential, CredentialBroker

app = FastAPI()


def get_broker() -> CredentialBroker:
    return get_credential_broker()


@app.get("/api/data")
async def get_data(broker: CredentialBroker = Depends(get_broker)):
    api_key = broker.get_credential("EXTERNAL_API_KEY", prompt=False)
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")

    # Use API key for external service call
    # ...
    return {"status": "ok"}
```

### 18.2 Celery Integration

```python
from celery import Celery
from pheno_credentials import get_credential

app = Celery("tasks")


@app.task
def process_with_api():
    api_key = get_credential("PROCESSING_API_KEY", prompt=False)
    if not api_key:
        raise ValueError("API key not configured for processing task")

    # Use API key for processing
    # ...
    return {"status": "processed"}
```

### 18.3 Django Integration

```python
# settings.py
from pheno_credentials import get_credential_broker

broker = get_credential_broker()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "mydb",
        "USER": broker.get_credential("DB_USER", prompt=False),
        "PASSWORD": broker.get_credential("DB_PASSWORD", prompt=False),
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# Use pheno-credentials for all sensitive settings
SECRET_KEY = broker.get_credential("DJANGO_SECRET_KEY", prompt=False)
```

---

## 19. References

### 19.1 Standards and Specifications

- NIST SP 800-57: Recommendation for Key Management
- NIST SP 800-132: PBKDF2 Recommendation
- NIST SP 800-38D: AES-GCM Specification
- NIST SP 800-53: Security and Privacy Controls
- RFC 9106: Argon2 Memory-Hard Function
- RFC 7519: JSON Web Token (JWT)
- RFC 6749: OAuth 2.0 Authorization Framework
- RFC 7914: scrypt Key Derivation Function
- RFC 7521: Assertion Framework for OAuth 2.0
- RFC 7636: PKCE for OAuth 2.0
- OWASP Secret Management Cheat Sheet
- OWASP Cryptographic Storage Cheat Sheet
- PCI DSS v4.0: Requirement 3 (Protect Stored Account Data)

### 19.2 Libraries and Tools

- `cryptography` (Python): https://cryptography.io
- `argon2-cffi` (Python): https://argon2-cffi.readthedocs.io
- `keyring` (Python): https://pypi.org/project/keyring
- `sops`: https://github.com/getsops/sops
- `pass`: https://www.passwordstore.org
- `gopass`: https://www.gopass.pw
- HashiCorp Vault: https://www.vaultproject.io
- AWS Secrets Manager: https://aws.amazon.com/secrets-manager
- Doppler: https://www.doppler.com
- Akeyless: https://www.akeyless.io

### 19.3 Research Papers

- "SoK: Password Hashing Competition" - 2015
- "Practical Guidance on Password Hashing" - USENIX 2023
- "Secret Management in Cloud-Native Applications" - ACM 2024
- "Zero-Trust Credential Access Patterns" - IEEE 2024
- "Confidential Computing: A Survey" - ACM Computing Surveys 2023
- "Post-Quantum Cryptography: Current State and Future Directions" - 2024

### 19.4 Industry Reports

- Gartner: Market Guide for Privileged Access Management (2024)
- Forrester: The State of Secret Management (2024)
- SANS: Credential Security Best Practices (2024)
- CSA: Cloud Security Alliance - Secret Management Guide (2024)

### 19.5 Pheno Ecosystem Documents

- PhenoSpecs Registry: Storage backend specifications
- PhenoHandbook: Patterns and guidelines for credential management
- AgilePlus Kitty Specs: Feature specifications for pheno-credentials

---

*This document is part of the Phenotype architecture research series. For related documents, see ADR-001 (Storage Backend), ADR-002 (Encryption Model), and ADR-003 (Rotation Policy).*
