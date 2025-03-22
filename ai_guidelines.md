# AI Guidelines for Browser Automation Research Project

## Overview

This document serves as a comprehensive guide for large language models (LLMs) like Cline to understand and implement the Browser Automation for Research project. This system combines browser automation capabilities with natural language processing to create an AI-powered knowledge companion that can autonomously navigate the web, extract information, and synthesize comprehensive reports based on user queries.

---

## 1. System Architecture

The Browser Automation for Research project consists of the following core components:

### 1.1. Key Components

- **Orchestration Engine**: Coordinates all system activities, including query analysis, research planning, execution, and result synthesis.
- **Browser-Use Module**: Provides automated web browsing capabilities for information gathering.
- **LLM Integration**: Utilizes Ollama with Llama 3.2 (or equivalent models) for natural language understanding and generation.
- **Model Context Protocol (MCP)**: Enables standardized communication with external knowledge sources.
- **Knowledge Source Manager**: Handles connections to various knowledge repositories (arXiv, Wikipedia, etc.).
- **User Interface**: Accepts user queries and presents research results in a structured format.

### 1.2. Data Flow

1. User submits a research query through the interface
2. The orchestration engine analyzes the query and develops a research strategy
3. Research is conducted through browser automation and MCP-connected knowledge sources
4. Retrieved information is processed and synthesized into a coherent report
5. The final report is presented to the user with source attributions

---

## 2. Implementation Guidelines for LLMs

As an LLM working with this codebase, you should understand the following aspects to effectively assist in implementation:

### 2.1. Query Analysis

When analyzing user queries:

- Break down complex research topics into searchable sub-queries
- Identify relevant knowledge domains for each query (academic, business, general knowledge)
- Determine appropriate sources for information (web search, academic databases, specialized sources)
- Formulate a structured research plan with prioritized steps

Example implementation approach:
```python
async def analyze_query(query_text):
    """
    Analyze a user query to create a research plan.
    
    The research plan should include:
    1. Main research question breakdown
    2. Key search terms for different sources
    3. Priority order for sources to consult
    4. Potential follow-up questions
    
    Your analysis should be thorough and consider the domain expertise required.
    """
    # Implementation code here
```

### 2.2. Browser Automation

When implementing browser automation:

- Focus on ethical web scraping practices (respecting robots.txt, appropriate delays)
- Implement robust page navigation handling different site structures
- Extract relevant content while filtering out advertisements and navigation elements
- Maintain state across multi-page research sessions

Example pattern:
```python
class ResearchBrowser:
    """
    Provides browser automation capabilities for web research.
    
    This class should:
    1. Handle navigation across websites
    2. Extract relevant content from pages
    3. Follow citation links when appropriate
    4. Respect ethical scraping guidelines
    
    Implement with clear error handling for web navigation failures.
    """
    # Implementation code here
```

### 2.3. Knowledge Integration

When integrating external knowledge sources:

- Use the Model Context Protocol to create standardized access patterns
- Implement appropriate data transformation between different source formats
- Create specialized handlers for academic sources like arXiv
- Cache frequently accessed information to improve performance

Example pattern:
```python
class KnowledgeSourceManager:
    """
    Manages connections to external knowledge sources through MCP.
    
    This class should:
    1. Provide a unified interface to diverse knowledge sources
    2. Handle authentication and rate limiting
    3. Transform source-specific data into standardized formats
    4. Implement appropriate caching strategies
    
    Each source should have specialized methods that understand source-specific parameters.
    """
    # Implementation code here
```

### 2.4. Report Generation

When synthesizing research reports:

- Structure information logically with clear sections and hierarchy
- Distinguish between factual information and analytical insights
- Provide proper source attribution
- Address contradictions or knowledge gaps explicitly
- Use appropriate formatting (Markdown) for readability

Example pattern:
```python
async def generate_research_report(query, research_results):
    """
    Synthesize research findings into a comprehensive report.
    
    The report should:
    1. Begin with an executive summary
    2. Organize information by topic in a logical progression
    3. Highlight key findings and insights
    4. Note contradictions or limitations in the research
    5. Include proper citations to original sources
    6. Format in Markdown for readability
    
    Balance comprehensiveness with clarity and conciseness.
    """
    # Implementation code here
```

---

## 3. Code Organization

The project should be organized with the following structure:

