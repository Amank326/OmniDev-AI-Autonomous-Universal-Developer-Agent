"""
Dependency Resolver Service for OmniDev AI
Resolves task dependencies, detects cycles, and optimizes execution order
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import deque, defaultdict


class DependencyType(str, Enum):
    """Types of task dependencies"""
    MUST_COMPLETE = "must_complete"  # Dependent task waits for completion
    SHOULD_COMPLETE = "should_complete"  # Dependent task can proceed if failed
    PARALLEL = "parallel"  # Can execute in parallel
    DATA_FLOW = "data_flow"  # Uses output of dependent task
    EVENT_DRIVEN = "event_driven"  # Triggered by event from dependent
    RESOURCE_LOCK = "resource_lock"  # Shares resource with dependent


@dataclass
class DependencyGraph:
    """Directed acyclic graph for task dependencies"""
    nodes: Set[str]
    edges: Dict[str, List[str]]  # task_id -> list of dependent task_ids
    reverse_edges: Dict[str, List[str]]  # task_id -> list of dependency task_ids
    weights: Dict[Tuple[str, str], float]  # (from, to) -> weight


class DependencyResolverService:
    """Service for resolving and optimizing task dependencies"""

    def __init__(self):
        """Initialize dependency resolver"""
        self.graphs: Dict[str, DependencyGraph] = {}  # workspace_id -> graph
        self.cycle_cache: Dict[str, bool] = {}  # task_id -> has_cycle
        self.execution_order_cache: Dict[str, List[str]] = {}  # workspace_id -> ordered list

    def create_graph(self, workspace_id: str) -> DependencyGraph:
        """Create new dependency graph for workspace"""
        graph = DependencyGraph(
            nodes=set(),
            edges=defaultdict(list),
            reverse_edges=defaultdict(list),
            weights={},
        )
        self.graphs[workspace_id] = graph
        return graph

    def get_graph(self, workspace_id: str) -> Optional[DependencyGraph]:
        """Get dependency graph for workspace"""
        if workspace_id not in self.graphs:
            self.create_graph(workspace_id)
        return self.graphs[workspace_id]

    def add_task_node(self, workspace_id: str, task_id: str) -> bool:
        """Add task as node in graph"""
        graph = self.get_graph(workspace_id)
        if graph:
            graph.nodes.add(task_id)
            if task_id not in graph.edges:
                graph.edges[task_id] = []
            if task_id not in graph.reverse_edges:
                graph.reverse_edges[task_id] = []
            return True
        return False

    def add_dependency(
        self,
        workspace_id: str,
        task_id: str,
        depends_on_task_id: str,
        dependency_type: DependencyType = DependencyType.MUST_COMPLETE,
        weight: float = 1.0,
    ) -> bool:
        """
        Add dependency between tasks
        
        Args:
            workspace_id: Workspace scope
            task_id: Task that depends on another
            depends_on_task_id: Task that must complete first
            dependency_type: Type of dependency
            weight: Priority weight for ordering
            
        Returns:
            True if successful
        """
        graph = self.get_graph(workspace_id)
        if not graph:
            return False
        
        # Ensure both tasks exist as nodes
        self.add_task_node(workspace_id, task_id)
        self.add_task_node(workspace_id, depends_on_task_id)
        
        # Check for cycles before adding
        if self._would_create_cycle(graph, depends_on_task_id, task_id):
            return False
        
        # Add edge (from depends_on to task, so depends_on must complete first)
        if task_id not in graph.edges[depends_on_task_id]:
            graph.edges[depends_on_task_id].append(task_id)
        
        if depends_on_task_id not in graph.reverse_edges[task_id]:
            graph.reverse_edges[task_id].append(depends_on_task_id)
        
        # Store weight for priority
        graph.weights[(depends_on_task_id, task_id)] = weight
        
        # Invalidate cache
        if workspace_id in self.execution_order_cache:
            del self.execution_order_cache[workspace_id]
        
        return True

    def remove_dependency(
        self,
        workspace_id: str,
        task_id: str,
        depends_on_task_id: str,
    ) -> bool:
        """Remove dependency between tasks"""
        graph = self.get_graph(workspace_id)
        if not graph:
            return False
        
        try:
            if task_id in graph.edges.get(depends_on_task_id, []):
                graph.edges[depends_on_task_id].remove(task_id)
            
            if depends_on_task_id in graph.reverse_edges.get(task_id, []):
                graph.reverse_edges[task_id].remove(depends_on_task_id)
            
            # Remove weight
            key = (depends_on_task_id, task_id)
            if key in graph.weights:
                del graph.weights[key]
            
            # Invalidate cache
            if workspace_id in self.execution_order_cache:
                del self.execution_order_cache[workspace_id]
            
            return True
        except (KeyError, ValueError):
            return False

    def get_dependencies(
        self,
        workspace_id: str,
        task_id: str,
    ) -> List[str]:
        """Get all tasks that a task depends on"""
        graph = self.get_graph(workspace_id)
        return graph.reverse_edges.get(task_id, []) if graph else []

    def get_dependents(
        self,
        workspace_id: str,
        task_id: str,
    ) -> List[str]:
        """Get all tasks that depend on this task"""
        graph = self.get_graph(workspace_id)
        return graph.edges.get(task_id, []) if graph else []

    def get_all_dependencies_recursive(
        self,
        workspace_id: str,
        task_id: str,
    ) -> Set[str]:
        """Get all transitive dependencies"""
        graph = self.get_graph(workspace_id)
        if not graph:
            return set()
        
        visited = set()
        stack = [task_id]
        
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            
            for dep in graph.reverse_edges.get(current, []):
                if dep not in visited:
                    stack.append(dep)
        
        visited.discard(task_id)
        return visited

    def get_all_dependents_recursive(
        self,
        workspace_id: str,
        task_id: str,
    ) -> Set[str]:
        """Get all tasks transitively depending on this task"""
        graph = self.get_graph(workspace_id)
        if not graph:
            return set()
        
        visited = set()
        stack = [task_id]
        
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            
            for dep in graph.edges.get(current, []):
                if dep not in visited:
                    stack.append(dep)
        
        visited.discard(task_id)
        return visited

    def has_cycle(self, workspace_id: str, task_id: str) -> bool:
        """Check if task is part of dependency cycle"""
        if task_id in self.cycle_cache:
            return self.cycle_cache[task_id]
        
        graph = self.get_graph(workspace_id)
        if not graph:
            return False
        
        visited = set()
        rec_stack = set()
        has_cycle = self._dfs_cycle_check(graph, task_id, visited, rec_stack)
        self.cycle_cache[task_id] = has_cycle
        
        return has_cycle

    def _dfs_cycle_check(
        self,
        graph: DependencyGraph,
        node: str,
        visited: Set[str],
        rec_stack: Set[str],
    ) -> bool:
        """DFS to detect cycles"""
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.reverse_edges.get(node, []):
            if neighbor not in visited:
                if self._dfs_cycle_check(graph, neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node)
        return False

    def find_all_cycles(self, workspace_id: str) -> List[List[str]]:
        """Find all dependency cycles in graph"""
        graph = self.get_graph(workspace_id)
        if not graph:
            return []
        
        cycles = []
        visited = set()
        
        for node in graph.nodes:
            if node not in visited:
                rec_stack = set()
                path = []
                if self._find_cycles_dfs(graph, node, visited, rec_stack, path, cycles):
                    pass
        
        return cycles

    def _find_cycles_dfs(
        self,
        graph: DependencyGraph,
        node: str,
        visited: Set[str],
        rec_stack: Set[str],
        path: List[str],
        cycles: List[List[str]],
    ) -> bool:
        """DFS to find cycles"""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.reverse_edges.get(node, []):
            if neighbor not in visited:
                if self._find_cycles_dfs(graph, neighbor, visited, rec_stack, path, cycles):
                    return True
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                if cycle not in cycles:
                    cycles.append(cycle)
                return True
        
        rec_stack.remove(node)
        path.pop()
        return False

    def _would_create_cycle(
        self,
        graph: DependencyGraph,
        from_node: str,
        to_node: str,
    ) -> bool:
        """Check if adding edge would create cycle"""
        # If we can reach `from_node` from `to_node`, adding this edge creates cycle
        visited = set()
        stack = [to_node]
        
        while stack:
            current = stack.pop()
            if current == from_node:
                return True
            
            if current in visited:
                continue
            visited.add(current)
            
            for neighbor in graph.reverse_edges.get(current, []):
                if neighbor not in visited:
                    stack.append(neighbor)
        
        return False

    def get_execution_order(
        self,
        workspace_id: str,
    ) -> List[str]:
        """
        Get optimal task execution order using topological sort
        Returns empty list if cycles exist
        
        Args:
            workspace_id: Workspace scope
            
        Returns:
            List of task IDs in execution order
        """
        if workspace_id in self.execution_order_cache:
            return self.execution_order_cache[workspace_id]
        
        graph = self.get_graph(workspace_id)
        if not graph or not graph.nodes:
            return []
        
        # Check for cycles
        if self.find_all_cycles(workspace_id):
            return []
        
        # Topological sort using Kahn's algorithm
        in_degree = {node: len(graph.reverse_edges.get(node, [])) for node in graph.nodes}
        queue = deque([node for node in graph.nodes if in_degree[node] == 0])
        order = []
        
        while queue:
            node = queue.popleft()
            order.append(node)
            
            for neighbor in graph.edges.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Cache result
        self.execution_order_cache[workspace_id] = order
        return order

    def get_parallelizable_groups(
        self,
        workspace_id: str,
    ) -> List[List[str]]:
        """
        Get groups of tasks that can execute in parallel
        Each group must complete before next group starts
        
        Args:
            workspace_id: Workspace scope
            
        Returns:
            List of task groups
        """
        graph = self.get_graph(workspace_id)
        if not graph or not graph.nodes:
            return []
        
        groups = []
        processed = set()
        remaining = set(graph.nodes)
        
        while remaining:
            # Find tasks with no unprocessed dependencies
            current_group = []
            for task in remaining:
                deps = graph.reverse_edges.get(task, [])
                if all(dep in processed for dep in deps):
                    current_group.append(task)
            
            if not current_group:
                # Cycle detected or all remaining have unmet deps
                break
            
            groups.append(current_group)
            processed.update(current_group)
            remaining -= set(current_group)
        
        return groups

    def get_critical_path(
        self,
        workspace_id: str,
        task_durations: Optional[Dict[str, float]] = None,
    ) -> Tuple[List[str], float]:
        """
        Get critical path (longest execution path) through dependencies
        
        Args:
            workspace_id: Workspace scope
            task_durations: Dict mapping task_id to duration in seconds
            
        Returns:
            Tuple of (critical path task list, total duration)
        """
        graph = self.get_graph(workspace_id)
        if not graph or not graph.nodes:
            return [], 0.0
        
        if task_durations is None:
            task_durations = {task: 1.0 for task in graph.nodes}
        
        # Use dynamic programming for longest path in DAG
        memo = {}
        max_path = []
        max_duration = 0.0
        
        def longest_path_from(node: str) -> Tuple[List[str], float]:
            if node in memo:
                return memo[node]
            
            duration = task_durations.get(node, 1.0)
            best_path = [node]
            best_duration = duration
            
            for dependent in graph.edges.get(node, []):
                sub_path, sub_duration = longest_path_from(dependent)
                total_duration = duration + sub_duration
                
                if total_duration > best_duration:
                    best_duration = total_duration
                    best_path = [node] + sub_path
            
            memo[node] = (best_path, best_duration)
            return best_path, best_duration
        
        # Find longest path starting from any root node
        for task in graph.nodes:
            if not graph.reverse_edges.get(task, []):  # Root node
                path, duration = longest_path_from(task)
                if duration > max_duration:
                    max_duration = duration
                    max_path = path
        
        return max_path, max_duration

    def get_impact_analysis(
        self,
        workspace_id: str,
        task_id: str,
    ) -> Dict:
        """
        Analyze impact of task change/failure
        
        Args:
            workspace_id: Workspace scope
            task_id: Task to analyze
            
        Returns:
            Impact analysis
        """
        graph = self.get_graph(workspace_id)
        if not graph:
            return {}
        
        dependencies = self.get_all_dependencies_recursive(workspace_id, task_id)
        dependents = self.get_all_dependents_recursive(workspace_id, task_id)
        
        return {
            "task_id": task_id,
            "dependencies_count": len(dependencies),
            "dependencies": list(dependencies),
            "dependents_count": len(dependents),
            "dependents": list(dependents),
            "total_impact": len(dependencies) + len(dependents),
            "is_critical": len(dependents) > 0 and len(dependencies) > 0,
        }

    def validate_graph(self, workspace_id: str) -> Tuple[bool, List[str]]:
        """
        Validate graph integrity
        
        Args:
            workspace_id: Workspace scope
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        graph = self.get_graph(workspace_id)
        if not graph:
            return False, ["Graph not found"]
        
        issues = []
        
        # Check for cycles
        cycles = self.find_all_cycles(workspace_id)
        if cycles:
            issues.append(f"Found {len(cycles)} cycles: {cycles}")
        
        # Check for orphaned nodes
        for node in graph.nodes:
            if not graph.edges.get(node, []) and not graph.reverse_edges.get(node, []):
                issues.append(f"Orphaned node: {node}")
        
        # Check for invalid edges
        for node in graph.nodes:
            edges = graph.edges.get(node, [])
            reverse_edges = graph.reverse_edges.get(node, [])
            
            for edge in edges:
                if edge not in graph.nodes:
                    issues.append(f"Invalid edge target: {node} -> {edge}")
            
            for reverse_edge in reverse_edges:
                if reverse_edge not in graph.nodes:
                    issues.append(f"Invalid reverse edge: {reverse_edge} -> {node}")
        
        return len(issues) == 0, issues

    def optimize_execution_plan(
        self,
        workspace_id: str,
        task_durations: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """
        Generate optimized execution plan
        
        Args:
            workspace_id: Workspace scope
            task_durations: Task duration estimates
            
        Returns:
            Execution plan with groups and critical path
        """
        is_valid, issues = self.validate_graph(workspace_id)
        
        if not is_valid:
            return {
                "valid": False,
                "issues": issues,
            }
        
        groups = self.get_parallelizable_groups(workspace_id)
        critical_path, critical_duration = self.get_critical_path(workspace_id, task_durations)
        
        return {
            "valid": True,
            "parallelizable_groups": groups,
            "group_count": len(groups),
            "critical_path": critical_path,
            "critical_duration_seconds": critical_duration,
            "can_parallelize": len(groups) > 1,
        }

    def export_graph(self, workspace_id: str) -> Dict:
        """Export graph as dictionary"""
        graph = self.get_graph(workspace_id)
        if not graph:
            return {}
        
        return {
            "nodes": list(graph.nodes),
            "edges": dict(graph.edges),
            "reverse_edges": dict(graph.reverse_edges),
            "weights": {f"{k[0]}->{k[1]}": v for k, v in graph.weights.items()},
        }
