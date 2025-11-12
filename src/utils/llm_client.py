"""LLM client wrapper supporting OpenAI and Anthropic"""

import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from .logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)


class LLMClient:
    """Unified client for OpenAI and Anthropic LLMs"""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000
    ):
        """
        Initialize LLM client
        
        Args:
            provider: "openai" or "anthropic" (defaults to env var LLM_PROVIDER)
            model: Model name (defaults to env var model)
            temperature: Sampling temperature
            max_tokens: Max tokens in response
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
                logger.info(f"Initialized OpenAI client with model: {self.model}")
            except ImportError:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
            except Exception as e:
                raise Exception(f"Failed to initialize OpenAI client: {e}")
                
        elif self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
                logger.info(f"Initialized Anthropic client with model: {self.model}")
            except ImportError:
                raise ImportError("Anthropic package not installed. Run: pip install anthropic")
            except Exception as e:
                raise Exception(f"Failed to initialize Anthropic client: {e}")
        else:
            raise ValueError(f"Unknown provider: {self.provider}. Use 'openai' or 'anthropic'")
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False
    ) -> str:
        """
        Generate completion from LLM
        
        Args:
            system_prompt: System instruction
            user_prompt: User message
            temperature: Override default temperature
            max_tokens: Override default max tokens
            json_mode: Request JSON output (OpenAI only)
        
        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            if self.provider == "openai":
                return self._generate_openai(
                    system_prompt, user_prompt, temp, tokens, json_mode
                )
            else:
                return self._generate_anthropic(
                    system_prompt, user_prompt, temp, tokens
                )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> str:
        """Generate using OpenAI"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
    
    def _generate_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using Anthropic"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.content[0].text if response.content else ""
    
    def generate_with_retries(
        self,
        system_prompt: str,
        user_prompt: str,
        retries: int = 3,
        **kwargs
    ) -> str:
        """Generate with automatic retries on failure"""
        for attempt in range(retries):
            try:
                return self.generate(system_prompt, user_prompt, **kwargs)
            except Exception as e:
                if attempt == retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
        
        return ""  # Should never reach here