```
browser_research/
├── main.py                     # Application entry point
├── orchestration/              # Orchestration engine
│   ├── __init__.py
│   ├── research_planner.py     # Query analysis and planning
│   ├── task_executor.py        # Task execution coordination
│   └── report_generator.py     # Report synthesis
├── browser/                    # Browser automation
│   ├── __init__.py
│   ├── browser_session.py      # Browser control
│   ├── content_extractor.py    # Web content parsing
│   └── navigation.py           # Web navigation logic
├── knowledge/                  # Knowledge sources
│   ├── __init__.py
│   ├── mcp_client.py           # MCP implementation
│   ├── source_manager.py       # Knowledge source registry
│   └── sources/                # Source-specific implementations
│       ├── __init__.py
│       ├── arxiv.py            # arXiv integration
│       ├── wikipedia.py        # Wikipedia integration
│       └── web_search.py       # General web search
├── models/                     # LLM integration
│   ├── __init__.py
│   ├── llm_client.py           # Ollama/LLM interface
│   └── prompts.py              # System prompts
├── ui/                         # User interface
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface
│   └── web.py                  # Web interface (FastAPI)
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── cache.py                # Caching system
│   ├── logging.py              # Logging utilities
│   └── rate_limiter.py         # Rate limiting for external services
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 4. Component Implementation Details

### 4.1. Orchestration Engine

The orchestration engine is the central coordinator. When implementing this component:

- Design it to maintain the overall state of research tasks
- Implement clear interfaces between subcomponents
- Create a pipeline architecture that allows for both sequential and parallel operations
- Provide mechanisms for error recovery and task retry

Key methods:
```python
async def process_query(query_text):
    """Master method that coordinates the entire research process."""

async def analyze_and_plan(query_text):
    """Analyzes the query and creates a research plan."""

async def execute_research_plan(research_plan):
    """Executes a research plan across multiple sources."""

async def synthesize_report(query, research_results):
    """Creates the final research report."""
```

### 4.2. Browser-Use Module

The Browser-Use module enables automated web interaction. When implementing:

- Create abstract interfaces for browser operations
- Implement robust error handling for network issues and site structure changes
- Design content extraction to be adaptable to different website layouts
- Include options for both headless and visible browser operation for debugging

Key methods:
```python
async def search(query, search_engine="google"):
    """Perform a search and extract results."""

async def visit_page(url):
    """Visit a specific web page and extract its content."""

async def extract_main_content():
    """Intelligently extract the main content from the current page."""

async def follow_link(link_text):
    """Find and follow a specific link on the current page."""
```

### 4.3. LLM Integration

The LLM integration connects to Ollama or other LLM services. Implementation should:

- Create a thin client that handles communication with the LLM service
- Implement appropriate error handling and retry logic
- Support streaming responses when appropriate
- Include mechanisms for prompt management and versioning

Key methods:
```python
async def complete(prompt, max_tokens=1000, temperature=0.7):
    """Generate a completion from the LLM."""

async def classify(text, categories, explanation=True):
    """Classify text into provided categories with explanation."""

async def summarize(text, max_length=200, focus=None):
    """Summarize text with optional focus areas."""
```

### 4.4. Model Context Protocol (MCP)

The MCP implementation should:

- Define a standard interface for external knowledge sources
- Implement authentication and request signing
- Handle response parsing and validation
- Provide logging and debugging capabilities

Key methods:
```python
async def query_context(context_name, parameters):
    """Query a specific knowledge context with parameters."""

async def list_contexts():
    """List available knowledge contexts."""

async def get_context_schema(context_name):
    """Get the parameter schema for a specific context."""
