"""
Research Planner module for Browser Automation for Research.

This module analyzes user queries and creates structured research plans,
breaking down complex topics into searchable components.
"""
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ResearchPlanner:
    """
    Analyzes queries and creates structured research plans.
    """
    
    def __init__(self, llm_client):
        """
        Initialize the research planner.
        
        Args:
            llm_client: The LLM client for query analysis
        """
        self.llm_client = llm_client
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a research query and create a structured plan.
        
        Args:
            query: The user's research query
            
        Returns:
            A dictionary containing the research plan
        """
        logger.info(f"Analyzing query: {query}")
        
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
        
        response = await self.llm_client.complete(
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
                "requires_followup": False,
                "domain_knowledge": []
            }
    
    async def create_research_plan(self, query: str) -> Dict[str, Any]:
        """
        Create a comprehensive research plan for a query.
        
        Args:
            query: The user's research query
            
        Returns:
            A dictionary containing the complete research plan with execution steps
        """
        # First analyze the query
        analysis = await self.analyze_query(query)
        
        # Create a structured plan with execution steps
        research_plan = {
            "query": query,
            "analysis": analysis,
            "steps": []
        }
        
        # Generate research steps based on priority order
        for source in analysis["priority_order"]:
            if source == "web_search":
                # Add web search steps for each term
                for term in analysis["search_terms"].get("web_search", []):
                    research_plan["steps"].append({
                        "type": "web_search",
                        "search_engine": "google",
                        "query": term,
                        "max_results": 5,
                        "status": "pending"
                    })
            elif source == "arxiv":
                # Add arxiv search step
                if "arxiv" in analysis["search_terms"]:
                    research_plan["steps"].append({
                        "type": "knowledge_source",
                        "source": "arxiv",
                        "query": analysis["search_terms"]["arxiv"],
                        "max_results": 3,
                        "status": "pending"
                    })
            elif source == "wikipedia":
                # Add wikipedia search step
                if "wikipedia" in analysis["search_terms"]:
                    research_plan["steps"].append({
                        "type": "knowledge_source",
                        "source": "wikipedia",
                        "query": analysis["search_terms"]["wikipedia"],
                        "max_results": 2,
                        "status": "pending"
                    })
        
        # Add follow-up steps if needed
        if analysis.get("requires_followup", False):
            research_plan["steps"].append({
                "type": "generate_followup",
                "based_on": "initial_results",
                "status": "pending"
            })
        
        logger.info(f"Created research plan with {len(research_plan['steps'])} steps")
        return research_plan
