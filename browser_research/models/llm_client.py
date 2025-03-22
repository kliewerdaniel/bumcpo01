"""
LLM Client module for Browser Automation for Research.

This module provides integration with the Ollama/LLM interface,
handling API communication and response parsing.
"""
import logging
import json
import aiohttp
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with Ollama or other LLM services.
    
    This class handles communication with the LLM, including query formatting,
    response processing, and error handling.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM client.
        
        Args:
            config: Configuration dictionary for the LLM service
        """
        self.provider = config.get("provider", "ollama")
        self.model = config.get("model", "llama3.2")
        self.api_base = config.get("api_base", "http://localhost:11434/api")
        self.default_temperature = config.get("temperature", 0.7)
        self.default_max_tokens = config.get("max_tokens", 4000)
        self.session = None
    
    async def initialize(self):
        """Initialize the LLM client."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"}
            )
    
    async def close(self):
        """Close the LLM client session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def complete(self, 
                      system_prompt: str,
                      user_prompt: str,
                      max_tokens: int = None,
                      temperature: float = None) -> str:
        """
        Generate a completion from the LLM.
        
        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt for the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation (0.0 to 1.0)
            
        Returns:
            Generated text
        """
        await self.initialize()
        
        # Use default values if not specified
        max_tokens = max_tokens or self.default_max_tokens
        temperature = temperature or self.default_temperature
        
        if self.provider == "ollama":
            return await self._complete_ollama(system_prompt, user_prompt, max_tokens, temperature)
        else:
            logger.error(f"Unsupported LLM provider: {self.provider}")
            return "Error: Unsupported LLM provider"
    
    async def _complete_ollama(self, 
                             system_prompt: str,
                             user_prompt: str,
                             max_tokens: int,
                             temperature: float) -> str:
        """
        Generate a completion using Ollama.
        
        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt for the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation (0.0 to 1.0)
            
        Returns:
            Generated text
        """
        if not self.session:
            await self.initialize()
        
        # Endpoint for completion
        endpoint = f"{self.api_base}/generate"
        
        # Prepare the request body
        request_body = {
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False  # We want a complete response, not streaming
        }
        
        try:
            async with self.session.post(endpoint, json=request_body) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "")
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama API error: {response.status} - {error_text}")
                    return f"Error: LLM request failed with status {response.status}"
                
        except Exception as e:
            logger.error(f"Error communicating with Ollama: {e}")
            return f"Error: {str(e)}"
    
    async def classify(self, 
                      text: str, 
                      categories: List[str],
                      explanation: bool = True) -> Dict[str, Any]:
        """
        Classify text into provided categories.
        
        Args:
            text: Text to classify
            categories: List of possible categories
            explanation: Whether to include explanation
            
        Returns:
            Dictionary with classification result and explanation
        """
        await self.initialize()
        
        system_prompt = """
        You are an expert text classifier. Classify the provided text into exactly one of the 
        available categories. Your response should be in JSON format with the following structure:
        {
            "category": "selected_category",
            "confidence": 0.95,
            "explanation": "Explanation of why this category was selected"
        }
        """
        
        user_prompt = f"""
        Text to classify:
        
        {text}
        
        Available categories:
        {json.dumps(categories)}
        
        Classify this text into exactly one of the categories above.
        {'' if explanation else 'Do not include an explanation.'}
        """
        
        result = await self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2  # Lower temperature for classification
        )
        
        try:
            # Parse JSON result
            classification = json.loads(result)
            return classification
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM classification response as JSON: {result}")
            # Fallback to a simple result
            return {
                "category": categories[0] if categories else "unknown",
                "confidence": 0.0,
                "explanation": "Failed to parse LLM response"
            }
    
    async def summarize(self, 
                       text: str, 
                       max_length: int = 200,
                       focus: Optional[str] = None) -> str:
        """
        Summarize text with optional focus.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary in words
            focus: Optional focus for the summary
            
        Returns:
            Summarized text
        """
        await self.initialize()
        
        focus_instruction = f"Focus on {focus}." if focus else ""
        
        system_prompt = f"""
        You are an expert summarizer. Create a concise and informative summary of the provided text.
        The summary should be no longer than {max_length} words. {focus_instruction}
        Extract the most important information while maintaining accuracy.
        """
        
        user_prompt = f"""
        Text to summarize:
        
        {text}
        
        Provide a concise summary (max {max_length} words).
        """
        
        return await self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,  # Lower temperature for more deterministic summary
            max_tokens=max_length * 2  # Generous token limit
        )
    
    async def extract_structured_data(self, 
                                    text: str, 
                                    schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from text based on a schema.
        
        Args:
            text: Text to extract data from
            schema: JSON schema describing the expected structure
            
        Returns:
            Extracted structured data
        """
        await self.initialize()
        
        system_prompt = """
        You are an expert in information extraction. Extract structured data from the provided text
        according to the specified schema. Your response should be valid JSON that matches the schema.
        If information is not present in the text, use null or appropriate default values.
        """
        
        user_prompt = f"""
        Text to extract information from:
        
        {text}
        
        Schema for extraction:
        {json.dumps(schema, indent=2)}
        
        Extract the relevant information into a JSON object that matches this schema.
        """
        
        result = await self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2  # Lower temperature for more deterministic extraction
        )
        
        try:
            # Parse JSON result
            extracted_data = json.loads(result)
            return extracted_data
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM extraction response as JSON: {result}")
            return {"error": "Failed to parse extraction result"}
    
    async def generate_questions(self, 
                               text: str, 
                               num_questions: int = 3) -> List[str]:
        """
        Generate follow-up questions based on the provided text.
        
        Args:
            text: Text to generate questions from
            num_questions: Number of questions to generate
            
        Returns:
            List of generated questions
        """
        await self.initialize()
        
        system_prompt = f"""
        You are an expert researcher skilled at formulating insightful questions. 
        Generate {num_questions} follow-up questions based on the provided text.
        The questions should explore key aspects that would deepen understanding of the topic.
        Your response should be in the format of a JSON array of strings, each string being a question.
        """
        
        user_prompt = f"""
        Text:
        
        {text}
        
        Generate {num_questions} follow-up research questions based on this text.
        """
        
        result = await self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7  # Higher temperature for creative questions
        )
        
        try:
            # Parse JSON result
            questions = json.loads(result)
            if isinstance(questions, list):
                return questions[:num_questions]
            else:
                logger.error(f"LLM response is not a list: {result}")
                return []
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM questions response as JSON: {result}")
            
            # Fallback: Try to extract questions directly from text
            lines = result.split('\n')
            extracted_questions = []
            
            for line in lines:
                line = line.strip()
                # Check if line looks like a question
                if line and (line.endswith('?') or line.startswith(('What', 'How', 'Why', 'When', 'Where', 'Which', 'Who', 'Is', 'Are', 'Can', 'Could', 'Should', 'Would'))):
                    extracted_questions.append(line)
            
            return extracted_questions[:num_questions] if extracted_questions else []
