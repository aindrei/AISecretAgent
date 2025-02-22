import logging

class WorkflowValidator:
    def __init__(self, workflow):
        self.workflow = workflow
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def validate_graph(self) -> bool:
        # Check if all nodes are connected except the last one
        for node_id in list(self.workflow.nodes.keys())[:-1]:
            if node_id not in self.workflow.connections:
                self.logger.error(f"Node {node_id} is not connected")
                return False

        # Check if there are no cycles
        if self.has_cycle():
            self.logger.error("Cycle detected")
            return False

        # Check that all the nodes are reachable from the start node
        if not self.is_reachable():
            self.logger.error("Not all nodes are reachable")
            return False

        # Check that all connections are valid
        if not self.is_valid_connection():
            self.logger.error("Invalid connection pointing to non-existing node")
            return False

        return True

    def has_cycle(self) -> bool:
        current_stack = []

        def has_cycle_util(node_id: str) -> bool:
            # TODO this is not the fastest. Optimize if the depth of the graph is large
            if node_id in current_stack:
                self.logger.error(f"Cycle detected at node {node_id}")
                return True
            current_stack.append(node_id)

            if node_id in self.workflow.connections:
                for target_id in self.workflow.connections[node_id]:
                    if has_cycle_util(target_id):
                        return True
            current_stack.pop()

            return False

        return has_cycle_util(list(self.workflow.nodes.keys())[0])

    # Check that all the nodes are reachable from the start node
    def is_reachable(self) -> bool:
        visited = set()

        def is_reachable_util(node_id: str) -> None:
            visited.add(node_id)

            if node_id in self.workflow.connections:
                for target_id in self.workflow.connections[node_id]:
                    if target_id not in visited:
                        is_reachable_util(target_id)

        is_reachable_util(list(self.workflow.nodes.keys())[0])

        if len(visited) != len(self.workflow.nodes):
            self.logger.error("Not all nodes are reachable")
            self.logger.error(f"Visited nodes: {visited}")
            self.logger.error(f"All nodes: {list(self.workflow.nodes.keys())}")
        return len(visited) == len(self.workflow.nodes)

    # Check that all connections are valid (aka not pointing to non-existing nodes)
    def is_valid_connection(self) -> bool:
        for source_id in self.workflow.connections:
            if source_id not in self.workflow.nodes:
                self.logger.error(f"Source node {source_id} does not exist")
                return False
            for target_id in self.workflow.connections[source_id]:
                if target_id not in self.workflow.nodes:
                    self.logger.error(f"Target node {target_id} does not exist")
                    return False

        return True
