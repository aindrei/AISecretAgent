from typing import Dict, Any
import requests
from pydantic import BaseModel

from ollama import chat
from ollama import ChatResponse

from workers.llm.ai_worker import AIWorker

# Uses Ollama to generate responses with the specified model
class OllamaWorker(AIWorker):
    def __init__(self, worker_name: str, instructions: str, model_name: str="llama2", use_lib: bool=True, base_url: str="http://localhost:11434"):
        super().__init__(worker_name)
        self.model_name = model_name
        self.instructions = instructions
        self.use_lib = use_lib # can use the library or the local server url
        self.base_url = base_url.rstrip('/')

        self.prompt = None
        self.system_prompt = None

    # Generates a response using the Ollama library or server url
    #@override
    def generate_response(self, prompt: str, system_prompt: str = None, output_format: str = None, response_model: BaseModel = None, **kwargs) -> str:
        # If instructions are provided, replace the placeholder from instructions with the prompt
        if self.instructions:
            # replace {input_text} from instructions with the prompt
            prompt = self.instructions.replace("{input_text}", prompt)
        print(f"Generating response with prompt: {prompt[:1000]}")

        self.prompt = prompt
        self.system_prompt = system_prompt

        response = None
        if self.use_lib:
            response = self._generate_response_with_client(prompt, system_prompt, output_format, response_model)
        else:
            response = self._generate_response_with_url(prompt, system_prompt, output_format, response_model)
        print(f"Generated response: {response[:1000]}")
        return response

    # Generates a response using the Ollama library
    def _generate_response_with_client(self, prompt: str, system_prompt: str, output_format: str, response_model: BaseModel) -> str:
        try:
            print("Using Ollama client")
            messages = [
                {
                    'role': 'user',
                    'content': prompt,
                }]
            if response_model:
                response: ChatResponse = chat(model=self.model_name, messages=messages, format=response_model.model_json_schema())
            else:
                response: ChatResponse = chat(model=self.model_name, messages=messages)
            return response["message"]["content"]
        except Exception as e:
            print(f"Error generating prediction: {e}")
            return None

    # Generates a response using the Ollama server url
    def _generate_response_with_url(self, prompt: str, system_prompt: str, output_format: str) -> str:
        print("Using Ollama url")
        headers = {'Content-Type': 'application/json'}
        data: Dict[Any, Any] = {
            'model': self.model_name,
            'prompt': prompt,
            'stream': False
        }
        
        if system_prompt:
            data['system'] = system_prompt

        try:
            response = requests.post(f"{self.base_url}/api/generate", json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except requests.RequestException as e:
            raise Exception(f"Failed to communicate with Ollama: {str(e)}")

    #@override
    def get_worker_prompts(self) -> dict:
        return {"prompt": self.prompt, "system_prompt": self.system_prompt}
