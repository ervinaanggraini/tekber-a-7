import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel

from ...core.config import settings
from ...core.logger import logging

logger = logging.getLogger(__name__)


class OpenRouterMessage(BaseModel):
    """Model untuk message OpenRouter API"""
    role: str
    content: str


class OpenRouterRequest(BaseModel):
    """Model untuk request ke OpenRouter API"""
    model: str
    messages: List[OpenRouterMessage]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stream: bool = False


class OpenRouterUsage(BaseModel):
    """Model untuk usage statistics dari OpenRouter"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenRouterResponse(BaseModel):
    """Model untuk response dari OpenRouter API"""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[OpenRouterUsage] = None


class OpenRouterService:
    """
    Service untuk integrasi dengan OpenRouter API
    
    Provides methods untuk:
    - Send chat requests
    - Get available models
    - Calculate costs
    - Handle rate limiting
    """
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.site_url = settings.OPENROUTER_SITE_URL or "http://localhost:8000"
        self.app_name = settings.APP_NAME or "FastAPI Financial App"
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # seconds between requests
        self.last_request_time = 0.0
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Internal method untuk membuat HTTP request ke OpenRouter
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data as dict
            
        Raises:
            Exception: Jika request gagal
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers, params=params) as response:
                        self.last_request_time = time.time()
                        response.raise_for_status()
                        return await response.json()
                        
                elif method.upper() == "POST":
                    async with session.post(url, headers=headers, json=data) as response:
                        self.last_request_time = time.time()
                        response.raise_for_status()
                        return await response.json()
                        
        except aiohttp.ClientError as e:
            logger.error(f"OpenRouter API request failed: {e}")
            raise Exception(f"Failed to communicate with OpenRouter API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in OpenRouter request: {e}")
            raise
    
    async def send_chat_request(
        self,
        messages: List[Dict[str, str]],
        model: str = "anthropic/claude-3.5-sonnet",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """
        Mengirim chat request ke OpenRouter API
        
        Args:
            messages: List of messages dengan format [{"role": "user", "content": "..."}]
            model: Model name to use
            max_tokens: Maximum tokens untuk response
            temperature: Sampling temperature (0.0 to 2.0)
            top_p: Nucleus sampling parameter
            
        Returns:
            Dict berisi response dari API dan metadata
            
        Example:
            >>> service = OpenRouterService()
            >>> messages = [{"role": "user", "content": "Hello!"}]
            >>> response = await service.send_chat_request(messages)
            >>> print(response["content"])  # AI response
        """
        start_time = time.time()
        
        request_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False
        }
        
        if max_tokens:
            request_data["max_tokens"] = max_tokens
        
        logger.info(f"Sending chat request to OpenRouter with model: {model}")
        
        try:
            response_data = await self._make_request("POST", "/chat/completions", request_data)
            end_time = time.time()
            response_time = end_time - start_time
            
            # Extract response content
            if not response_data.get("choices") or len(response_data["choices"]) == 0:
                raise Exception("No response choices returned from OpenRouter")
            
            choice = response_data["choices"][0]
            content = choice.get("message", {}).get("content", "")
            
            if not content:
                raise Exception("Empty response content from OpenRouter")
            
            # Calculate cost (estimate)
            usage = response_data.get("usage", {})
            estimated_cost = self._calculate_cost(
                model, 
                usage.get("prompt_tokens", 0), 
                usage.get("completion_tokens", 0)
            )
            
            result = {
                "content": content,
                "model": response_data.get("model", model),
                "usage": usage,
                "response_time": response_time,
                "estimated_cost": estimated_cost,
                "raw_response": response_data
            }
            
            logger.info(f"Chat request completed in {response_time:.2f}s, "
                       f"tokens: {usage.get('total_tokens', 0)}, "
                       f"cost: ${estimated_cost:.4f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            raise Exception(f"OpenRouter chat request failed: {str(e)}")
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Mendapatkan list model yang tersedia di OpenRouter
        
        Returns:
            List of models dengan informasi pricing dan capabilities
        """
        try:
            response = await self._make_request("GET", "/models")
            models = response.get("data", [])
            
            # Format model information
            formatted_models = []
            for model in models:
                formatted_model = {
                    "id": model.get("id", ""),
                    "name": model.get("name", ""),
                    "description": model.get("description", ""),
                    "context_length": model.get("context_length", 0),
                    "architecture": model.get("architecture", {}),
                    "pricing": model.get("pricing", {}),
                    "top_provider": model.get("top_provider", {})
                }
                formatted_models.append(formatted_model)
            
            logger.info(f"Retrieved {len(formatted_models)} available models from OpenRouter")
            return formatted_models
            
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            # Return default models as fallback
            return self._get_default_models()
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost berdasarkan model dan token usage
        
        Note: Ini adalah estimasi. Actual cost mungkin berbeda.
        """
        # Pricing estimates (per 1M tokens) - update sesuai OpenRouter pricing
        pricing = {
            "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
            "openai/gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "openai/gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "google/gemini-pro": {"input": 0.5, "output": 1.5},
            "mistralai/mixtral-8x7b-instruct": {"input": 0.27, "output": 0.27},
        }
        
        model_pricing = pricing.get(model, {"input": 1.0, "output": 2.0})  # default fallback
        
        input_cost = (prompt_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * model_pricing["output"]
        
        return input_cost + output_cost
    
    def _get_default_models(self) -> List[Dict[str, Any]]:
        """Return default models jika API call gagal"""
        return [
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "description": "Most intelligent model, best for complex reasoning tasks",
                "context_length": 200000,
                "pricing": {"input": 0.003, "output": 0.015}
            },
            {
                "id": "openai/gpt-4-turbo",
                "name": "GPT-4 Turbo",
                "description": "OpenAI's most capable model",
                "context_length": 128000,
                "pricing": {"input": 0.01, "output": 0.03}
            },
            {
                "id": "openai/gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "description": "Fast and efficient for most tasks",
                "context_length": 16385,
                "pricing": {"input": 0.0005, "output": 0.0015}
            },
            {
                "id": "google/gemini-pro",
                "name": "Gemini Pro",
                "description": "Google's advanced AI model",
                "context_length": 30720,
                "pricing": {"input": 0.0005, "output": 0.0015}
            }
        ]
    
    async def health_check(self) -> bool:
        """
        Cek apakah OpenRouter API accessible
        
        Returns:
            True jika API accessible, False otherwise
        """
        try:
            await self.get_available_models()
            return True
        except Exception as e:
            logger.error(f"OpenRouter health check failed: {e}")
            return False


# Global instance
openrouter_service = OpenRouterService()
