import requests
import json
#from typing import override
from workflows.nodes.abstract_node import AbstractNode
from workflows.workflow_tracer import WorkflowTracer
from workers.reports.local_file_writer_worker import LocalFileWriterWorker

# Writes the input somewhere
class WriterNode(AbstractNode):
    LOCAL_DISK = "local_disk"
    def __init__(self, node_id: str, location_type: str, location: str, cache_enabled: bool = False):
        super().__init__(node_id, cache_enabled)
        self.location_type = location_type
        self.location = location

    #@override
    def start_impl(self):
        if self.location_type == self.LOCAL_DISK:
            worker_name = f"brave_image_search_worker{self.node_id}"
            self.worker = LocalFileWriterWorker(worker_name, self.location)
        else:
            raise ValueError(f"Invalid location_type {self.location_type}")

    #@override
    def run_impl(self, input_text: str) -> str:
        return self.worker.write(input_text)

    #@override
    def stop_impl(self) -> str:
        pass
    
    #@override
    def get_cache_key(self) -> str:
        return self.node_id + "_" + self.location
    
def main():
    node = WriterNode("writer node", WriterNode.LOCAL_DISK, "test.txt", False)
    tracer = WorkflowTracer()
    node.start(tracer)
    result = node.run("cute puppies")
    print(result)
    node.stop()

if __name__ == "__main__":
    main()