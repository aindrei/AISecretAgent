from abc import ABC, abstractmethod
from state.nodes_cache import NodesCache
from ..workflow_tracer import WorkflowTracer

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

    def start(self, tracer: WorkflowTracer):
        self.tracer = tracer
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