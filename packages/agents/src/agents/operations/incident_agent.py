"""
Incident Agent

Generates incident response playbooks, escalation procedures,
and post-mortem templates for effective incident management.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
import json
import yaml

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.base_agent import BaseOpenForgeAgent
from agent_framework.state_management import (
    OperationsState,
    Decision,
    Message,
    add_decision,
    mark_for_review
)


INCIDENT_AGENT_SYSTEM_PROMPT = """You are an expert Incident Management Agent for Open Forge, an enterprise data platform.

Your role is to design comprehensive incident response procedures, escalation paths, and post-incident review processes.

## Your Capabilities:
1. Generate incident response playbooks for various failure scenarios
2. Design escalation procedures with clear triggers and contacts
3. Create post-mortem templates that encourage blameless retrospectives
4. Define incident severity classifications

## Incident Severity Levels:
- **SEV1 (Critical)**: Complete service outage, data loss, security breach
  - Response time: Immediate (< 15 min)
  - Escalation: Page on-call, notify leadership
- **SEV2 (High)**: Major functionality impaired, significant user impact
  - Response time: < 30 min
  - Escalation: Alert on-call team
- **SEV3 (Medium)**: Partial degradation, workaround available
  - Response time: < 2 hours
  - Escalation: Create ticket, notify team
- **SEV4 (Low)**: Minor issue, minimal user impact
  - Response time: Next business day
  - Escalation: Backlog for planning

## Playbook Structure Best Practices:
1. **Detection**: How was the incident detected? (Alerts, user reports, monitoring)
2. **Assessment**: Initial triage and severity classification
3. **Communication**: Who to notify and how
4. **Mitigation**: Immediate steps to reduce impact
5. **Investigation**: Root cause analysis steps
6. **Resolution**: Permanent fix implementation
7. **Recovery**: Service restoration verification
8. **Post-incident**: Documentation and review

## Escalation Matrix Components:
- Incident commander role assignment
- Technical lead responsibilities
- Communication lead duties
- Executive escalation triggers
- External communication (customers, regulators)

## Post-Mortem Guidelines (Blameless):
- Focus on system and process improvements
- Document timeline with timestamps
- Identify contributing factors (not blame)
- Define actionable remediation items
- Track metrics (MTTD, MTTR, impact)

