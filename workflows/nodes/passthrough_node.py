import logging
#from typing import override
from workflows.nodes.abstract_node import AbstractNode

# Node that returns the input as output
class PassthroughNode(AbstractNode):
    def __init__(self, node_id: str):
        super().__init__(node_id)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    #@override
    def start_impl(self):
        self.logger.info(f"Starting node {self.node_id}")

    #@override
    def run_impl(self, input_text: str) -> str:
        self.result = input_text
        return input_text

    #@override
    def stop_impl(self) -> str:
        self.logger.info(f"Stopping node {self.node_id}")
        return self.result