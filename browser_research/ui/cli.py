"""
Command-line Interface module for Browser Automation for Research.

This module provides a command-line interface for interacting with the research system,
allowing users to submit queries and view results.
"""
import logging
import asyncio
import sys
import os
import textwrap
import json
import argparse
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class CLI:
    """
    Command-line interface for the research system.
    
    This class handles user input/output through the terminal,
    processes research queries, and displays results.
    """
    
    def __init__(self, orchestrator: Dict[str, Any]):
        """
        Initialize the CLI.
        
        Args:
            orchestrator: Dictionary containing orchestration components
        """
        self.planner = orchestrator["planner"]
        self.executor = orchestrator["executor"]
        self.generator = orchestrator["generator"]
        
        # Terminal dimensions
        self.terminal_width = os.get_terminal_size().columns
        self.terminal_height = os.get_terminal_size().lines
    
    async def start_interactive(self):
        """Start an interactive CLI session."""
        self._print_header()
        
        try:
            while True:
                # Get query from user
                query = input("\n📚 Research query: ")
                
                if not query:
                    continue
                
                if query.lower() in ["exit", "quit", "q"]:
                    print("\nExiting research assistant. Goodbye!")
                    break
                
                # Process the query
                await self.process_query(query)
                
                # Ask if user wants to continue
                continue_research = input("\nWould you like to research something else? (y/n): ")
                if continue_research.lower() not in ["y", "yes"]:
                    print("\nExiting research assistant. Goodbye!")
                    break
                
        except KeyboardInterrupt:
            print("\n\nExiting research assistant. Goodbye!")
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            print(f"\nAn error occurred: {e}")
    
    async def process_query(self, query: str):
        """
        Process a research query.
        
        Args:
            query: The research query to process
        """
        try:
            print(f"\n🔍 Researching: {query}")
            print("\n⏳ Analyzing query and planning research...")
            
            # Create a research plan
            research_plan = await self.planner.create_research_plan(query)
            
            # Display research plan
            self._display_research_plan(research_plan)
            
            # Execute the research plan
            print("\n⏳ Executing research plan...")
            self._setup_progress_display(len(research_plan["steps"]))
            
            research_results = await self.executor.execute_research_plan(research_plan)
            
            # Generate report from results
            print("\n⏳ Generating research report...")
            report = await self.generator.generate_report(research_results)
            
            # Display the report
            self._display_report(report)
            
            # Save report to file
            self._save_report_to_file(report, query)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            print(f"\nAn error occurred while processing your query: {e}")
    
    def _print_header(self):
        """Print the application header."""
        header = """
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   🔍 BROWSER AUTOMATION FOR RESEARCH - COMMAND LINE INTERFACE │
│                                                               │
└───────────────────────────────────────────────────────────────┘
        
Welcome to the Browser Automation for Research system.
Enter your research query to get started, or type 'exit' to quit.
"""
        print(header)
    
    def _display_research_plan(self, research_plan: Dict[str, Any]):
        """
        Display the research plan.
        
        Args:
            research_plan: The research plan to display
        """
        print("\n📋 Research Plan:")
        print(f"  Main Question: {research_plan['analysis']['main_question']}")
        
        print("\n  Sub-Questions:")
        for i, question in enumerate(research_plan["analysis"]["sub_questions"], 1):
            print(f"   {i}. {question}")
        
        print("\n  Search Strategy:")
        for i, source in enumerate(research_plan["analysis"]["priority_order"], 1):
            search_terms = research_plan["analysis"]["search_terms"].get(source, "")
            if isinstance(search_terms, list):
                search_terms = ", ".join(search_terms)
            print(f"   {i}. {source.capitalize()}: {search_terms}")
        
        print(f"\n  Total Steps: {len(research_plan['steps'])}")
    
    def _setup_progress_display(self, total_steps: int):
        """
        Set up the progress display for executing research steps.
        
        Args:
            total_steps: Total number of steps in the research plan
        """
        self.total_steps = total_steps
        self.completed_steps = 0
        
        print()  # Add a blank line before progress starts
    
    def _update_progress(self, step: Dict[str, Any], result: Dict[str, Any]):
        """
        Update the progress display.
        
        Args:
            step: The current step
            result: The result of the current step
        """
        self.completed_steps += 1
        progress = int((self.completed_steps / self.total_steps) * 20)
        progress_bar = f"[{'#' * progress}{' ' * (20 - progress)}]"
        
        print(f"\r  {progress_bar} {self.completed_steps}/{self.total_steps} steps completed", end="")
    
    def _display_report(self, report: str):
        """
        Display the research report.
        
        Args:
            report: The research report to display
        """
        print("\n\n📊 Research Report:\n")
        
        # Simple rendering of markdown to terminal
        for line in report.split("\n"):
            if line.startswith("# "):
                # Main header
                print(f"\n\033[1m{line[2:]}\033[0m")
                print("=" * len(line[2:]))
            elif line.startswith("## "):
                # Subheader
                print(f"\n\033[1m{line[3:]}\033[0m")
                print("-" * len(line[3:]))
            elif line.startswith("### "):
                # Sub-subheader
                print(f"\n\033[1m{line[4:]}\033[0m")
            elif line.startswith("- "):
                # List item
                wrapped = textwrap.fill(line, width=self.terminal_width - 2)
                print(wrapped)
            else:
                # Regular text with wrapping
                if line.strip():
                    wrapped = textwrap.fill(line, width=self.terminal_width)
                    print(wrapped)
                else:
                    print()
    
    def _save_report_to_file(self, report: str, query: str):
        """
        Save the research report to a file.
        
        Args:
            report: The research report to save
            query: The original query
        """
        # Create a safe filename from the query
        safe_filename = "".join(c if c.isalnum() or c in " -_" else "_" for c in query)
        safe_filename = safe_filename[:50]  # Limit length
        filename = f"research_{safe_filename}_{int(asyncio.get_event_loop().time())}.md"
        
        try:
            with open(filename, "w") as f:
                f.write(report)
            print(f"\nReport saved to: {filename}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            print(f"\nCould not save report to file: {e}")


async def main():
    """Run the CLI as a standalone application."""
    # This would be used if running the CLI directly
    pass


if __name__ == "__main__":
    asyncio.run(main())
