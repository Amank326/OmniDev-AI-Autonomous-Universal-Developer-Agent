"""
Phase 11: NLP Workflow Generator
Generate workflows from natural language descriptions using intent and entity extraction
"""

import logging
import json
import uuid
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """Extracted intent from user input"""
    type: str  # "send", "create", "update", "query", "trigger", etc
    confidence: float
    context: Dict[str, Any]


@dataclass
class Entity:
    """Extracted entity from user input"""
    type: str  # "action", "condition", "target", "schedule", etc
    value: str
    confidence: float


class NLPWorkflowGenerator:
    """
    Generate workflows from natural language descriptions
    Uses intent extraction and entity recognition to create DAGs
    """

    def __init__(self):
        # Action mapping: user phrases -> automation actions
        self.action_mappings = {
            "send email": "send_email",
            "send slack": "send_slack",
            "send sms": "send_sms",
            "create record": "create_record",
            "create entry": "create_record",
            "add to": "create_record",
            "update record": "update_record",
            "modify": "update_record",
            "delete record": "delete_record",
            "remove": "delete_record",
            "query": "query_data",
            "fetch": "query_data",
            "retrieve": "query_data",
            "export": "export_data",
            "call api": "call_api",
            "trigger workflow": "trigger_workflow",
            "log": "log_event",
            "create alert": "create_alert",
            "notify": "send_notification",
        }

        # Trigger mapping
        self.trigger_mappings = {
            "when": "event",
            "on": "event",
            "if": "condition",
            "every": "time",
            "daily": "time",
            "weekly": "time",
            "monthly": "time",
            "hourly": "time",
            "schedule": "time",
        }

        # Connector words that indicate sequencing
        self.connectors = [
            "then", "and", "next", "after", "followed by", "afterward",
            ",", "subsequently", "later"
        ]

    def generate_workflow_from_description(self, description: str) -> Dict[str, Any]:
        """
        Generate a complete workflow from natural language description
        Returns a workflow DAG structure
        """
        logger.info(f"Generating workflow from: {description}")

        # Step 1: Extract components
        components = self._parse_description(description)

        # Step 2: Extract intents and entities
        intents = self._extract_intents(components)
        entities = self._extract_entities(components, intents)

        # Step 3: Build workflow structure
        nodes = self._build_workflow_nodes(intents, entities)
        edges = self._build_workflow_edges(nodes, components)

        # Step 4: Validate and refine
        workflow = {
            "id": str(uuid.uuid4()),
            "name": self._generate_workflow_name(description),
            "description": description,
            "nodes": nodes,
            "edges": edges,
            "variables": {},
            "generated_from_nlp": True,
            "confidence": self._calculate_confidence(intents),
        }

        logger.info(f"Generated workflow with {len(nodes)} nodes and {len(edges)} edges")
        return workflow

    def _parse_description(self, text: str) -> List[str]:
        """Split description into logical components"""
        # Replace connector words with delimiters
        for connector in self.connectors:
            text = text.replace(connector, "|")

        # Split by the delimiter
        components = [c.strip() for c in text.split("|") if c.strip()]
        return components

    def _extract_intents(self, components: List[str]) -> List[Intent]:
        """Extract intents from text components"""
        intents = []

        for component in components:
            component_lower = component.lower()

            # Determine intent type
            intent_type = "action"
            confidence = 0.7

            # Check for trigger keywords
            for trigger_phrase, trigger_type in self.trigger_mappings.items():
                if trigger_phrase in component_lower:
                    intent_type = trigger_type
                    confidence = 0.9
                    break

            intent = Intent(
                type=intent_type,
                confidence=confidence,
                context={"text": component}
            )

            intents.append(intent)

        return intents

    def _extract_entities(self, components: List[str], intents: List[Intent]) -> List[Entity]:
        """Extract entities (actions, targets, conditions) from components"""
        entities = []

        for component in components:
            component_lower = component.lower()

            # Find matching action
            for phrase, action in self.action_mappings.items():
                if phrase in component_lower:
                    entity = Entity(
                        type="action",
                        value=action,
                        confidence=0.85
                    )
                    entities.append(entity)
                    break

            # Extract specific targets
            targets = self._extract_targets(component)
            for target in targets:
                entity = Entity(
                    type="target",
                    value=target,
                    confidence=0.7
                )
                entities.append(entity)

        return entities

    def _extract_targets(self, text: str) -> List[str]:
        """Extract action targets (email, Slack, record types, etc)"""
        targets = []

        target_keywords = {
            "email": ["email", "mail", "inbox"],
            "slack": ["slack", "channel"],
            "sms": ["sms", "text", "message"],
            "crm": ["crm", "salesforce"],
            "database": ["database", "db", "table", "record"],
            "api": ["api", "endpoint", "service"],
        }

        text_lower = text.lower()
        for target, keywords in target_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    targets.append(target)
                    break

        return targets

    def _build_workflow_nodes(self, intents: List[Intent], entities: List[Entity]) -> Dict:
        """Build workflow nodes from extracted intents and entities"""
        nodes = {}
        node_counter = 0

        # Create START node
        start_node_id = f"node_{node_counter}"
        nodes[start_node_id] = {
            "id": start_node_id,
            "name": "Start",
            "type": "start",
            "config": {}
        }
        node_counter += 1

        # Create nodes for each action
        for entity in entities:
            if entity.type == "action":
                node_id = f"node_{node_counter}"
                nodes[node_id] = {
                    "id": node_id,
                    "name": entity.value.replace("_", " ").title(),
                    "type": "action",
                    "action_type": entity.value,
                    "config": {
                        "confidence": entity.confidence
                    }
                }
                node_counter += 1

        # Create END node
        end_node_id = f"node_{node_counter}"
        nodes[end_node_id] = {
            "id": end_node_id,
            "name": "End",
            "type": "end",
            "config": {}
        }

        return nodes

    def _build_workflow_edges(self, nodes: Dict, components: List[str]) -> List[Dict]:
        """Build edges between nodes based on sequence"""
        edges = []
        node_ids = list(nodes.keys())

        # Connect nodes in sequence
        for i in range(len(node_ids) - 1):
            edge = {
                "source": node_ids[i],
                "target": node_ids[i + 1],
                "label": "next"
            }
            edges.append(edge)

        return edges

    def _generate_workflow_name(self, description: str) -> str:
        """Generate a descriptive workflow name"""
        # Take first 50 chars and capitalize
        words = description.split()[:5]
        name = " ".join(words).title()
        return name if name else "Generated Workflow"

    def _calculate_confidence(self, intents: List[Intent]) -> float:
        """Calculate overall workflow confidence"""
        if not intents:
            return 0.0

        avg_confidence = sum(i.confidence for i in intents) / len(intents)
        return round(avg_confidence, 2)

    def refine_workflow(self, workflow: Dict, feedback: Dict) -> Dict:
        """
        Refine generated workflow based on user feedback
        Feedback format: {"remove_nodes": [...], "add_nodes": [...], "reorder": [...]}
        """
        refined = workflow.copy()

        # Remove nodes
        for node_id in feedback.get("remove_nodes", []):
            if node_id in refined["nodes"]:
                del refined["nodes"][node_id]
                # Remove edges connected to this node
                refined["edges"] = [
                    e for e in refined["edges"]
                    if e["source"] != node_id and e["target"] != node_id
                ]

        # Add nodes
        for i, node_config in enumerate(feedback.get("add_nodes", [])):
            node_id = f"node_added_{i}"
            refined["nodes"][node_id] = {
                **node_config,
                "id": node_id
            }

        # Reorder nodes
        if feedback.get("reorder"):
            # Rebuild edges based on new order
            ordered_ids = feedback["reorder"]
            refined["edges"] = []
            for i in range(len(ordered_ids) - 1):
                refined["edges"].append({
                    "source": ordered_ids[i],
                    "target": ordered_ids[i + 1]
                })

        return refined

    def suggest_improvements(self, workflow: Dict) -> List[str]:
        """Suggest improvements to generated workflow"""
        suggestions = []

        nodes = workflow.get("nodes", {})
        edges = workflow.get("edges", [])

        # Check for isolated nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge["source"])
            connected_nodes.add(edge["target"])

        isolated = set(nodes.keys()) - connected_nodes
        if isolated:
            suggestions.append(f"Remove isolated nodes: {isolated}")

        # Check for missing error handlers
        action_nodes = [n for n in nodes.values() if n.get("type") == "action"]
        if action_nodes:
            suggestions.append("Consider adding error handling nodes for critical actions")

        # Check for long sequential chains that could be parallelized
        if len(edges) > 5:
            suggestions.append("Consider parallelizing independent action sequences")

        # Check for missing conditions
        if len(action_nodes) > 2:
            suggestions.append("Consider adding decision nodes for conditional execution")

        return suggestions

    def validate_generated_workflow(self, workflow: Dict) -> Tuple[bool, List[str]]:
        """Validate the generated workflow"""
        errors = []

        nodes = workflow.get("nodes", {})
        edges = workflow.get("edges", [])

        # Check for start and end nodes
        start_nodes = [n for n in nodes.values() if n.get("type") == "start"]
        end_nodes = [n for n in nodes.values() if n.get("type") == "end"]

        if not start_nodes:
            errors.append("Missing START node")
        if not end_nodes:
            errors.append("Missing END node")

        # Check edges reference valid nodes
        for edge in edges:
            if edge["source"] not in nodes:
                errors.append(f"Edge references invalid source: {edge['source']}")
            if edge["target"] not in nodes:
                errors.append(f"Edge references invalid target: {edge['target']}")

        # Check for cycles
        has_cycle, cycle_path = self._detect_cycle_in_workflow(nodes, edges)
        if has_cycle:
            errors.append(f"Workflow contains cycle: {cycle_path}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def _detect_cycle_in_workflow(self, nodes: Dict, edges: List) -> Tuple[bool, List]:
        """Detect cycles in workflow graph"""
        from collections import defaultdict, deque

        graph = defaultdict(list)
        for edge in edges:
            graph[edge["source"]].append(edge["target"])

        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node_id in nodes:
            if node_id not in visited:
                if dfs(node_id, []):
                    return True, []

        return False, []

    def batch_generate_workflows(self, descriptions: List[str]) -> List[Dict]:
        """Generate multiple workflows from descriptions"""
        workflows = []
        for description in descriptions:
            try:
                workflow = self.generate_workflow_from_description(description)
                workflows.append(workflow)
            except Exception as e:
                logger.error(f"Failed to generate workflow from '{description}': {e}")
                continue

        return workflows
