import os
from pydantic import BaseModel
from mistralai import Mistral
from workflows.api_keys import mistral_api_key
from workers.llm.ai_worker import AIWorker

# Uses Mistral library to generate responses
# Find model names here: https://docs.mistral.ai/getting-started/models/models_overview/
class MistralWorker(AIWorker):
    def __init__(self, worker_name: str, instructions: str, model_name: str, api_key: str=None):
        super().__init__(worker_name)
        self.instructions = instructions
        self.model_name = model_name
        if not api_key:
            api_key = os.environ["MISTRAL_API_KEY"]

        self.prompt = None
        self.system_prompt = None

        self.client= Mistral(api_key=api_key)

    #@override
    def generate_response(self, prompt: str, system_prompt: str = None, output_format: str = None, response_model: BaseModel = None, **kwargs) -> str:
        print("Using Mistral client")
        # If instructions are provided, replace the placeholder from instructions with the prompt
        if self.instructions:
            prompt = self.instructions.replace("{input_text}", prompt)
        print(f"Generating response with prompt: {prompt[:1000]}")

        messages = []
        self.prompt = prompt
        self.system_prompt = system_prompt
        if system_prompt:
            messages.append(
                {
                   "role": "system",
                    "content": system_prompt,
                }
            )
        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )
        if output_format == "json":
            chat_response = self.client.chat.complete(
                model = self.model_name,
                messages = messages,
                response_format = {
                    "type": "json_object",
                }
            )
        else:
            chat_response = self.client.chat.complete(
                model = self.model_name,
                messages = messages,
            )

        return chat_response.choices[0].message.content

    #@override
    def get_worker_prompts(self) -> dict:
        return {"prompt": self.prompt, "system_prompt": self.system_prompt}

def __main__():
    worker = MistralWorker("mistral", "What is the capital of {input_text}?", "mistral-large-latest", mistral_api_key)
    response = worker.generate_response("France")
    print(response)

if __name__ == "__main__":
    __main__()
