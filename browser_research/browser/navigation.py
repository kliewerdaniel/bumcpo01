"""
Navigation module for Browser Automation for Research.

This module provides specialized navigation functionality including
URL handling, robots.txt compliance, and ethical scraping practices.
"""
import logging
import asyncio
import urllib.parse
import urllib.robotparser
import time
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class RobotsParser:
    """
    Handles robots.txt parsing and compliance for ethical web scraping.
    """
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize the robots parser.
        
        Args:
            cache_ttl: Cache time-to-live in seconds
        """
        self.robot_parsers = {}  # Maps domain to RobotFileParser
        self.cache_ttl = cache_ttl  # Cache TTL in seconds
        self.cache_timestamps = {}  # Maps domain to timestamp
    
    async def can_fetch(self, url: str, user_agent: str) -> bool:
        """
        Check if the URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            user_agent: User agent to check against
            
        Returns:
            True if the URL can be fetched, False otherwise
        """
        try:
            # Parse URL to get domain
            parsed_url = urllib.parse.urlparse(url)
            if not parsed_url.netloc:
                logger.warning(f"Invalid URL: {url}")
                return True  # Allow by default for invalid URLs
            
            domain = parsed_url.netloc
            robots_url = f"{parsed_url.scheme}://{domain}/robots.txt"
            
            # Check if we have a cached parser that's still valid
            current_time = time.time()
            if domain in self.robot_parsers and current_time - self.cache_timestamps.get(domain, 0) < self.cache_ttl:
                # Use cached parser
                return self.robot_parsers[domain].can_fetch(user_agent, url)
            
            # Create a new parser
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            
            # Fetch robots.txt asynchronously
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(robots_url, timeout=10) as response:
                        if response.status == 200:
                            robots_txt = await response.text()
                            # Split by lines and feed to parser
                            rp.parse(robots_txt.splitlines())
                        else:
                            logger.warning(f"Could not fetch robots.txt for {domain}: {response.status}")
                            rp.disallow_all = False  # Allow all by default if robots.txt not available
            except Exception as e:
                logger.warning(f"Error fetching robots.txt for {domain}: {e}")
                rp.disallow_all = False  # Allow all by default if error
            
            # Cache the parser
            self.robot_parsers[domain] = rp
            self.cache_timestamps[domain] = current_time
            
            # Check if URL can be fetched
            return rp.can_fetch(user_agent, url)
            
        except Exception as e:
            logger.error(f"Error checking robots.txt for {url}: {e}")
            return True  # Allow by default in case of error
    
    def clear_cache(self):
        """Clear the robots.txt cache."""
        self.robot_parsers.clear()
        self.cache_timestamps.clear()


class RateLimiter:
    """
    Manages rate limiting for ethical web scraping.
    """
    
    def __init__(self, 
                requests_per_minute: int = 10,
                delay_between_requests: float = 1.0):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            delay_between_requests: Minimum delay between requests in seconds
        """
        self.requests_per_minute = requests_per_minute
        self.delay_between_requests = delay_between_requests
        
        # Domain-specific tracking
        self.domain_timestamps = {}  # Maps domain to list of request timestamps
        self.domain_locks = {}  # Maps domain to lock object
    
    async def acquire(self, url: str) -> None:
        """
        Acquire permission to make a request, waiting if necessary.
        
        Args:
            url: URL to request
        """
        # Extract domain from URL
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        
        # Ensure domain has a lock
        if domain not in self.domain_locks:
            self.domain_locks[domain] = asyncio.Lock()
        
        # Ensure domain has a timestamp list
        if domain not in self.domain_timestamps:
            self.domain_timestamps[domain] = []
        
        # Clean up old timestamps
        current_time = time.time()
        self.domain_timestamps[domain] = [
            ts for ts in self.domain_timestamps[domain]
            if current_time - ts < 60  # Keep timestamps less than 1 minute old
        ]
        
        # Acquire lock to prevent race conditions
        async with self.domain_locks[domain]:
            # Check if we need to wait due to rate limiting
            if len(self.domain_timestamps[domain]) >= self.requests_per_minute:
                # Calculate wait time to respect requests per minute
                oldest_timestamp = min(self.domain_timestamps[domain])
                wait_time = max(0, 60 - (current_time - oldest_timestamp))
                
                if wait_time > 0:
                    logger.info(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
                    await asyncio.sleep(wait_time)
            
            # Check if we need to wait to respect delay between requests
            if self.domain_timestamps[domain]:
                last_request = max(self.domain_timestamps[domain])
                time_since_last = current_time - last_request
                
                if time_since_last < self.delay_between_requests:
                    wait_time = self.delay_between_requests - time_since_last
                    
                    if wait_time > 0:
                        logger.debug(f"Respecting delay: waiting {wait_time:.2f}s for {domain}")
                        await asyncio.sleep(wait_time)
            
            # Record this request
            self.domain_timestamps[domain].append(time.time())


class NavigationManager:
    """
    Manages web navigation with ethical scraping practices.
    """
    
    def __init__(self, 
                user_agent: str,
                respect_robots_txt: bool = True,
                requests_per_minute: int = 10,
                delay_between_requests: float = 1.0):
        """
        Initialize the navigation manager.
        
        Args:
            user_agent: User agent to use for requests
            respect_robots_txt: Whether to respect robots.txt
            requests_per_minute: Maximum requests per minute
            delay_between_requests: Minimum delay between requests in seconds
        """
        self.user_agent = user_agent
        self.respect_robots_txt = respect_robots_txt
        
        # Initialize components
        self.robots_parser = RobotsParser()
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            delay_between_requests=delay_between_requests
        )
        
        # Site-specific crawl rules (might be expanded)
        self.site_rules = {
            "wikipedia.org": {
                "allowed_paths": ["/wiki/"],
                "disallowed_paths": ["/wiki/Special:", "/wiki/Talk:", "/wiki/User:"]
            }
        }
    
    async def can_navigate(self, url: str) -> bool:
        """
        Check if the URL can be navigated according to ethical rules.
        
        Args:
            url: URL to check
            
        Returns:
            True if the URL can be navigated, False otherwise
        """
        # Check if URL is valid
        try:
            parsed_url = urllib.parse.urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.warning(f"Invalid URL: {url}")
                return False
        except Exception:
            logger.warning(f"Invalid URL: {url}")
            return False
        
        # Check robots.txt if enabled
        if self.respect_robots_txt:
            can_fetch = await self.robots_parser.can_fetch(url, self.user_agent)
            if not can_fetch:
                logger.warning(f"robots.txt disallows: {url}")
                return False
        
        # Check site-specific rules
        domain = parsed_url.netloc
        for site_domain, rules in self.site_rules.items():
            if site_domain in domain:
                path = parsed_url.path
                
                # Check disallowed paths
                for disallowed in rules.get("disallowed_paths", []):
                    if path.startswith(disallowed):
                        logger.warning(f"Site rule disallows: {url}")
                        return False
                
                # Check allowed paths if specified
                allowed_paths = rules.get("allowed_paths", [])
                if allowed_paths:
                    if not any(path.startswith(allowed) for allowed in allowed_paths):
                        logger.warning(f"URL not in site's allowed paths: {url}")
                        return False
        
        return True
    
    async def prepare_navigation(self, url: str) -> bool:
        """
        Prepare to navigate to a URL (checking permissions and rate limiting).
        
        Args:
            url: URL to navigate to
            
        Returns:
            True if navigation is allowed, False otherwise
        """
        # Check if we can navigate to this URL
        can_navigate = await self.can_navigate(url)
        if not can_navigate:
            return False
        
        # Apply rate limiting
        await self.rate_limiter.acquire(url)
        
        return True
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize a URL for consistent handling.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        try:
            # Parse the URL
            parsed = urllib.parse.urlparse(url)
            
            # Ensure scheme is present
            if not parsed.scheme:
                url = f"https://{url}"
                parsed = urllib.parse.urlparse(url)
            
            # Normalize the path (remove duplicate slashes, etc.)
            path = re.sub(r'/+', '/', parsed.path)
            
            # Remove trailing slash from path if present (except if path is just "/")
            if path.endswith('/') and len(path) > 1:
                path = path[:-1]
            
            # Reconstruct the URL with normalized components
            normalized = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                path,
                parsed.params,
                parsed.query,
                ''  # Remove fragment
            ))
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Error normalizing URL {url}: {e}")
            return url
    
    def is_same_domain(self, url1: str, url2: str) -> bool:
        """
        Check if two URLs belong to the same domain.
        
        Args:
            url1: First URL
            url2: Second URL
            
        Returns:
            True if URLs belong to the same domain, False otherwise
        """
        try:
            domain1 = urllib.parse.urlparse(url1).netloc
            domain2 = urllib.parse.urlparse(url2).netloc
            
            return domain1 == domain2
            
        except Exception:
            return False
    
    def extract_domain(self, url: str) -> str:
        """
        Extract the domain from a URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain of the URL
        """
        try:
            return urllib.parse.urlparse(url).netloc
        except Exception:
            return ""
    
    def is_allowed_filetype(self, url: str, allowed_extensions: List[str] = None) -> bool:
        """
        Check if a URL points to an allowed file type.
        
        Args:
            url: URL to check
            allowed_extensions: List of allowed file extensions (without dot)
            
        Returns:
            True if URL has an allowed extension, False otherwise
        """
        if not allowed_extensions:
            # Default allowed extensions for research
            allowed_extensions = [
                # Web pages
                'html', 'htm', 'xhtml', 'php', 'asp', 'aspx', 'jsp',
                # Documents
                'pdf', 'doc', 'docx', 'txt', 'rtf', 
                # Data
                'json', 'xml',
                # No extension (could be a directory or web page)
                ''
            ]
        
        try:
            # Get the path from the URL
            path = urllib.parse.urlparse(url).path
            
            # Extract extension (if any)
            extension = path.split('.')[-1].lower() if '.' in path else ''
            
            return extension in allowed_extensions
            
        except Exception:
            return True  # Allow by default in case of error
