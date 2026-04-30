"""
CLI commands for credential management.
"""

from pathlib import Path

try:
    import typer
    from rich import print as rprint
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False

import builtins

from .broker import CredentialBroker, get_credential_broker
from .models import CredentialScope, CredentialType
from .oauth.automation import AutomationRuleBuilder
from .oauth.models import OAuthFlow, OAuthProviderType
from .tui import run_credential_tui

if TYPER_AVAILABLE:
    app = typer.Typer(name="credentials", help="Credential management commands")
    console = Console()
else:
    app = None
    console = None


def get_broker() -> CredentialBroker:
    """Get credential broker instance."""
    return get_credential_broker()


if TYPER_AVAILABLE:
    @app.command()
    def list(
        scope: str | None = typer.Option(None, "--scope", "-s", help="Filter by scope"),
        project: str | None = typer.Option(None, "--project", "-p", help="Filter by project"),
        service: str | None = typer.Option(None, "--service", help="Filter by service"),
        expired: bool = typer.Option(False, "--expired", help="Show only expired credentials"),
    ):
        """List credentials."""
        broker = get_broker()

        # Set project context if specified
        if project:
            broker.set_project(project)

        # Get credentials
        credentials = broker.list_credentials(scope=scope, project_id=project)

        # Filter by service
        if service:
            credentials = [c for c in credentials if c.service == service]

        # Filter by expired
        if expired:
            credentials = [c for c in credentials if c.is_expired]

        # Display table
        table = Table(title="Credentials")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Scope", style="blue")
        table.add_column("Service", style="yellow")
        table.add_column("Status", style="red")
        table.add_column("Last Used", style="dim")

        for cred in credentials:
            status = "✅ Valid" if cred.is_valid else "❌ Invalid"
            if cred.is_expired:
                status = "⏰ Expired"

            last_used = cred.last_used.strftime("%Y-%m-%d") if cred.last_used else "Never"

            table.add_row(
                cred.name,
                cred.type.value,
                cred.scope.value,
                cred.service or "",
                status,
                last_used,
            )

        console.print(table)

    @app.command()
    def get(
        name: str = typer.Argument(..., help="Credential name"),
        project: str | None = typer.Option(None, "--project", "-p", help="Project context"),
        prompt: bool = typer.Option(True, "--prompt/--no-prompt", help="Prompt if not found"),
    ):
        """Get a credential value."""
        broker = get_broker()

        # Set project context if specified
        if project:
            broker.set_project(project)

        # Get credential
        value = broker.get_credential(name, prompt=prompt)

        if value:
            console.print(f"[green]{name}[/green]: {value}")
        else:
            console.print(f"[red]Credential '{name}' not found[/red]")

    @app.command()
    def set(
        name: str = typer.Argument(..., help="Credential name"),
        value: str | None = typer.Argument(None, help="Credential value"),
        type: str = typer.Option("secret", "--type", "-t", help="Credential type"),
        scope: str = typer.Option("project", "--scope", "-s", help="Credential scope"),
        service: str | None = typer.Option(None, "--service", help="Service provider"),
        description: str | None = typer.Option(None, "--description", "-d", help="Description"),
        project: str | None = typer.Option(None, "--project", "-p", help="Project context"),
        prompt: bool = typer.Option(True, "--prompt/--no-prompt", help="Prompt for value if not provided"),
    ):
        """Set a credential value."""
        broker = get_broker()

        # Set project context if specified
        if project:
            broker.set_project(project)

        # Get value if not provided
        if not value:
            if prompt:
                value = Prompt.ask(f"Enter value for {name}")
            else:
                console.print(f"[red]Value required for {name}[/red]")
                raise typer.Exit(1)

        # Validate type and scope
        try:
            cred_type = CredentialType(type)
        except ValueError:
            console.print(f"[red]Invalid credential type: {type}[/red]")
            raise typer.Exit(1)

        try:
            cred_scope = CredentialScope(scope)
        except ValueError:
            console.print(f"[red]Invalid credential scope: {scope}[/red]")
            raise typer.Exit(1)

        # Store credential
        success = broker.store_credential(
            name=name,
            value=value,
            credential_type=cred_type.value,
            scope=cred_scope.value,
            service=service,
            description=description,
        )

        if success:
            console.print(f"[green]Credential '{name}' stored successfully[/green]")
        else:
            console.print(f"[red]Failed to store credential '{name}'[/red]")
            raise typer.Exit(1)

    @app.command()
    def delete(
        name: str = typer.Argument(..., help="Credential name"),
        project: str | None = typer.Option(None, "--project", "-p", help="Project context"),
        force: bool = typer.Option(False, "--force", "-f", help="Force deletion without confirmation"),
    ):
        """Delete a credential."""
        broker = get_broker()

        # Set project context if specified
        if project:
            broker.set_project(project)

        # Confirm deletion
        if not force and not Confirm.ask(f"Delete credential '{name}'?"):
            console.print("Deletion cancelled")
            return

        # Delete credential
        success = broker.delete_credential(name)

        if success:
            console.print(f"[green]Credential '{name}' deleted successfully[/green]")
        else:
            console.print(f"[red]Failed to delete credential '{name}'[/red]")
            raise typer.Exit(1)

    @app.command()
    def validate(
        credentials: builtins.list[str] = typer.Argument(..., help="Credential names to validate"),
        project: str | None = typer.Option(None, "--project", "-p", help="Project context"),
    ):
        """Validate credentials."""
        broker = get_broker()

        # Set project context if specified
        if project:
            broker.set_project(project)

        # Validate credentials
        results = broker.validate_credentials(credentials)

        # Display results
        table = Table(title="Credential Validation")
        table.add_column("Credential", style="cyan")
        table.add_column("Status", style="green")

        all_valid = True
        for cred_name, is_valid in results.items():
            status = "✅ Valid" if is_valid else "❌ Invalid"
            if not is_valid:
                all_valid = False

            table.add_row(cred_name, status)

        console.print(table)

        if not all_valid:
            raise typer.Exit(1)

    @app.command()
    def audit(
        credential: str | None = typer.Option(None, "--credential", "-c", help="Filter by credential"),
        limit: int = typer.Option(100, "--limit", "-l", help="Limit number of entries"),
    ):
        """Show audit log."""
        broker = get_broker()

        # Get audit log
        audit_log = broker.get_audit_log(credential_id=credential, limit=limit)

        if not audit_log:
            console.print("No audit log entries found")
            return

        # Display table
        table = Table(title="Audit Log")
        table.add_column("Timestamp", style="dim")
        table.add_column("Action", style="cyan")
        table.add_column("User", style="blue")
        table.add_column("Success", style="green")
        table.add_column("Error", style="red")

        for entry in audit_log:
            success = "✅" if entry["success"] else "❌"
            error = entry["error_message"] or ""

            table.add_row(
                entry["timestamp"],
                entry["action"],
                entry["user"] or "",
                success,
                error,
            )

        console.print(table)

    @app.command()
    def stats():
        """Show credential statistics."""
        broker = get_broker()

        # Get statistics
        stats = broker.get_stats()

        # Display panel
        stats_text = f"""
Total Credentials: {stats['total_credentials']}
Valid Credentials: {stats['valid_credentials']}
Expired Credentials: {stats['expired_credentials']}
Global Credentials: {stats['global_credentials']}
Project Credentials: {stats['project_credentials']}
Environment Credentials: {stats['environment_credentials']}
OAuth Tokens: {stats['oauth_tokens']}
API Keys: {stats['api_keys']}
        """.strip()

        panel = Panel(stats_text, title="Credential Statistics", border_style="blue")
        console.print(panel)

    @app.command()
    def cleanup():
        """Clean up expired credentials."""
        broker = get_broker()

        # Clean up expired credentials
        cleaned_count = broker.cleanup_expired_credentials()

        console.print(f"[green]Cleaned up {cleaned_count} expired credentials[/green]")

    @app.command()
    def tui():
        """Open credential management TUI."""
        broker = get_broker()
        run_credential_tui(broker)

    @app.command()
    def export(
        file_path: Path = typer.Argument(..., help="Export file path"),
        format: str = typer.Option("json", "--format", "-f", help="Export format (json, csv)"),
        scope: str | None = typer.Option(None, "--scope", "-s", help="Filter by scope"),
    ):
        """Export credentials to file."""
        broker = get_broker()

        # Export credentials
        success = broker.export_credentials(file_path, format=format, scope=scope)

        if success:
            console.print(f"[green]Credentials exported to {file_path}[/green]")
        else:
            console.print("[red]Failed to export credentials[/red]")
            raise typer.Exit(1)

    # OAuth Commands

    @app.command()
    def oauth_start(
        provider: str = typer.Argument(..., help="OAuth provider"),
        name: str = typer.Argument(..., help="Flow name"),
        client_id: str = typer.Argument(..., help="Client ID"),
        client_secret: str = typer.Argument(..., help="Client secret"),
        redirect_uri: str = typer.Argument(..., help="Redirect URI"),
        scopes: builtins.list[str] = typer.Option([], "--scope", "-s", help="OAuth scopes"),
    ):
        """Start OAuth flow."""
        broker = get_broker()

        try:
            # Create OAuth flow
            flow = OAuthFlow(
                name=name,
                provider=OAuthProviderType(provider),
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scopes=scopes,
            )

            # Start flow
            import asyncio
            auth_url, state = asyncio.run(broker.start_oauth_flow(flow))

            console.print("[green]OAuth flow started[/green]")
            console.print(f"Authorization URL: {auth_url}")
            console.print(f"State: {state}")
            console.print("Please visit the URL and complete the authorization.")

        except Exception as e:
            console.print(f"[red]Failed to start OAuth flow: {e}[/red]")
            raise typer.Exit(1)

    @app.command()
    def oauth_complete(
        code: str = typer.Argument(..., help="Authorization code"),
        state: str = typer.Argument(..., help="State parameter"),
    ):
        """Complete OAuth flow."""
        broker = get_broker()

        try:
            import asyncio
            success = asyncio.run(broker.complete_oauth_flow(code, state))

            if success:
                console.print("[green]OAuth flow completed successfully[/green]")
            else:
                console.print("[red]Failed to complete OAuth flow[/red]")
                raise typer.Exit(1)

        except Exception as e:
            console.print(f"[red]Failed to complete OAuth flow: {e}[/red]")
            raise typer.Exit(1)

    @app.command()
    def oauth_refresh(
        provider: str = typer.Argument(..., help="OAuth provider"),
        name: str = typer.Argument(..., help="Flow name"),
    ):
        """Refresh OAuth token."""
        broker = get_broker()

        try:
            # Create OAuth flow (simplified)
            flow = OAuthFlow(
                name=name,
                provider=OAuthProviderType(provider),
                client_id="",
                client_secret="",
                redirect_uri="",
            )

            import asyncio
            success = asyncio.run(broker.refresh_oauth_token(flow))

            if success:
                console.print("[green]OAuth token refreshed successfully[/green]")
            else:
                console.print("[red]Failed to refresh OAuth token[/red]")
                raise typer.Exit(1)

        except Exception as e:
            console.print(f"[red]Failed to refresh OAuth token: {e}[/red]")
            raise typer.Exit(1)

    @app.command()
    def automation_list():
        """List automation rules."""
        broker = get_broker()

        rules = broker.list_automation_rules()

        if not rules:
            console.print("No automation rules found")
            return

        table = Table(title="Automation Rules")
        table.add_column("Name", style="cyan")
        table.add_column("Trigger", style="green")
        table.add_column("Actions", style="blue")
        table.add_column("Enabled", style="yellow")
        table.add_column("Executions", style="dim")

        for rule in rules:
            table.add_row(
                rule.name,
                rule.trigger_type,
                ", ".join(rule.actions),
                "✅" if rule.enabled else "❌",
                str(rule.execution_count),
            )

        console.print(table)

    @app.command()
    def automation_add(
        name: str = typer.Argument(..., help="Rule name"),
        trigger: str = typer.Argument(..., help="Trigger type"),
        actions: builtins.list[str] = typer.Argument(..., help="Actions to perform"),
    ):
        """Add automation rule."""
        broker = get_broker()

        try:
            # Create rule using builder
            builder = AutomationRuleBuilder()
            rule = (builder
                   .with_name(name)
                   .on_event(trigger)
                   .cleanup_expired()
                   .build())

            # Add actions
            for action in actions:
                if action == "refresh_tokens":
                    builder.refresh_tokens()
                elif action == "cleanup_expired":
                    builder.cleanup_expired()
                elif action == "validate_credentials":
                    builder.validate_credentials()

            rule = builder.build()
            success = broker.add_automation_rule(rule)

            if success:
                console.print(f"[green]Automation rule '{name}' added successfully[/green]")
            else:
                console.print("[red]Failed to add automation rule[/red]")
                raise typer.Exit(1)

        except Exception as e:
            console.print(f"[red]Failed to add automation rule: {e}[/red]")
            raise typer.Exit(1)

    @app.command()
    def services_start():
        """Start background services."""
        broker = get_broker()

        try:
            import asyncio
            asyncio.run(broker.start_services())
            console.print("[green]Background services started[/green]")
        except Exception as e:
            console.print(f"[red]Failed to start services: {e}[/red]")
            raise typer.Exit(1)

    @app.command()
    def services_stop():
        """Stop background services."""
        broker = get_broker()

        try:
            import asyncio
            asyncio.run(broker.stop_services())
            console.print("[green]Background services stopped[/green]")
        except Exception as e:
            console.print(f"[red]Failed to stop services: {e}[/red]")
            raise typer.Exit(1)

    # Hierarchical Scoping Commands

    @app.command()
    def hierarchy_list():
        """List scope hierarchies."""
        broker = get_broker()

        hierarchies = broker.hierarchy_manager.list_hierarchies()

        if not hierarchies:
            console.print("No hierarchies found")
            return

        table = Table(title="Scope Hierarchies")
        table.add_column("Name", style="cyan")
        table.add_column("Nodes", style="green")
        table.add_column("Depth", style="blue")
        table.add_column("Version", style="yellow")

        for name in hierarchies:
            hierarchy = broker.get_hierarchy(name)
            if hierarchy:
                stats = broker.get_scope_statistics(name)
                table.add_row(
                    name,
                    str(stats.get("total_nodes", 0)),
                    str(stats.get("depth", 0)),
                    str(hierarchy.version),
                )

        console.print(table)

    @app.command()
    def hierarchy_create(
        name: str = typer.Argument(..., help="Hierarchy name"),
        description: str = typer.Option(None, "--description", "-d", help="Hierarchy description"),
    ):
        """Create a new scope hierarchy."""
        broker = get_broker()

        try:
            broker.create_hierarchy(name, description)
            console.print(f"[green]Hierarchy '{name}' created successfully[/green]")
        except ValueError as e:
            console.print(f"[red]Failed to create hierarchy: {e}[/red]")
            raise typer.Exit(1)

    @app.command()
    def hierarchy_show(
        name: str = typer.Argument("default", help="Hierarchy name"),
    ):
        """Show hierarchy tree."""
        broker = get_broker()

        hierarchy = broker.get_hierarchy(name)
        if not hierarchy:
            console.print(f"[red]Hierarchy '{name}' not found[/red]")
            raise typer.Exit(1)

        tree = broker.get_scope_hierarchy_tree(name)
        console.print(f"[bold]Hierarchy: {name}[/bold]")
        console.print(json.dumps(tree, indent=2))

    @app.command()
    def scope_resolve(
        name: str = typer.Argument(..., help="Credential name"),
        scope_path: str = typer.Argument(..., help="Scope path"),
        hierarchy: str = typer.Option("default", "--hierarchy", "-h", help="Hierarchy name"),
    ):
        """Resolve credential using hierarchical scoping."""
        broker = get_broker()

        try:
            value = broker.resolve_credential_hierarchical(name, scope_path, hierarchy)
            if value:
                console.print(f"[green]{name}[/green]: {value}")
            else:
                console.print(f"[red]Credential '{name}' not found in scope '{scope_path}'[/red]")
        except Exception as e:
            console.print(f"[red]Failed to resolve credential: {e}[/red]")
            raise typer.Exit(1)

    @app.command()
    def scope_list(
        scope_path: str = typer.Argument(..., help="Scope path"),
        hierarchy: str = typer.Option("default", "--hierarchy", "-h", help="Hierarchy name"),
    ):
        """List credentials for a scope."""
        broker = get_broker()

        try:
            credentials = broker.get_scope_credentials(scope_path, hierarchy)

            if not credentials:
                console.print(f"No credentials found for scope '{scope_path}'")
                return

            table = Table(title=f"Credentials for scope: {scope_path}")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Service", style="blue")
            table.add_column("Status", style="yellow")

            for cred in credentials:
                status = "✅ Valid" if cred.is_valid else "❌ Invalid"
                if cred.is_expired:
                    status = "⏰ Expired"

                table.add_row(
                    cred.name,
                    cred.type.value,
                    cred.service or "",
                    status,
                )

            console.print(table)
        except Exception as e:
            console.print(f"[red]Failed to list scope credentials: {e}[/red]")
            raise typer.Exit(1)

    @app.command()
    def scope_create(
        name: str = typer.Argument(..., help="Credential name"),
        value: str = typer.Argument(..., help="Credential value"),
        scope_path: str = typer.Argument(..., help="Scope path"),
        type: str = typer.Option("secret", "--type", "-t", help="Credential type"),
        hierarchy: str = typer.Option("default", "--hierarchy", "-h", help="Hierarchy name"),
    ):
        """Create credential in a specific scope."""
        broker = get_broker()

        try:
            success = broker.create_scope_credential(name, value, scope_path, type, hierarchy)

            if success:
                console.print(f"[green]Credential '{name}' created in scope '{scope_path}'[/green]")
            else:
                console.print("[red]Failed to create credential[/red]")
                raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Failed to create credential: {e}[/red]")
            raise typer.Exit(1)

    @app.command()
    def scope_stats(
        hierarchy: str = typer.Option("default", "--hierarchy", "-h", help="Hierarchy name"),
    ):
        """Show scope statistics."""
        broker = get_broker()

        try:
            stats = broker.get_scope_statistics(hierarchy)

            panel = Panel(
                json.dumps(stats, indent=2),
                title=f"Scope Statistics: {hierarchy}",
                border_style="blue",
            )
            console.print(panel)
        except Exception as e:
            console.print(f"[red]Failed to get scope statistics: {e}[/red]")
            raise typer.Exit(1)


def main():
    """Main entry point for credential CLI."""
    if not TYPER_AVAILABLE:
        print("Typer not available. Install with: pip install typer")
        return

    app()


if __name__ == "__main__":
    main()


__all__ = ["app", "main"]
