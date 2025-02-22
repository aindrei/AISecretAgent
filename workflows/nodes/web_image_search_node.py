import requests
import json
#from typing import override
from workflows.nodes.abstract_node import AbstractNode
from workflows.api_keys import brave_search_api_key
from workflows.workflow_tracer import WorkflowTracer
from workers.web.brave_web_search_worker import BraveWebSearchWorker
from workers.web.web_search_worker import WebSearchWorker

# Does a web image search (using the Brave Search API)
class WebImageSearchNode(AbstractNode):
    def __init__(self, node_id: str, api_key: str, number_of_results = 10, cache_enabled: bool = False):
        super().__init__(node_id, cache_enabled)
        self.api_key = api_key
        self.number_of_results = number_of_results
        self.worker = None # web search worker

    #@override
    def start_impl(self):
        worker_name = f"brave_image_search_worker{self.node_id}"
        self.worker = BraveWebSearchWorker(worker_name, WebSearchWorker.RESULT_TYPE_IMAGE, self.api_key)

    #@override
    def run_impl(self, input_text: str) -> str:
        return self.worker.search(input_text, self.number_of_results)        

    #@override
    def stop_impl(self) -> str:
        self.worker.cleanup()
    
    #@override
    def get_cache_key(self) -> str:
        return self.node_id + "_" + str(self.number_of_results)
    
def main():
    node = WebImageSearchNode("brave image search node", brave_search_api_key, 1, False)
    tracer = WorkflowTracer()
    node.start(tracer)
    result = node.run("cute puppies")
    print(result)
    node.stop()

if __name__ == "__main__":
    main()