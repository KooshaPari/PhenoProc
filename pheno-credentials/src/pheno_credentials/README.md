# Credentials Broker System

A comprehensive credential management system for the ATOMS-PHENO ecosystem that provides secure storage, project-scoped access, and enhanced environment variable management.

## Features

### 🔐 **Secure Storage**
- **OS Keyring Integration**: Uses Windows Credential Manager, macOS Keychain, and Linux Secret Service
- **Encrypted File Storage**: Local encrypted storage for bulk credentials
- **Master Password Protection**: PBKDF2 key derivation with configurable iterations
- **Automatic Encryption**: All sensitive data encrypted at rest

### 🏗️ **Project Management**
- **Project Scoping**: Credentials can be global, project-specific, or environment-specific
- **Auto-Detection**: Automatically detects projects from `pyproject.toml`, `setup.py`, etc.
- **Context Switching**: Easy switching between project contexts
- **Isolation**: Project credentials are isolated from each other

### 🌍 **Enhanced Environment Management**
- **Smart Resolution**: Automatically resolves credentials from multiple sources
- **Fallback Chain**: Secure store → Environment variables → .env files → Defaults → Interactive prompt
- **Interactive Setup**: Guided credential configuration with validation
- **Team Sharing**: Secure credential sharing between team members

### 📊 **Audit & Monitoring**
- **Access Logging**: Track all credential access and modifications
- **Security Alerts**: Monitor for suspicious activity and failed access attempts
- **Usage Statistics**: Detailed analytics on credential usage
- **Export Capabilities**: Export audit logs and credential data

### 🖥️ **User Interfaces**
- **CLI Commands**: Rich command-line interface with typer
- **TUI Interface**: Textual-based terminal user interface
- **Programmatic API**: Easy integration with existing code

## Quick Start

### Installation

The credentials system is included in pheno-sdk:

```bash
pip install pheno-sdk[cli]
```

### Basic Usage

```python
from pheno.credentials import get_credential, CredentialBroker

# Simple credential retrieval (replaces os.getenv)
api_key = get_credential("OPENAI_API_KEY")
# Automatically checks: secure store → env vars → .env files → prompts user

# Advanced usage with broker
broker = CredentialBroker()

# Store a credential
broker.store_credential(
    name="GITHUB_TOKEN",
    value="ghp_1234567890",
    credential_type="oauth_token",
    scope="global",
    service="github",
    description="GitHub personal access token"
)

# Get credential with project context
broker.set_project("my-project")
db_url = broker.get_credential("DATABASE_URL")
```

### CLI Usage

```bash
# List all credentials
pheno credentials list

# Set a credential
pheno credentials set OPENAI_API_KEY sk-1234567890 --type api_key --scope global

# Get a credential
pheno credentials get OPENAI_API_KEY

# Open TUI interface
pheno credentials tui

# Show statistics
pheno credentials stats

# Export credentials
pheno credentials export credentials.json --format json
```

## Architecture

### Core Components

1. **CredentialBroker**: Main interface for credential management
2. **CredentialStore**: Abstract storage backend (Keyring, Encrypted Files)
3. **EnvironmentManager**: Enhanced environment variable management
4. **ProjectManager**: Project context and scoping
5. **EncryptionService**: Secure encryption/decryption
6. **AuditLogger**: Access logging and monitoring

### Storage Backends

- **KeyringStore**: OS keyring for high-value credentials
- **EncryptedFileStore**: Local encrypted storage for bulk data
- **CompositeStore**: Combines multiple backends with fallback

### Credential Scoping

- **Global**: Available to all projects (`$GLOBAL`)
- **Project**: Scoped to specific project (`$PROJECT_ID[:4]`)
- **Environment**: Development/staging/production variants
- **User**: User-specific credentials

## Advanced Features

### Project Management

```python
# Create a project
project = broker.create_project(
    project_id="my-awesome-project",
    name="My Awesome Project",
    description="A sample project",
    path="/path/to/project"
)

# Set project context
broker.set_project(project.id)

# Store project-scoped credentials
broker.store_credential(
    name="DATABASE_URL",
    value="postgresql://localhost/mydb",
    scope="project",
    service="postgres"
)
```

### Environment Variable Integration

```python
# Enhanced environment management
env_manager = broker.environment_manager

# Set environment variables
env_manager.set("MY_API_KEY", "secret-value")

# Get with smart resolution
api_key = env_manager.get("MY_API_KEY")

# Validate required variables
required_vars = ["API_KEY", "DATABASE_URL"]
results = env_manager.validate_required(required_vars)
```

### Credential Search

```python
from pheno.credentials.models import CredentialSearch

# Search by type
api_keys = broker.search_credentials(
    CredentialSearch(type="api_key")
)

# Search by service
github_creds = broker.search_credentials(
    CredentialSearch(service="github")
)

# Search by scope
project_creds = broker.search_credentials(
    CredentialSearch(scope="project", project_id="my-project")
)
```

