"""Ecosystem-specific scanning adapters"""

from .base import EcosystemAdapter
from .npm_adapter import NpmAdapter

__all__ = [
    'EcosystemAdapter',
    'NpmAdapter',
]

# Registry of available adapters
ADAPTER_REGISTRY = {
    'npm': NpmAdapter,
    # 'maven': JavaAdapter,  # Coming soon
    # 'pip': PythonAdapter,   # Coming soon
    # 'gem': RubyAdapter,     # Coming soon
}


def get_adapter_class(ecosystem: str):
    """
    Get adapter class for a specific ecosystem

    Args:
        ecosystem: Ecosystem name (npm, maven, pip, gem, etc.)

    Returns:
        Adapter class or None if not found
    """
    return ADAPTER_REGISTRY.get(ecosystem.lower())


def get_available_ecosystems():
    """
    Get list of ecosystems with implemented adapters

    Returns:
        List of ecosystem names
    """
    return list(ADAPTER_REGISTRY.keys())
