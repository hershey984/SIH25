"""
Configuration management
"""
from .settings import get_settings, Settings

settings = get_settings()

__all__ = ["settings", "Settings", "get_settings"]