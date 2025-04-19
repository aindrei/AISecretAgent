import pytest
import json
from workflows.nodes.collate_node import CollateNode

def test_collate_node_initialization():
    node = CollateNode("test_node")
    assert node.node_id == "test_node"
    assert node.inputs == {}

def test_collate_single_input():
    node = CollateNode("test_node")
    node.start()
    test_input = json.dumps({"attractions": [{"name": "Test1", "score": 10}]})
    result = node.run(test_input)
    expected = json.dumps({"attractions": [{"name": "Test1", "score": 10}]})
    assert json.loads(result) == json.loads(expected)

def test_collate_multiple_inputs():
    node = CollateNode("test_node")
    node.start()
    input1 = json.dumps({"attractions": [{"name": "Test1", "score": 10}]})
    input2 = json.dumps({"attractions": [{"name": "Test2", "score": 20}]})
    node.run(input1)
    result = node.run(input2)
    expected = json.dumps({
        "attractions": [
            {"name": "Test1", "score": 10},
            {"name": "Test2", "score": 20}
        ]
    })
    assert json.loads(result) == json.loads(expected)

def test_collate_deduplication():
    node = CollateNode("test_node")
    node.start()
    input1 = json.dumps({"attractions": [{"name": "Test1", "score": 10}]})
    input2 = json.dumps({"attractions": [{"name": "Test1", "score": 20}]})
    node.run(input1)
    result = node.run(input2)
    expected = json.dumps({
        "attractions": [{"name": "Test1", "score": 10}]
    })
    assert json.loads(result) == json.loads(expected)

def test_collate_missing_attribute():
    node = CollateNode("test_node")
    node.start()
    test_input = json.dumps({"wrong_attr": [{"name": "Test1"}]})
    result = node.run(test_input)
    expected = json.dumps({"attractions": []})
    assert json.loads(result) == json.loads(expected)

def test_collate_invalid_json():
    node = CollateNode("test_node")
    node.start()
    with pytest.raises(json.JSONDecodeError):
        node.run("invalid json")
