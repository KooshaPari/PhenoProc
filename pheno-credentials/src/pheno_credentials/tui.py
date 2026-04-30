"""
TUI for credential management using Textual.
"""


try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical
    from textual.message import Message
    from textual.reactive import reactive
    from textual.screen import Screen
    from textual.widgets import (
        Button,
        DataTable,
        Footer,
        Header,
        Input,
        Label,
        Select,
        Static,
        Tab,
        Tabs,
        TextArea,
    )
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from typing import TYPE_CHECKING

from .broker import CredentialBroker

if TYPE_CHECKING:
    from .models import Credential


class CredentialTUI(App):
    """TUI application for credential management."""

    CSS = """
    Screen {
        layout: vertical;
    }

    .header {
        dock: top;
        height: 3;
    }

    .main {
        layout: horizontal;
    }

    .sidebar {
        width: 30%;
        border: solid $primary;
        margin: 1;
    }

    .content {
        width: 70%;
        border: solid $primary;
        margin: 1;
    }

    .footer {
        dock: bottom;
        height: 3;
    }

    DataTable {
        height: 100%;
    }

    .form {
        padding: 1;
    }

    .form Input {
        margin: 1;
    }

    .form Button {
        margin: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("n", "new_credential", "New Credential"),
        Binding("e", "edit_credential", "Edit Credential"),
        Binding("d", "delete_credential", "Delete Credential"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "search", "Search"),
    ]

    def __init__(self, broker: CredentialBroker | None = None):
        """Initialize credential TUI.

        Args:
            broker: Credential broker instance
        """
        super().__init__()
        self.broker = broker or CredentialBroker()
        self.current_credentials: list[Credential] = []
        self.selected_credential: Credential | None = None

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()

        with Container(classes="main"):
            with Container(classes="sidebar"):
                yield Label("Projects", classes="header")
                yield Select([], id="project_select")
                yield Label("Credentials", classes="header")
                yield DataTable(id="credential_table")

            with Container(classes="content"):
                yield Tabs(
                    Tab("Details", id="details_tab"),
                    Tab("Edit", id="edit_tab"),
                    Tab("Audit", id="audit_tab"),
                    id="content_tabs",
                )

                with Container(id="details_tab_content"):
                    yield Static("Select a credential to view details", id="credential_details")

                with Container(id="edit_tab_content"):
                    yield Static("Edit form will appear here", id="edit_form")

                with Container(id="audit_tab_content"):
                    yield DataTable(id="audit_table")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the UI."""
        self.load_projects()
        self.load_credentials()
        self.setup_credential_table()
        self.setup_audit_table()

    def load_projects(self):
        """Load projects into the select widget."""
        projects = self.broker.project_manager.list_projects()
        options = [(f"{p.name} ({p.id})", p.id) for p in projects]

        project_select = self.query_one("#project_select", Select)
        project_select.set_options(options)

    def load_credentials(self):
        """Load credentials into the table."""
        self.current_credentials = self.broker.list_credentials()
        self.update_credential_table()

    def setup_credential_table(self):
        """Setup the credential table."""
        table = self.query_one("#credential_table", DataTable)
        table.add_columns("Name", "Type", "Scope", "Service", "Status")

    def update_credential_table(self):
        """Update the credential table with current data."""
        table = self.query_one("#credential_table", DataTable)
        table.clear()

        for cred in self.current_credentials:
            status = "✅ Valid" if cred.is_valid else "❌ Invalid"
            if cred.is_expired:
                status = "⏰ Expired"

            table.add_row(
                cred.name,
                cred.type.value,
                cred.scope.value,
                cred.service or "",
                status,
            )

    def setup_audit_table(self):
        """Setup the audit table."""
        table = self.query_one("#audit_table", DataTable)
        table.add_columns("Timestamp", "Action", "User", "Success", "Error")

    def update_audit_table(self, credential_id: str | None = None):
        """Update the audit table."""
        table = self.query_one("#audit_table", DataTable)
        table.clear()

        audit_log = self.broker.get_audit_log(credential_id=credential_id, limit=50)

        for entry in audit_log:
            table.add_row(
                entry["timestamp"],
                entry["action"],
                entry["user"] or "",
                "✅" if entry["success"] else "❌",
                entry["error_message"] or "",
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle credential table row selection."""
        if event.data_table.id == "credential_table":
            row_index = event.row_index
            if row_index < len(self.current_credentials):
                self.selected_credential = self.current_credentials[row_index]
                self.update_credential_details()
                self.update_audit_table(str(self.selected_credential.id))

    def update_credential_details(self):
        """Update the credential details display."""
        if not self.selected_credential:
            return

        cred = self.selected_credential
        details = f"""
Name: {cred.name}
Type: {cred.type.value}
Scope: {cred.scope.value}
Service: {cred.service or "N/A"}
Description: {cred.description or "N/A"}
Tags: {", ".join(cred.tags) if cred.tags else "None"}
Created: {cred.created_at.strftime("%Y-%m-%d %H:%M:%S")}
Last Modified: {cred.last_modified.strftime("%Y-%m-%d %H:%M:%S")}
Last Used: {cred.last_used.strftime("%Y-%m-%d %H:%M:%S") if cred.last_used else "Never"}
Expires: {cred.expires_at.strftime("%Y-%m-%d %H:%M:%S") if cred.expires_at else "Never"}
Status: {"Valid" if cred.is_valid else "Invalid"}
Encrypted: {"Yes" if cred.encrypted else "No"}
Auto Refresh: {"Yes" if cred.auto_refresh else "No"}
        """.strip()

        details_widget = self.query_one("#credential_details", Static)
        details_widget.update(details)

    def action_new_credential(self) -> None:
        """Create a new credential."""
        # This would open a new credential form
        # For now, just show a message
        self.notify("New credential form would open here")

    def action_edit_credential(self) -> None:
        """Edit the selected credential."""
        if not self.selected_credential:
            self.notify("Please select a credential to edit")
            return

        # This would open an edit form
        # For now, just show a message
        self.notify(f"Edit form for {self.selected_credential.name} would open here")

    def action_delete_credential(self) -> None:
        """Delete the selected credential."""
        if not self.selected_credential:
            self.notify("Please select a credential to delete")
            return

        # This would show a confirmation dialog
        # For now, just show a message
        self.notify(f"Delete confirmation for {self.selected_credential.name} would show here")

    def action_refresh(self) -> None:
        """Refresh the credential list."""
        self.load_credentials()
        self.notify("Credential list refreshed")

    def action_search(self) -> None:
        """Search credentials."""
        # This would open a search dialog
        # For now, just show a message
        self.notify("Search dialog would open here")


def run_credential_tui(broker: CredentialBroker | None = None) -> None:
    """Run the credential management TUI.

    Args:
        broker: Credential broker instance
    """
    if not TEXTUAL_AVAILABLE:
        print("Textual not available. Install with: pip install textual")
        return

    app = CredentialTUI(broker)
    app.run()


__all__ = ["CredentialTUI", "run_credential_tui"]
