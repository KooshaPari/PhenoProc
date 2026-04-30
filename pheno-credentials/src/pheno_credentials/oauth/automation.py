"""
Automation engine for credential management.
"""

import asyncio
import contextlib
from datetime import datetime
from typing import Any
from uuid import UUID

from .models import AutomationEvent, AutomationRule


class AutomationEngine:
    """Automation engine for credential management."""

    def __init__(self, credential_store, token_manager):
        """Initialize automation engine.

        Args:
            credential_store: Credential store
            token_manager: Token manager
        """
        self.credential_store = credential_store
        self.token_manager = token_manager
        self.rules: dict[UUID, AutomationRule] = {}
        self.events: list[AutomationEvent] = []
        self._running = False
        self._event_processor_task: asyncio.Task | None = None

    async def start(self):
        """Start automation engine."""
        if self._running:
            return

        self._running = True
        self._event_processor_task = asyncio.create_task(self._event_processor_loop())

    async def stop(self):
        """Stop automation engine."""
        self._running = False
        if self._event_processor_task:
            self._event_processor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._event_processor_task

    def add_rule(self, rule: AutomationRule) -> bool:
        """Add automation rule.

        Args:
            rule: Automation rule

        Returns:
            True if successful
        """
        self.rules[rule.id] = rule
        return True

    def remove_rule(self, rule_id: UUID) -> bool:
        """Remove automation rule.

        Args:
            rule_id: Rule ID

        Returns:
            True if successful
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    def get_rule(self, rule_id: UUID) -> AutomationRule | None:
        """Get automation rule.

        Args:
            rule_id: Rule ID

        Returns:
            Automation rule if found
        """
        return self.rules.get(rule_id)

    def list_rules(self) -> list[AutomationRule]:
        """List all automation rules.

        Returns:
            List of automation rules
        """
        return list(self.rules.values())

    async def trigger_event(self, event_type: str, source: str, data: dict[str, Any] | None = None):
        """Trigger automation event.

        Args:
            event_type: Event type
            source: Event source
            data: Event data
        """
        event = AutomationEvent(
            event_type=event_type,
            source=source,
            data=data or {},
        )

        self.events.append(event)

    async def _event_processor_loop(self):
        """Event processor loop."""
        while self._running:
            try:
                await self._process_events()
                await asyncio.sleep(10)  # Check every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but continue
                pass

    async def _process_events(self):
        """Process pending events."""
        unprocessed_events = [
            event for event in self.events
            if not event.processed
        ]

        for event in unprocessed_events:
            await self._process_event(event)

    async def _process_event(self, event: AutomationEvent):
        """Process single event.

        Args:
            event: Event to process
        """
        try:
            # Find matching rules
            matching_rules = self._find_matching_rules(event)

            for rule in matching_rules:
                if rule.can_execute:
                    await self._execute_rule(rule, event)
                    rule.execution_count += 1
                    rule.last_executed = datetime.utcnow()

            event.processed = True

        except Exception:
            # Log error but mark event as processed to avoid infinite retry
            event.processed = True

    def _find_matching_rules(self, event: AutomationEvent) -> list[AutomationRule]:
        """Find rules matching event.

        Args:
            event: Event to match

        Returns:
            List of matching rules
        """
        matching_rules = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            if self._rule_matches_event(rule, event):
                matching_rules.append(rule)

        # Sort by priority (higher priority first)
        matching_rules.sort(key=lambda r: r.priority, reverse=True)

        return matching_rules

    def _rule_matches_event(self, rule: AutomationRule, event: AutomationEvent) -> bool:
        """Check if rule matches event.

        Args:
            rule: Automation rule
            event: Event

        Returns:
            True if rule matches event
        """
        # Check trigger type
        if rule.trigger_type != "event":
            return False

        # Check event type
        expected_event_type = rule.trigger_config.get("event_type")
        if expected_event_type and expected_event_type != event.event_type:
            return False

        # Check source
        expected_source = rule.trigger_config.get("source")
        if expected_source and expected_source != event.source:
            return False

        # Check additional conditions
        conditions = rule.trigger_config.get("conditions", {})
        for key, expected_value in conditions.items():
            if event.data.get(key) != expected_value:
                return False

        return True

    async def _execute_rule(self, rule: AutomationRule, event: AutomationEvent):
        """Execute automation rule.

        Args:
            rule: Automation rule
            event: Triggering event
        """
        for action in rule.actions:
            await self._execute_action(action, rule.action_config, event)

    async def _execute_action(self, action: str, config: dict[str, Any], event: AutomationEvent):
        """Execute automation action.

        Args:
            action: Action name
            config: Action configuration
            event: Triggering event
        """
        if action == "refresh_tokens":
            await self._action_refresh_tokens(config, event)
        elif action == "cleanup_expired":
            await self._action_cleanup_expired(config, event)
        elif action == "validate_credentials":
            await self._action_validate_credentials(config, event)
        elif action == "notify":
            await self._action_notify(config, event)
        elif action == "export_credentials":
            await self._action_export_credentials(config, event)
        else:
            # Unknown action
            pass

    async def _action_refresh_tokens(self, config: dict[str, Any], event: AutomationEvent):
        """Refresh tokens action.

        Args:
            config: Action configuration
            event: Triggering event
        """
        providers = config.get("providers", [])
        if not providers:
            return

        for provider_name in providers:
            try:
                # Find OAuth flows for this provider
                flows = await self._find_flows_for_provider(provider_name)
                for flow in flows:
                    await self.token_manager.refresh_token(flow)
            except Exception:
                # Log error but continue
                pass

    async def _action_cleanup_expired(self, config: dict[str, Any], event: AutomationEvent):
        """Cleanup expired credentials action.

        Args:
            config: Action configuration
            event: Triggering event
        """
        try:
            cleaned_count = self.credential_store.cleanup_expired_credentials()

            # Trigger notification event
            await self.trigger_event(
                "cleanup_completed",
                "automation_engine",
                {"cleaned_count": cleaned_count},
            )
        except Exception:
            # Log error
            pass

    async def _action_validate_credentials(self, config: dict[str, Any], event: AutomationEvent):
        """Validate credentials action.

        Args:
            config: Action configuration
            event: Triggering event
        """
        credential_patterns = config.get("credential_patterns", [])
        if not credential_patterns:
            return

        try:
            # Get all credentials
            all_credentials = self.credential_store.list_credentials()

            # Filter by patterns
            matching_credentials = []
            for cred in all_credentials:
                for pattern in credential_patterns:
                    if pattern in cred.name:
                        matching_credentials.append(cred.name)
                        break

            # Validate credentials
            validation_results = self.credential_store.validate_credentials(matching_credentials)

            # Trigger notification event
            await self.trigger_event(
                "validation_completed",
                "automation_engine",
                {"validation_results": validation_results},
            )
        except Exception:
            # Log error
            pass

    async def _action_notify(self, config: dict[str, Any], event: AutomationEvent):
        """Send notification action.

        Args:
            config: Action configuration
            event: Triggering event
        """
        message = config.get("message", "Automation event occurred")
        config.get("channels", [])

        # This is a placeholder - in a real implementation, you'd integrate
        # with notification services like Slack, email, etc.
        print(f"NOTIFICATION: {message}")

    async def _action_export_credentials(self, config: dict[str, Any], event: AutomationEvent):
        """Export credentials action.

        Args:
            config: Action configuration
            event: Triggering event
        """
        file_path = config.get("file_path")
        format_type = config.get("format", "json")
        scope = config.get("scope")

        if not file_path:
            return

        try:
            success = self.credential_store.export_credentials(
                file_path=file_path,
                format=format_type,
                scope=scope,
            )

            if success:
                await self.trigger_event(
                    "export_completed",
                    "automation_engine",
                    {"file_path": file_path, "format": format_type},
                )
        except Exception:
            # Log error
            pass

    async def _find_flows_for_provider(self, provider_name: str) -> list[Any]:
        """Find OAuth flows for provider.

        Args:
            provider_name: Provider name

        Returns:
            List of OAuth flows
        """
        # This is a placeholder - in a real implementation, you'd query
        # the credential store for OAuth flows for this provider
        return []

    def get_automation_status(self) -> dict[str, Any]:
        """Get automation engine status.

        Returns:
            Status information
        """
        return {
            "running": self._running,
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r.enabled]),
            "total_events": len(self.events),
            "unprocessed_events": len([e for e in self.events if not e.processed]),
        }


class AutomationRuleBuilder:
    """Builder for automation rules."""

    def __init__(self):
        """Initialize rule builder."""
        self.rule = AutomationRule(
            name="",
            trigger_type="",
            actions=[],
            trigger_config={},
            action_config={},
        )

    def with_name(self, name: str) -> "AutomationRuleBuilder":
        """Set rule name.

        Args:
            name: Rule name

        Returns:
            Self for chaining
        """
        self.rule.name = name
        return self

    def with_description(self, description: str) -> "AutomationRuleBuilder":
        """Set rule description.

        Args:
            description: Rule description

        Returns:
            Self for chaining
        """
        self.rule.description = description
        return self

    def on_event(self, event_type: str, source: str | None = None, **conditions) -> "AutomationRuleBuilder":
        """Set event trigger.

        Args:
            event_type: Event type
            source: Event source
            **conditions: Additional conditions

        Returns:
            Self for chaining
        """
        self.rule.trigger_type = "event"
        self.rule.trigger_config = {
            "event_type": event_type,
            "source": source,
            "conditions": conditions,
        }
        return self

    def on_schedule(self, cron_expression: str) -> "AutomationRuleBuilder":
        """Set schedule trigger.

        Args:
            cron_expression: Cron expression

        Returns:
            Self for chaining
        """
        self.rule.trigger_type = "schedule"
        self.rule.trigger_config = {
            "cron": cron_expression,
        }
        return self

    def refresh_tokens(self, providers: list[str] | None = None) -> "AutomationRuleBuilder":
        """Add refresh tokens action.

        Args:
            providers: List of providers to refresh

        Returns:
            Self for chaining
        """
        self.rule.actions.append("refresh_tokens")
        self.rule.action_config["providers"] = providers or []
        return self

    def cleanup_expired(self) -> "AutomationRuleBuilder":
        """Add cleanup expired action.

        Returns:
            Self for chaining
        """
        self.rule.actions.append("cleanup_expired")
        return self

    def validate_credentials(self, patterns: list[str] | None = None) -> "AutomationRuleBuilder":
        """Add validate credentials action.

        Args:
            patterns: Credential name patterns

        Returns:
            Self for chaining
        """
        self.rule.actions.append("validate_credentials")
        self.rule.action_config["credential_patterns"] = patterns or []
        return self

    def notify(self, message: str, channels: list[str] | None = None) -> "AutomationRuleBuilder":
        """Add notification action.

        Args:
            message: Notification message
            channels: Notification channels

        Returns:
            Self for chaining
        """
        self.rule.actions.append("notify")
        self.rule.action_config.update({
            "message": message,
            "channels": channels or [],
        })
        return self

    def export_credentials(self, file_path: str, format_type: str = "json", scope: str | None = None) -> "AutomationRuleBuilder":
        """Add export credentials action.

        Args:
            file_path: Export file path
            format_type: Export format
            scope: Credential scope

        Returns:
            Self for chaining
        """
        self.rule.actions.append("export_credentials")
        self.rule.action_config.update({
            "file_path": file_path,
            "format": format_type,
            "scope": scope,
        })
        return self

    def with_priority(self, priority: int) -> "AutomationRuleBuilder":
        """Set rule priority.

        Args:
            priority: Rule priority

        Returns:
            Self for chaining
        """
        self.rule.priority = priority
        return self

    def with_max_executions(self, max_executions: int) -> "AutomationRuleBuilder":
        """Set maximum executions per day.

        Args:
            max_executions: Maximum executions

        Returns:
            Self for chaining
        """
        self.rule.max_executions = max_executions
        return self

    def build(self) -> AutomationRule:
        """Build automation rule.

        Returns:
            Built automation rule
        """
        return self.rule


__all__ = ["AutomationEngine", "AutomationRuleBuilder"]
