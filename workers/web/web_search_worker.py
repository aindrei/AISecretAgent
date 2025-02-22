from abc import ABC, abstractmethod

class WebSearchWorker(ABC):
    """Base class for web search workers that return web sites or images"""
    # enum of result types (web, image)
    RESULT_TYPE_WEB = "web"
    RESULT_TYPE_IMAGE = "image"
    
    def __init__(self, name: str, result_type: str = RESULT_TYPE_WEB):
        self._name = name
        self._result_type = result_type

    @abstractmethod
    def search(self, keywords: str, number_of_results: int = 10) -> str:
        """
        Does a web search for the given keywords and returns the results.        
        """
        pass

    @abstractmethod
    def cleanup(self):
        pass

    @property
    def name(self) -> str:
        """
        Get the name of the worker.
        
        Returns:
            str: The name of the worker
        """
        return self._name    