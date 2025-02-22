import os
from google import genai
from pydantic import BaseModel
from workflows.api_keys import gemini_api_key
from workers.llm.ai_worker import AIWorker

# Uses Google Gemini to generate responses
# https://ai.google.dev/gemini-api/docs/quickstart?lang=python
class GeminiWorker(AIWorker):
    def __init__(self, worker_name: str, instructions: str, model_name: str = "gemini-2.0-flash", api_key: str=None):
        super().__init__(worker_name)
        self.instructions = instructions
        self.model_name = model_name
        if not api_key:
            api_key = os.environ["GEMINI_API_KEY"]
        assert api_key, "API key is required for GeminiWorker"

        self.prompt = None
        self.system_prompt = None

        self.client = genai.Client(api_key=api_key)

    #@override
    def generate_response(self, prompt: str, system_prompt: str = None, output_format: str = None, response_model: BaseModel = None, **kwargs) -> str:
        print("Using Gemini client")
        # If instructions are provided, replace the placeholder from instructions with the prompt
        if self.instructions:
            # replace {input_text} from instructions with the prompt
            prompt = self.instructions.replace("{input_text}", prompt)
        print(f"Generating response with prompt: {prompt[:1000]}")
        self.prompt = prompt
        self.system_prompt = system_prompt

        if output_format == "json" and response_model:
            response = self.client.models.generate_content(
                        model=self.model_name, 
                        contents=prompt,
                        config={
                            'response_mime_type': 'application/json',
                            'response_schema': list[response_model],
                        },
                )
        else:
            response = self.client.models.generate_content(
                        model=self.model_name, 
                        contents=prompt
                )
        print(f"response: {response.text}")
        return response.text
    
    #@override
    def get_worker_prompts(self) -> dict:
        return {"prompt": self.prompt, "system_prompt": self.system_prompt}
    
def __main__():
    worker = GeminiWorker("gemini", "What is the capital of {input_text}?", "gemini-2.0-flash", gemini_api_key)
    response = worker.generate_response("France")
    print(response)

if __name__ == "__main__":
    __main__()
