from abc import ABC, abstractmethod
from pydantic import BaseModel

class AIWorker(ABC):
    """Base class for AI workers that process text input and produce text output."""
    
    def __init__(self, name: str):
        """
        Initialize the AI worker.
        
        Args:
            name (str): The name of the worker
        """
        self._name = name

    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: str = None, output_format: str = None, response_model: BaseModel = None, **kwargs) -> str:
        """
        Process the input text and return the predicted output.
        
        Args:
            prompt (str): The llm prompt
            system_prompt (str): The system prompt
            output_format (str): The output format (e.g. json)
            response_model (BaseModel): The response model for structured output
            
        Returns:
            str: The llm response
        """
        pass

    @abstractmethod
    def get_worker_prompts(self) -> dict:
        """
        Get the prompts for the worker.
        
        Returns:
            dict: The prompts for the worker {"prompt": "prompt text", "system_prompt": "system prompt text"}
        """
        pass

    @property
    def name(self) -> str:
        """
        Get the name of the worker.
        
        Returns:
            str: The name of the worker
        """
        return self._name    