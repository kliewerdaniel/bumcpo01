# Browser Automation for Research

An AI-powered research assistant that combines browser automation with LLMs to conduct comprehensive research across multiple sources.

## Overview

This system can autonomously navigate the web, extract information from various sources, and synthesize comprehensive reports based on user queries. It uses a combination of:

- **Browser Automation**: For web navigation and content extraction
- **LLM Integration**: For query analysis, information synthesis, and report generation
- **Knowledge Sources**: Integration with Wikipedia, arXiv, and web search

## Project Structure

```
browser_research/
├── main.py                     # Application entry point
├── orchestration/              # Orchestration engine
│   ├── research_planner.py     # Query analysis and planning
│   ├── task_executor.py        # Task execution coordination
│   └── report_generator.py     # Report synthesis
├── browser/                    # Browser automation
│   ├── browser_session.py      # Browser control
│   ├── content_extractor.py    # Web content parsing
│   └── navigation.py           # Web navigation logic
├── knowledge/                  # Knowledge sources
│   ├── mcp_client.py           # MCP implementation
│   ├── source_manager.py       # Knowledge source registry
│   └── sources/                # Source-specific implementations
│       ├── arxiv.py            # arXiv integration
│       ├── wikipedia.py        # Wikipedia integration
│       └── web_search.py       # General web search
├── models/                     # LLM integration
│   ├── llm_client.py           # Ollama/LLM interface
│   └── prompts.py              # System prompts
├── ui/                         # User interface
│   ├── cli.py                  # Command-line interface
│   └── web.py                  # Web interface (FastAPI)
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

## Installation

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```bash
   playwright install
   ```
4. Install Ollama and download the Llama model:
   ```bash
   # Install Ollama as per instructions at https://ollama.ai
   # Then run:
   ollama pull llama3.2
   ```

## Configuration

The system uses a YAML configuration file (default: `config.yaml`). A default configuration is provided, but you can customize it by creating a `config.yaml` file in the project root:

```yaml
llm:
  provider: "ollama"
  model: "llama3.2"
  api_base: "http://localhost:11434/api"
  temperature: 0.7
  max_tokens: 4000

browser:
  headless: true
  user_agent: "ResearchAssistant/1.0 (+https://example.com/bot; for research purposes)"
  timeout: 30
  screenshots_dir: "screenshots"
  respect_robots_txt: true
  rate_limit:
    requests_per_minute: 10
    delay_between_requests: 6

knowledge:
  sources: ["web_search", "wikipedia", "arxiv"]
  cache:
    enabled: true
    ttl: 3600  # Cache time-to-live in seconds
    max_size: 1000  # Maximum number of items in cache

web:
  host: "127.0.0.1"
  port: 8080
  debug: false
```

## Usage

### Command Line Interface

```bash
# Run with CLI interface
python main.py

# Run with CLI and process a single query
python main.py --query "What are the latest advancements in AI?"

# Show debug logs
python main.py --debug
```

### Web Interface

```bash
# Start web interface
python main.py --web

# Specify port and host
python main.py --web --config custom_config.yaml
```

Then open your browser to http://127.0.0.1:8080 (or the configured host/port).

## API Keys for Search Engines (Optional)

For web search functionality, you can optionally configure API keys:

1. Google Custom Search:
   - Get an API key from Google Cloud Console
   - Set up a Custom Search Engine
   - Add the details to your config.yaml:
     ```yaml
     knowledge:
       web_search:
         engine: "google"
         api_key: "YOUR_API_KEY"
         search_id: "YOUR_SEARCH_ENGINE_ID"
     ```

2. Bing Search:
   - Get an API key from Microsoft Azure
   - Add to your config:
     ```yaml
     knowledge:
       web_search:
         engine: "bing"
         api_key: "YOUR_API_KEY"
     ```

Without API keys, the system will use simulated search results for demonstration purposes.

## Features

- **Query Analysis**: Breaks down complex research questions into manageable components
- **Ethical Web Crawling**: Respects robots.txt and implements rate limiting
- **Content Extraction**: Intelligently extracts main content from web pages
- **Knowledge Integration**: Unified interface to Wikipedia, arXiv, and web search
- **Report Generation**: Creates well-structured, comprehensive research reports
- **Caching**: Stores frequently accessed information for improved performance
- **Progress Tracking**: Real-time updates on research progress
- **Multiple Interfaces**: Both CLI and web-based interfaces

## Ethical Considerations

This tool is designed for ethical research purposes:
- Respects website terms of service and robots.txt
- Implements rate limiting to avoid overloading servers
- Provides proper attribution for information sources
- Is transparent about AI-generated content

## Example Usage

```python
from orchestration.research_planner import ResearchPlanner
from orchestration.task_executor import TaskExecutor
from orchestration.report_generator import ReportGenerator
from models.llm_client import LLMClient
from config import load_config

async def research_example():
    # Load config
    config = load_config()
    
    # Initialize components
    llm_client = LLMClient(config["llm"])
    planner = ResearchPlanner(llm_client)
    executor = TaskExecutor(config)
    generator = ReportGenerator(llm_client)
    
    # Research query
    query = "What are the environmental impacts of blockchain technology?"
    
    # Create research plan
    research_plan = await planner.create_research_plan(query)
    
    # Execute plan
    research_results = await executor.execute_research_plan(research_plan)
    
    # Generate report
    report = await generator.generate_report(research_results)
    
    # Print or save report
    print(report)
    
    # Clean up
    await executor.close()
```

## License

This project is licensed under the MIT License.
