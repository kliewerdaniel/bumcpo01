"""
Model Context Protocol (MCP) client for Browser Automation for Research.

This module implements the Model Context Protocol for standardized communication
with external knowledge sources.
"""
import logging
import json
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Union
import aiohttp
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class McpClient:
    """
    Client for the Model Context Protocol (MCP) for knowledge source integration.
    
    This class provides a standardized interface for connecting to and querying
    external knowledge sources using the MCP protocol.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the MCP client.
        
        Args:
            base_url: Base URL for the MCP server (if None, uses local implementation)
            api_key: API key for authentication (if required)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
        self.contexts = {}  # Registered context schemas
        
        # If no base_url, we're using local implementation
        self.is_remote = base_url is not None
    
    async def initialize(self):
        """Initialize the client session."""
        if self.is_remote and not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
                }
            )
            # Fetch available contexts
            await self.list_contexts()
    
    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def list_contexts(self) -> List[Dict[str, Any]]:
        """
        List available knowledge contexts.
        
        Returns:
            List of context information dictionaries
        """
        if self.is_remote:
            return await self._remote_list_contexts()
        else:
            return self._local_list_contexts()
    
    async def _remote_list_contexts(self) -> List[Dict[str, Any]]:
        """Query remote MCP server for available contexts."""
        if not self.session:
            await self.initialize()
        
        try:
            async with self.session.get(urljoin(self.base_url, "contexts")) as response:
                if response.status == 200:
                    data = await response.json()
                    self.contexts = {ctx["name"]: ctx for ctx in data["contexts"]}
                    return data["contexts"]
                else:
                    error_text = await response.text()
                    logger.error(f"Error listing contexts: {response.status} - {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Error listing contexts: {e}")
            return []
    
    def _local_list_contexts(self) -> List[Dict[str, Any]]:
        """Return locally registered contexts."""
        return list(self.contexts.values())
    
    async def get_context_schema(self, context_name: str) -> Dict[str, Any]:
        """
        Get the schema for a specific context.
        
        Args:
            context_name: Name of the context
            
        Returns:
            Context schema
        """
        # Check if we already have this context's schema
        if context_name in self.contexts:
            return self.contexts[context_name]
        
        if self.is_remote:
            return await self._remote_get_context_schema(context_name)
        else:
            return self._local_get_context_schema(context_name)
    
    async def _remote_get_context_schema(self, context_name: str) -> Dict[str, Any]:
        """Query remote MCP server for context schema."""
        if not self.session:
            await self.initialize()
        
        try:
            url = urljoin(self.base_url, f"contexts/{context_name}")
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.contexts[context_name] = data
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Error getting context schema: {response.status} - {error_text}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting context schema: {e}")
            return {}
    
    def _local_get_context_schema(self, context_name: str) -> Dict[str, Any]:
        """Return locally registered context schema."""
        return self.contexts.get(context_name, {})
    
    async def query_context(self, 
                          context_name: str, 
                          parameters: Dict[str, Any],
                          max_results: int = 5) -> Dict[str, Any]:
        """
        Query a knowledge context with parameters.
        
        Args:
            context_name: Name of the context to query
            parameters: Query parameters
            max_results: Maximum number of results to return
            
        Returns:
            Query results
        """
        if self.is_remote:
            return await self._remote_query_context(context_name, parameters, max_results)
        else:
            return await self._local_query_context(context_name, parameters, max_results)
    
    async def _remote_query_context(self, 
                                  context_name: str, 
                                  parameters: Dict[str, Any],
                                  max_results: int) -> Dict[str, Any]:
        """Send query to remote MCP server."""
        if not self.session:
            await self.initialize()
        
        try:
            url = urljoin(self.base_url, f"query/{context_name}")
            payload = {
                "parameters": parameters,
                "max_results": max_results
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Error querying context: {response.status} - {error_text}")
                    return {"error": error_text}
        except Exception as e:
            logger.error(f"Error querying context: {e}")
            return {"error": str(e)}
    
    async def _local_query_context(self, 
                                 context_name: str, 
                                 parameters: Dict[str, Any],
                                 max_results: int) -> Dict[str, Any]:
        """Route query to local handler."""
        # Local handlers would be registered by knowledge sources
        # This is just a skeleton - actual implementation would be in source classes
        handler = self.contexts.get(context_name, {}).get("handler")
        if handler and callable(handler):
            try:
                return await handler(parameters, max_results)
            except Exception as e:
                logger.error(f"Error in local context handler: {e}")
                return {"error": str(e)}
        else:
            logger.error(f"No handler registered for context: {context_name}")
            return {"error": f"No handler registered for context: {context_name}"}
    
    def register_context(self, 
                       name: str, 
                       schema: Dict[str, Any],
                       handler=None) -> None:
        """
        Register a new knowledge context.
        
        Args:
            name: Context name
            schema: Context parameter schema
            handler: Function to handle queries to this context
        """
        self.contexts[name] = {
            "name": name,
            "schema": schema,
            "handler": handler
        }
        logger.info(f"Registered knowledge context: {name}")