```

---

## 5. Implementation Context for LLMs

When assisting with this project, LLMs should:

### 5.1. Maintain Ethical Standards

- Ensure all web scraping is respectful (using robots.txt, rate limiting)
- Implement proper attribution for information sources
- Be transparent about AI-generated content
- Consider privacy implications when handling user queries

### 5.2. Focus on Code Quality

- Write modular, reusable components
- Include comprehensive error handling
- Document code thoroughly with docstrings
- Create appropriate abstractions and separation of concerns

### 5.3. Consider Performance

- Implement caching for frequently accessed information
- Use asynchronous programming for I/O-bound operations
- Balance parallelism with responsible resource use
- Monitor and optimize memory usage, especially for large research tasks

### 5.4. Ensure Reliability

- Design the system to recover gracefully from failures
- Implement logging for debugging and audit purposes
- Create appropriate retry mechanisms for transient errors
- Design with fault isolation to prevent cascading failures

---

## 6. Example Implementation Patterns

### 6.1. Query Analysis

```python
async def analyze_query(query, llm_client):
    """Analyze a research query and create a structured plan."""
    system_prompt = """
    You are an expert research strategist. Analyze the research query and develop 
    a comprehensive research plan. Break down the query into components, identify 
    key search terms, and determine the most relevant information sources.
    
    Return your analysis as a structured JSON object with the following format:
    {
        "main_question": "Restated main research question",
        "sub_questions": ["Specific sub-question 1", "Specific sub-question 2"],
        "search_terms": {
            "web_search": ["Term 1", "Term 2"],
            "arxiv": "Specialized academic search term",
            "wikipedia": "General knowledge search term"
        },
        "priority_order": ["web_search", "wikipedia", "arxiv"],
        "requires_followup": true/false,
        "domain_knowledge": ["relevant domain 1", "relevant domain 2"]
    }
    """
    
    user_prompt = f"RESEARCH QUERY: {query}\n\nCreate a detailed research plan."
    
    response = await llm_client.complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1500,
        temperature=0.2
    )
    
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Fallback handling if response isn't valid JSON
        logger.error(f"Failed to parse LLM response as JSON: {response[:100]}...")
        return {
            "main_question": query,
            "sub_questions": [query],
            "search_terms": {"web_search": [query]},
            "priority_order": ["web_search"],
            "requires_followup": False
        }
```

### 6.2. Web Navigation

```python
class ResearchBrowser:
    """Browser automation for research tasks."""
    
    def __init__(self, headless=True, user_agent=None):
        """Initialize the research browser."""
        self.headless = headless
        
        # Set ethical user agent if not provided
        if user_agent is None:
            user_agent = "ResearchAssistant/1.0 (+https://example.com/bot)"
        
        self.browser_session = BrowserSession(headless=headless, user_agent=user_agent)
        self.history = []
        self.rate_limiter = RateLimiter()
        self.robots_parser = RobotsParser()
        
    async def search(self, query, search_engine="google"):
        """Perform a search and return results."""
        # Determine search URL based on engine
        if search_engine == "google":
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        elif search_engine == "bing":
            url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
        else:
            raise ValueError(f"Unsupported search engine: {search_engine}")
        
        # Check robots.txt and apply rate limiting
        if not await self.robots_parser.can_fetch(url, self.browser_session.user_agent):
            logger.warning(f"Access to {url} disallowed by robots.txt")
            return []
        
        await self.rate_limiter.acquire(url)
        
        # Perform the search
        await self.browser_session.navigate(url)
        self.history.append({"action": "search", "query": query, "url": url})
        
        # Extract search results (implementation depends on search engine)
        if search_engine == "google":
            return await self._extract_google_results()
        elif search_engine == "bing":
            return await self._extract_bing_results()
            
    async def _extract_google_results(self):
        """Extract search results from Google."""
        results = []
        
        # Find all search result containers
        result_elements = await self.browser_session.find_elements("div.g")
        
        for element in result_elements:
            try:
                # Extract title
                title_elem = await self.browser_session.find_element_within(element, "h3")
                title = await self.browser_session.get_text(title_elem) if title_elem else ""
                
                # Extract URL
                link_elem = await self.browser_session.find_element_within(element, "a")
                url = await self.browser_session.get_attribute(link_elem, "href") if link_elem else ""
                
                # Extract snippet
                snippet_elem = await self.browser_session.find_element_within(element, "div.VwiC3b")
                snippet = await self.browser_session.get_text(snippet_elem) if snippet_elem else ""
                
                if title and url:
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
            except Exception as e:
                logger.error(f"Error extracting search result: {e}")
                continue
                
        return results
        
    async def visit_page(self, url):
        """Visit a page and extract its main content."""
        # Check robots.txt and apply rate limiting
        if not await self.robots_parser.can_fetch(url, self.browser_session.user_agent):
            logger.warning(f"Access to {url} disallowed by robots.txt")
            return {
                "url": url,
                "error": "Access disallowed by robots.txt",
                "content": None
            }
        
        await self.rate_limiter.acquire(url)
        
        # Navigate to the page
        try:
            await self.browser_session.navigate(url)
            self.history.append({"action": "visit", "url": url})
            
            # Wait for page to load fully
            await self.browser_session.wait_for_page_load()
            
            # Extract page information
            title = await self.browser_session.get_page_title()
            content = await self.extract_main_content()
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "error": None
            }
        except Exception as e:
            logger.error(f"Error visiting page {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "content": None
            }
            
    async def extract_main_content(self):
        """Extract the main content from the current page."""
        # Try common content selectors
        content_selectors = [
            "article", "main", "#content", ".content", 
            "[role='main']", ".post-content", ".entry-content"
        ]
        
        for selector in content_selectors:
            element = await self.browser_session.find_element(selector)
            if element:
                content = await self.browser_session.get_text(element)
                if content and len(content) > 200:  # Content seems substantial
                    return content
        
        # Fallback: use a more sophisticated content extraction algorithm
        # based on text density and element positioning
        return await self._extract_content_by_density()
        
    async def _extract_content_by_density(self):
        """Extract content based on text density heuristics."""
        # Implementation would analyze text density and formatting
        # to identify the main content area
        # ...