Always output playbooks and procedures in clear, actionable formats.
Include checklists, decision trees, and contact templates.
"""


class IncidentAgent(BaseOpenForgeAgent):
    """
    Agent that generates incident response playbooks, escalation procedures,
    and post-mortem templates for effective incident management.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        memory: Optional[MemorySaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(llm, memory, config)

    @property
    def name(self) -> str:
        return "incident_agent"

    @property
    def description(self) -> str:
        return (
            "Generates incident response playbooks, escalation procedures, "
            "and post-mortem templates for effective incident management."
        )

    @property
    def required_inputs(self) -> List[str]:
        return ["system_architecture", "team_structure"]

    @property
    def output_keys(self) -> List[str]:
        return [
            "incident_playbooks",
            "escalation_procedures",
            "postmortem_templates",
            "severity_definitions"
        ]

    @property
    def state_class(self) -> Type[OperationsState]:
        return OperationsState

    def get_system_prompt(self) -> str:
        return INCIDENT_AGENT_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools for incident management configuration generation."""
        return []  # LLM-only agent for now

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for incident management generation."""
        graph = StateGraph(OperationsState)

        # Add nodes
        graph.add_node("analyze_failure_modes", self._analyze_failure_modes)
        graph.add_node("generate_playbooks", self._generate_playbooks)
        graph.add_node("generate_escalation_procedures", self._generate_escalation_procedures)
        graph.add_node("generate_postmortem_templates", self._generate_postmortem_templates)
        graph.add_node("validate_incident_configs", self._validate_incident_configs)

        # Define edges
        graph.set_entry_point("analyze_failure_modes")
        graph.add_edge("analyze_failure_modes", "generate_playbooks")
        graph.add_edge("generate_playbooks", "generate_escalation_procedures")
        graph.add_edge("generate_escalation_procedures", "generate_postmortem_templates")
        graph.add_edge("generate_postmortem_templates", "validate_incident_configs")
        graph.add_edge("validate_incident_configs", END)

        return graph

    async def _analyze_failure_modes(self, state: OperationsState) -> Dict[str, Any]:
        """Analyze system to identify potential failure modes."""
        context = state.get("agent_context", {})
        system_architecture = context.get("system_architecture", {})
        team_structure = context.get("team_structure", {})
        ontology_schema = context.get("ontology_schema", "")
        historical_incidents = context.get("historical_incidents", [])

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Analyze the system architecture to identify potential failure modes and incident scenarios.

System Architecture:
{json.dumps(system_architecture, indent=2) if isinstance(system_architecture, dict) else system_architecture}

Team Structure:
{json.dumps(team_structure, indent=2) if isinstance(team_structure, dict) else team_structure}

Ontology Schema (for entity-related failures):
{ontology_schema}

Historical Incidents (if available):
{json.dumps(historical_incidents, indent=2) if isinstance(historical_incidents, list) else historical_incidents}

Analyze and identify:

1. **Infrastructure Failures**:
   - Database failures (primary down, replication lag, corruption)
   - Network failures (connectivity loss, DNS issues, certificate expiry)
   - Compute failures (node failures, resource exhaustion)
   - Storage failures (disk full, I/O errors, data corruption)

2. **Application Failures**:
   - Service crashes (OOM, unhandled exceptions)
   - Performance degradation (slow queries, memory leaks)
   - Integration failures (API timeouts, auth failures)
   - Configuration errors (misconfigurations, secret issues)

3. **Data/Entity Failures** (based on ontology):
   - Data consistency violations
   - Entity relationship integrity issues
   - Data pipeline failures
   - Import/export failures

4. **Security Incidents**:
   - Authentication/authorization failures
   - Data breach scenarios
   - DDoS attacks
   - Credential compromise

5. **Business Logic Failures**:
   - Workflow failures
   - Business rule violations
   - SLA breaches

For each failure mode, provide:
- Failure name and description
- Likelihood (high/medium/low)
- Impact severity (SEV1-4)
- Detection methods
- Key symptoms

Output as a structured failure mode analysis.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="failure_analysis",
            description="Analyzed potential failure modes",
            confidence=0.85,
            reasoning="Identified infrastructure, application, data, and security failure scenarios"
        )

        return {
            "outputs": {"failure_mode_analysis": response.content},
            "decisions": [decision],
            "current_step": "analyze_failure_modes",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_playbooks(self, state: OperationsState) -> Dict[str, Any]:
        """Generate incident response playbooks for identified failure modes."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        failure_analysis = outputs.get("failure_mode_analysis", "")
        team_structure = context.get("team_structure", {})
        communication_channels = context.get("communication_channels", {
            "slack": "#incidents",
            "pagerduty": "default-service",
            "email": "incidents@company.com"
        })

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate incident response playbooks for the identified failure modes.

Failure Mode Analysis:
{failure_analysis}

Team Structure:
{json.dumps(team_structure, indent=2) if isinstance(team_structure, dict) else team_structure}

Communication Channels:
{json.dumps(communication_channels, indent=2)}

For each major failure category, create a detailed playbook:

```yaml
playbook:
  name: "Playbook Name"
  id: "PLB-XXX"
  version: "1.0"
  last_updated: "YYYY-MM-DD"
  owner: "Team Name"

  applicable_to:
    - failure-mode-1
    - failure-mode-2

  severity_guidance:
    sev1_criteria:
      - "Complete service outage"
    sev2_criteria:
      - "Major feature unavailable"
    sev3_criteria:
      - "Degraded performance"

  detection:
    alerts:
      - name: "Alert Name"
        source: "prometheus/datadog/etc"
        threshold: "description"
    manual_checks:
      - "Check item 1"
      - "Check item 2"

  initial_response:
    time_limit: "X minutes"
    steps:
      - order: 1
        action: "Action description"
        responsible: "Role"
        automation: "script/runbook link if available"

  triage:
    questions:
      - "What is the user impact?"
      - "When did this start?"
      - "What changed recently?"
    assessment_checklist:
      - item: "Check system health dashboard"
        severity_impact: "Determines if SEV1 or SEV2"

  mitigation:
    immediate_actions:
      - action: "Action 1"
        command: "kubectl rollback ... or similar"
        expected_outcome: "Service restored"
    fallback_options:
      - trigger: "If primary mitigation fails"
        action: "Failover to DR"

  investigation:
    data_to_collect:
      - "Application logs from last 2 hours"
      - "Metrics dashboards"
      - "Recent deployment history"
    tools:
      - name: "Tool name"
        purpose: "What to look for"
        command: "Example command"
    common_root_causes:
      - cause: "Description"
        indicators: ["indicator1", "indicator2"]
        resolution: "How to fix"

  resolution:
    verification_steps:
      - "Verify service is responding"
      - "Check error rates returned to normal"
      - "Confirm no data loss"
    communication_template: |
      Subject: [RESOLVED] Incident: <incident_name>

      Status: RESOLVED
      Duration: X hours Y minutes
      Impact: Brief description
      Resolution: What fixed it

      A post-mortem will follow within 48 hours.

  post_incident:
    required_actions:
      - "Create post-mortem document"
      - "Update runbook if needed"
      - "Create tickets for follow-up items"
    timeline_deadline: "48 hours"
```

Generate playbooks for:
1. Database Failure Playbook
2. Service Outage Playbook
3. Performance Degradation Playbook
4. Security Incident Playbook
5. Data Pipeline Failure Playbook

Output as YAML, separated by `---`.""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse playbooks
        playbooks = self._parse_yaml_configs(response.content)

        decision = add_decision(
            state,
            decision_type="playbook_generation",
            description="Generated incident response playbooks",
            confidence=0.80,
            reasoning="Created detailed playbooks for major failure categories"
        )

        return {
            "outputs": {"incident_playbooks": playbooks, "incident_playbooks_raw": response.content},
            "incident_playbooks": playbooks,
            "decisions": [decision],
            "current_step": "generate_playbooks",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_escalation_procedures(self, state: OperationsState) -> Dict[str, Any]:
        """Generate escalation procedures and contact matrices."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        failure_analysis = outputs.get("failure_mode_analysis", "")
        team_structure = context.get("team_structure", {})
        business_hours = context.get("business_hours", "09:00-18:00 UTC, Mon-Fri")
        sla_requirements = context.get("sla_requirements", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate escalation procedures and contact matrices.

Failure Mode Analysis:
{failure_analysis}

Team Structure:
{json.dumps(team_structure, indent=2) if isinstance(team_structure, dict) else team_structure}

Business Hours: {business_hours}

SLA Requirements:
{json.dumps(sla_requirements, indent=2) if isinstance(sla_requirements, dict) else sla_requirements}

Create comprehensive escalation procedures:

```yaml
escalation_matrix:
  name: "Open Forge Escalation Matrix"
  version: "1.0"
  last_updated: "YYYY-MM-DD"

  severity_definitions:
    sev1:
      name: "Critical"
      description: "Complete service outage or data loss"
      response_time: "15 minutes"
      resolution_target: "4 hours"
      examples:
        - "Production database down"
        - "Security breach detected"

    sev2:
      name: "High"
      description: "Major functionality impaired"
      response_time: "30 minutes"
      resolution_target: "8 hours"
      examples:
        - "API error rate > 10%"

    sev3:
      name: "Medium"
      description: "Partial degradation with workaround"
      response_time: "2 hours"
      resolution_target: "24 hours"
      examples:
        - "Non-critical feature unavailable"

    sev4:
      name: "Low"
      description: "Minor issue, minimal impact"
      response_time: "Next business day"
      resolution_target: "5 business days"
      examples:
        - "Documentation error"

  roles:
    incident_commander:
      responsibilities:
        - "Overall incident coordination"
        - "Make escalation decisions"
        - "Approve communications"
      authority:
        - "Can declare incident resolved"
        - "Can escalate to executives"

    technical_lead:
      responsibilities:
        - "Lead technical investigation"
        - "Coordinate engineering response"
        - "Approve technical changes"

    communications_lead:
      responsibilities:
        - "Draft status updates"
        - "Manage stakeholder notifications"
        - "Update status page"

  escalation_paths:
    business_hours:
      sev1:
        - time: "0 min"
          action: "Page on-call engineer"
          contact: "{{on_call_engineer}}"
        - time: "15 min"
          action: "Page engineering manager"
          contact: "{{eng_manager}}"
        - time: "30 min"
          action: "Notify VP Engineering"
          contact: "{{vp_engineering}}"
        - time: "1 hour"
          action: "Executive briefing"
          contact: "{{cto}}"

      sev2:
        - time: "0 min"
          action: "Alert on-call engineer"
          contact: "{{on_call_engineer}}"
        - time: "30 min"
          action: "Notify team lead"
          contact: "{{team_lead}}"

    after_hours:
      sev1:
        - time: "0 min"
          action: "Page primary on-call"
          contact: "{{primary_oncall}}"
        - time: "10 min"
          action: "Page secondary on-call"
          contact: "{{secondary_oncall}}"
        - time: "30 min"
          action: "Page engineering manager"
          contact: "{{eng_manager}}"

  contact_directory:
    template:
      name: "Contact Name"
      role: "Role/Title"
      email: "email@company.com"
      phone: "+1-XXX-XXX-XXXX"
      slack: "@username"
      pagerduty: "service-id"
      availability: "business hours/24x7"
      backup: "Backup contact name"

  communication_templates:
    initial_notification:
      subject: "[{{severity}}] Incident: {{incident_title}}"
      body: |
        An incident has been declared.

        **Severity**: {{severity}}
        **Started**: {{start_time}}
        **Impact**: {{impact_description}}
        **Current Status**: Investigating
        **Incident Commander**: {{ic_name}}

        Updates will be provided every {{update_interval}}.

    status_update:
      subject: "[UPDATE] {{incident_title}}"
      body: |
        **Status Update #{{update_number}}**
        **Time**: {{current_time}}

        **Current Status**: {{status}}
        **Actions Taken**: {{actions}}
        **Next Steps**: {{next_steps}}
        **ETA for Resolution**: {{eta}}

    resolution:
      subject: "[RESOLVED] {{incident_title}}"
      body: |
        The incident has been resolved.

        **Resolved At**: {{resolved_time}}
        **Duration**: {{duration}}
        **Root Cause**: {{root_cause_summary}}
        **Resolution**: {{resolution_summary}}

        A detailed post-mortem will be shared within 48 hours.
```

Output as YAML.""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse escalation procedures
        escalation_procedures = self._parse_yaml_configs(response.content)

        decision = add_decision(
            state,
            decision_type="escalation_generation",
            description="Generated escalation procedures",
            confidence=0.85,
            reasoning="Created severity definitions, escalation paths, and communication templates"
        )

        return {
            "outputs": {"escalation_procedures": escalation_procedures, "escalation_procedures_raw": response.content},
            "escalation_procedures": escalation_procedures,
            "decisions": [decision],
            "current_step": "generate_escalation_procedures",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_postmortem_templates(self, state: OperationsState) -> Dict[str, Any]:
        """Generate post-mortem templates for incident review."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        failure_analysis = outputs.get("failure_mode_analysis", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate post-mortem templates for blameless incident reviews.

Failure Mode Analysis (for context):
{failure_analysis}

Create comprehensive post-mortem templates:

```yaml
postmortem_template:
  metadata:
    title: "Post-Mortem: [Incident Title]"
    incident_id: "INC-XXXX"
    date: "YYYY-MM-DD"
    author: "[Name]"
    reviewers:
      - "[Name 1]"
      - "[Name 2]"
    status: "Draft | In Review | Final"

  executive_summary:
    duration: "[X hours Y minutes]"
    severity: "[SEV1-4]"
    impact: |
      - Number of users affected: X
      - Revenue impact: $X (if applicable)
      - Data affected: Description
    root_cause_summary: "[One-sentence summary]"
    resolution_summary: "[How it was fixed]"

  timeline:
    format: |
      | Time (UTC) | Event | Actor/System | Notes |
      |------------|-------|--------------|-------|
      | HH:MM | Event description | Who/what | Additional context |

    key_milestones:
      detection_time: "YYYY-MM-DD HH:MM UTC"
      acknowledgment_time: "YYYY-MM-DD HH:MM UTC"
      mitigation_time: "YYYY-MM-DD HH:MM UTC"
      resolution_time: "YYYY-MM-DD HH:MM UTC"

    metrics:
      time_to_detect_minutes: X
      time_to_acknowledge_minutes: X
      time_to_mitigate_minutes: X
      time_to_resolve_minutes: X
      total_duration_minutes: X

  incident_description:
    what_happened: |
      [Detailed description of what occurred from the user/system perspective]

    technical_details: |
      [Technical explanation of the failure]

    scope:
      services_affected:
        - service-1
        - service-2
      regions_affected:
        - region-1
      customers_affected: "All | Subset | Specific customers"

  root_cause_analysis:
    methodology: "5 Whys | Fishbone | Fault Tree"

    analysis: |
      ## 5 Whys Analysis

      1. **Why** did [symptom] happen?
         - Because [reason 1]

      2. **Why** did [reason 1] happen?
         - Because [reason 2]

      [Continue until root cause identified]

    contributing_factors:
      - factor: "Description"
        category: "Process | Technical | Human | External"
        how_it_contributed: "Explanation"

    root_cause: |
      [Clear statement of the root cause]

  detection:
    how_detected: "Alert | Customer report | Manual check"
    alert_name: "[Alert that fired, if any]"
    detection_gap: |
      [Any gaps in detection that delayed response]
    improvements_needed:
      - "Improvement description"

  response:
    what_went_well:
      - "Thing 1"
      - "Thing 2"

    what_could_be_improved:
      - "Area 1"
      - "Area 2"

    responders:
      - name: "[Name]"
        role: "[Incident Commander | Tech Lead | etc.]"
        actions: "[Key actions taken]"

  remediation:
    immediate_actions_taken:
      - action: "Description"
        completed_by: "Name"
        completion_time: "YYYY-MM-DD HH:MM"

    follow_up_items:
      - id: "JIRA-XXX"
        description: "Action item description"
        owner: "Name"
        priority: "P1 | P2 | P3"
        due_date: "YYYY-MM-DD"
        status: "Open | In Progress | Done"
        prevents_recurrence: true | false

  lessons_learned:
    - category: "Detection | Response | Recovery | Prevention"
      lesson: "What we learned"
      action: "What we will do differently"

  appendix:
    related_incidents:
      - incident_id: "INC-XXXX"
        relationship: "Similar root cause | Same system | etc."

    logs_and_evidence:
      - type: "Log | Screenshot | Metric graph"
        description: "What it shows"
        location: "Link or path"

    references:
      - "[Link to relevant documentation]"
      - "[Link to monitoring dashboard]"
```

Also create a simplified template for SEV3/SEV4 incidents:

```yaml
simple_postmortem_template:
  incident_id: "INC-XXXX"
  date: "YYYY-MM-DD"
  severity: "SEV3 | SEV4"
  duration: "X minutes"

  summary: |
    Brief description of what happened and how it was resolved.

  impact: |
    Who/what was affected and to what extent.

  root_cause: |
    One paragraph explanation of the root cause.

  action_items:
    - description: "Action item"
      owner: "Name"
      ticket: "JIRA-XXX"

  prevention: |
    What changes will prevent recurrence.
```

Output templates as YAML, separated by `---`.""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse templates
        postmortem_templates = self._parse_yaml_configs(response.content)

        decision = add_decision(
            state,
            decision_type="postmortem_generation",
            description="Generated post-mortem templates",
            confidence=0.85,
            reasoning="Created comprehensive and simplified post-mortem templates"
        )

        return {
            "outputs": {"postmortem_templates": postmortem_templates, "postmortem_templates_raw": response.content},
            "postmortem_templates": postmortem_templates,
            "decisions": [decision],
            "current_step": "generate_postmortem_templates",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _validate_incident_configs(self, state: OperationsState) -> Dict[str, Any]:
        """Validate all incident management configurations."""
        outputs = state.get("outputs", {})

        failure_analysis = outputs.get("failure_mode_analysis", "")
        playbooks = outputs.get("incident_playbooks_raw", "")
        escalation = outputs.get("escalation_procedures_raw", "")
        postmortem = outputs.get("postmortem_templates_raw", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate all incident management configurations.

Failure Mode Analysis:
{failure_analysis}

Incident Playbooks:
{playbooks}

Escalation Procedures:
{escalation}

Post-Mortem Templates:
{postmortem}

Validate:
1. All identified failure modes have corresponding playbooks
2. Escalation paths are complete for all severity levels
3. Response times align with SLA requirements
4. Roles and responsibilities are clearly defined
5. Communication templates are complete
6. Post-mortem template captures all essential information
7. No gaps in coverage
8. Procedures are actionable and clear

Provide:
1. Validation status (PASS/FAIL)
2. Coverage matrix (failure mode vs playbook)
3. Gaps identified
4. Recommendations for improvement
5. Incident readiness score (0-100)

Also provide a summary of:
- Total playbooks generated
- Severity levels defined
- Escalation paths covered
- Estimated response preparedness""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse validation result
        response_lower = response.content.lower()
        is_valid = "pass" in response_lower and "fail" not in response_lower

        confidence = 0.90 if is_valid else 0.70

        decision = add_decision(
            state,
            decision_type="incident_validation",
            description="Validated incident management configurations",
            confidence=confidence,
            reasoning=response.content[:500],
            requires_approval=not is_valid
        )

        review_items = []
        if not is_valid:
            review_items.append(mark_for_review(
                state,
                item_type="incident_config",
                item_id="validation_issues",
                description="Incident management configuration has gaps that need review",
                priority="medium"
            ))

        return {
            "outputs": {
                "validation_result": response.content,
                "is_valid": is_valid,
                "incident_readiness_summary": response.content
            },
            "decisions": [decision],
            "requires_human_review": not is_valid,
            "review_items": review_items,
            "current_step": "validate_incident_configs",
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _parse_yaml_configs(self, content: str) -> List[Dict[str, Any]]:
        """Parse YAML configurations from content."""
        configs = []
        try:
            # Split by YAML document separator
            documents = content.split("---")
            for doc in documents:
                doc = doc.strip()
                if not doc:
                    continue

                # Try to extract YAML from code blocks
                import re
                if "```yaml" in doc or "```" in doc:
                    yaml_match = re.search(r'```ya?ml?\s*([\s\S]*?)```', doc)
                    if yaml_match:
                        doc = yaml_match.group(1)

                try:
                    parsed = yaml.safe_load(doc)
                    if parsed and isinstance(parsed, dict):
                        configs.append(parsed)
                except yaml.YAMLError:
                    continue

        except Exception:
            pass

        if not configs:
            configs = [{"raw_config": content}]
        return configs
