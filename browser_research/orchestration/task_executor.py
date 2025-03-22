"""
Task Executor module for Browser Automation for Research.

This module executes research plans by coordinating between browser automation
and knowledge sources to gather information for the research query.
"""
import logging
import asyncio
from typing import Dict, List, Any

from browser.browser_session import BrowserSession
from knowledge.source_manager import KnowledgeSourceManager

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Executes research plans by coordinating data collection from multiple sources.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the task executor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.browser_session = None
        self.knowledge_source_manager = KnowledgeSourceManager(config["knowledge"])
        self.research_results = {}
    
    async def initialize(self):
        """Initialize browser session and knowledge sources."""
        # Initialize browser if not already initialized
        if self.browser_session is None:
            self.browser_session = BrowserSession(
                headless=self.config["browser"]["headless"],
                user_agent=self.config["browser"]["user_agent"],
                timeout=self.config["browser"]["timeout"]
            )
            await self.browser_session.initialize()
        
        # Initialize knowledge sources
        await self.knowledge_source_manager.initialize()
    
    async def execute_research_plan(self, research_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a research plan and collect results.
        
        Args:
            research_plan: The research plan to execute
            
        Returns:
            Dictionary containing research results
        """
        logger.info(f"Executing research plan for query: {research_plan['query']}")
        
        # Initialize components if needed
        await self.initialize()
        
        # Reset research results for this query
        query_id = research_plan.get("query_id", str(hash(research_plan["query"])))
        self.research_results[query_id] = {
            "query": research_plan["query"],
            "results": [],
            "status": "in_progress",
            "completed_steps": 0,
            "total_steps": len(research_plan["steps"])
        }
        
        # Process steps in priority order
        for i, step in enumerate(research_plan["steps"]):
            step_result = await self._execute_step(step)
            
            # Update results and status
            if step_result:
                self.research_results[query_id]["results"].append(step_result)
            
            self.research_results[query_id]["completed_steps"] += 1
            
            # Check if we need to pause briefly between steps
            if i < len(research_plan["steps"]) - 1:
                await asyncio.sleep(self.config["browser"]["rate_limit"]["delay_between_requests"])
        
        # Mark research as complete
        self.research_results[query_id]["status"] = "complete"
        
        logger.info(f"Research plan execution complete. Collected {len(self.research_results[query_id]['results'])} results.")
        return self.research_results[query_id]
    
    async def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single research step.
        
        Args:
            step: The research step to execute
            
        Returns:
            Dictionary containing step results
        """
        step_type = step["type"]
        logger.info(f"Executing research step of type: {step_type}")
        
        try:
            if step_type == "web_search":
                return await self._execute_web_search(step)
            elif step_type == "knowledge_source":
                return await self._execute_knowledge_source_query(step)
            elif step_type == "generate_followup":
                return await self._generate_followup(step)
            else:
                logger.warning(f"Unknown step type: {step_type}")
                return {
                    "type": step_type,
                    "status": "error",
                    "error": f"Unknown step type: {step_type}"
                }
        except Exception as e:
            logger.error(f"Error executing step {step_type}: {e}")
            return {
                "type": step_type,
                "status": "error",
                "error": str(e)
            }
    
    async def _execute_web_search(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a web search step using the browser.
        
        Args:
            step: The web search step
            
        Returns:
            Dictionary containing search results
        """
        search_engine = step["search_engine"]
        query = step["query"]
        max_results = step.get("max_results", 5)
        
        logger.info(f"Executing web search for '{query}' using {search_engine}")
        
        # Execute search and get results
        search_results = await self.browser_session.search(
            query=query,
            search_engine=search_engine,
            max_results=max_results
        )
        
        # Visit top pages and extract content
        page_contents = []
        for result in search_results[:max_results]:
            try:
                page_content = await self.browser_session.visit_page(result["url"])
                if page_content:
                    page_contents.append({
                        **result,
                        "content": page_content
                    })
            except Exception as e:
                logger.error(f"Error visiting page {result['url']}: {e}")
        
        return {
            "type": "web_search",
            "search_engine": search_engine,
            "query": query,
            "results": page_contents,
            "status": "complete"
        }
    
    async def _execute_knowledge_source_query(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a knowledge source query.
        
        Args:
            step: The knowledge source step
            
        Returns:
            Dictionary containing query results
        """
        source = step["source"]
        query = step["query"]
        max_results = step.get("max_results", 3)
        
        logger.info(f"Querying knowledge source '{source}' for '{query}'")
        
        # Query the knowledge source
        results = await self.knowledge_source_manager.query(
            source=source,
            query=query,
            max_results=max_results
        )
        
        return {
            "type": "knowledge_source",
            "source": source,
            "query": query,
            "results": results,
            "status": "complete"
        }
    
    async def _generate_followup(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate follow-up questions based on initial results.
        
        Args:
            step: The follow-up generation step
            
        Returns:
            Dictionary containing follow-up questions
        """
        based_on = step["based_on"]
        
        # This would typically use an LLM to generate follow-up questions
        # based on the results collected so far
        
        # Placeholder for now
        followup_questions = [
            "How does this relate to recent developments?",
            "What are alternative perspectives on this topic?",
            "What are the practical applications of these findings?"
        ]
        
        return {
            "type": "generate_followup",
            "questions": followup_questions,
            "status": "complete"
        }
    
    async def close(self):
        """Clean up resources."""
        if self.browser_session:
            await self.browser_session.close()
        await self.knowledge_source_manager.close()
