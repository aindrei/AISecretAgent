import pytest
from workflows.nodes.passthrough_node import PassthroughNode

def test_passthrough_node_initialization():
    node = PassthroughNode("test_node")
    assert node.node_id == "test_node"

def test_passthrough_node_returns_input():
    node = PassthroughNode("test_node")
    node.start()
    test_input = "Hello World"
    result = node.run(test_input)
    assert result == test_input

def test_passthrough_node_with_empty_string():
    node = PassthroughNode("test_node") 
    node.start()
    result = node.run("")
    assert result == ""
