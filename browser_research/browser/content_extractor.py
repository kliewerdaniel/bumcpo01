"""
Content Extractor module for Browser Automation for Research.

This module provides specialized functionality for extracting and parsing content
from web pages, including main text, structured data, and metadata.
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Extracts and processes content from web pages.
    
    This class provides methods for extracting main content, parsing structured data,
    and identifying key elements from raw HTML.
    """
    
    def __init__(self):
        """Initialize the content extractor."""
        # Common patterns to identify non-content sections
        self.noise_patterns = [
            r'comment', r'share', r'social', r'footer', r'header',
            r'banner', r'menu', r'nav', r'ad-', r'popup', r'cookie',
            r'sidebar', r'related', r'recommended', r'popular'
        ]
        
        # Common tags for main content areas
        self.content_tags = [
            'article', 'main', 'section', 'div.content', 'div.post',
            'div.entry', 'div.page', 'div.blog-post', 'div.article'
        ]
    
    def extract_main_content(self, html: str) -> str:
        """
        Extract the main content from an HTML page.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Extracted main content as plain text
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'noscript', 'iframe', 'svg']):
                element.decompose()
            
            # Remove common noise elements
            for pattern in self.noise_patterns:
                for element in soup.find_all(class_=re.compile(pattern, re.I)):
                    element.decompose()
                for element in soup.find_all(id=re.compile(pattern, re.I)):
                    element.decompose()
            
            # Try to find main content container
            main_element = None
            
            # Look for structured elements first
            for tag in ['article', 'main']:
                elements = soup.find_all(tag)
                if elements:
                    # Use the largest element by text length
                    main_element = max(elements, key=lambda x: len(x.get_text()))
                    break
            
            # Try content divs if no structured elements
            if not main_element:
                for selector in ['div.content', 'div.post', 'div.entry', '.post-content', '.entry-content']:
                    elements = []
                    if '.' in selector:
                        tag, cls = selector.split('.')
                        elements = soup.find_all(tag, class_=cls)
                    else:
                        elements = soup.find_all(selector)
                    
                    if elements:
                        main_element = max(elements, key=lambda x: len(x.get_text()))
                        break
            
            # Fall back to text density analysis if still no main element
            if not main_element:
                main_element = self._extract_by_density(soup)
            
            # Extract text from the main element
            if main_element:
                # Replace breaks with newlines
                for br in main_element.find_all('br'):
                    br.replace_with('\n')
                
                # Replace paragraphs with double newlines
                for p in main_element.find_all('p'):
                    p_text = p.get_text().strip()
                    if p_text:
                        p.replace_with(f"\n\n{p_text}\n\n")
                
                # Get text and clean it
                text = main_element.get_text()
                return self._clean_text(text)
            
            # Last resort: extract all text from body
            body_text = soup.body.get_text() if soup.body else soup.get_text()
            return self._clean_text(body_text)
            
        except Exception as e:
            logger.error(f"Error extracting main content: {e}")
            return ""
    
    def _extract_by_density(self, soup) -> Any:
        """
        Extract main content based on text density.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Element with the highest text density
        """
        # Get all divs with substantial content
        candidates = []
        
        for div in soup.find_all('div'):
            # Skip small or empty divs
            text = div.get_text().strip()
            if len(text) < 200:
                continue
            
            # Calculate text to tag ratio (text density)
            tags = len(div.find_all())
            if tags == 0:
                continue
                
            text_length = len(text)
            ratio = text_length / tags
            
            # Skip low-density divs
            if ratio < 10:
                continue
            
            candidates.append((div, ratio, text_length))
        
        if not candidates:
            return None
        
        # Sort by text density and length
        candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return candidates[0][0]
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Replace multiple newlines with a single one
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace multiple spaces with a single one
        text = re.sub(r' {2,}', ' ', text)
        
        # Clean up lines
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        
        return '\n'.join(lines)
    
    def extract_metadata(self, html: str) -> Dict[str, str]:
        """
        Extract metadata from HTML.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Dictionary of metadata
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            metadata = {}
            
            # Extract standard meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                
                if name and content:
                    # Clean up name (remove 'og:' prefix from Open Graph tags)
                    clean_name = name.lower().replace('og:', '')
                    metadata[clean_name] = content
            
            # Extract title
            if soup.title:
                metadata['title'] = soup.title.string.strip() if soup.title.string else ''
            
            # Extract author information
            author_selectors = [
                ('meta', {'name': 'author'}),
                ('a', {'rel': 'author'}),
                (None, {'class': 'author'}),
                (None, {'class': 'byline'})
            ]
            
            for tag, attrs in author_selectors:
                author_elem = soup.find(tag, attrs) if tag else soup.find(**attrs)
                if author_elem:
                    if tag == 'meta':
                        metadata['author'] = author_elem.get('content', '')
                    else:
                        metadata['author'] = author_elem.get_text().strip()
                    break
            
            # Extract publication date
            date_selectors = [
                ('meta', {'name': 'date'}),
                ('meta', {'property': 'article:published_time'}),
                ('time', {}),
                (None, {'class': 'date'}),
                (None, {'class': 'published'})
            ]
            
            for tag, attrs in date_selectors:
                date_elem = soup.find(tag, attrs) if tag else soup.find(**attrs)
                if date_elem:
                    if tag == 'meta':
                        metadata['date'] = date_elem.get('content', '')
                    elif tag == 'time':
                        metadata['date'] = date_elem.get('datetime') or date_elem.get_text().strip()
                    else:
                        metadata['date'] = date_elem.get_text().strip()
                    break
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}
    
    def extract_structured_data(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract structured data (JSON-LD, microdata) from HTML.
        
        Args:
            html: Raw HTML content
            
        Returns:
            List of structured data objects
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            structured_data = []
            
            # Extract JSON-LD
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    import json
                    data = json.loads(script.string)
                    structured_data.append({
                        'type': 'json-ld',
                        'data': data
                    })
                except Exception as e:
                    logger.warning(f"Error parsing JSON-LD: {e}")
            
            # Extract OpenGraph
            og_data = {}
            for meta in soup.find_all('meta', property=re.compile(r'^og:')):
                property_name = meta.get('property')[3:]  # Remove 'og:' prefix
                og_data[property_name] = meta.get('content')
            
            if og_data:
                structured_data.append({
                    'type': 'opengraph',
                    'data': og_data
                })
            
            # Extract Twitter Card
            twitter_data = {}
            for meta in soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')}):
                property_name = meta.get('name')[8:]  # Remove 'twitter:' prefix
                twitter_data[property_name] = meta.get('content')
            
            if twitter_data:
                structured_data.append({
                    'type': 'twitter',
                    'data': twitter_data
                })
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return []
    
    def extract_links(self, html: str, base_url: str = '') -> List[Dict[str, str]]:
        """
        Extract links from HTML.
        
        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of link dictionaries
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                
                # Skip empty links and javascript/mailto links
                if not href or href.startswith(('javascript:', 'mailto:', '#')):
                    continue
                
                # Resolve relative URLs if base_url provided
                if base_url and not href.startswith(('http://', 'https://')):
                    import urllib.parse
                    href = urllib.parse.urljoin(base_url, href)
                
                # Extract link text and title
                text = a.get_text().strip()
                title = a.get('title', '')
                
                links.append({
                    'url': href,
                    'text': text,
                    'title': title
                })
            
            return links
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    def extract_tables(self, html: str) -> List[List[List[str]]]:
        """
        Extract tables from HTML.
        
        Args:
            html: Raw HTML content
            
        Returns:
            List of tables, where each table is a list of rows and each row is a list of cells
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            tables = []
            
            for table in soup.find_all('table'):
                parsed_table = []
                
                # Process table rows
                for tr in table.find_all('tr'):
                    row = []
                    
                    # Process cells (th and td)
                    for cell in tr.find_all(['th', 'td']):
                        # Extract text and clean it
                        cell_text = cell.get_text().strip()
                        row.append(cell_text)
                    
                    if row:  # Skip empty rows
                        parsed_table.append(row)
                
                if parsed_table:  # Skip empty tables
                    tables.append(parsed_table)
            
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []
    
    def summarize_text(self, text: str, max_sentences: int = 5) -> str:
        """
        Create a simple extractive summary of text.
        
        Args:
            text: Text to summarize
            max_sentences: Maximum number of sentences to include
            
        Returns:
            Summarized text
        """
        if not text or max_sentences <= 0:
            return ""
        
        try:
            # Split into sentences (simple approach)
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            # If we already have fewer sentences than max, return as is
            if len(sentences) <= max_sentences:
                return text
            
            # Score sentences (very basic algorithm - rank by length and position)
            scored_sentences = []
            
            for i, sentence in enumerate(sentences):
                # Skip very short sentences
                if len(sentence) < 10:
                    continue
                
                # Score based on position (earlier is better)
                position_score = 1.0 - (i / len(sentences))
                
                # Score based on length (medium-length sentences are better)
                length = len(sentence)
                length_score = min(1.0, length / 100) if length < 100 else 2.0 - (length / 100)
                
                # Calculate total score
                total_score = position_score * 0.6 + length_score * 0.4
                
                scored_sentences.append((sentence, total_score))
            
            # Sort by score and take top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            selected_sentences = [sentence for sentence, _ in scored_sentences[:max_sentences]]
            
            # Re-order sentences to match original order
            ordered_sentences = []
            for sentence in sentences:
                if sentence in selected_sentences:
                    ordered_sentences.append(sentence)
                    selected_sentences.remove(sentence)
                
                if not selected_sentences:
                    break
            
            return ' '.join(ordered_sentences)
            
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            return text[:200] + "..." if len(text) > 200 else text
    
    def clean_html(self, html: str) -> str:
        """
        Clean HTML by removing unnecessary elements.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Cleaned HTML
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for tag in ['script', 'style', 'noscript', 'iframe', 'svg']:
                for element in soup.find_all(tag):
                    element.decompose()
            
            # Remove common noise elements
            for pattern in self.noise_patterns:
                for element in soup.find_all(class_=re.compile(pattern, re.I)):
                    element.decompose()
                for element in soup.find_all(id=re.compile(pattern, re.I)):
                    element.decompose()
            
            # Remove comments
            for comment in soup.find_all(text=lambda text: isinstance(text, str) and text.strip().startswith('<!')):
                comment.extract()
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"Error cleaning HTML: {e}")
            return html
