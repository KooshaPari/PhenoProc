"""
Token management and refresh scheduling.
"""

import asyncio
import contextlib
import json
from datetime import datetime, timedelta
from uuid import UUID

from .flows import OAuthFlowManager
from .models import OAuthFlow, OAuthToken, TokenRefreshJob


class TokenManager:
    """Manages OAuth tokens and refresh scheduling."""

    def __init__(self, credential_store, flow_manager: OAuthFlowManager | None = None):
        """Initialize token manager.

        Args:
            credential_store: Credential store for persistence
            flow_manager: OAuth flow manager
        """
        self.credential_store = credential_store
        self.flow_manager = flow_manager or OAuthFlowManager()
        self.refresh_jobs: dict[UUID, TokenRefreshJob] = {}
        self._running = False
        self._refresh_task: asyncio.Task | None = None

    async def start(self):
        """Start token manager."""
        if self._running:
            return

        self._running = True
        self._refresh_task = asyncio.create_task(self._refresh_loop())

    async def stop(self):
        """Stop token manager."""
        self._running = False
        if self._refresh_task:
            self._refresh_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._refresh_task

    async def store_token(self, token: OAuthToken, flow: OAuthFlow) -> bool:
        """Store OAuth token.

        Args:
            token: OAuth token
            flow: OAuth flow configuration

        Returns:
            True if successful
        """
        # Convert token to credential format
        credential_name = f"oauth_{flow.provider.value}_{flow.name}"

        # Store token data
        token_data = {
            "provider": token.provider.value,
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "token_type": token.token_type,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "scope": token.scope,
            "created_at": token.created_at.isoformat(),
            "last_used": token.last_used.isoformat() if token.last_used else None,
            "last_refreshed": token.last_refreshed.isoformat() if token.last_refreshed else None,
            "provider_data": token.provider_data,
        }

        # Store as credential
        success = self.credential_store.store_credential(
            name=credential_name,
            value=json.dumps(token_data),
            credential_type="oauth_token",
            scope="global",
            service=flow.provider.value,
            description=f"OAuth token for {flow.name}",
            expires_at=token.expires_at,
            auto_refresh=flow.auto_refresh,
        )

        if success and flow.auto_refresh and token.can_refresh:
            # Schedule refresh job
            await self._schedule_refresh(token.id, flow, token.expires_at)

        return success

    async def get_token(self, flow: OAuthFlow) -> OAuthToken | None:
        """Get OAuth token for flow.

        Args:
            flow: OAuth flow configuration

        Returns:
            OAuth token if found
        """
        credential_name = f"oauth_{flow.provider.value}_{flow.name}"
        credential = self.credential_store.retrieve(credential_name)

        if not credential:
            return None

        try:
            token_data = json.loads(credential.value)
            return OAuthToken(
                id=credential.id,
                provider=token_data["provider"],
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type=token_data.get("token_type", "Bearer"),
                expires_at=datetime.fromisoformat(token_data["expires_at"]) if token_data.get("expires_at") else None,
                scope=token_data.get("scope", []),
                created_at=datetime.fromisoformat(token_data["created_at"]),
                last_used=datetime.fromisoformat(token_data["last_used"]) if token_data.get("last_used") else None,
                last_refreshed=datetime.fromisoformat(token_data["last_refreshed"]) if token_data.get("last_refreshed") else None,
                provider_data=token_data.get("provider_data", {}),
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    async def refresh_token(self, flow: OAuthFlow) -> OAuthToken | None:
        """Refresh OAuth token.

        Args:
            flow: OAuth flow configuration

        Returns:
            Refreshed token if successful
        """
        token = await self.get_token(flow)
        if not token or not token.can_refresh:
            return None

        try:
            refreshed_token = await self.flow_manager.refresh_token(flow, token)
            refreshed_token.id = token.id  # Preserve ID
            refreshed_token.last_refreshed = datetime.utcnow()

            # Update stored token
            await self.store_token(refreshed_token, flow)

            return refreshed_token

        except Exception:
            return None

    async def revoke_token(self, flow: OAuthFlow) -> bool:
        """Revoke OAuth token.

        Args:
            flow: OAuth flow configuration

        Returns:
            True if successful
        """
        token = await self.get_token(flow)
        if not token:
            return False

        try:
            success = await self.flow_manager.revoke_token(flow, token)

            if success:
                # Remove from store
                credential_name = f"oauth_{flow.provider.value}_{flow.name}"
                self.credential_store.delete(credential_name)

                # Cancel refresh job
                if token.id in self.refresh_jobs:
                    del self.refresh_jobs[token.id]

            return success

        except Exception:
            return False

    async def _schedule_refresh(self, token_id: UUID, flow: OAuthFlow, expires_at: datetime | None):
        """Schedule token refresh.

        Args:
            token_id: Token ID
            flow: OAuth flow configuration
            expires_at: Token expiration time
        """
        if not expires_at:
            return

        # Schedule refresh 5 minutes before expiration
        refresh_time = expires_at - timedelta(minutes=5)

        job = TokenRefreshJob(
            token_id=token_id,
            scheduled_at=refresh_time,
            max_retries=flow.max_retries,
        )

        self.refresh_jobs[token_id] = job

    async def _refresh_loop(self):
        """Token refresh loop."""
        while self._running:
            try:
                await self._process_refresh_jobs()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but continue
                pass

    async def _process_refresh_jobs(self):
        """Process pending refresh jobs."""
        datetime.utcnow()
        due_jobs = [
            job for job in self.refresh_jobs.values()
            if job.is_due and job.status == "pending"
        ]

        for job in due_jobs:
            await self._execute_refresh_job(job)

    async def _execute_refresh_job(self, job: TokenRefreshJob):
        """Execute refresh job.

        Args:
            job: Refresh job
        """
        try:
            # Find flow for this token
            flow = await self._find_flow_for_token(job.token_id)
            if not flow:
                job.status = "failed"
                job.error_message = "Flow not found"
                return

            # Refresh token
            refreshed_token = await self.refresh_token(flow)
            if refreshed_token:
                job.status = "completed"
                job.retry_count = 0

                # Schedule next refresh
                if refreshed_token.expires_at:
                    await self._schedule_refresh(
                        job.token_id,
                        flow,
                        refreshed_token.expires_at,
                    )
            else:
                await self._handle_refresh_failure(job)

        except Exception as e:
            await self._handle_refresh_failure(job, str(e))

    async def _handle_refresh_failure(self, job: TokenRefreshJob, error: str = "Unknown error"):
        """Handle refresh failure.

        Args:
            job: Refresh job
            error: Error message
        """
        job.retry_count += 1
        job.error_message = error

        if job.can_retry:
            # Retry with exponential backoff
            delay = 2 ** job.retry_count * 60  # 2, 4, 8 minutes
            job.scheduled_at = datetime.utcnow() + timedelta(seconds=delay)
            job.status = "pending"
        else:
            job.status = "failed"

    async def _find_flow_for_token(self, token_id: UUID) -> OAuthFlow | None:
        """Find flow for token ID.

        Args:
            token_id: Token ID

        Returns:
            OAuth flow if found
        """
        # This is a simplified implementation
        # In a real system, you'd maintain a mapping between token IDs and flows
        return None

    def get_refresh_status(self) -> dict[str, int]:
        """Get refresh job status.

        Returns:
            Dictionary of job counts by status
        """
        status_counts = {}
        for job in self.refresh_jobs.values():
            status = job.status
            status_counts[status] = status_counts.get(status, 0) + 1

        return status_counts


class TokenRefreshScheduler:
    """Token refresh scheduler."""

    def __init__(self, token_manager: TokenManager):
        """Initialize scheduler.

        Args:
            token_manager: Token manager instance
        """
        self.token_manager = token_manager
        self._scheduler_task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        """Start scheduler."""
        if self._running:
            return

        self._running = True
        await self.token_manager.start()

    async def stop(self):
        """Stop scheduler."""
        self._running = False
        await self.token_manager.stop()

    async def schedule_token_refresh(self, flow: OAuthFlow, token: OAuthToken):
        """Schedule token refresh.

        Args:
            flow: OAuth flow configuration
            token: OAuth token
        """
        if flow.auto_refresh and token.can_refresh:
            await self.token_manager._schedule_refresh(
                token.id,
                flow,
                token.expires_at,
            )

    def get_scheduler_status(self) -> dict[str, any]:
        """Get scheduler status.

        Returns:
            Scheduler status information
        """
        return {
            "running": self._running,
            "refresh_jobs": self.token_manager.get_refresh_status(),
            "total_jobs": len(self.token_manager.refresh_jobs),
        }


__all__ = ["TokenManager", "TokenRefreshScheduler"]
