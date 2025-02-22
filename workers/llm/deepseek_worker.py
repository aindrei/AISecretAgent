import os
from openai import OpenAI
from pydantic import BaseModel
import instructor
from workers.llm.ai_worker import AIWorker

# Uses DeepSeek to generate responses
class DeepSeekWorker(AIWorker):
    def __init__(self, worker_name: str, instructions: str, model_name: str, api_key: str=None):
        super().__init__(worker_name)
        self.instructions = instructions
        self.model_name = model_name
        if not api_key:
            api_key = os.environ["DEEPSEEK_API_KEY"]
        assert api_key, "API key is required for DeepSeekWorker"

        self.prompt = None
        self.system_prompt = None

        self.client= OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.structured_client = instructor.from_openai(
            OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        )

    #@override
    def generate_response(self, prompt: str, system_prompt: str = None, output_format: str = None, response_model: BaseModel = None, **kwargs) -> str:
        print("Using DeepSeek with OpenAI client")
        # If instructions are provided, replace the placeholder from instructions with the prompt
        if self.instructions:
            # replace {input_text} from instructions with the prompt
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

        print(f"response_model: {response_model}")
        if response_model:
            response_obj = self.structured_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=False,
                response_model=response_model
            )
            # Convert object to json
            response_json = response_obj.json()
            print(f"response_json: {response_json}")
            return response_json # return the structured response as json string
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=False
            )

        return response.choices[0].message.content # return the text response

    #@override
    def get_worker_prompts(self) -> dict:
        return {"prompt": self.prompt, "system_prompt": self.system_prompt}