### Audit and Monitoring

```python
# Get audit log
audit_log = broker.get_audit_log(limit=100)

# Get security alerts
alerts = broker.get_security_alerts()

# Get statistics
stats = broker.get_stats()
print(f"Total credentials: {stats['total_credentials']}")
```

## Security Features

### Encryption

- **Algorithm**: Fernet (AES 128 in CBC mode with HMAC-SHA256)
- **Key Derivation**: PBKDF2 with SHA-256 and 100,000 iterations
- **Salt**: Random 16-byte salt per credential
- **Master Password**: Required for encryption/decryption

### Access Control

- **Project Isolation**: Credentials are isolated by project
- **Scope Enforcement**: Global vs project vs environment scoping
- **Read-Only Credentials**: Mark credentials as read-only
- **Expiration**: Automatic expiration of time-limited credentials

### Audit Trail

- **Access Logging**: All credential access is logged
- **Change Tracking**: Modifications and deletions are tracked
- **Security Alerts**: Automatic detection of suspicious activity
- **Export Capabilities**: Export audit logs for analysis

## Integration Examples

### Replace os.getenv()

```python
# Old way
import os
api_key = os.getenv("OPENAI_API_KEY")

# New way
from pheno.credentials import get_credential
api_key = get_credential("OPENAI_API_KEY")
# Automatically handles secure storage, fallbacks, and prompting
```

### Configuration Management

```python
from pheno.credentials import CredentialBroker
from pheno.config import Config

class MyAppConfig(Config):
    openai_api_key: str
    database_url: str
    github_token: str
    
    def __init__(self):
        broker = CredentialBroker()
        
        # Load from credential broker
        self.openai_api_key = broker.get_credential("OPENAI_API_KEY")
        self.database_url = broker.get_credential("DATABASE_URL")
        self.github_token = broker.get_credential("GITHUB_TOKEN")
```

### Team Onboarding

```python
# Automated credential setup
def setup_team_credentials():
    broker = CredentialBroker()
    
    required_credentials = [
        "OPENAI_API_KEY",
        "GITHUB_TOKEN", 
        "AWS_ACCESS_KEY",
        "DATABASE_URL"
    ]
    
    # Check what's missing
    missing = broker.environment_manager.get_missing_required(required_credentials)
    
    if missing:
        print(f"Missing credentials: {missing}")
        print("Please run: pheno credentials tui")
        return False
    
    return True
```

## CLI Reference

### Commands

- `pheno credentials list` - List all credentials
- `pheno credentials get <name>` - Get credential value
- `pheno credentials set <name> <value>` - Set credential value
- `pheno credentials delete <name>` - Delete credential
- `pheno credentials validate <names...>` - Validate credentials
- `pheno credentials audit` - Show audit log
- `pheno credentials stats` - Show statistics
- `pheno credentials cleanup` - Clean up expired credentials
- `pheno credentials tui` - Open TUI interface
- `pheno credentials export <file>` - Export credentials

### Options

- `--scope <scope>` - Filter by scope (global, project, environment)
- `--project <id>` - Set project context
- `--service <name>` - Filter by service
- `--format <format>` - Export format (json, csv)
- `--prompt/--no-prompt` - Enable/disable interactive prompting

## Best Practices

### Security

1. **Use Strong Master Passwords**: Choose a strong master password for encryption
2. **Regular Cleanup**: Periodically clean up expired credentials
3. **Audit Regularly**: Review audit logs for suspicious activity
4. **Limit Scope**: Use project-scoped credentials when possible
5. **Rotate Credentials**: Regularly rotate sensitive credentials

### Organization

1. **Use Descriptive Names**: Use clear, descriptive names for credentials
2. **Add Descriptions**: Include helpful descriptions for team members
3. **Use Tags**: Tag credentials for easy organization
4. **Service Grouping**: Group related credentials by service
5. **Environment Separation**: Use different credentials for different environments

### Team Workflow

1. **Onboarding**: Use TUI for guided credential setup
2. **Sharing**: Export/import credentials securely
3. **Documentation**: Document required credentials in README
4. **Validation**: Use validation commands in CI/CD
5. **Monitoring**: Set up alerts for credential issues

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Keyring Issues**: Check OS keyring configuration
3. **Permission Errors**: Verify file permissions for data directory
4. **Encryption Errors**: Check master password and key derivation

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for credentials
from pheno.credentials import CredentialBroker
broker = CredentialBroker()
```

### Reset Credentials

```bash
# Remove all credential data (use with caution)
rm -rf ~/.pheno/credentials/
rm -rf ~/.pheno/projects/
rm -rf ~/.pheno/audit/
```

## Contributing

The credentials system is part of the pheno-sdk. See the main project documentation for contributing guidelines.

## License

Proprietary - ATOMS-PHENO Team