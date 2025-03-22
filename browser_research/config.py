"""
Configuration module for Browser Automation for Research.

This module handles loading, validating, and providing access to application 
configuration from YAML files, environment variables, or defaults.
"""
import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "llm": {
        "provider": "ollama",
        "model": "llama3.2",
        "api_base": "http://localhost:11434/api",
        "temperature": 0.7,
        "max_tokens": 4000
    },
    "browser": {
        "headless": True,
        "user_agent": "ResearchAssistant/1.0 (+https://example.com/bot; for research purposes)",
        "timeout": 30,
        "screenshots_dir": "screenshots",
        "respect_robots_txt": True,
        "rate_limit": {
            "requests_per_minute": 10,
            "delay_between_requests": 6
        }
    },
    "knowledge": {
        "sources": ["web_search", "wikipedia", "arxiv"],
        "cache": {
            "enabled": True,
            "ttl": 3600,  # Cache time-to-live in seconds
            "max_size": 1000  # Maximum number of items in cache
        }
    },
    "web": {
        "host": "127.0.0.1",
        "port": 8080,
        "debug": False
    }
}


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing the merged configuration
    """
    config = DEFAULT_CONFIG.copy()
    
    # Try to load configuration from file
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    # Merge configurations
                    deep_merge(config, file_config)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            logger.info("Using default configuration")
    else:
        logger.warning(f"Configuration file {config_path} not found. Using default configuration.")
    
    # Override with environment variables
    env_overrides = {
        "LLM_API_BASE": ("llm", "api_base"),
        "LLM_MODEL": ("llm", "model"),
        "BROWSER_HEADLESS": ("browser", "headless", bool),
        "KNOWLEDGE_CACHE_ENABLED": ("knowledge", "cache", "enabled", bool),
        "WEB_PORT": ("web", "port", int)
    }
    
    for env_var, path in env_overrides.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            
            # Convert value if needed
            if len(path) > 2 and path[-1] == bool:
                value = value.lower() in ("true", "yes", "1", "y")
                path = path[:-1]  # Remove the type conversion hint
            elif len(path) > 2 and path[-1] == int:
                value = int(value)
                path = path[:-1]  # Remove the type conversion hint
            
            # Navigate to the right level in the config dict
            cfg = config
            for key in path[:-1]:
                cfg = cfg[key]
            
            # Set the value
            cfg[path[-1]] = value
            logger.debug(f"Override configuration with environment variable {env_var}")
    
    return config


def deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> None:
    """
    Recursively merge two dictionaries, modifying base in-place.
    
    Args:
        base: Base dictionary to update
        update: Dictionary with values to merge into base
    """
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            # Recursively update dictionaries
            deep_merge(base[key], value)
        else:
            # Replace or add values
            base[key] = value
