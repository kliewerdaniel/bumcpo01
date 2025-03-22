"""
Web Search knowledge source for Browser Automation for Research.

This module provides integration with web search engines as a knowledge source
for general information gathering.
"""
import logging
import aiohttp
import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from urllib.parse import quote

from ..mcp_client import McpClient
from ..source_manager import KnowledgeSource

logger = logging.getLogger(__name__)


class Web_searchSource(KnowledgeSource):
    """
    Web search knowledge source using available search engine APIs.
    
    This class provides a unified interface to search engines,
    with placeholders for API integration. In a real implementation,
    it would connect to a specific search API with credentials.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the web search source.
        
        Args:
            config: Configuration dictionary for this source
        """
        super().__init__(config)
        
        # Search engine configuration
        self.search_engine = config.get("engine", "google")
        self.api_key = config.get("api_key", "")
        self.search_id = config.get("search_id", "")
        
        # Configure API URLs based on search engine
        self.api_urls = {
            "google": "https://www.googleapis.com/customsearch/v1",
            "bing": "https://api.bing.microsoft.com/v7.0/search"
        }
        
        self.api_url = self.api_urls.get(self.search_engine, self.api_urls["google"])
        self.user_agent = config.get("user_agent", "ResearchAssistant/1.0 (research project)")
        self.session = None
        
        # Rate limiting
        self.requests_per_minute = config.get("requests_per_minute", 10)
        self.last_request_time = 0
    
    async def initialize(self, mcp_client: McpClient):
        """
        Initialize the web search source.
        
        Args:
            mcp_client: MCP client for registering contexts
        """
        logger.info("Initializing web search knowledge source")
        
        # Create session
        headers = {"User-Agent": self.user_agent}
        
        # Add API key header if available
        if self.api_key:
            if self.search_engine == "google":
                # Google uses query param, not header
                pass
            elif self.search_engine == "bing":
                headers["Ocp-Apim-Subscription-Key"] = self.api_key
        
        self.session = aiohttp.ClientSession(headers=headers)
        
        # Register MCP context
        mcp_client.register_context(
            name="web_search",
            schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for web search"
                    },
                    "site": {
                        "type": "string",
                        "description": "Limit search to a specific site (e.g., 'site:example.com')",
                        "default": ""
                    },
                    "safe_search": {
                        "type": "boolean",
                        "description": "Whether to enable safe search",
                        "default": True
                    }
                },
                "required": ["query"]
            },
            handler=self._handle_mcp_query
        )
    
    async def _handle_mcp_query(self, parameters: Dict[str, Any], max_results: int) -> Dict[str, Any]:
        """
        Handle an MCP query.
        
        Args:
            parameters: Query parameters
            max_results: Maximum number of results to return
            
        Returns:
            Query results
        """
        query = parameters.get("query", "")
        site = parameters.get("site", "")
        safe_search = parameters.get("safe_search", True)
        
        # Add site restriction if specified
        if site:
            if not query.endswith(" "):
                query += " "
            query += f"site:{site}"
        
        results = await self.query(
            query=query,
            max_results=max_results,
            safe_search=safe_search
        )
        
        return {"results": results}
    
    async def query(self, 
                   query: str, 
                   max_results: int = 5,
                   safe_search: bool = True) -> List[Dict[str, Any]]:
        """
        Query web search for information.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            safe_search: Whether to enable safe search
            
        Returns:
            List of search result dictionaries
        """
        if not self.session:
            logger.warning("Web search session not initialized")
            return []
        
        # Respect rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # If we need to wait to respect rate limits
        if time_since_last < (60 / self.requests_per_minute):
            wait_time = (60 / self.requests_per_minute) - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for web search")
            await asyncio.sleep(wait_time)
        
        # If API key is provided, use the actual search API
        if self.api_key:
            if self.search_engine == "google":
                results = await self._query_google_api(query, max_results, safe_search)
            elif self.search_engine == "bing":
                results = await self._query_bing_api(query, max_results, safe_search)
            else:
                logger.warning(f"Unsupported search engine: {self.search_engine}")
                results = []
        else:
            # If no API key, use a simulated response for demonstration
            logger.warning("No API key provided, using simulated search results")
            results = self._simulate_search_results(query, max_results)
        
        # Update last request time
        self.last_request_time = time.time()
        
        return results
    
    async def _query_google_api(self, 
                              query: str, 
                              max_results: int,
                              safe_search: bool) -> List[Dict[str, Any]]:
        """
        Query Google Custom Search API.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            safe_search: Whether to enable safe search
            
        Returns:
            List of search result dictionaries
        """
        try:
            params = {
                "key": self.api_key,
                "cx": self.search_id,
                "q": query,
                "num": min(10, max_results)  # API max is 10 per request
            }
            
            if safe_search:
                params["safe"] = "active"
            
            async with self.session.get(self.api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    
                    results = []
                    for item in items[:max_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "google"
                        })
                    
                    return results
                else:
                    error_text = await response.text()
                    logger.error(f"Google search API error: {response.status} - {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Error querying Google search API: {e}")
            return []
    
    async def _query_bing_api(self, 
                            query: str, 
                            max_results: int,
                            safe_search: bool) -> List[Dict[str, Any]]:
        """
        Query Bing Search API.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            safe_search: Whether to enable safe search
            
        Returns:
            List of search result dictionaries
        """
        try:
            params = {
                "q": query,
                "count": max_results
            }
            
            if safe_search:
                params["safeSearch"] = "Strict"
            
            async with self.session.get(self.api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    web_pages = data.get("webPages", {}).get("value", [])
                    
                    results = []
                    for page in web_pages[:max_results]:
                        results.append({
                            "title": page.get("name", ""),
                            "url": page.get("url", ""),
                            "snippet": page.get("snippet", ""),
                            "source": "bing"
                        })
                    
                    return results
                else:
                    error_text = await response.text()
                    logger.error(f"Bing search API error: {response.status} - {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Error querying Bing search API: {e}")
            return []
    
    def _simulate_search_results(self, 
                              query: str, 
                              max_results: int) -> List[Dict[str, Any]]:
        """
        Simulate search results for demonstration.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of simulated search result dictionaries
        """
        # This would be replaced with actual API calls in a real implementation
        # Just providing placeholder results for demonstration
        
        # Some basic simulated results
        results = [
            {
                "title": f"About {query} - Overview and Information",
                "url": f"https://example.com/about-{quote(query)}",
                "snippet": f"Comprehensive information about {query}. Learn about the history, applications, and future developments in this field.",
                "source": "simulated"
            },
            {
                "title": f"{query} - Latest Research and Developments",
                "url": f"https://research-journal.example/articles/{quote(query)}",
                "snippet": f"The latest research findings related to {query}. Recent studies have shown significant advancements in understanding and applying these concepts.",
                "source": "simulated"
            },
            {
                "title": f"Understanding {query} - A Complete Guide",
                "url": f"https://guide.example/topics/{quote(query)}",
                "snippet": f"A complete guide to understanding {query}. This comprehensive resource covers all aspects from basic principles to advanced applications.",
                "source": "simulated"
            },
            {
                "title": f"{query} in Modern Applications",
                "url": f"https://tech-review.example/modern-{quote(query)}",
                "snippet": f"How {query} is being used in modern applications across various industries. Case studies and examples of successful implementations.",
                "source": "simulated"
            },
            {
                "title": f"The Future of {query} - Trends and Predictions",
                "url": f"https://future-trends.example/topics/{quote(query)}",
                "snippet": f"Expert predictions about the future developments in {query}. Analysis of current trends and their implications for the next decade.",
                "source": "simulated"
            }
        ]
        
        # Return limited number of results
        return results[:max_results]
    
    async def close(self):
        """Close the web search session."""
        if self.session:
            await self.session.close()
            self.session = None
