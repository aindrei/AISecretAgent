import logging
import json
from typing import List
from workflows.nodes.abstract_node import AbstractNode

class RagContextPreparerNode(AbstractNode):
    def __init__(self, node_id: str):
        super().__init__(node_id)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.context_segments = None
        self.input = None
        self.result = None

    def start_impl(self):
        self.logger.info(f"Starting RAG context preparer node {self.node_id}")
        self.context_segments = None
        self.input = None
        self.result = None

    def run_impl(self, input_text: str) -> str:
        # First call - store context segments
        # Input: [{"text": "What is the capital of France?", "embeddings": [1,2], "closest_embeddings": [[1,2], [3,4]], "closest_texts": ["Paris", "Nice"]}]
        # Output: combined prompt (text with relevant context)
        self.input = json.loads(input_text)
        first_prompt = self.input[0]

        self.context_segments = self._get_context(first_prompt)
        self.prompt = first_prompt.get("text", None)

        # Combine context and prompt in RAG format
        combined_text = "Relevant information:\n"
        for i, segment in enumerate(self.context_segments, 1):
            combined_text += f"[{i}] {segment}\n"
        
        combined_text += "\nUse the provided relevant information to respond to this prompt:\n" + self.prompt
        
        self.result = combined_text
        return self.result
        
    def stop_impl(self) -> str:
        self.logger.info(f"Stopping RAG context preparer node {self.node_id}")
        return self.result
    
    def _get_context(self, prompt_obj) -> List[str]:
        # parse the input string to extract context closest_texts
        # ex {"prompt": "What is the capital of France?", "embeddings": [1,2], "closest_embeddings": [[1,2], [3,4]], "closest_texts": ["Paris", "Nice"]}
        closest_texts = prompt_obj.get("closest_texts", [])
        if isinstance(closest_texts, str):
            closest_texts = [closest_texts]
        return closest_texts
        
    def get_cache_key(self) -> str:
        return self.node_id + str(self.input)
    
def main(input_text):
    node = RagContextPreparerNode("rag_context_preparer_node")
    node.start()
    result = node.run(input_text)
    node.stop()
    print(result)

if __name__ == "__main__":
    input_text = json.dumps([
        {"text": "What is the capital of France?", "embeddings": [1,2], "closest_embeddings": [[1,2], [3,4]], "closest_texts": ["Paris", "Nice"]}
    ])
    main(input_text)