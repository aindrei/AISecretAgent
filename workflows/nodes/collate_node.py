import json
import logging
#from typing import override
from workflows.nodes.abstract_node import AbstractNode

# Node that receives the output of all the nodes and returns the output
class CollateNode(AbstractNode):
    def __init__(self, node_id: str):
        super().__init__(node_id)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.inputs = {}

    #@override
    def start_impl(self):
        self.logger.info(f"Starting node {self.node_id}")

    def append_input(self, input_json: str, attribute_name: str):
        input_object = json.loads(input_json)
        input_values = []
        if attribute_name not in input_object:
            print(f"Attribute {attribute_name} not found in input object {input_json}")
        else:
            input_values = input_object[attribute_name]
        if attribute_name not in self.inputs:
            self.inputs[attribute_name] = []

        # TODO Optimize this if size becames a problem
        # Append the input values to the list but deduplicate based on the "name" attribute
        for input_value in input_values:
            name = input_value.get("name", None)
            if name is None:
                continue
            found = False
            for existing_input in self.inputs[attribute_name]:
                if existing_input.get("name", None) == name:
                    found = True
                    break
            if not found:
                self.inputs[attribute_name].append(input_value)

    #@override
    def run_impl(self, input_text: str) -> str:
        # TODO make this attribute configurable
        # Keep appending the inputs to the result (as json string)
        self.append_input(input_text, "attractions")
        self.result = json.dumps(self.inputs)
        return self.result

    #@override
    def stop_impl(self) -> str:
        self.logger.info(f"Stopping node {self.node_id}")
        return self.result