```

### 6.3. Report Generation

```python
async def generate_research_report(query, research_results, llm_client):
    """Generate a comprehensive research report from collected information."""
    
    # Prepare the research results for inclusion in the prompt
    formatted_results = json.dumps(research_results, indent=2)
    
    # If results are too large, summarize each source first
    if len(formatted_results) > 6000:
        summarized_results = await summarize_research_results(research_results, llm_client)
        formatted_results = json.dumps(summarized_results, indent=2)
    
    system_prompt = """
    You are an expert research analyst and writer. Create a comprehensive, well-structured 
    research report based on the provided information. Your report should:
    
    1. Begin with an executive summary that captures key insights
    2. Organize information logically by topic and subtopic
    3. Present information objectively with appropriate context
    4. Address contradictions or knowledge gaps explicitly
    5. Include proper citations to original sources
    6. Conclude with a summary of findings and potential next steps
    
    Format your report in Markdown with clear headings, subheadings, lists, and 
    emphasis where appropriate. Ensure the report is readable, informative, and
    comprehensive.
    """
    
    user_prompt = f"""
    RESEARCH QUERY: {query}
    
    RESEARCH FINDINGS:
    {formatted_results}
    
    Based on this information, create a comprehensive research report.
    """
    
    report = await llm_client.complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=4000,
        temperature=0.3
    )
    
    # Ensure the report has proper structure
    if not report.startswith("# "):
        report = f"# Research Report: {query}\n\n{report}"
        
    return report

async def summarize_research_results(research_results, llm_client):
    """Summarize verbose research results to fit within token limits."""
    summarized_results = []
    
    for result in research_results:
        # Check if this result needs summarization
        if "content" in result and result["content"] and len(result["content"]) > 1000:
            summary = await llm_client.summarize(
                result["content"],
                max_length=500,
                focus="key facts and insights"
            )
            # Replace original content with summary
            result["content"] = summary
            result["summarized"] = True
        
        summarized_results.append(result)
        
    return summarized_results
```

---

## 7. Implementation Phases

When implementing this project, LLMs should follow these phases:

### Phase 1: Core Architecture
- Implement the orchestration engine with basic query handling
- Create the Browser-Use module with essential navigation capabilities
- Set up the LLM client for query analysis and report generation
- Develop a simple CLI interface for testing

### Phase 2: Knowledge Integration
- Implement the MCP client for standardized knowledge access
- Create specialized handlers for key knowledge sources
- Develop caching mechanisms for frequently accessed information
- Enhance browser navigation with more sophisticated content extraction

### Phase 3: Advanced Features
- Implement parallel processing for multi-source research
- Add follow-up question generation for deeper research
- Develop visualization components for research results
- Create a web-based interface using FastAPI

### Phase 4: Optimization & Refinement
- Optimize performance for handling complex queries
- Implement comprehensive error handling and recovery
- Add user feedback mechanisms to improve results
- Create detailed logging for debugging and analysis

---

## 8. Conclusion

This guide provides the architectural overview, implementation details, and best practices for the Browser Automation for Research project. LLMs like Cline should use this document to understand the project's structure, component interactions, and implementation approaches.

The most important aspects to focus on are:
1. Ethical web interaction with proper rate limiting and robots.txt compliance
2. Robust error handling throughout the system
3. Clean separation of concerns between components
4. Comprehensive documentation of all code
5. Scalable architecture that can adapt to different research domains

By following these guidelines, LLMs can effectively contribute to building a powerful, ethical, and efficient AI-powered research assistant.