"""
OAuth integration and automation flows for credential management.
"""

from .automation import AutomationEngine, AutomationRule
from .flows import OAuthFlow, OAuthFlowManager, OAuthProvider
from .providers import (
    GenericOAuthProvider,
    GitHubOAuthProvider,
    GoogleOAuthProvider,
    MicrosoftOAuthProvider,
    OpenAIOAuthProvider,
)
from .token_manager import TokenManager, TokenRefreshScheduler

__all__ = [
    "AutomationEngine",
    "AutomationRule",
    "GenericOAuthProvider",
    "GitHubOAuthProvider",
    "GoogleOAuthProvider",
    "MicrosoftOAuthProvider",
    "OAuthFlow",
    "OAuthFlowManager",
    "OAuthProvider",
    "OpenAIOAuthProvider",
    "TokenManager",
    "TokenRefreshScheduler",
]
