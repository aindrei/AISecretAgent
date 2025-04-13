import logging
import json
from workers.llm.ollama_worker import OllamaWorker
from workflows.nodes.abstract_node import AbstractNode

class EmbeddingsGeneratorNode(AbstractNode):
    def __init__(self, node_id: str, model_properties: dict, cache_enabled: bool = False):
        super().__init__(node_id, cache_enabled)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.model_properties = model_properties

    def _create_worker(self, model_properties: dict):
        """Create an embeddings worker based on the model properties."""
        self.model_provider = model_properties.get("model_provider", None)
        assert self.model_provider is not None, "Model provider is required"
        self.model_name = model_properties.get("model_name")
        self.worker_name = self.model_provider + "_" + self.model_name

        if self.model_provider == "ollama":
            use_lib = True
            return OllamaWorker(self.worker_name, None, self.model_name, use_lib) # 512 context, 1024 enbedding size
        
        raise ValueError(f"Invalid model provider: {self.model_provider}")

    def start_impl(self):
        self.worker = self._create_worker(self.model_properties)
        self.logger.info(f"Starting embeddings node {self.node_id}")

    def run_impl(self, input_text: str) -> str:
        #Input [{"text": "hello", "text_location_in_doc": None, "doc_location": file_path}]
        #Output [{"text": "hello", "embeddings": [1,2], "text_location_in_doc": None, "doc_location": file_path}]
        text_segments = json.loads(input_text)

        for text_segment in text_segments:
            text = text_segment["text"]
            embeddings = self.worker.generate_embeddings(text)
            text_segment["embeddings"] = embeddings

        self.result = json.dumps(text_segments)
        # Log the generation of embeddings without including the actual vectors
        self.tracer.log_worker(self.node_id, self.worker_name, input_text, 
                             f"Generated embeddings of dimension {len(embeddings)}", 
                             "generate_embeddings", None)
        return self.result

    def stop_impl(self) -> str:
        self.logger.info(f"Stopping embeddings node {self.node_id}")
        return str(self.result)

    def get_cache_key(self) -> str:
        return self.node_id + "_" + self.model_provider + "_" + self.model_name
    
def main(input_text, model_properties):
    embeddings_node = EmbeddingsGeneratorNode("generate_embeddings_node", model_properties)
    embeddings_node.start()
    response = embeddings_node.run(input_text)
    embeddings_node.stop()
    return response

if __name__ == "__main__":
    model_properties = {"model_provider": "ollama", "model_name": "mxbai-embed-large"}
    input_text = json.dumps([{"segments": [{"text": "This is a test"}], "doc_location": "test.txt"}])
    input_text = json.dumps([{"text": "This is a test", "text_location_in_doc": 0, "doc_location": "test.txt"}])
    response = main(input_text, model_properties)
    print(response[:300])