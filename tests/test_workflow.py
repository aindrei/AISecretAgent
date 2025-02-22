import pytest
from workflows.nodes.abstract_node import AbstractNode
from workflows.workflow import Workflow
from workflows.workflow_validator import WorkflowValidator

class MockNode(AbstractNode):
    def __init__(self, node_id: str):
        super().__init__(node_id)
        self.input_data = []
    
    def start_impl(self) -> None:
        pass

    def run_impl(self, input_data: str) -> str:
        self.input_data.append(input_data)
        return input_data
    
    def stop_impl(self) -> None:
        self.result = self.input_data[-1]
        return self.input_data[-1]

class TestWorkflow:
    @pytest.fixture
    def workflow(self):
        return Workflow()
    
    @pytest.fixture
    def mock_nodes(self):
        return {
            "node1": MockNode("node1"),
            "node2": MockNode("node2"),
            "node3": MockNode("node3"),
            "start": MockNode("start"),
            "end":   MockNode("end")
        }
    
    # node1
    def test_add_node(self, workflow, mock_nodes):
        workflow.add_node("node1", mock_nodes["node1"])
        assert "node1" in workflow.nodes
        assert workflow.nodes["node1"] == mock_nodes["node1"]
    
    # node1 -> node2
    def test_connect_nodes(self, workflow, mock_nodes):
        workflow.add_node("node1", mock_nodes["node1"])
        workflow.add_node("node2", mock_nodes["node2"])
        workflow.connect("node1", "node2")
        assert "node2" in workflow.connections["node1"]
    
    # node1    node2
    def test_validate_graph_unconnected(self, workflow, mock_nodes):
        workflow.add_node("node1", mock_nodes["node1"])
        workflow.add_node("node2", mock_nodes["node2"])
        workflow_validator = WorkflowValidator(workflow)
        assert workflow_validator.validate_graph() == False
    
    # node1 -> node2 -> node3
    def test_validate_graph_connected_3(self, workflow, mock_nodes):
        workflow.add_node("node1", mock_nodes["node1"])
        workflow.add_node("node2", mock_nodes["node2"])
        workflow.add_node("node3", mock_nodes["node3"])
        workflow.connect("node1", "node2")
        workflow.connect("node2", "node3")
        workflow_validator = WorkflowValidator(workflow)
        assert workflow_validator.validate_graph() == True
    
    # node1 -> ?
    def test_invalid_connection(self, workflow, mock_nodes):
        workflow.add_node("node1", mock_nodes["node1"])
        workflow.connect("node1", "nonexistent")
        workflow_validator = WorkflowValidator(workflow)
        assert workflow_validator.is_valid_connection() == False


    # node1 -> node2 -> node3 \
    #   ^______________________|
    def test_validate_graph_cycle(self, workflow, mock_nodes):
        workflow.add_node("node1", mock_nodes["node1"])
        workflow.add_node("node2", mock_nodes["node2"])
        workflow.add_node("node3", mock_nodes["node3"])
        workflow.connect("node1", "node2")
        workflow.connect("node2", "node3")
        workflow.connect("node3", "node1")
        workflow_validator = WorkflowValidator(workflow)
        assert workflow_validator.has_cycle() == True

    # start --> node1 -> end
    #       \-> node2 ---^
    def test_validate_graph_multi_2_one(self, workflow, mock_nodes):
        workflow.add_node("start", mock_nodes["start"])
        workflow.add_node("node1", mock_nodes["node1"])
        workflow.add_node("node2", mock_nodes["node2"])
        workflow.add_node("end", mock_nodes["end"])
        workflow.connect("start", "node1")
        workflow.connect("start", "node2")
        workflow.connect("node1", "end")
        workflow.connect("node2", "end")
        workflow_validator = WorkflowValidator(workflow)
        assert workflow_validator.validate_graph() == True

        workflow_tracer = workflow.tracer
         
        result = workflow.run("hello")
        assert result == "hello"

        # Check the order of execution
        assert workflow_tracer.traces["start"].start_time is not None
        assert workflow_tracer.traces["start"].end_time is not None
        assert workflow_tracer.traces["start"].end_time >= workflow_tracer.traces["start"].start_time

        assert workflow_tracer.traces["node1"].start_time >= workflow_tracer.traces["start"].start_time
        assert workflow_tracer.traces["node1"].start_time is not None
        assert workflow_tracer.traces["node1"].end_time is not None
        assert workflow_tracer.traces["node1"].end_time >= workflow_tracer.traces["node1"].start_time

        assert workflow_tracer.traces["node2"].start_time >= workflow_tracer.traces["start"].start_time
        assert workflow_tracer.traces["node2"].start_time is not None
        assert workflow_tracer.traces["node2"].end_time is not None
        assert workflow_tracer.traces["node2"].end_time >= workflow_tracer.traces["node2"].start_time

        assert workflow_tracer.traces["end"].start_time >= workflow_tracer.traces["node1"].start_time
        assert workflow_tracer.traces["end"].start_time >= workflow_tracer.traces["node2"].start_time
        assert workflow_tracer.traces["end"].start_time is not None
        assert workflow_tracer.traces["end"].end_time is not None
        assert workflow_tracer.traces["end"].end_time >= workflow_tracer.traces["end"].start_time

        # Check the input and output
        assert workflow_tracer.traces["start"].input_data == ["hello"]
        assert workflow_tracer.traces["start"].output_data == "hello"
        assert workflow_tracer.traces["start"].cache_hit == False
        assert workflow_tracer.traces["start"].worker_executions == []

        assert workflow_tracer.traces["node1"].input_data == ["hello"]
        assert workflow_tracer.traces["node1"].output_data == "hello"
        assert workflow_tracer.traces["node1"].cache_hit == False
        assert workflow_tracer.traces["node1"].worker_executions == []

        assert workflow_tracer.traces["node2"].input_data == ["hello"]
        assert workflow_tracer.traces["node2"].output_data == "hello"
        assert workflow_tracer.traces["node2"].cache_hit == False
        assert workflow_tracer.traces["node2"].worker_executions == []

        assert workflow_tracer.traces["end"].input_data == ["hello", "hello"]
        assert workflow_tracer.traces["end"].output_data == "hello"
        assert workflow_tracer.traces["end"].cache_hit == False
        assert workflow_tracer.traces["end"].worker_executions == []
    