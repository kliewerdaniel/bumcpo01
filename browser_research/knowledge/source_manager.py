"""
Knowledge Source Manager for Browser Automation for Research.

This module manages connections to various knowledge sources and provides
a unified interface for querying them.
"""
import logging
import asyncio
import importlib
from typing import Dict, List, Any, Optional

from .mcp_client import McpClient

logger = logging.getLogger(__name__)


class KnowledgeSourceManager:
    """
    Manages connections to external knowledge sources.
    
    This class provides a unified interface to diverse knowledge sources,
    handles source-specific parameters, and implements appropriate caching strategies.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the knowledge source manager.
        
        Args:
            config: Configuration dictionary for knowledge sources
        """
        self.config = config
        self.mcp_client = McpClient()
        self.sources = {}  # Maps source name to source instance
        self.cache = {}  # Simple in-memory cache
        
        # Configure enabled sources
        self.enabled_sources = config.get("sources", ["web_search", "wikipedia", "arxiv"])
    
    async def initialize(self):
        """Initialize knowledge sources."""
        logger.info("Initializing knowledge sources")
        
        # Initialize MCP client
        await self.mcp_client.initialize()
        
        # Load and initialize sources
        for source_name in self.enabled_sources:
            try:
                # Import source module
                module_name = f".sources.{source_name}"
                source_module = importlib.import_module(module_name, package="knowledge")
                
                # Get source class
                source_class = getattr(source_module, f"{source_name.capitalize()}Source")
                
                # Create source instance
                source_config = self.config.get(source_name, {})
                source = source_class(source_config)
                
                # Initialize source
                await source.initialize(self.mcp_client)
                
                # Register source
                self.sources[source_name] = source
                logger.info(f"Initialized knowledge source: {source_name}")
                
            except (ImportError, AttributeError, Exception) as e:
                logger.error(f"Error initializing knowledge source {source_name}: {e}")
    
    async def query(self, source: str, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Query a specific knowledge source.
        
        Args:
            source: Name of the knowledge source
            query: Query string
            max_results: Maximum number of results to return
            
        Returns:
            List of result dictionaries
        """
        # Check if source is enabled
        if source not in self.enabled_sources:
            logger.warning(f"Knowledge source not enabled: {source}")
            return []
        
        # Check if source is initialized
        if source not in self.sources:
            logger.warning(f"Knowledge source not initialized: {source}")
            return []
        
        # Check cache if enabled
        if self.config.get("cache", {}).get("enabled", False):
            cache_key = f"{source}:{query}:{max_results}"
            if cache_key in self.cache:
                logger.info(f"Using cached results for {source} query: {query}")
                return self.cache[cache_key]
        
        # Query the source
        logger.info(f"Querying knowledge source {source} for: {query}")
        try:
            results = await self.sources[source].query(query, max_results)
            
            # Cache results if enabled
            if self.config.get("cache", {}).get("enabled", False):
                cache_key = f"{source}:{query}:{max_results}"
                self.cache[cache_key] = results
                
                # Prune cache if needed
                self._prune_cache()
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying knowledge source {source}: {e}")
            return []
    
    def _prune_cache(self):
        """Prune cache if it exceeds the configured maximum size."""
        max_size = self.config.get("cache", {}).get("max_size", 1000)
        
        if len(self.cache) > max_size:
            # Simple strategy: remove oldest entries
            # In a real implementation, we might use LRU or other strategies
            items_to_remove = len(self.cache) - max_size
            keys_to_remove = list(self.cache.keys())[:items_to_remove]
            
            for key in keys_to_remove:
                del self.cache[key]
    
    async def close(self):
        """Close connections to knowledge sources."""
        logger.info("Closing knowledge sources")
        
        # Close each source
        for source_name, source in self.sources.items():
            try:
                await source.close()
                logger.info(f"Closed knowledge source: {source_name}")
            except Exception as e:
                logger.error(f"Error closing knowledge source {source_name}: {e}")
        
        # Close MCP client
        await self.mcp_client.close()


class KnowledgeSource:
    """
    Base class for knowledge sources.
    
    This abstract class defines the interface that all knowledge sources must implement.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the knowledge source.
        
        Args:
            config: Configuration dictionary for this source
        """
        self.config = config
        self.name = self.__class__.__name__.lower().replace("source", "")
    
    async def initialize(self, mcp_client: McpClient):
        """
        Initialize the knowledge source.
        
        Args:
            mcp_client: MCP client for registering contexts
        """
        pass
    
    async def query(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Query the knowledge source.
        
        Args:
            query: Query string
            max_results: Maximum number of results to return
            
        Returns:
            List of result dictionaries
        """
        raise NotImplementedError("Knowledge sources must implement query method")
    
    async def close(self):
        """Close the knowledge source."""
        pass
