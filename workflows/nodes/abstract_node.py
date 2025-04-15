from abc import ABC, abstractmethod
from typing import Optional
from state.nodes_cache import NodesCache
from workflows.workflow_tracer import WorkflowTracer

# Silent tracer class
class SilentTracer:
    def start_trace(self, node_id: str) -> None:
        pass

    def stop_trace(self, node_id: str) -> None:
        pass

    def record_input(self, node_id: str, input_text: str) -> None:
        pass

    def record_output(self, node_id: str, output_text: str, cache_hit: bool = False) -> None:
        pass

    def log_worker(self, node_id: str, worker_name: str, worker_input, worker_output, prompt: str = None, system_prompt: str = None) -> None:
        pass

    def log_error(self, node_id: str, error: str) -> None:
        pass

    def get_node_trace(self, node_id: str):
        return None
    
    def get_execution_time(self, node_id: str) -> Optional[float]:
        return None

    def get_all_traces(self):
        return {}

    def generate_report_as_html(self) -> str:
        return ""

# Abstract class for a node in a workflow. All nodes should derive from this class.
class AbstractNode(ABC):

    @classmethod
    def init_output_cache(cls):
        NodesCache.init_database("database.db")

    def __init__(self, node_id: str, cache_enabled: bool = False):
        AbstractNode.init_output_cache()
        self.node_id = node_id
        self.cache_enabled = cache_enabled
        self.cache_hit = False
        self.result = None # The result of the node to be filled by the run() method
        self.tracer = None

    def start(self, tracer: WorkflowTracer = None):
        self.tracer = tracer if tracer is not None else SilentTracer()
        self.tracer.start_trace(self.node_id)
        self.start_impl()
        pass

    @abstractmethod
    def start_impl(self):
        pass

    def run(self, input_text: str) -> str:
        self.tracer.record_input(self.node_id, input_text)
        if self.cache_enabled:
            cache_key = self.get_cache_key()
            cached_result = NodesCache.get_output(cache_key, input_text)
            if cached_result is not None:
                self.cache_hit =True
                # Store the result in the node so that the stop_impl method can return it
                self.result = cached_result
                return cached_result

        node_output = self.run_impl(input_text)

        if self.cache_enabled:
            cache_key = self.get_cache_key()
            NodesCache.set_output(cache_key, input_text, node_output)

        return node_output

    @abstractmethod
    def run_impl(self, input_text: str) -> str:
        pass

    # Use this to clean up the node
    def stop(self):
        output = self.stop_impl()
        self.tracer.record_output(self.node_id, output, self.cache_hit)
        self.tracer.stop_trace(self.node_id)

    # Implementations need to return the output of the node
    @abstractmethod
    def stop_impl(self) -> str:
        pass

    # Override this to change the cache key, ex. include node context
    def get_cache_key(self) -> str:
        return self.node_id