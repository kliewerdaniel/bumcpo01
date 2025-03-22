"""
arXiv knowledge source for Browser Automation for Research.

This module provides integration with arXiv as a knowledge source
for academic papers and research articles.
"""
import logging
import aiohttp
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Any
from datetime import datetime
import urllib.parse

from ..mcp_client import McpClient
from ..source_manager import KnowledgeSource

logger = logging.getLogger(__name__)


class ArxivSource(KnowledgeSource):
    """
    arXiv knowledge source using the arXiv API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the arXiv source.
        
        Args:
            config: Configuration dictionary for this source
        """
        super().__init__(config)
        self.api_url = config.get("api_url", "http://export.arxiv.org/api/query")
        self.user_agent = config.get("user_agent", "ResearchAssistant/1.0 (research project)")
        self.max_results_per_query = config.get("max_results_per_query", 10)
        self.session = None
        
        # ArXiv recommends no more than 1 request per 3 seconds
        self.request_delay = config.get("request_delay", 3)
        self.last_request_time = 0
    
    async def initialize(self, mcp_client: McpClient):
        """
        Initialize the arXiv source.
        
        Args:
            mcp_client: MCP client for registering contexts
        """
        logger.info("Initializing arXiv knowledge source")
        
        # Create session
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": self.user_agent}
        )
        
        # Register MCP context
        mcp_client.register_context(
            name="arxiv",
            schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for arXiv papers"
                    },
                    "category": {
                        "type": "string",
                        "description": "arXiv category (e.g., 'cs.AI', 'physics')",
                        "default": ""
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["relevance", "lastUpdatedDate", "submittedDate"],
                        "default": "relevance"
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
        category = parameters.get("category", "")
        sort_by = parameters.get("sort_by", "relevance")
        
        results = await self.query(
            query=query,
            max_results=max_results,
            category=category,
            sort_by=sort_by
        )
        
        return {"results": results}
    
    async def query(self, 
                   query: str, 
                   max_results: int = 3, 
                   category: str = "", 
                   sort_by: str = "relevance") -> List[Dict[str, Any]]:
        """
        Query arXiv for papers matching the query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            category: arXiv category (e.g., 'cs.AI', 'physics')
            sort_by: Sort order ("relevance", "lastUpdatedDate", or "submittedDate")
            
        Returns:
            List of paper information dictionaries
        """
        if not self.session:
            logger.warning("arXiv session not initialized")
            return []
        
        # Enforce result limit
        max_results = min(max_results, self.max_results_per_query)
        
        # Build the query
        search_query = query
        if category:
            search_query = f"cat:{category} AND {search_query}"
        
        # Convert sort parameter to arXiv format
        if sort_by == "lastUpdatedDate":
            sort_param = "lastUpdatedDate"
        elif sort_by == "submittedDate":
            sort_param = "submittedDate"
        else:
            sort_param = "relevance"
        
        # Build parameters
        params = {
            "search_query": search_query,
            "max_results": max_results,
            "sortBy": sort_param,
            "sortOrder": "descending"
        }
        
        try:
            # Make the request
            async with self.session.get(self.api_url, params=params) as response:
                if response.status == 200:
                    # Get the response content
                    content = await response.text()
                    
                    # Parse XML response
                    return self._parse_arxiv_response(content)
                else:
                    logger.error(f"arXiv API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error querying arXiv: {e}")
            return []
    
    def _parse_arxiv_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse XML response from arXiv API.
        
        Args:
            xml_content: XML response from arXiv
            
        Returns:
            List of parsed paper dictionaries
        """
        try:
            # Define namespaces
            namespaces = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom"
            }
            
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Extract papers
            papers = []
            for entry in root.findall(".//atom:entry", namespaces):
                paper = self._parse_entry(entry, namespaces)
                if paper:
                    papers.append(paper)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error parsing arXiv response: {e}")
            return []
    
    def _parse_entry(self, entry, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """
        Parse a single entry from arXiv response.
        
        Args:
            entry: XML entry element
            namespaces: XML namespaces
            
        Returns:
            Parsed paper dictionary
        """
        try:
            # Extract title
            title_elem = entry.find("atom:title", namespaces)
            title = title_elem.text.strip() if title_elem is not None else ""
            
            # Extract authors
            authors = []
            for author_elem in entry.findall("atom:author", namespaces):
                name_elem = author_elem.find("atom:name", namespaces)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())
            
            # Extract abstract
            summary_elem = entry.find("atom:summary", namespaces)
            abstract = summary_elem.text.strip() if summary_elem is not None else ""
            
            # Clean abstract (remove line breaks and extra whitespace)
            abstract = re.sub(r'\s+', ' ', abstract)
            
            # Extract publication info
            published_elem = entry.find("atom:published", namespaces)
            published = published_elem.text if published_elem is not None else ""
            
            # Parse publication date
            pub_date = None
            if published:
                try:
                    pub_date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                    published = pub_date.strftime("%Y-%m-%d")
                except Exception:
                    pass
            
            # Extract ID (convert from URL to arXiv ID)
            id_elem = entry.find("atom:id", namespaces)
            arxiv_id = ""
            if id_elem is not None and id_elem.text:
                # Extract ID from URL (e.g., http://arxiv.org/abs/1234.5678 -> 1234.5678)
                id_match = re.search(r'abs/([^/]+)$', id_elem.text)
                if id_match:
                    arxiv_id = id_match.group(1)
            
            # Extract PDF URL
            pdf_url = ""
            for link in entry.findall("atom:link", namespaces):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href", "")
                    break
            
            # Extract categories
            categories = []
            primary_category = entry.find("arxiv:primary_category", namespaces)
            if primary_category is not None:
                cat = primary_category.get("term")
                if cat:
                    categories.append(cat)
            
            for category in entry.findall("atom:category", namespaces):
                cat = category.get("term")
                if cat and cat not in categories:
                    categories.append(cat)
            
            # Extract DOI if available
            doi = ""
            for link in entry.findall("atom:link", namespaces):
                if link.get("title") == "doi":
                    doi_url = link.get("href", "")
                    # Extract DOI from URL
                    doi_match = re.search(r'doi.org/(.+)$', doi_url)
                    if doi_match:
                        doi = doi_match.group(1)
                    break
            
            return {
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "published": published,
                "arxiv_id": arxiv_id,
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": pdf_url,
                "categories": categories,
                "doi": doi,
                "source": "arxiv"
            }
            
        except Exception as e:
            logger.error(f"Error parsing arXiv entry: {e}")
            return {}
    
    async def close(self):
        """Close the arXiv session."""
        if self.session:
            await self.session.close()
            self.session = None
