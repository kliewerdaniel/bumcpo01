"""
Report Generator module for Browser Automation for Research.

This module synthesizes collected research data into comprehensive
reports with appropriate structure and attribution.
"""
import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Synthesizes research results into comprehensive reports.
    """
    
    def __init__(self, llm_client):
        """
        Initialize the report generator.
        
        Args:
            llm_client: The LLM client for report generation
        """
        self.llm_client = llm_client
    
    async def generate_report(self, research_results: Dict[str, Any]) -> str:
        """
        Generate a comprehensive research report from collected data.
        
        Args:
            research_results: Dictionary containing research results
            
        Returns:
            Markdown-formatted research report
        """
        logger.info(f"Generating report for query: {research_results['query']}")
        
        # Prepare the research results for inclusion in the prompt
        formatted_results = json.dumps(research_results, indent=2)
        
        # If results are too large, we need to summarize each source first
        if len(formatted_results) > 6000:
            summarized_results = await self._summarize_research_results(research_results)
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
        RESEARCH QUERY: {research_results['query']}
        
        RESEARCH FINDINGS:
        {formatted_results}
        
        Based on this information, create a comprehensive research report.
        """
        
        report = await self.llm_client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000,
            temperature=0.3
        )
        
        # Ensure the report has proper structure
        if not report.startswith("# "):
            report = f"# Research Report: {research_results['query']}\n\n{report}"
        
        logger.info("Report generation complete")
        return report
    
    async def _summarize_research_results(self, research_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize verbose research results to fit within token limits.
        
        Args:
            research_results: Dictionary containing research results
            
        Returns:
            Dictionary with summarized content
        """
        logger.info("Summarizing research results due to size")
        
        summarized_results = {
            "query": research_results["query"],
            "status": research_results["status"],
            "results": []
        }
        
        for step_result in research_results["results"]:
            summarized_step = step_result.copy()
            
            if step_result["type"] == "web_search":
                # Summarize each web search result
                summarized_pages = []
                for page in step_result.get("results", []):
                    if "content" in page and page["content"] and len(page["content"]) > 800:
                        summary = await self.llm_client.summarize(
                            text=page["content"],
                            max_length=500,
                            focus="key facts and insights"
                        )
                        # Replace original content with summary
                        page = page.copy()
                        page["content"] = summary
                        page["summarized"] = True
                    
                    summarized_pages.append(page)
                
                summarized_step["results"] = summarized_pages
            
            elif step_result["type"] == "knowledge_source":
                # Summarize each knowledge source result
                summarized_items = []
                for item in step_result.get("results", []):
                    if "content" in item and item["content"] and len(item["content"]) > 800:
                        summary = await self.llm_client.summarize(
                            text=item["content"],
                            max_length=500,
                            focus="key facts and insights"
                        )
                        # Replace original content with summary
                        item = item.copy()
                        item["content"] = summary
                        item["summarized"] = True
                    
                    summarized_items.append(item)
                
                summarized_step["results"] = summarized_items
            
            summarized_results["results"].append(summarized_step)
        
        return summarized_results
    
    async def format_citations(self, research_results: Dict[str, Any]) -> str:
        """
        Format citations from research sources for inclusion in reports.
        
        Args:
            research_results: Dictionary containing research results
            
        Returns:
            Markdown-formatted citations section
        """
        citations = []
        citation_index = 1
        
        # Process web search results
        for step_result in research_results.get("results", []):
            if step_result["type"] == "web_search":
                for page in step_result.get("results", []):
                    if "url" in page and "title" in page:
                        citation = f"{citation_index}. {page['title']}. Retrieved from {page['url']}"
                        citations.append(citation)
                        citation_index += 1
            
            elif step_result["type"] == "knowledge_source":
                source = step_result.get("source")
                for item in step_result.get("results", []):
                    if "title" in item and "url" in item:
                        citation = f"{citation_index}. {item['title']}. {source.capitalize()}. Retrieved from {item['url']}"
                        citations.append(citation)
                        citation_index += 1
        
        if not citations:
            return ""
        
        # Format citations section
        citations_section = "## References\n\n"
        citations_section += "\n".join(citations)
        
        return citations_section
