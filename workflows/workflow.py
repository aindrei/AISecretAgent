from typing import Dict, List, Any
import logging
from workflows.nodes.abstract_node import AbstractNode
from workflows.workflow_tracer import WorkflowTracer

# Execution DAG for an AI workflow
class Workflow:
    """Class that manages execution flow between connected nodes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Maps node_id to node instance; the first node is the start node and the last node is the end node
        self.nodes: Dict[str, AbstractNode] = {}
        # Maps source node_id to list of target node_id
        self.connections: Dict[str, List[str]] = {}
        # Maps target node_id to list of input node_id
        self.input_connections: Dict[str, List[str]] = {}
        self.tracer = WorkflowTracer()
    
    def add_node(self, node_id: str, node: AbstractNode) -> None:
        """Add a node to the workflow"""
        self.nodes[node_id] = node
    
    def connect(self, source_node_id: str, target_node_id: str) -> None:
        """Connect output of source node to input of target node"""
        if source_node_id not in self.connections:
            self.connections[source_node_id] = []
        self.connections[source_node_id].append(target_node_id)

        if target_node_id not in self.input_connections:
            self.input_connections[target_node_id] = []
        self.input_connections[target_node_id].append(source_node_id)
    
    # Run the workflow graph starting with the first node and passing the output to connected nodes
    # This runs the nodes sequentially in one thread
    # Returns the output of the last node
    def run(self, input: str) -> Dict[str, Any]:
        """Execute the workflow and return all node outputs"""
        # Using this to determine when the first and last run of a node is made
        call_counter: Dict[str, int] = {}

        def run_node(node_id: str, node_input: str) -> Any:
            node = self.nodes[node_id]
            if node_id not in call_counter:
                node.start(self.tracer)
                call_counter[node_id] = 1
            else:
                call_counter[node_id] += 1
            output = node.run(node_input)

            # Notify the node if all input connections have been processed
            # Since the start node has no input connections, we need to default to 1 for the input connections count
            if call_counter[node_id] == len(self.input_connections.get(node_id, ["start"])):
                node.stop()

            # Pass output to connected nodes
            if node_id in self.connections:
                # if the output is a list, we need to pass each element to one of the next nodes
                if isinstance(output, list):
                    next_node_inputs = output
                    for i, target_node_id in enumerate(self.connections[node_id]):
                        next_node_input = None
                        if i < len(next_node_inputs):
                            next_node_input = next_node_inputs[i]
                        run_node(target_node_id, next_node_input)
                else:
                    next_node_input = output
                    
                    # if the current node has multiple input connections, only call run_node once, at the end
                    input_connections = self.input_connections.get(node_id, [])
                    if len(input_connections) > 1 and call_counter[node_id] < len(input_connections):
                        return output

                    # pass the same output value to all the connected nodes
                    target_node_ids = self.connections[node_id]
                    for target_node_id in target_node_ids:
                        run_node(target_node_id, next_node_input)

            return output

        node_ids = list(self.nodes.keys())
        start_node_id = node_ids[0]
        run_node(start_node_id, input)
        end_node_id = node_ids[-1]

        last_node = self.nodes[end_node_id]
        return last_node.result
    
    def save_trace_report(self, filename: str) -> None:
        """Save the trace report to a file"""
        report_html = self.tracer.generate_report_as_html()
        with open(filename, "w", encoding='utf-8') as file:
            file.write(report_html)

# Example usage
def main():
    print("Running workflow example")

if __name__ == "__main__":
    main()