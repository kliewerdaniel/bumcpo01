"""
Browser Session module for Browser Automation for Research.

This module provides browser automation capabilities for web browsing,
information gathering, and content extraction.
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
import urllib.parse
import os
import time

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright, Browser, Page, ElementHandle
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright not available. Install with: pip install playwright")
    logger.warning("Then install browsers with: playwright install")
    PLAYWRIGHT_AVAILABLE = False


class BrowserSession:
    """
    Manages browser sessions for automated web research.
    
    This class handles browser initialization, navigation, content extraction,
    and search operations using Playwright for browser automation.
    """
    
    def __init__(self, 
                 headless: bool = True, 
                 user_agent: Optional[str] = None, 
                 timeout: int = 30,
                 screenshots_dir: str = "screenshots"):
        """
        Initialize the browser session.
        
        Args:
            headless: Whether to run browser in headless mode
            user_agent: Custom user agent string (if None, uses default)
            timeout: Default timeout for operations in seconds
            screenshots_dir: Directory to save screenshots
        """
        self.headless = headless
        self.user_agent = user_agent or "ResearchAssistant/1.0 (+https://example.com/bot; for research)"
        self.timeout = timeout * 1000  # Convert to ms
        self.screenshots_dir = screenshots_dir
        
        # Will be set during initialization
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None
        
        # History tracking
        self.history = []
    
    async def initialize(self):
        """Initialize the browser session."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required for browser automation")
        
        logger.info("Initializing browser session")
        
        # Create screenshots directory if it doesn't exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Launch playwright and browser
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        
        # Create a browser context with custom settings
        self.context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1280, "height": 800},
            java_script_enabled=True
        )
        
        # Set default timeout
        self.context.set_default_timeout(self.timeout)
        
        # Create a new page
        self.page = await self.context.new_page()
        
        # Set up event listeners
        self.page.on("console", lambda msg: logger.debug(f"CONSOLE: {msg.text}"))
        self.page.on("pageerror", lambda err: logger.error(f"PAGE ERROR: {err}"))
        
        logger.info("Browser session initialized")
        
        return self
    
    async def navigate(self, url: str) -> bool:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            True if navigation succeeded, False otherwise
        """
        if not self.page:
            await self.initialize()
        
        try:
            logger.info(f"Navigating to: {url}")
            
            # Record in history
            self.history.append({
                "action": "navigate",
                "url": url,
                "timestamp": time.time()
            })
            
            # Navigate to the page
            response = await self.page.goto(url, wait_until="domcontentloaded")
            
            if not response:
                logger.warning(f"No response received when navigating to {url}")
                return False
            
            # Check response status
            if not response.ok:
                logger.warning(f"Navigation to {url} failed with status {response.status}")
                return False
            
            # Wait for page to be fully loaded
            await self.wait_for_page_load()
            
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return False
    
    async def wait_for_page_load(self):
        """Wait for the page to be fully loaded."""
        try:
            # Wait for network to be idle
            await self.page.wait_for_load_state("networkidle", timeout=self.timeout)
            
            # Additional waiting for dynamic content
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"Timeout waiting for page to load completely: {e}")
    
    async def search(self, query: str, search_engine: str = "google", max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a search using the specified search engine and return results.
        
        Args:
            query: Search query
            search_engine: Search engine to use (google, bing, duckduckgo)
            max_results: Maximum number of results to return
            
        Returns:
            List of search result dictionaries
        """
        # Format the search URL based on the search engine
        encoded_query = urllib.parse.quote(query)
        
        search_urls = {
            "google": f"https://www.google.com/search?q={encoded_query}",
            "bing": f"https://www.bing.com/search?q={encoded_query}",
            "duckduckgo": f"https://duckduckgo.com/?q={encoded_query}"
        }
        
        if search_engine not in search_urls:
            logger.warning(f"Unsupported search engine: {search_engine}. Falling back to Google.")
            search_engine = "google"
        
        url = search_urls[search_engine]
        
        # Navigate to the search page
        success = await self.navigate(url)
        if not success:
            logger.error(f"Failed to navigate to search page: {url}")
            return []
        
        # Take a screenshot of the search page
        await self.take_screenshot(f"search_{search_engine}_{encoded_query[:20]}")
        
        # Extract search results
        logger.info(f"Extracting search results from {search_engine}")
        
        try:
            results = []
            
            if search_engine == "google":
                results = await self._extract_google_results(max_results)
            elif search_engine == "bing":
                results = await self._extract_bing_results(max_results)
            elif search_engine == "duckduckgo":
                results = await self._extract_duckduckgo_results(max_results)
            
            logger.info(f"Extracted {len(results)} search results")
            return results
            
        except Exception as e:
            logger.error(f"Error extracting search results: {e}")
            return []
    
    async def _extract_google_results(self, max_results: int) -> List[Dict[str, Any]]:
        """Extract search results from Google."""
        results = []
        
        # Find result containers
        # Google search results are typically in <div class="g"> elements
        selectors = [
            "div.g",  # Main result selector
            "div.tF2Cxc"  # Alternative result container
        ]
        
        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            if elements and len(elements) > 0:
                break
        
        if not elements:
            logger.warning("No search result elements found on Google")
            return results
        
        # Process each result
        for element in elements[:max_results]:
            try:
                # Extract title
                title_element = await element.query_selector("h3")
                title = await title_element.inner_text() if title_element else "No title"
                
                # Extract URL
                link_element = await element.query_selector("a")
                url = await link_element.get_attribute("href") if link_element else None
                
                # Skip if no valid URL
                if not url or not url.startswith("http"):
                    continue
                
                # Extract snippet
                snippet_selectors = ["div.VwiC3b", "span.aCOpRe"]
                snippet = ""
                for snippet_selector in snippet_selectors:
                    snippet_element = await element.query_selector(snippet_selector)
                    if snippet_element:
                        snippet = await snippet_element.inner_text()
                        break
                
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "source": "google"
                })
                
                if len(results) >= max_results:
                    break
                    
            except Exception as e:
                logger.error(f"Error processing Google search result: {e}")
        
        return results
    
    async def _extract_bing_results(self, max_results: int) -> List[Dict[str, Any]]:
        """Extract search results from Bing."""
        results = []
        
        # Find result containers (Bing search results are in <li class="b_algo"> elements)
        elements = await self.page.query_selector_all("li.b_algo")
        
        if not elements:
            logger.warning("No search result elements found on Bing")
            return results
        
        # Process each result
        for element in elements[:max_results]:
            try:
                # Extract title
                title_element = await element.query_selector("h2")
                title = await title_element.inner_text() if title_element else "No title"
                
                # Extract URL
                link_element = await element.query_selector("a")
                url = await link_element.get_attribute("href") if link_element else None
                
                # Skip if no valid URL
                if not url or not url.startswith("http"):
                    continue
                
                # Extract snippet
                snippet_element = await element.query_selector("p")
                snippet = await snippet_element.inner_text() if snippet_element else ""
                
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "source": "bing"
                })
                
                if len(results) >= max_results:
                    break
                    
            except Exception as e:
                logger.error(f"Error processing Bing search result: {e}")
        
        return results
    
    async def _extract_duckduckgo_results(self, max_results: int) -> List[Dict[str, Any]]:
        """Extract search results from DuckDuckGo."""
        results = []
        
        # Find result containers
        elements = await self.page.query_selector_all("article.result")
        
        if not elements:
            logger.warning("No search result elements found on DuckDuckGo")
            return results
        
        # Process each result
        for element in elements[:max_results]:
            try:
                # Extract title
                title_element = await element.query_selector("h2")
                title = await title_element.inner_text() if title_element else "No title"
                
                # Extract URL
                link_element = await element.query_selector("a.result__a")
                url = await link_element.get_attribute("href") if link_element else None
                
                # Skip if no valid URL
                if not url or not url.startswith("http"):
                    continue
                
                # Extract snippet
                snippet_element = await element.query_selector(".result__snippet")
                snippet = await snippet_element.inner_text() if snippet_element else ""
                
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "source": "duckduckgo"
                })
                
                if len(results) >= max_results:
                    break
                    
            except Exception as e:
                logger.error(f"Error processing DuckDuckGo search result: {e}")
        
        return results
    
    async def visit_page(self, url: str) -> Dict[str, Any]:
        """
        Visit a page and extract its content.
        
        Args:
            url: The URL to visit
            
        Returns:
            Dictionary with page title, content, and metadata
        """
        success = await self.navigate(url)
        if not success:
            return {"error": f"Failed to navigate to {url}"}
        
        # Take a screenshot
        await self.take_screenshot(f"page_{urllib.parse.quote(url, safe='')[:30]}")
        
        # Get page title
        title = await self.get_page_title()
        
        # Extract main content
        content = await self.extract_main_content()
        
        # Extract metadata
        metadata = await self.extract_metadata()
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "metadata": metadata,
            "timestamp": time.time()
        }
    
    async def get_page_title(self) -> str:
        """Get the title of the current page."""
        try:
            return await self.page.title()
        except Exception as e:
            logger.error(f"Error getting page title: {e}")
            return "Unknown Title"
    
    async def extract_main_content(self) -> str:
        """
        Extract the main content from the current page.
        
        Returns:
            Extracted text content
        """
        try:
            # Try common content selectors
            content_selectors = [
                "article", "main", "#content", ".content", 
                "[role='main']", ".post-content", ".entry-content"
            ]
            
            for selector in content_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    content = await element.inner_text()
                    if content and len(content) > 200:  # Content seems substantial
                        return content
            
            # Fallback: Extract content using text density analysis
            # This is a simplified approach - actual implementation would be more sophisticated
            content = await self.page.evaluate('''() => {
                // JavaScript to extract main content based on text density
                // This is a basic implementation - real world would be more complex
                const paragraphs = Array.from(document.querySelectorAll('p'));
                
                // Filter paragraphs with substantial text
                const contentParagraphs = paragraphs
                    .filter(p => p.textContent.length > 50)
                    .map(p => p.textContent.trim())
                    .join('\\n\\n');
                
                return contentParagraphs.length > 200 ? contentParagraphs : document.body.innerText;
            }''')
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting main content: {e}")
            return await self.page.inner_text("body") or "Failed to extract content"
    
    async def extract_metadata(self) -> Dict[str, str]:
        """
        Extract metadata from the current page.
        
        Returns:
            Dictionary of metadata
        """
        try:
            return await self.page.evaluate('''() => {
                const metadata = {};
                
                // Extract meta tags
                document.querySelectorAll('meta').forEach(meta => {
                    const name = meta.getAttribute('name') || meta.getAttribute('property');
                    const content = meta.getAttribute('content');
                    if (name && content) {
                        metadata[name] = content;
                    }
                });
                
                // Author information
                const authorSelectors = [
                    'meta[name="author"]',
                    '[rel="author"]',
                    '.author',
                    '.byline'
                ];
                
                for (const selector of authorSelectors) {
                    const authorElement = document.querySelector(selector);
                    if (authorElement) {
                        const author = authorElement.getAttribute('content') || authorElement.textContent;
                        if (author) {
                            metadata['author'] = author.trim();
                            break;
                        }
                    }
                }
                
                // Publication date
                const dateSelectors = [
                    'meta[name="date"]',
                    'time',
                    '.date',
                    '.published'
                ];
                
                for (const selector of dateSelectors) {
                    const dateElement = document.querySelector(selector);
                    if (dateElement) {
                        const date = dateElement.getAttribute('datetime') || 
                                    dateElement.getAttribute('content') || 
                                    dateElement.textContent;
                        if (date) {
                            metadata['date'] = date.trim();
                            break;
                        }
                    }
                }
                
                return metadata;
            }''')
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}
    
    async def take_screenshot(self, filename: str) -> str:
        """
        Take a screenshot of the current page.
        
        Args:
            filename: Base filename (without extension)
            
        Returns:
            Path to the saved screenshot
        """
        if not self.page:
            logger.warning("Cannot take screenshot, no active page")
            return ""
        
        try:
            # Ensure valid filename
            clean_filename = "".join(c if c.isalnum() or c in "._- " else "_" for c in filename)
            path = os.path.join(self.screenshots_dir, f"{clean_filename}.png")
            
            # Take screenshot
            await self.page.screenshot(path=path)
            logger.debug(f"Screenshot saved to: {path}")
            
            return path
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return ""
    
    async def click(self, selector: str) -> bool:
        """
        Click an element on the page.
        
        Args:
            selector: CSS selector for the element to click
            
        Returns:
            True if click succeeded, False otherwise
        """
        if not self.page:
            logger.warning("Cannot click, no active page")
            return False
        
        try:
            await self.page.click(selector)
            await self.wait_for_page_load()
            return True
            
        except Exception as e:
            logger.error(f"Error clicking element {selector}: {e}")
            return False
    
    async def type_text(self, selector: str, text: str) -> bool:
        """
        Type text into an input field.
        
        Args:
            selector: CSS selector for the input field
            text: Text to type
            
        Returns:
            True if typing succeeded, False otherwise
        """
        if not self.page:
            logger.warning("Cannot type text, no active page")
            return False
        
        try:
            # Clear the field first
            await self.page.fill(selector, "")
            
            # Type the text
            await self.page.type(selector, text)
            return True
            
        except Exception as e:
            logger.error(f"Error typing text into element {selector}: {e}")
            return False
    
    async def extract_links(self, selector: str = "a") -> List[Dict[str, str]]:
        """
        Extract links from the current page.
        
        Args:
            selector: CSS selector for link elements
            
        Returns:
            List of dictionaries with link text and URL
        """
        if not self.page:
            logger.warning("Cannot extract links, no active page")
            return []
        
        try:
            return await self.page.evaluate(f'''selector => {{
                const links = Array.from(document.querySelectorAll(selector));
                return links.map(link => {{
                    return {{
                        text: link.innerText.trim(),
                        url: link.href,
                        title: link.getAttribute('title') || ''
                    }};
                }}).filter(link => link.url && link.url.startsWith('http'));
            }}''', selector)
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    async def scroll(self, amount: int = 500):
        """
        Scroll the page by the specified amount.
        
        Args:
            amount: Pixels to scroll (positive for down, negative for up)
        """
        if not self.page:
            logger.warning("Cannot scroll, no active page")
            return
        
        try:
            await self.page.evaluate(f'window.scrollBy(0, {amount})')
            await asyncio.sleep(0.5)  # Allow time for content to load
            
        except Exception as e:
            logger.error(f"Error scrolling page: {e}")
    
    async def scroll_to_bottom(self, step: int = 500, max_scrolls: int = 10):
        """
        Scroll to the bottom of the page in steps.
        
        Args:
            step: Pixels to scroll per step
            max_scrolls: Maximum number of scroll steps
        """
        if not self.page:
            logger.warning("Cannot scroll, no active page")
            return
        
        try:
            for _ in range(max_scrolls):
                # Check if we've reached the bottom
                is_bottom = await self.page.evaluate('''() => {
                    return window.innerHeight + window.scrollY >= document.body.scrollHeight;
                }''')
                
                if is_bottom:
                    break
                
                await self.scroll(step)
                await asyncio.sleep(0.5)  # Wait for content to load
                
        except Exception as e:
            logger.error(f"Error scrolling to bottom: {e}")
    
    async def close(self):
        """Close the browser session and clean up resources."""
        logger.info("Closing browser session")
        
        if self.page:
            await self.page.close()
            self.page = None
        
        if self.context:
            await self.context.close()
            self.context = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
