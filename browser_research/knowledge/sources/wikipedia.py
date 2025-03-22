"""
Wikipedia knowledge source for Browser Automation for Research.

This module provides integration with Wikipedia as a knowledge source
for gathering information on general topics.
"""
import logging
import aiohttp
import json
from typing import Dict, List, Any

from ..mcp_client import McpClient
from ..source_manager import KnowledgeSource

logger = logging.getLogger(__name__)


class WikipediaSource(KnowledgeSource):
    """
    Wikipedia knowledge source using the MediaWiki API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Wikipedia source.
        
        Args:
            config: Configuration dictionary for this source
        """
        super().__init__(config)
        self.api_url = config.get("api_url", "https://en.wikipedia.org/w/api.php")
        self.user_agent = config.get("user_agent", "ResearchAssistant/1.0 (research project)")
        self.session = None
    
    async def initialize(self, mcp_client: McpClient):
        """
        Initialize the Wikipedia source.
        
        Args:
            mcp_client: MCP client for registering contexts
        """
        logger.info("Initializing Wikipedia knowledge source")
        
        # Create session
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": self.user_agent}
        )
        
        # Register MCP context
        mcp_client.register_context(
            name="wikipedia",
            schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for Wikipedia"
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code (e.g., 'en' for English)",
                        "default": "en"
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
        language = parameters.get("language", "en")
        
        # Adjust API URL based on language
        if language != "en":
            self.api_url = f"https://{language}.wikipedia.org/w/api.php"
        
        results = await self.query(query, max_results)
        return {"results": results}
    
    async def query(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Query Wikipedia for information on a topic.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of Wikipedia article information
        """
        if not self.session:
            logger.warning("Wikipedia session not initialized")
            return []
        
        # First, search for articles
        search_results = await self._search_wikipedia(query, max_results)
        
        # Then, get extracts for each article
        articles = []
        for result in search_results:
            article = await self._get_article_extract(result["title"])
            if article:
                articles.append(article)
        
        return articles
    
    async def _search_wikipedia(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Search Wikipedia for articles matching the query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search result dictionaries
        """
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": max_results,
            "srinfo": "suggestion",
            "srprop": "snippet|titlesnippet"
        }
        
        try:
            async with self.session.get(self.api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    search_results = data.get("query", {}).get("search", [])
                    
                    # Format results
                    results = []
                    for item in search_results:
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "pageid": item.get("pageid", 0)
                        })
                    
                    return results
                else:
                    logger.error(f"Wikipedia search error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
            return []
    
    async def _get_article_extract(self, title: str) -> Dict[str, Any]:
        """
        Get a summary extract of a Wikipedia article.
        
        Args:
            title: Article title
            
        Returns:
            Article information dictionary
        """
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts|info|categories|links",
            "exintro": 1,
            "explaintext": 1,
            "inprop": "url",
            "cllimit": 5,
            "pllimit": 5,
            "titles": title
        }
        
        try:
            async with self.session.get(self.api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    pages = data.get("query", {}).get("pages", {})
                    
                    # There should be only one page
                    if not pages:
                        return {}
                    
                    # Get the first (and only) page
                    page_id, page_data = next(iter(pages.items()))
                    
                    # Extract categories
                    categories = []
                    for category in page_data.get("categories", []):
                        if "title" in category:
                            # Remove "Category:" prefix
                            cat_title = category["title"]
                            if ":" in cat_title:
                                cat_title = cat_title.split(":", 1)[1]
                            categories.append(cat_title)
                    
                    # Extract links
                    links = []
                    for link in page_data.get("links", []):
                        if "title" in link:
                            links.append(link["title"])
                    
                    return {
                        "title": page_data.get("title", ""),
                        "pageid": page_id,
                        "content": page_data.get("extract", ""),
                        "url": page_data.get("canonicalurl", ""),
                        "categories": categories,
                        "links": links,
                        "source": "wikipedia"
                    }
                else:
                    logger.error(f"Wikipedia article error: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching Wikipedia article: {e}")
            return {}
    
    async def close(self):
        """Close the Wikipedia session."""
        if self.session:
            await self.session.close()
            self.session = None
