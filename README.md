# AISecretAgent
Evolving AI agent workflows

# Idea

Explore if we can evolve AI agent workflows through a genetic approach.

# Execution plan
## Phase 1 (current): Static workflows that can chain different nodes to solve a problem

Ex. Workflow that finds the best tourist attractions in the city:

It executes a web search for "top attraction in <city>", it uses an llm to extract the top atractions from each web page,
It collates all attractions together, generates an HTML report and writes it to a file.
```
WebSearchNode --> WebPageFetcherNode --> TextGenNode --> CollateNode --> SummarizeNode -> WriterNode
              ..........................................
              \-> WebPageFetcherNode --> TextGenNode --/
```

A worker class is:
- a function that takes an input and produces an output
- uses an API or LLM to produce the output
- has a well defined role and interface
- workers are defined in the "workers" folder

A node class is:
- a chainable component that execures a specific task
- can utilize one or more workers
- derived from abstract_node.py
- implements the base class abstract methods
- nodes are defined in the "nodes" folder

An AI workflow is an execution graph:
- that given an input (prompt/problem/question)
- returns an output (solution/response)
- achieves this by chaining multiple AI workers, the output of one node is sent to the input of one or more nodes
- starts execution from the start node and executes the connected nodes in DFS manner

## Phase 2 (not started): Dynamic workflows constructed by an LLM for a specific problem

Instead of defining the execution graphs statically we let an LLM deconstruct the problem and select the best nodes to solve each step. This is what is usually called an agentic workflow.

## Phase 3 (not started): Genetic evolution of dynamic workflows to find the most optimal workflow

Assuming we are trying to solve a specific type of problems. We also assume we have a training set of problems with answers.
The idea is to generate a set of agentic workflows to try to solve this type of problems and to use genetic algorithms to evolve the workflows towards increase ability to solve the problems in the training set.

# Development

## How to build a workflow

See examples/tourist_attractions.py

```
# Create a workflow
workflow = Workflow()

# Create node example
node = WebSearchNode("web search node", brave_search_api_key, number_of_results, cached)

# Add node
workflow.add_node("node id", node)

# Connect nodes
workflow.connect(from_node_id, to_node_id)

# Validate the workflow
workflow_validator = WorkflowValidator(workflow)
valid = workflow_validator.validate_graph()

# Run the workflow
result = workflow.run(workflow_input)

# Save workflow execution traces
workflow.save_trace_report("workflow_report.html")
```

## How to add a new node

See nodes/passthrough_node.py

Create a class in nodes folder.
Derive from abstract_node.py

Override:
- start_impl() (called when node is initialized, called once)
- run_impl() (this is where processing is done, can be called multiple times if there are multiple input nodes, returns the output)
- stop_impl() (called at the end for cleanup, returns the final result)
- get_cache_key() (if you want to modify the cache key, ex. add the input and state as cache key)

In constructor call:
- super().__init__(node_id, cached)


## How to add a new worker

See workers/reports/local_file_writer_worker.py

LLM workers should derive from workers/llm/ai_worker.py

