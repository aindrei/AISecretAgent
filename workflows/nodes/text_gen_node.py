import json
import logging
#from typing import override

from workers.llm.ollama_worker import OllamaWorker
from workers.llm.mistral_worker import MistralWorker
from workers.llm.deepseek_worker import DeepSeekWorker
from workers.llm.gemini_worker import GeminiWorker
from workflows.nodes.abstract_node import AbstractNode

# Node for text generation using an LLM
class TextGenNode(AbstractNode):
    def __init__(self, node_id: str, model_properties: dict, prompt_properties: dict = {}, cache_enabled: bool = False):
        super().__init__(node_id, cache_enabled)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.model_properties = model_properties
        self.prompt_properties = prompt_properties

    def _create_worker(self, model_properties: dict):
        """
        Create an AI worker based on the model properties.
        This method should be implemented based on specific requirements.
        """
        self.model_provider = model_properties.get("model_provider", None)
        assert self.model_provider is not None, "Model provider is required"
        self.model_name = model_properties.get("model_name")
        assert self.model_name is not None, "Model name is required"
        self.worker_name = self.model_provider + "_" + self.model_name

        instructions = model_properties.get("instructions", None)
        if self.model_provider == "ollama":
            use_lib = model_properties.get("use_lib", True)
            model_url = model_properties.get("base_url", "http://localhost:11434")
            return OllamaWorker(self.worker_name, instructions, self.model_name, use_lib, model_url)
        else:
            api_key = model_properties.get("api_key", None)
            if self.model_provider == "mistral":
                return MistralWorker(self.worker_name, instructions, self.model_name, api_key)
            elif self.model_provider == "deepseek":
                return DeepSeekWorker(self.worker_name, instructions, self.model_name, api_key)
            elif self.model_provider == "gemini":
                return GeminiWorker(self.worker_name, instructions, self.model_name, api_key)

        raise ValueError(f"Invalid model provider: {self.model_provider}")
    
    def _extract_text_between_tags(self, text: str, start_tag: str, end_tag: str, include_tags: bool):
        start_pos = text.find(start_tag)
        if start_pos >= 0:
            end_pos = text.rfind(end_tag, start_pos)
            if end_pos >= 0:
                if include_tags:
                    end_pos = end_pos + len(end_tag)
                else:
                    start_pos = start_pos + len(start_tag)
                return text[start_pos:end_pos]
        return None

    def _extract_json(self, llm_response: str) -> str:
        # The llm return sometimes json wrapped into ```json ... ``` or just { ... }
        json_content = self._extract_text_between_tags(llm_response, "```json", "```", False)
        if json_content:
            return json_content
        
        json_content = self._extract_text_between_tags(llm_response, "{", "}", True)
        if json_content:
            return json_content
        
        print(f"No JSON content found in response: {llm_response}")
        return "{}" # Return empty JSON object if no JSON content is found
    
    def _extract_html(self, llm_response: str) -> str:
        # The llm return sometimes json wrapped into ```html ... ``` or just <html> ... </html> }
        html_content = self._extract_text_between_tags(llm_response, "```html", "```", False)
        if html_content:
            return html_content
        
        html_content = self._extract_text_between_tags(llm_response, "<html>", "</html>", True)
        if html_content:
            return html_content

        print(f"No HTML content found in response: {llm_response}")
        return "<html></html>" # Return empty HTML if no HTML content is found

    #@override
    def start_impl(self):
        self.worker = self._create_worker(self.model_properties)
        self.logger.info(f"Starting node {self.node_id}")

    #@override
    def run_impl(self, input_text: str) -> str:
        """
        Process the input text and generate output text.
        This method should be implemented based on specific text generation requirements.
        """
        system_prompt = self.prompt_properties.get("system_prompt", None)
        output_format = self.prompt_properties.get("output_format", None)
        response_model = self.prompt_properties.get("response_model", None)
        llm_response = self.worker.generate_response(input_text, system_prompt, output_format, response_model)
        worker_prompts = self.worker.get_worker_prompts()
        # TODO: some llms can return objects instead of json strings, support that too
        if output_format == "json":
            llm_response = self._extract_json(llm_response)
        elif output_format == "html":
            llm_response = self._extract_html(llm_response)
        self.tracer.log_worker(self.node_id, self.worker_name, input_text, llm_response, worker_prompts.get("prompt"), worker_prompts.get("system_prompt"))
        self.result = llm_response
        return llm_response

    #@override
    def stop_impl(self) -> str:
        self.logger.info(f"Stopping node {self.node_id}")
        return self.result
    
    def get_cache_key(self) -> str:
        return self.node_id + "_" + self.model_provider + "_" + self.model_name
    
