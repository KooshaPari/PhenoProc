# ADR-001: Credential Storage Backend

**Document ID:** PHENOTYPE_CREDENTIALS_ADR_001  
**Status:** Accepted  
**Last Updated:** 2026-04-03  
**Author:** Phenotype Architecture Team  
**Supersedes:** N/A  
**Related:** ADR-002 (Encryption Model), ADR-003 (Rotation Policy)

---

## Table of Contents

1. [Title](#adr-001-credential-storage-backend)
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

The pheno-credentials system requires a secure, portable, and flexible storage backend for managing credentials across the Phenotype ecosystem. Credentials include API keys, OAuth tokens, passwords, certificates, SSH keys, database URLs, and connection strings. The system must support multiple deployment contexts (local development, CI/CD, production) and multiple operating systems (macOS, Linux, Windows).

### Requirements

1. **Security:** Credentials must be encrypted at rest with industry-standard algorithms
2. **Portability:** Must work across macOS, Linux, and Windows without configuration changes
3. **Searchability:** Must support searching and listing credentials by type, scope, service, and tags
4. **Performance:** Credential retrieval must complete within 50ms for interactive use
5. **Scalability:** Must handle hundreds of credentials without degradation
6. **Backup:** Must support manual and automated backup strategies
7. **Integration:** Must integrate with OS-level credential stores where available

### Constraints

- Python 3.12+ runtime
- No external service dependencies for local operation
- Must function offline (no network requirement for basic operations)
- Must support both CLI and programmatic access patterns

### Options Considered

#### Option 1: OS Keyring Only

Use only the OS-level keyring (macOS Keychain, Windows Credential Manager, Linux Secret Service) for all credential storage.

**Pros:**
- Maximum security (OS-level protection)
- No application-level encryption needed
- Automatic backup via OS mechanisms
- Biometric authentication support (macOS Touch ID, Windows Hello)

**Cons:**
- No search capability (keyring APIs don't support listing all entries)
- No bulk operations
- Platform-specific behavior differences
- Limited metadata storage (keyring stores key-value pairs only)
- Cannot store hierarchical scope information efficiently
- CI/CD environments often lack keyring support

#### Option 2: Encrypted File Only

Use only encrypted files for all credential storage.

**Pros:**
- Full search and list capabilities
- Bulk operations supported
- Git-friendly (can version control encrypted files)
- Works in all environments (including CI/CD)
- Full metadata support

**Cons:**
- Application-level encryption only (no OS-level protection)
- Master password management complexity
- File system access is a single point of failure
- Less secure than OS keyring for high-value credentials

#### Option 3: Cloud Secret Manager

Use a cloud-based secret manager (AWS Secrets Manager, HashiCorp Vault, Doppler) as the primary backend.

**Pros:**
- Enterprise-grade security
- Automatic rotation
- Audit logging
- Team sharing
- Centralized management

**Cons:**
- Network dependency (cannot operate offline)
- Cost implications
- Operational complexity
- Overkill for local development
- Vendor lock-in risk

#### Option 4: Composite Store (Selected)

Combine OS keyring and encrypted file storage into a composite backend that leverages the strengths of both approaches.

**Pros:**
- Best security for high-value credentials (keyring)
- Full search and list capabilities (encrypted files)
- Works in all environments (fallback to file store)
- No network dependency
- Flexible and extensible

**Cons:**
- More complex implementation
- Potential for credential duplication across backends
- Requires careful synchronization logic

---

## Decision

**We will implement a Composite Store pattern** that combines `KeyringStore` and `EncryptedFileStore` as interchangeable backends, orchestrated by a `CompositeStore` coordinator.

### Architecture Decision

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Composite Store                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    CompositeStore                             │ │
│  │                                                               │ │
│  │  store(cred)    ──▶  Write to ALL available backends          │ │
│  │  retrieve(key)  ──▶  Read from FIRST backend that has it      │ │
│  │  delete(key)    ──▶  Delete from ALL backends                 │ │
│  │  list_keys()    ──▶  Union of keys from ALL backends          │ │
│  │  search(criteria)──▶ Search ALL backends, deduplicate results  │ │
│  └─────────────────────┬─────────────────────────────────────────┘ │
│                        │                                           │
│          ┌─────────────┴─────────────┐                            │
│          ▼                           ▼                             │
│  ┌──────────────────┐      ┌──────────────────┐                   │
│  │   KeyringStore   │      │ EncryptedFileStore│                   │
│  │                  │      │                  │                   │
│  │ • OS keyring     │      │ • ~/.pheno/      │                   │
│  │ • High security  │      │   credentials/   │                   │
│  │ • No search      │      │   cache.json     │                   │
│  │ • No list_keys   │      │ • Searchable     │                   │
│  │ • Platform dep.  │      │ • Listable       │                   │
│  │ • Graceful fail  │      │ • In-memory cache│                   │
│  └──────────────────┘      └──────────────────┘                   │
│                                                                     │
│  Storage Priority (store):                                          │
│  1. KeyringStore (if available) ← Primary for high-value creds     │
│  2. EncryptedFileStore (always) ← Primary for search/list          │
│                                                                     │
│  Retrieval Priority (retrieve):                                     │
│  1. KeyringStore (first match)                                      │
│  2. EncryptedFileStore (first match)                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Backend Selection Logic

```python
def _init_storage(self):
    """Initialize credential storage backends."""
    stores = []

    # Add keyring store if available (graceful degradation)
    try:
        keyring_store = KeyringStore()
        stores.append(keyring_store)
    except ImportError:
        # Keyring not available — fall back to file store only
        pass

    # Add encrypted file store (always available)
    file_store = EncryptedFileStore(
        data_dir=self.data_dir,
        encryption_service=self.encryption_service,
    )
    stores.append(file_store)

    # Create composite store
    self.credential_store = CompositeStore(stores)
```

### Key Design Decisions

1. **Abstract Base Class:** `CredentialStore` defines the interface with five abstract methods: `store`, `retrieve`, `delete`, `list_keys`, and `search`. This enables future backend additions (e.g., cloud secret managers, SQLite, Redis).

2. **Graceful Degradation:** If the `keyring` package is not installed or the OS keyring is unavailable, the system falls back to `EncryptedFileStore` without error.

3. **In-Memory Cache:** `EncryptedFileStore` maintains an in-memory cache (`self._cache`) loaded from `cache.json` at initialization. This provides fast retrieval while persisting to disk on every write.

4. **Deduplication:** `CompositeStore.search()` deduplicates results across backends using credential ID, preventing duplicate entries when the same credential exists in multiple backends.

5. **Metadata Separation (KeyringStore):** Keyring stores credential values and metadata separately (`{key}_value` and `{key}_meta`), working around keyring's key-value-only limitation.

---

## Consequences

### Positive Consequences

1. **Maximum Security with Fallback:** High-value credentials benefit from OS-level keyring protection while maintaining full functionality through the encrypted file fallback.

2. **Cross-Platform Compatibility:** The system works identically on macOS, Linux, and Windows, with automatic adaptation to each platform's native keyring implementation.

3. **Full Search and Discovery:** Unlike pure keyring solutions, the composite approach supports searching credentials by type, scope, service, tags, and expiration status.

4. **CI/CD Compatibility:** In environments without keyring support (CI runners, containers, headless servers), the encrypted file store provides full functionality.

5. **Extensibility:** The abstract `CredentialStore` interface enables adding new backends (e.g., AWS Secrets Manager, HashiCorp Vault, SQLite) without modifying existing code.

6. **Developer Experience:** Developers get secure storage by default with no configuration required. The system auto-detects available backends and configures itself.

7. **Backup Portability:** Encrypted file storage enables easy backup and migration of credential data across machines via the `cache.json` file.

### Negative Consequences

1. **Implementation Complexity:** The composite pattern requires careful coordination between backends, including deduplication, conflict resolution, and error handling across multiple storage layers.

2. **Credential Duplication:** Credentials may be stored in both keyring and encrypted file, consuming more storage space and creating potential consistency issues if one backend fails to write.

3. **Partial Write Risk:** If the keyring store succeeds but the file store fails (or vice versa), credentials may exist in only one backend, leading to inconsistent `list_keys()` and `search()` results.

4. **Cache Invalidation:** The in-memory cache in `EncryptedFileStore` may become stale if the `cache.json` file is modified externally, requiring manual cache refresh.

5. **Keyring Limitations:** The `KeyringStore` cannot support `list_keys()` or `search()` operations due to OS keyring API limitations, creating an asymmetric capability surface.

6. **Master Password Management:** The encrypted file store requires a master password, which must be provided at initialization or prompted interactively. This creates a UX challenge for automated workflows.

7. **Performance Overhead:** The composite store's write operations (store to all backends) and search operations (search all backends + deduplicate) introduce latency compared to a single-backend approach.

### Mitigation Strategies

| Consequence | Mitigation |
|------------|------------|
| Partial write risk | Implement transaction-like semantics with rollback on failure |
| Cache staleness | Add cache invalidation with TTL and file modification time checks |
| Keyring asymmetry | Document limitations clearly; use file store as source of truth for listing |
| Master password UX | Support environment variable, keyring-stored master key, and interactive prompt |
| Performance overhead | Implement parallel backend operations using `asyncio.gather()` |
| Credential duplication | Add deduplication cleanup command in CLI |

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Storage Architecture                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    CredentialBroker                           │ │
│  │                                                               │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │ │
│  │  │ EncryptionSvc   │  │ ProjectManager  │  │ AuditLogger   │ │ │
│  │  └────────┬────────┘  └────────┬────────┘  └───────┬───────┘ │ │
│  │           │                    │                    │         │ │
│  │           ▼                    ▼                    ▼         │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │                  CompositeStore                          │ │ │
│  │  │                                                          │ │ │
│  │  │  ┌────────────────────┐  ┌────────────────────────────┐ │ │ │
│  │  │  │    KeyringStore    │  │     EncryptedFileStore     │ │ │ │
│  │  │  │                    │  │                            │ │ │ │
│  │  │  │  • set_password()  │  │  • _cache: dict[str, Cred] │ │ │ │
│  │  │  │  • get_password()  │  │  • data_dir: Path          │ │ │ │
│  │  │  │  • delete_password │  │  • encryption_service      │ │ │ │
│  │  │  │                    │  │  • cache.json              │ │ │ │
│  │  │  └────────────────────┘  └────────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Data Flow:                                                         │
│  ─────────                                                          │
│  store_credential()                                                 │
│    └─▶ Create Credential model                                      │
│        └─▶ CompositeStore.store(credential)                         │
│            ├─▶ KeyringStore.store() (if available)                  │
│            │   └─▶ keyring.set_password(service, key_value, value)  │
│            │   └─▶ keyring.set_password(service, key_meta, json)    │
│            └─▶ EncryptedFileStore.store()                           │
│                └─▶ _cache[key] = credential                         │
│                └─▶ _save_cache() → cache.json (encrypted values)    │
│                                                                     │
│  get_credential()                                                   │
│    └─▶ EnvironmentManager.get()                                     │
│        └─▶ _get_credential_from_store(key)                          │
│            └─▶ CompositeStore.retrieve(key)                         │
│                ├─▶ KeyringStore.retrieve() (first)                  │
│                └─▶ EncryptedFileStore.retrieve() (fallback)         │
└─────────────────────────────────────────────────────────────────────┘
```

### Storage Layout

```
~/.pheno/
├── credentials/                    # EncryptedFileStore data directory
│   └── cache.json                  # Encrypted credential cache
│                                   # Structure: {key: {name, value(encrypted),
│                                   #   type, scope, salt, key_id, ...}}
│
├── projects/                       # ProjectManager data directory
│   └── projects.json               # Project registry
│                                   # Structure: {project_id: {id, name,
│                                   #   description, path, created_at, ...}}
│
├── audit/                          # AuditLogger data directory
│   └── credential_access.jsonl     # JSON Lines audit log
│                                   # One JSON object per line
│                                   # Fields: id, credential_id, action,
│                                   #   timestamp, user, project_id,
│                                   #   ip_address, user_agent, success,
│                                   #   error_message
│
└── hierarchy/                      # HierarchyManager data directory
    └── hierarchies.json            # Scope hierarchy definitions
                                    # Structure: {name: {id, name,
                                    #   nodes, root_node_id, path_index,
                                    #   type_index, version, ...}}
```

### Key Naming Convention

Credentials are stored with keys that encode scope information:

| Scope | Key Format | Example |
|-------|-----------|---------|
| Global | `{name}` | `OPENAI_API_KEY` |
| Project | `{project_id[:4]}_{name}` | `phen_OPENAI_API_KEY` |
| Environment | `{env}_{name}` | `prod_OPENAI_API_KEY` |
| Hierarchical | `{scope_path}_{name}` | `atoms.infra.pheno-sdk_OPENAI_API_KEY` |

---

## Implementation Details

### CredentialStore Interface

```python
class CredentialStore(ABC):
    """Abstract base class for credential storage backends."""

    @abstractmethod
    def store(self, credential: Credential) -> bool:
        """Store a credential. Returns True if successful."""

    @abstractmethod
    def retrieve(self, key: str) -> Credential | None:
        """Retrieve a credential by key. Returns None if not found."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a credential by key. Returns True if successful."""

    @abstractmethod
    def list_keys(self) -> list[str]:
        """List all credential keys."""

    @abstractmethod
    def search(self, search: CredentialSearch) -> list[Credential]:
        """Search for credentials matching criteria."""
```

### KeyringStore Limitations

The `KeyringStore` implementation has two known limitations due to OS keyring API constraints:

1. **No `list_keys()`:** OS keyring APIs do not provide a way to enumerate all stored entries for a service. Returns empty list `[]`.

2. **No `search()`:** Without the ability to list keys, searching is not possible. Returns empty list `[]`.

These limitations are documented and mitigated by the `EncryptedFileStore`, which provides full search and list capabilities.

### EncryptedFileStore Cache Strategy

The `EncryptedFileStore` uses an in-memory cache for performance:

- **Load:** Cache is populated from `cache.json` at initialization
- **Decrypt on Load:** All encrypted values are decrypted during cache load
- **Write-Through:** Every `store()` and `delete()` operation updates both cache and disk
- **Error Tolerance:** Cache loading and saving failures are silently ignored (graceful degradation)

**Risk:** If the process crashes between cache update and disk write, the in-memory state is lost. This is acceptable for credential storage since the master password would be required to re-populate the cache.

---

## Code Examples

### Adding a New Storage Backend

```python
from .models import Credential, CredentialSearch
from .storage import CredentialStore


class SQLiteStore(CredentialStore):
    """Credential storage using SQLite database."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or Path.home() / ".pheno" / "credentials.db"
        self._init_db()

    def _init_db(self):
        import sqlite3
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
        """)

    def store(self, credential: Credential) -> bool:
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO credentials (key, value, metadata) VALUES (?, ?, ?)",
                (credential.key, credential.value, credential.model_dump_json()),
            )
            self.conn.commit()
            return True
        except Exception:
            return False

    def retrieve(self, key: str) -> Credential | None:
        cursor = self.conn.execute(
            "SELECT value, metadata FROM credentials WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Credential.model_validate_json(row[1])

    def delete(self, key: str) -> bool:
        try:
            self.conn.execute("DELETE FROM credentials WHERE key = ?", (key,))
            self.conn.commit()
            return True
        except Exception:
            return False

    def list_keys(self) -> list[str]:
        cursor = self.conn.execute("SELECT key FROM credentials")
        return [row[0] for row in cursor.fetchall()]

    def search(self, search: CredentialSearch) -> list[Credential]:
        credentials = []
        cursor = self.conn.execute("SELECT metadata FROM credentials")
        for row in cursor.fetchall():
            cred = Credential.model_validate_json(row[0])
            if self._matches_search(cred, search):
                credentials.append(cred)
        return credentials
```

### Integrating the New Backend

```python
# In CredentialBroker._init_storage():
try:
    from .storage import SQLiteStore
    sqlite_store = SQLiteStore()
    stores.append(sqlite_store)
except ImportError:
    pass
```

---

## Cross-References

- **ADR-002 (Encryption Model):** Defines the encryption algorithm (Fernet/AES-256-GCM) and key derivation (PBKDF2/Argon2id) used by `EncryptedFileStore`.
- **ADR-003 (Rotation Policy):** Defines credential rotation strategies that operate on credentials stored via the Composite Store.
- **SOTA Research (CREDENTIALS_MGMT_SOTA_001):** Comprehensive analysis of storage backends, including OS keyring systems, encrypted file patterns, and cloud secret managers.
- **PhenoSpecs Registry:** Storage backend specifications and compliance requirements.

---

*This ADR was accepted on 2026-04-03. The Composite Store pattern is implemented in `src/pheno_credentials/storage.py`.*
