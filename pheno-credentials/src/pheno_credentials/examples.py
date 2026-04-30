"""
Examples of using the credentials broker system.
"""


from .broker import CredentialBroker, get_credential


def basic_usage_example():
    """Basic usage example."""
    print("=== Basic Credential Management ===")

    # Get credential broker
    broker = CredentialBroker()

    # Store a credential
    broker.store_credential(
        name="OPENAI_API_KEY",
        value="sk-1234567890abcdef",
        credential_type="api_key",
        scope="global",
        service="openai",
        description="OpenAI API key for GPT models",
    )

    # Get a credential
    api_key = broker.get_credential("OPENAI_API_KEY")
    print(f"OpenAI API Key: {api_key[:10]}...")

    # List credentials
    credentials = broker.list_credentials()
    print(f"Total credentials: {len(credentials)}")

    # Get statistics
    stats = broker.get_stats()
    print(f"Statistics: {stats}")


def project_scoped_example():
    """Project-scoped credentials example."""
    print("\n=== Project-Scoped Credentials ===")

    broker = CredentialBroker()

    # Create a project
    project = broker.create_project(
        project_id="my-awesome-project",
        name="My Awesome Project",
        description="A sample project for credential management",
        path="/path/to/project",
    )

    # Set project context
    broker.set_project(project.id)

    # Store project-scoped credentials
    broker.store_credential(
        name="DATABASE_URL",
        value="postgresql://user:pass@localhost/mydb",
        credential_type="database_url",
        scope="project",
        service="postgres",
        description="Project database connection",
    )

    # Get project credentials
    project_creds = broker.list_credentials(scope="project")
    print(f"Project credentials: {len(project_creds)}")

    # Get credential with project context
    db_url = broker.get_credential("DATABASE_URL")
    print(f"Database URL: {db_url[:20]}...")


def environment_management_example():
    """Environment variable management example."""
    print("\n=== Environment Variable Management ===")

    broker = CredentialBroker()

    # Get environment manager
    env_manager = broker.environment_manager

    # Set some environment variables
    env_manager.set("MY_API_KEY", "secret-value-123")
    env_manager.set("MY_DATABASE_URL", "postgresql://localhost/mydb")

    # Get environment variables
    api_key = env_manager.get("MY_API_KEY")
    db_url = env_manager.get("MY_DATABASE_URL")

    print(f"API Key: {api_key}")
    print(f"Database URL: {db_url}")

    # Validate required variables
    required_vars = ["MY_API_KEY", "MY_DATABASE_URL", "MISSING_VAR"]
    validation_results = env_manager.validate_required(required_vars)

    print(f"Validation results: {validation_results}")

    # Get missing variables
    missing = env_manager.get_missing_required(required_vars)
    print(f"Missing variables: {missing}")


def credential_search_example():
    """Credential search example."""
    print("\n=== Credential Search ===")

    broker = CredentialBroker()

    # Store various credentials
    credentials_data = [
        ("GITHUB_TOKEN", "ghp_1234567890", "oauth_token", "global", "github"),
        ("AWS_ACCESS_KEY", "AKIA1234567890", "api_key", "global", "aws"),
        ("OPENAI_API_KEY", "sk-1234567890", "api_key", "project", "openai"),
        ("DATABASE_PASSWORD", "secret123", "password", "project", "postgres"),
        ("REDIS_URL", "redis://localhost:6379", "connection_string", "environment", "redis"),
    ]

    for name, value, cred_type, scope, service in credentials_data:
        broker.store_credential(
            name=name,
            value=value,
            credential_type=cred_type,
            scope=scope,
            service=service,
        )

    # Search by type
    api_keys = broker.search_credentials(
        broker.models.CredentialSearch(type="api_key"),
    )
    print(f"API Keys: {[c.name for c in api_keys]}")

    # Search by service
    github_creds = broker.search_credentials(
        broker.models.CredentialSearch(service="github"),
    )
    print(f"GitHub credentials: {[c.name for c in github_creds]}")

    # Search by scope
    global_creds = broker.search_credentials(
        broker.models.CredentialSearch(scope="global"),
    )
    print(f"Global credentials: {[c.name for c in global_creds]}")


def audit_logging_example():
    """Audit logging example."""
    print("\n=== Audit Logging ===")

    broker = CredentialBroker()

    # Perform some operations
    broker.store_credential("TEST_KEY", "test-value", "secret")
    broker.get_credential("TEST_KEY")
    broker.delete_credential("TEST_KEY")

    # Get audit log
    audit_log = broker.get_audit_log(limit=10)
    print(f"Audit log entries: {len(audit_log)}")

    for entry in audit_log:
        print(f"  {entry['timestamp']}: {entry['action']} - {entry['success']}")


def security_alerts_example():
    """Security alerts example."""
    print("\n=== Security Alerts ===")

    broker = CredentialBroker()

    # Get security alerts
    alerts = broker.get_security_alerts()
    print(f"Security alerts: {len(alerts)}")

    for alert in alerts:
        print(f"  {alert['type']}: {alert['message']} ({alert['severity']})")


def integration_example():
    """Integration with existing code example."""
    print("\n=== Integration Example ===")

    # This shows how to integrate with existing code
    # Instead of using os.getenv() directly, use the credential broker

    # Old way:
    # import os
    # api_key = os.getenv("OPENAI_API_KEY")

    # New way:

    # This will automatically:
    # 1. Check secure credential store
    # 2. Check environment variables
    # 3. Check .env files
    # 4. Prompt user if not found
    api_key = get_credential("OPENAI_API_KEY", prompt=True)

    print(f"API Key retrieved: {api_key[:10]}...")


def main():
    """Run all examples."""
    try:
        basic_usage_example()
        project_scoped_example()
        environment_management_example()
        credential_search_example()
        audit_logging_example()
        security_alerts_example()
        integration_example()

        print("\n=== All Examples Completed Successfully! ===")

    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


__all__ = ["main"]
