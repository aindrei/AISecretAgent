from typing import Dict, Any, List
from datetime import datetime
import logging
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class WorkerExecution:
    worker_name: str
    worker_input: Any
    worker_output: Any
    worker_prompt: str
    worker_system_prompt: str
    execution_time: datetime

@dataclass
class NodeTrace:
    node_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    input_data: List[Any] = field(default_factory=list) # a node can have multiple inputs and be called multiple times
    output_data: Optional[Any] = None
    worker_executions: List[WorkerExecution] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.worker_executions is None:
            self.worker_executions = []

class WorkflowTracer:
    """Traces execution details for workflow nodes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.traces: Dict[str, NodeTrace] = {}

    def start_trace(self, node_id: str) -> None:
        """Start tracing a node's execution"""
        self.traces[node_id] = NodeTrace(
            node_id=node_id,
            start_time=datetime.now()
        )
        self.logger.debug(f"Started tracing node {node_id}")

    def stop_trace(self, node_id: str) -> None:
        """Record the node's output and end time"""
        if node_id in self.traces:
            self.traces[node_id].end_time = datetime.now()
            self.logger.debug(f"Completed tracing node {node_id}")
        else:
            self.logger.warning(f"Tried to end trace for unknown node {node_id}")

    def record_input(self, node_id: str, input_text: str) -> None:
        """Record the input data for a node"""
        if node_id in self.traces:
            self.traces[node_id].input_data.append(input_text)
            self.logger.debug(f"Recorded input for node {node_id}")
        else:
            self.logger.warning(f"Tried to record input for unknown node {node_id}")

    def record_output(self, node_id: str, output_text: str, cache_hit: bool = False) -> None:
        """Record the output data for a node"""
        if node_id in self.traces:
            self.traces[node_id].output_data = output_text
            self.traces[node_id].cache_hit = cache_hit
            self.logger.debug(f"Recorded output for node {node_id}")
        else:
            self.logger.warning(f"Tried to record output for unknown node {node_id}")

    def log_worker(self, node_id: str, worker_name: str, worker_input: Any, worker_output: Any, prompt: str = None, system_prompt: str = None) -> None:
        """Log details about a worker execution for the node"""
        if node_id in self.traces:
            worker_execution = WorkerExecution(
                worker_name=worker_name,
                worker_input=worker_input,
                worker_output=worker_output,
                worker_prompt=prompt,
                worker_system_prompt=system_prompt,
                execution_time=datetime.now()
            )
            self.traces[node_id].worker_executions.append(worker_execution)
            self.logger.debug(f"Logged worker {worker_name} details for node {node_id}")
        else:
            self.logger.warning(f"Tried to log worker for unknown node {node_id}")

    def log_error(self, node_id: str, error: str) -> None:
        """Log an error that occurred during node execution"""
        if node_id in self.traces:
            self.traces[node_id].error = error
            self.logger.error(f"Error in node {node_id}: {error}")
        else:
            self.logger.warning(f"Tried to log error for unknown node {node_id}")

    def get_node_trace(self, node_id: str) -> Optional[NodeTrace]:
        """Get the trace data for a specific node"""
        return self.traces.get(node_id)

    def get_execution_time(self, node_id: str) -> Optional[float]:
        """Get execution time in seconds for a node"""
        trace = self.traces.get(node_id)
        if trace and trace.end_time:
            return (trace.end_time - trace.start_time).total_seconds()
        return None

    def get_all_traces(self) -> Dict[str, NodeTrace]:
        """Get all trace data"""
        return self.traces
    
    # Generate a report of the workflow execution in HTML format with details of each node and workers
    def generate_report_as_html(self) -> str:
        """Generate a report of the workflow execution"""

        truncate_size = 2000 # truncate output data if it exceeds this size
        css = """
            <style>
                .hidden { display: none; }
                .show-more { color: blue; cursor: pointer; text-decoration: underline; }
            </style>
            """
        
        javascript = """
            <script>
                function toggleOutput(id) {
                    console.log(id);
                    const shortText = document.getElementById('short-' + id);
                    console.log(shortText);
                    const fullText = document.getElementById('full-' + id);
                    console.log(fullText);
                    const link = document.getElementById('link-' + id);
                    console.log(link);
                    
                    if (fullText.classList.contains('hidden')) {
                        shortText.classList.add('hidden');
                        fullText.classList.remove('hidden');
                        link.textContent = 'Show Less';
                    } else {
                        shortText.classList.remove('hidden');
                        fullText.classList.add('hidden');
                        link.textContent = 'Show More';
                    }
                }
            </script>
            """

        report = f"<html><head><title>Workflow Execution Report</title>{css}{javascript}</head><body>"
        node_index = 0
        for node_id, trace in self.traces.items():
            report += f"<h2>Node: {node_id}</h2>"
            report += f"<p>Start Time: {trace.start_time}</p>"
            if trace.end_time:
                report += f"<p>End Time: {trace.end_time}</p>"
                report += f"<p>Execution Time: {self.get_execution_time(node_id)} seconds</p>"
            if trace.input_data:
                report += "<h3>Input Data:</h3>"
                for i, input_data in enumerate(trace.input_data):
                    report += f"<p>Input {i + 1}:</p>"
                    element_suffix = f"input-{node_index}-{i}"
                    input_html = self._create_expandable_text(element_suffix, input_data, truncate_size)
                    report += input_html
            if trace.output_data:
                report += f"<h3>Output Data: (cache hit={trace.cache_hit}) </h3>"
                output = trace.output_data
                element_suffix = f"output-{node_index}"
                output_html = self._create_expandable_text(element_suffix, output, truncate_size)
                report += output_html
            if trace.worker_executions:
                report += "<h3>Worker Executions:</h3>"
                for i, worker_execution in enumerate(trace.worker_executions):
                    report += f"<p>Worker {i + 1}: {worker_execution.worker_name}</p>"
                    report += f"<p>Input:</p>"
                    input_element_suffix = f"worker-input-{node_index}-{i}"
                    report += self._create_expandable_text(input_element_suffix, worker_execution.worker_input, truncate_size)
                    
                    report += f"<p>Output:</p>"
                    output_element_suffix = f"worker-output-{node_index}-{i}"
                    report += self._create_expandable_text(output_element_suffix, worker_execution.worker_output, truncate_size)

                    if worker_execution.worker_prompt:
                        report += f"<p>Prompt:</p>"
                        prompt_element_suffix = f"worker-prompt-{node_index}-{i}"
                        report += self._create_expandable_text(prompt_element_suffix, worker_execution.worker_prompt, truncate_size)

                    if worker_execution.worker_system_prompt:
                        report += f"<p>System Prompt:</p>"
                        system_prompt_element_suffix = f"worker-system-prompt-{node_index}-{i}"
                        report += self._create_expandable_text(system_prompt_element_suffix, worker_execution.worker_system_prompt, truncate_size)

                    report += f"<p>Execution Time: {worker_execution.execution_time}</p>"
            if trace.error:
                report += f"<h3>Error:</h3><p>{trace.error}</p>"
            node_index += 1
        report += "</body></html>"
        return report
    
    # Creates HTML to show the text fully if it is smaller than truncate_size, 
    # or truncated and with a "Show More" link if it is larger
    def _create_expandable_text(self, element_suffix: str, text: str, truncate_size: int = 1000) -> str:
        """Create expandable text for HTML display"""
        if len(text) > truncate_size:
            return f"""
                <div id="short-{element_suffix}">{text[:truncate_size]}...</div>
                <div id="full-{element_suffix}" class="hidden">{text}</div>
                <span class="show-more" id="link-{element_suffix}" 
                    onclick="toggleOutput('{element_suffix}')">Show More (total {len(text)} chars)</span>
            """
        else:
            return f"<p>{text}</p>"