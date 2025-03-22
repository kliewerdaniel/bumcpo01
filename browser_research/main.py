#!/usr/bin/env python3
"""
Browser Automation for Research - Main Application Entry Point

This module serves as the entry point for the Browser Automation for Research application.
It initializes all necessary components and starts the appropriate interface based on
configuration.
"""
import asyncio
import argparse
import logging
import sys

from orchestration.research_planner import ResearchPlanner
from orchestration.task_executor import TaskExecutor
from orchestration.report_generator import ReportGenerator
from models.llm_client import LLMClient
from ui.cli import CLI
from ui.web import WebInterface
from config import load_config


async def main():
    """Main entry point for the application."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Browser Automation for Research")
    parser.add_argument("--web", action="store_true", help="Start web interface")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--query", type=str, help="Research query (CLI mode only)")
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Browser Automation for Research")
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize components
    llm_client = LLMClient(config["llm"])
    research_planner = ResearchPlanner(llm_client)
    task_executor = TaskExecutor(config)
    report_generator = ReportGenerator(llm_client)
    
    # Create orchestration pipeline
    orchestrator = {
        "planner": research_planner,
        "executor": task_executor,
        "generator": report_generator
    }
    
    # Start appropriate interface
    if args.web:
        # Start web interface
        web_interface = WebInterface(orchestrator, config["web"])
        await web_interface.start()
    else:
        # Start CLI interface
        cli = CLI(orchestrator)
        if args.query:
            # Process a single query and exit
            await cli.process_query(args.query)
        else:
            # Start interactive CLI
            await cli.start_interactive()

    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)
