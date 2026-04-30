# ADR-002: Encryption Model

**Document ID:** PHENOTYPE_CREDENTIALS_ADR_002  
**Status:** Accepted  
**Last Updated:** 2026-04-03  
**Author:** Phenotype Architecture Team  
**Supersedes:** N/A  
**Related:** ADR-001 (Storage Backend), ADR-003 (Rotation Policy)

---

## Table of Contents

1. [Title](#adr-002-encryption-model)
2. [Context](#context)
3. [Decision](#decision)
4. [Consequences](#consequences)
5. [Architecture](#architecture)
6. [Implementation Details](#implementation-details)
7. [Code Examples](#code-examples)
8. [Cross-References](#cross-references)

---

## Context

### Problem Statement

The pheno-credentials system must encrypt credential values at rest to protect sensitive data (API keys, tokens, passwords, certificates) from unauthorized access. The encryption model must balance security strength, performance, portability, and ease of use. The system operates in diverse environments including developer workstations, CI/CD pipelines, and production servers.

### Requirements

1. **Confidentiality:** Credential values must be unreadable without the master password
2. **Integrity:** Encrypted data must be detectable if tampered with
3. **Key Derivation:** Master password must be transformed into a cryptographic key using a secure KDF
4. **Per-Credential Salt:** Each credential must use a unique salt to prevent rainbow table attacks
5. **Performance:** Encryption/decryption must complete within 10ms per credential
6. **Portability:** Encrypted data must be decryptable across platforms and Python versions
7. **No Key Storage:** The master password and derived keys must never be persisted to disk

### Constraints

- Python 3.12+ runtime
- `cryptography` library as the primary crypto provider
- Must support interactive master password entry for first-time use
- Must support non-interactive operation for automated workflows (via environment variable or keyring-stored key)

### Options Considered

#### Option 1: Fernet (Symmetric Encryption)

Use the `cryptography.fernet.Fernet` recipe, which provides AES-128-CBC encryption with HMAC-SHA256 authentication.

**Current Implementation:**
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
)
key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
fernet = Fernet(key)
encrypted = fernet.encrypt(value.encode())
```

**Pros:**
- Simple, well-tested API
- Built-in authentication (HMAC)
- Includes timestamp for token expiry
- Part of the `cryptography` library (no additional dependencies)
- Widely adopted in the Python ecosystem

**Cons:**
- AES-128 (not AES-256) — key is truncated from 256-bit PBKDF2 output to 128-bit
- CBC mode requires separate HMAC for authentication (not authenticated encryption)
- No associated data (AAD) support — cannot bind metadata to ciphertext
- Fixed token format limits flexibility
- Timestamp-based replay protection is weak (only prevents reuse after 24h by default)

#### Option 2: AES-256-GCM (Authenticated Encryption)

Use AES-256 in Galois/Counter Mode with the `cryptography.hazmat.primitives.ciphers.aead.AESGCM` primitive.

**Proposed Implementation:**
```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

aesgcm = AESGCM(key)  # 256-bit key
nonce = os.urandom(12)
aad = f"pheno-credentials:v1:{credential_id}".encode()
ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), aad)
# Store: nonce + ciphertext
```

**Pros:**
- AES-256 (full 256-bit key)
- Authenticated encryption (encryption + authentication in one operation)
- Associated data (AAD) support — can bind credential metadata to ciphertext
- Hardware acceleration via AES-NI on modern CPUs
- Industry standard for modern encryption

**Cons:**
- Lower-level API (more implementation responsibility)
- Must manage nonce generation and storage
- Must handle AAD construction and validation
- No built-in timestamp or token format

#### Option 3: ChaCha20-Poly1305

Use ChaCha20-Poly1305 authenticated encryption via `cryptography.hazmat.primitives.ciphers.aead.ChaCha20Poly1305`.

**Pros:**
- 256-bit key
- Authenticated encryption
- No hardware acceleration dependency (software-optimized)
- Faster than AES-GCM on systems without AES-NI (ARM, some mobile)
- Resistant to cache-timing side-channel attacks

**Cons:**
- Slower than AES-GCM on systems with AES-NI (most x86_64 servers)
- Less widely adopted in Python ecosystem
- Larger ciphertext overhead (16-byte tag + 12-byte nonce)

#### Option 4: libsodium / PyNaCl

Use the libsodium library via PyNaCl for high-level cryptographic operations.

**Pros:**
- High-level, hard-to-misuse API
- XChaCha20-Poly1305 (extended nonce, safe for random nonces)
- Built-in key derivation (Argon2id)
- Sealed boxes for public-key encryption

**Cons:**
- Additional dependency (`pynacl`)
- Native library compilation required
- Overkill for symmetric encryption use case
- Less familiar to Python developers

---

## Decision

**We will maintain Fernet as the current default encryption model** for backward compatibility, but **design the system to support AES-256-GCM as the primary encryption model for new deployments**.

### Decision Rationale

1. **Backward Compatibility:** Existing credential data encrypted with Fernet must remain accessible. Migrating all existing credentials to a new algorithm requires the master password and access to all credentials simultaneously, which is not always feasible.

2. **Security Adequacy:** Fernet's AES-128-CBC + HMAC-SHA256 provides adequate security for the current threat model. AES-128 is still considered secure against all known practical attacks.

3. **Upgrade Path:** The `EncryptionService` is designed with key versioning support (`key_id` parameter), enabling gradual migration to AES-256-GCM for new credentials while maintaining Fernet decryption for legacy credentials.

4. **KDF Upgrade Priority:** The higher-priority upgrade is from PBKDF2 to Argon2id for key derivation, which provides significantly better protection against brute-force attacks than upgrading from AES-128 to AES-256.

### Encryption Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Encryption Architecture                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    EncryptionService                          │ │
│  │                                                               │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │              Key Derivation Layer                       │ │ │
│  │  │                                                         │ │ │
│  │  │  Master Password ──▶ PBKDF2-HMAC-SHA256 ──▶ Key       │ │ │
│  │  │                      (100K iterations)                  │ │ │
│  │  │                      ↑ Future: Argon2id                │ │ │
│  │  │                                                         │ │ │
│  │  │  Key Cache: {key_id:salt} → derived_key                │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                                                               │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │              Encryption Layer                           │ │ │
│  │  │                                                         │ │ │
│  │  │  Current:  Fernet (AES-128-CBC + HMAC-SHA256)          │ │ │
│  │  │  Future:   AESGCM (AES-256-GCM)                        │ │ │
│  │  │                                                         │ │ │
│  │  │  encrypt(value, key_id) → (encrypted_b64, salt_b64)    │ │ │
│  │  │  decrypt(encrypted_b64, salt_b64, key_id) → value      │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Data Flow:                                                         │
│  ─────────                                                          │
│  Store Credential:                                                  │
│    plaintext value ──▶ EncryptionService.encrypt()                  │
│      └─▶ Generate random 16-byte salt                              │
│      └─▶ Derive key from master_password + salt (PBKDF2)           │
│      └─▶ Encrypt with Fernet (AES-128-CBC + HMAC)                  │
│      └─▶ Return (base64(encrypted), base64(salt))                  │
│                                                                     │
│  Retrieve Credential:                                               │
│    (encrypted_b64, salt_b64) ──▶ EncryptionService.decrypt()       │
│      └─▶ Decode base64 values                                      │
│      └─▶ Derive key from master_password + salt (PBKDF2)           │
│      └─▶ Decrypt with Fernet                                      │
│      └─▶ Return plaintext value                                    │
│                                                                     │
│  Key Structure:                                                     │
│  ─────────────                                                      │
│  Master Password (user input, never stored)                         │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────┐                                          │
│  │  PBKDF2-HMAC-SHA256 │                                          │
│  │  iterations: 100,000│                                          │
│  │  salt: 16 bytes     │                                          │
│  │  output: 32 bytes   │  ← Truncated to 16 bytes for Fernet      │
│  └─────────┬───────────┘                                          │
│            │                                                       │
│            ▼                                                       │
│  ┌─────────────────────┐                                          │
│  │  Fernet Key         │                                          │
│  │  32 bytes base64    │  ← 16 bytes encryption + 16 bytes HMAC   │
│  │  (urlsafe_b64)      │                                          │
│  └─────────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Versioning Strategy

The `key_id` parameter in `EncryptionService.encrypt()` and `decrypt()` enables key versioning:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Key Versioning Strategy                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Version 1 (Current):                                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  KDF: PBKDF2-HMAC-SHA256 (100K iterations)                 │   │
│  │  Cipher: Fernet (AES-128-CBC + HMAC-SHA256)                │   │
│  │  Salt: 16 bytes random                                     │   │
│  │  Key ID: "default"                                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Version 2 (Future):                                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  KDF: Argon2id (time=3, memory=64MB, parallelism=4)        │   │
│  │  Cipher: AES-256-GCM                                       │   │
│  │  Salt: 16 bytes random                                     │   │
│  │  AAD: "pheno-credentials:v2:{credential_id}"               │   │
│  │  Key ID: "v2:{uuid}"                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Migration Path:                                                    │
│  ──────────────                                                     │
│  1. New credentials encrypted with V2                               │
│  2. Existing credentials remain V1                                  │
│  3. Decryption supports both V1 and V2 (key_id determines method)  │
│  4. Background migration re-encrypts V1 credentials on access       │
│  5. V1 deprecated after all credentials migrated                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Consequences

### Positive Consequences

1. **Backward Compatibility:** Existing credential data remains accessible without migration. Users are not forced to re-enter all credentials when upgrading the encryption model.

2. **Incremental Upgrade Path:** The key versioning design enables gradual migration from Fernet to AES-256-GCM without a disruptive "big bang" migration event.

3. **Security Adequacy:** Fernet's AES-128-CBC + HMAC-SHA256 provides strong security for the current threat model. The 128-bit key space (2^128) is computationally infeasible to brute-force.

4. **Simple Implementation:** Fernet's high-level API reduces the risk of implementation errors that could compromise security (e.g., incorrect nonce handling, missing authentication).

5. **Per-Credential Salt:** Each credential uses a unique random salt, preventing rainbow table attacks and ensuring that identical credential values produce different ciphertexts.

6. **Key Caching:** Derived keys are cached in memory (`self._key_cache`) to avoid repeated KDF computation for the same key_id:salt combination, improving performance for bulk operations.

7. **Master Password Protection:** The master password is never stored on disk. It is held in memory only during the session and can be provided interactively via `getpass.getpass()`.

### Negative Consequences

1. **AES-128 Limitation:** Fernet uses only 128-bit encryption keys, truncating the 256-bit PBKDF2 output. This provides less security margin than AES-256, though still computationally infeasible to break.

2. **No Associated Data:** Fernet does not support associated data (AAD), meaning credential metadata (type, scope, service) cannot be cryptographically bound to the ciphertext. An attacker could swap encrypted values between credentials without detection.

3. **PBKDF2 Iteration Count:** 100,000 iterations is the OWASP 2023 minimum recommendation but below the 2024 recommendation of 600,000 iterations for PBKDF2-HMAC-SHA256. This provides less brute-force resistance than optimal.

4. **No Memory-Hard KDF:** PBKDF2 is not memory-hard, making it vulnerable to GPU and ASIC-based brute-force attacks. Argon2id would provide significantly better protection.

5. **Timestamp Weakness:** Fernet tokens include a timestamp, but the default verification only checks that the token is not older than 24 hours. This provides weak replay protection and is not relevant for credential storage (credentials don't expire based on encryption time).

6. **Key Cache Security:** Derived keys are cached in memory as plain bytes. If the process memory is compromised (e.g., via core dump or memory scraping), cached keys could be extracted.

7. **Encryption Service Coupling:** The `EncryptionService` is tightly coupled to the Fernet implementation. Supporting AES-256-GCM will require significant refactoring of the encrypt/decrypt methods.

### Mitigation Strategies

| Consequence | Mitigation |
|------------|------------|
| AES-128 limitation | Plan migration to AES-256-GCM (key_id versioning supports this) |
| No AAD support | Add credential ID to Fernet token metadata for integrity verification |
| PBKDF2 iterations | Increase to 600,000 in next major version (backward compatible via key_id) |
| Non-memory-hard KDF | Add Argon2id as alternative KDF (key_id determines KDF method) |
| Key cache exposure | Implement secure memory zeroing on service shutdown |
| Fernet coupling | Define encryption interface abstraction before adding AES-256-GCM |

---

## Architecture

### Encryption Service Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Encryption Service Flow                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ENCRYPTION:                                                        │
│  ───────────                                                        │
│                                                                     │
│  plaintext_value                                                    │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────┐                                               │
│  │  Generate Salt  │  os.urandom(16)                               │
│  │  (16 bytes)     │                                               │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │  Derive Key     │  PBKDF2HMAC(SHA256, master_password, salt,   │
│  │  (PBKDF2)       │  100000 iterations) → 32 bytes               │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │  Base64 Encode  │  base64.urlsafe_b64encode(key)               │
│  │  Key            │                                               │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │  Fernet Encrypt │  Fernet(key).encrypt(plaintext.encode())     │
│  │  (AES-128-CBC   │  → ciphertext (includes IV + HMAC)           │
│  │  + HMAC)        │                                               │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │  Base64 Encode  │  base64.urlsafe_b64encode(ciphertext)        │
│  │  Ciphertext     │                                               │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  Return: (encrypted_b64, salt_b64)                                 │
│                                                                     │
│  DECRYPTION:                                                        │
│  ───────────                                                        │
│                                                                     │
│  (encrypted_b64, salt_b64, key_id)                                 │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────┐                                               │
│  │  Base64 Decode  │  base64.urlsafe_b64decode(encrypted_b64)     │
│  │  Inputs         │  base64.urlsafe_b64decode(salt_b64)          │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │  Check Key      │  If key_id:salt in _key_cache, use cached    │
│  │  Cache          │  Otherwise derive from master_password       │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │  Fernet Decrypt │  Fernet(key).decrypt(ciphertext)             │
│  │  (Verify HMAC)  │  → plaintext bytes (raises InvalidToken      │
│  │                 │  if HMAC verification fails)                 │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  Return: plaintext_value (decoded string)                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Derivation Parameters

| Parameter | Current Value | Recommended Future | Rationale |
|-----------|--------------|-------------------|-----------|
| Algorithm | PBKDF2-HMAC-SHA256 | Argon2id | Memory-hard, GPU-resistant |
| Iterations | 100,000 | 600,000 (PBKDF2) / 3 (Argon2id) | OWASP 2024 recommendation |
| Salt Length | 16 bytes | 16 bytes | Sufficient for uniqueness |
| Key Length | 32 bytes | 32 bytes | Matches AES-256 key size |
| Memory Cost | N/A | 64 MiB | Argon2id parameter |
| Parallelism | N/A | 4 threads | Argon2id parameter |

---

## Implementation Details

### Current Implementation

The `EncryptionService` class in `src/pheno_credentials/encryption.py` implements:

1. **Key Derivation:** PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte random salt
2. **Key Caching:** In-memory cache keyed by `key_id:salt` to avoid repeated KDF computation
3. **Encryption:** Fernet (AES-128-CBC + HMAC-SHA256)
4. **Decryption:** Fernet with automatic HMAC verification
5. **Master Password:** Interactive prompt via `getpass.getpass()` if not provided
6. **Key Generation:** `secrets.token_urlsafe(16)` for key_id generation

### EncryptionKey Model

```python
class EncryptionKey(BaseModel):
    id: str
    algorithm: str = "fernet"
    created_at: datetime
    last_used: datetime | None
    key_derivation: str = "pbkdf2"
    iterations: int = 100000
```

This model tracks encryption key metadata for versioning and migration purposes.

### Security Properties

| Property | Implementation | Status |
|----------|---------------|--------|
| Confidentiality | AES-128-CBC (Fernet) | Adequate |
| Integrity | HMAC-SHA256 (Fernet) | Strong |
| Authentication | HMAC-SHA256 (Fernet) | Strong |
| Key Derivation | PBKDF2-HMAC-SHA256 | Adequate |
| Salt Uniqueness | 16-byte random per credential | Strong |
| Replay Protection | Fernet timestamp (24h) | Weak (not relevant) |
| Key Zeroing | Not implemented | Missing |
| Memory Locking | Not implemented | Missing |

---

## Code Examples

### Upgrading to AES-256-GCM

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64


class AES256EncryptionService:
    """AES-256-GCM encryption service (future implementation)."""

    def __init__(self, master_password: str | None = None):
        self.master_password = master_password
        self._key_cache: dict[str, bytes] = {}

    def _derive_key(self, key_id: str, salt: bytes) -> bytes:
        """Derive 256-bit key using PBKDF2."""
        cache_key = f"{key_id}:{base64.b64encode(salt).decode()}"
        if cache_key in self._key_cache:
            return self._key_cache[cache_key]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key for AES-256
            salt=salt,
            iterations=600000,  # OWASP 2024 recommendation
        )
        key = kdf.derive(self.master_password.encode())
        self._key_cache[cache_key] = key
        return key

    def encrypt(self, value: str, key_id: str = "v2:default") -> tuple[str, str]:
        """Encrypt with AES-256-GCM."""
        if not value:
            return "", ""

        salt = os.urandom(16)
        key = self._derive_key(key_id, salt)
        nonce = os.urandom(12)  # 96-bit nonce for GCM

        # Associated data binds credential metadata to ciphertext
        aad = f"pheno-credentials:v2:{key_id}".encode()

        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, value.encode(), aad)

        # Store: nonce + ciphertext (both needed for decryption)
        encrypted_blob = nonce + ciphertext

        return (
            base64.urlsafe_b64encode(encrypted_blob).decode(),
            base64.urlsafe_b64encode(salt).decode(),
        )

    def decrypt(self, encrypted_value: str, salt: str, key_id: str = "v2:default") -> str:
        """Decrypt with AES-256-GCM."""
        if not encrypted_value or not salt:
            return ""

        encrypted_bytes = base64.urlsafe_b64decode(encrypted_value)
        salt_bytes = base64.urlsafe_b64decode(salt)
        key = self._derive_key(key_id, salt_bytes)

        # Split nonce (12 bytes) and ciphertext
        nonce = encrypted_bytes[:12]
        ciphertext = encrypted_bytes[12:]

        aad = f"pheno-credentials:v2:{key_id}".encode()

        aesgcm = AESGCM(key)
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, aad)

        return decrypted_bytes.decode()
```

### Dual-Mode Encryption Service

```python
class DualModeEncryptionService:
    """Supports both Fernet (v1) and AES-256-GCM (v2) encryption."""

    def __init__(self, master_password: str | None = None, default_version: str = "v1"):
        self.master_password = master_password
        self.default_version = default_version
        self.v1 = EncryptionService(master_password)  # Fernet
        self.v2 = AES256EncryptionService(master_password)  # AES-256-GCM

    def encrypt(self, value: str, key_id: str | None = None) -> tuple[str, str]:
        """Encrypt using the default or specified version."""
        version = self._extract_version(key_id) or self.default_version
        if version == "v2":
            return self.v2.encrypt(value, key_id or "v2:default")
        return self.v1.encrypt(value, key_id or "default")

    def decrypt(self, encrypted_value: str, salt: str, key_id: str) -> str:
        """Decrypt using the version indicated by key_id."""
        version = self._extract_version(key_id) or "v1"
        if version == "v2":
            return self.v2.decrypt(encrypted_value, salt, key_id)
        return self.v1.decrypt(encrypted_value, salt, key_id)

    def _extract_version(self, key_id: str | None) -> str | None:
        """Extract version from key_id (e.g., 'v2:abc' -> 'v2')."""
        if key_id and key_id.startswith("v2:"):
            return "v2"
        return None
```

---

## Cross-References

- **ADR-001 (Storage Backend):** Defines the storage backends (`EncryptedFileStore`, `KeyringStore`) that use this encryption model for protecting credential values at rest.
- **ADR-003 (Rotation Policy):** Defines credential rotation strategies that may trigger re-encryption of credentials with updated encryption parameters.
- **SOTA Research (CREDENTIALS_MGMT_SOTA_001):** Comprehensive analysis of encryption algorithms, key derivation functions, and key management systems.
- **NIST SP 800-57:** Recommendation for Key Management — provides guidance on key lifecycle management.
- **OWASP Cryptographic Storage Cheat Sheet:** Best practices for encrypting data at rest.

---

*This ADR was accepted on 2026-04-03. The Fernet encryption model is implemented in `src/pheno_credentials/encryption.py`.*
