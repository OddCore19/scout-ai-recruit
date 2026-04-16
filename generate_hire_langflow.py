import copy
import json
import uuid
from pathlib import Path


ROOT = Path("/Users/mengshangjun/Documents/cmu/14789/project")
BACKUP = ROOT / "HR Recruiting (Backup).json"
OUTPUT = ROOT / "Hire Agent Preliminary Screening.json"
COMPONENTS_DIR = ROOT / "components"


FLOW_ID = str(uuid.uuid4())
FOLDER_ID = str(uuid.uuid4())


def load_backup():
    return json.loads(BACKUP.read_text())


def find_node(backup, component_type):
    for node in backup["data"]["nodes"]:
        if node["data"]["type"] == component_type:
            return copy.deepcopy(node)
    raise KeyError(component_type)


def reset_common(node, node_id, position, display_name=None):
    node["id"] = node_id
    node["position"] = position
    node["selected"] = False
    node["dragging"] = False
    node["data"]["id"] = node_id
    node["data"]["showNode"] = True
    if display_name:
        node["data"]["node"]["display_name"] = display_name
    template = node["data"]["node"].get("template", {})
    if "_frontend_node_flow_id" in template:
        template["_frontend_node_flow_id"]["value"] = FLOW_ID
    if "_frontend_node_folder_id" in template:
        template["_frontend_node_folder_id"]["value"] = FOLDER_ID
    return node


def prompt_node(base, node_id, position, display_name, prompt_text):
    node = reset_common(copy.deepcopy(base), node_id, position, display_name)
    node["data"]["node"]["template"]["template"]["value"] = prompt_text
    return node


def file_node(base, node_id, position, display_name, separator, advanced_mode=True, markdown=False):
    node = reset_common(copy.deepcopy(base), node_id, position, display_name)
    template = node["data"]["node"]["template"]
    template["advanced_mode"]["value"] = advanced_mode
    template["markdown"]["value"] = markdown
    template["separator"]["value"] = separator
    return node


def loop_node(base, node_id, position, display_name):
    return reset_common(copy.deepcopy(base), node_id, position, display_name)


def agent_node(base, node_id, position, display_name, system_prompt):
    node = reset_common(copy.deepcopy(base), node_id, position, display_name)
    template = node["data"]["node"]["template"]
    template["system_prompt"]["value"] = system_prompt
    template["add_current_date_tool"]["value"] = False
    template["tools"]["value"] = ""
    template["output_schema"]["value"] = []
    return node


def chat_output_node(base, node_id, position):
    return reset_common(copy.deepcopy(base), node_id, position, "Chat Output")


def custom_component_node(
    node_id,
    position,
    class_name,
    display_name,
    description,
    icon,
    inputs,
    outputs,
    code,
    output_bases,
    component_name=None,
):
    resolved_component_name = component_name or class_name
    field_order = [item["name"] for item in inputs]
    template = {
        "_frontend_node_flow_id": {"value": FLOW_ID},
        "_frontend_node_folder_id": {"value": FOLDER_ID},
        "_type": "Component",
        "code": {
            "advanced": True,
            "dynamic": True,
            "fileTypes": [],
            "file_path": "",
            "info": "",
            "list": False,
            "load_from_db": False,
            "multiline": True,
            "name": "code",
            "password": False,
            "placeholder": "",
            "required": True,
            "show": True,
            "title_case": False,
            "type": "code",
            "value": code,
        },
    }
    for item in inputs:
        template[item["name"]] = item["template"]

    node_outputs = []
    for output in outputs:
        node_outputs.append(
            {
                "allows_loop": False,
                "cache": True,
                "display_name": output["display_name"],
                "group_outputs": False,
                "hidden": False,
                "loop_types": None,
                "method": output["method"],
                "name": output["name"],
                "options": None,
                "required_inputs": None,
                "selected": output["types"][0],
                "tool_mode": True,
                "types": output["types"],
                "value": "__UNDEFINED__",
            }
        )

    return {
        "data": {
            "id": node_id,
            "node": {
                "base_classes": output_bases,
                "beta": False,
                "conditional_paths": [],
                "custom_fields": {},
                "description": description,
                "display_name": display_name,
                "documentation": "",
                "edited": False,
                "field_order": ["code", *field_order],
                "frozen": False,
                "icon": icon,
                "legacy": False,
                "metadata": {
                    "module": f"custom_components.{class_name.lower()}",
                },
                "minimized": False,
                "name": resolved_component_name,
                "output_types": [],
                "outputs": node_outputs,
                "pinned": False,
                "template": template,
                "tool_mode": False,
            },
            "showNode": True,
            "type": resolved_component_name,
        },
        "dragging": False,
        "id": node_id,
        "position": position,
        "selected": False,
        "type": "genericNode",
    }


def handle_input(name, display_name, input_types, info, required=True):
    return {
        "name": name,
        "template": {
            "_input_type": "HandleInput",
            "advanced": False,
            "display_name": display_name,
            "dynamic": False,
            "info": info,
            "input_types": input_types,
            "list": False,
            "list_add_label": "Add More",
            "name": name,
            "override_skip": False,
            "placeholder": "",
            "required": required,
            "show": True,
            "title_case": False,
            "trace_as_metadata": True,
            "track_in_telemetry": False,
            "type": "other",
            "value": "",
        },
    }


def text_input(name, display_name, value, info="", advanced=True):
    return {
        "name": name,
        "template": {
            "_input_type": "MessageTextInput",
            "advanced": advanced,
            "display_name": display_name,
            "dynamic": False,
            "info": info,
            "input_types": ["Message"],
            "list": False,
            "list_add_label": "Add More",
            "load_from_db": False,
            "name": name,
            "override_skip": False,
            "placeholder": "",
            "required": False,
            "show": True,
            "title_case": False,
            "tool_mode": False,
            "trace_as_input": True,
            "trace_as_metadata": True,
            "track_in_telemetry": False,
            "type": "str",
            "value": value,
        },
    }


def file_input(name, display_name, info="", file_types=None, required=False):
    return {
        "name": name,
        "template": {
            "_input_type": "FileInput",
            "advanced": False,
            "display_name": display_name,
            "dynamic": False,
            "fileTypes": file_types or [],
            "file_path": [],
            "info": info,
            "list": False,
            "list_add_label": "Add More",
            "name": name,
            "override_skip": False,
            "placeholder": "",
            "required": required,
            "show": True,
            "temp_file": False,
            "title_case": False,
            "tool_mode": False,
            "trace_as_metadata": True,
            "track_in_telemetry": False,
            "type": "file",
            "value": "",
        },
    }


def str_input(name, display_name, value="", info="", advanced=True):
    return {
        "name": name,
        "template": {
            "_input_type": "StrInput",
            "advanced": advanced,
            "display_name": display_name,
            "dynamic": False,
            "info": info,
            "list": False,
            "list_add_label": "Add More",
            "load_from_db": False,
            "name": name,
            "override_skip": False,
            "placeholder": "",
            "required": False,
            "show": True,
            "title_case": False,
            "tool_mode": False,
            "trace_as_metadata": True,
            "track_in_telemetry": False,
            "type": "str",
            "value": value,
        },
    }


def int_input(name, display_name, value=0, info="", advanced=True):
    return {
        "name": name,
        "template": {
            "_input_type": "IntInput",
            "advanced": advanced,
            "display_name": display_name,
            "dynamic": False,
            "info": info,
            "input_types": [],
            "list": False,
            "list_add_label": "Add More",
            "name": name,
            "override_skip": False,
            "placeholder": "",
            "required": False,
            "show": True,
            "title_case": False,
            "tool_mode": False,
            "trace_as_metadata": True,
            "track_in_telemetry": True,
            "type": "int",
            "value": value,
        },
    }


def float_input(name, display_name, value=0.0, info="", advanced=True):
    return {
        "name": name,
        "template": {
            "_input_type": "FloatInput",
            "advanced": advanced,
            "display_name": display_name,
            "dynamic": False,
            "info": info,
            "input_types": [],
            "list": False,
            "list_add_label": "Add More",
            "name": name,
            "override_skip": False,
            "placeholder": "",
            "required": False,
            "show": True,
            "title_case": False,
            "tool_mode": False,
            "trace_as_metadata": True,
            "track_in_telemetry": True,
            "type": "float",
            "value": value,
        },
    }


def multiline_input(name, display_name, value="", info="", advanced=False, required=False, tool_mode=False):
    return {
        "name": name,
        "template": {
            "_input_type": "MultilineInput",
            "advanced": advanced,
            "ai_enabled": False,
            "copy_field": False,
            "display_name": display_name,
            "dynamic": False,
            "info": info,
            "input_types": ["Message"],
            "list": False,
            "list_add_label": "Add More",
            "load_from_db": False,
            "multiline": True,
            "name": name,
            "override_skip": False,
            "password": False,
            "placeholder": "",
            "required": required,
            "show": True,
            "title_case": False,
            "tool_mode": tool_mode,
            "trace_as_input": True,
            "trace_as_metadata": True,
            "track_in_telemetry": False,
            "type": "str",
            "value": value,
        },
    }


def table_input(name, display_name, value, table_schema, info="", required=True):
    return {
        "name": name,
        "template": {
            "_input_type": "TableInput",
            "advanced": False,
            "display_name": display_name,
            "dynamic": False,
            "info": info,
            "is_list": True,
            "list_add_label": "Add More",
            "load_from_db": False,
            "name": name,
            "override_skip": False,
            "placeholder": "",
            "required": required,
            "show": True,
            "table_icon": "Table",
            "table_schema": table_schema,
            "title_case": False,
            "tool_mode": False,
            "trace_as_metadata": True,
            "track_in_telemetry": False,
            "trigger_icon": "Table",
            "trigger_text": "Open table",
            "type": "table",
            "value": value,
        },
    }


def output_spec(name, display_name, method, types):
    return {
        "name": name,
        "display_name": display_name,
        "method": method,
        "types": types,
    }


def edge(source_node, source_output, target_node, target_field=None, loop_target=False, loop_output_types=None):
    source_meta = {
        "dataType": source_node["data"]["type"],
        "id": source_node["id"],
        "name": source_output["name"],
        "output_types": source_output["types"],
    }
    source_handle = (
        "{œdataTypeœ:œ"
        + source_meta["dataType"]
        + "œ,œidœ:œ"
        + source_meta["id"]
        + "œ,œnameœ:œ"
        + source_meta["name"]
        + "œ,œoutput_typesœ:["
        + ",".join(f"œ{item}œ" for item in source_meta["output_types"])
        + "]}"
    )

    if loop_target:
        target_meta = {
            "dataType": target_node["data"]["type"],
            "id": target_node["id"],
            "name": target_field,
            "output_types": loop_output_types or ["Data"],
        }
        target_handle = (
            "{œdataTypeœ:œ"
            + target_meta["dataType"]
            + "œ,œidœ:œ"
            + target_meta["id"]
            + "œ,œnameœ:œ"
            + target_meta["name"]
            + "œ,œoutput_typesœ:["
            + ",".join(f"œ{item}œ" for item in target_meta["output_types"])
            + "]}"
        )
        edge_id = f"reactflow__edge-{source_node['id']}{source_handle}-{target_node['id']}{target_handle}"
        return {
            "animated": False,
            "className": "",
            "data": {"sourceHandle": source_meta, "targetHandle": target_meta},
            "id": edge_id,
            "selected": False,
            "source": source_node["id"],
            "sourceHandle": source_handle,
            "target": target_node["id"],
            "targetHandle": target_handle,
        }

    target_template = target_node["data"]["node"]["template"][target_field]
    target_meta = {
        "fieldName": target_field,
        "id": target_node["id"],
        "inputTypes": target_template.get("input_types", []),
        "type": target_template["type"],
    }
    target_handle = (
        "{œfieldNameœ:œ"
        + target_meta["fieldName"]
        + "œ,œidœ:œ"
        + target_meta["id"]
        + "œ,œinputTypesœ:["
        + ",".join(f"œ{item}œ" for item in target_meta["inputTypes"])
        + "],œtypeœ:œ"
        + target_meta["type"]
        + "œ}"
    )
    edge_id = f"reactflow__edge-{source_node['id']}{source_handle}-{target_node['id']}{target_handle}"
    return {
        "animated": False,
        "className": "",
        "data": {"sourceHandle": source_meta, "targetHandle": target_meta},
        "id": edge_id,
        "selected": False,
        "source": source_node["id"],
        "sourceHandle": source_handle,
        "target": target_node["id"],
        "targetHandle": target_handle,
    }


JD_PROMPT = """Extract a normalized hiring requirements profile from the job description.

Rules:
- Separate explicit hard requirements from preferred qualifications.
- Do not infer requirements that are not stated.
- Normalize equivalent skills and credentials where obvious.
- If a requirement is missing, return an empty list or null-compatible default.
- Return only information supported by the job description text.
"""


CANDIDATE_PROMPT = """Extract a normalized candidate profile from the resume text.

Rules:
- Use only evidence present in the resume.
- Do not infer unstated qualifications.
- Normalize equivalent skills and titles where obvious.
- Estimate years of experience conservatively from the resume if a direct number is not stated.
- Keep short evidence snippets for core claims.
"""


FIT_PROMPT = """Assess fit only after considering the hard requirement decision.

Rules:
- If the candidate failed hard requirements, keep fit_score low and explain the failure.
- Evaluate preference fit across skills alignment, relevant experience, industry fit, seniority fit, and education fit.
- Use evidence from the candidate profile and job profile only.
- Return concise strengths, gaps, and a fit rationale.
"""


SUMMARY_PROMPT = """You are writing a recruiter-facing shortlist summary.

Summarize only the top recommended candidates. Compare their strengths, tradeoffs, and notable gaps.
Do not make a final hiring decision. Be concise and evidence-based.
"""


STRUCTURED_SYSTEM = "Return valid structured JSON matching the provided schema. Do not add extra keys."


RESUME_SPLITTER_CODE = """
from __future__ import annotations

import re

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import HandleInput, MessageTextInput
from lfx.schema.dataframe import DataFrame
from lfx.schema.message import Message
from lfx.template.field.base import Output


class ResumeSplitterComponent(Component):
    display_name = "Resume Splitter"
    description = "Split concatenated resume text into one row per candidate."
    icon = "split"
    name = "ResumeSplitterComponent"

    inputs = [
        HandleInput(name="input_value", display_name="Resume Files", input_types=["Message"], required=True),
        MessageTextInput(
            name="separator",
            display_name="Separator",
            value="\\n\\n===FILE_BOUNDARY===\\n\\n",
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Candidate DataFrame", name="dataframe_output", method="build_dataframe"),
    ]

    def build_dataframe(self) -> DataFrame:
        message = self.input_value
        text = message.text if isinstance(message, Message) else str(message)
        separator = self.separator or "\\n\\n===FILE_BOUNDARY===\\n\\n"
        parts = [part.strip() for part in text.split(separator) if part and part.strip()]
        rows = []
        for index, part in enumerate(parts, start=1):
            filename_match = re.search(r"(?im)^(?:file|filename)\\s*:\\s*(.+)$", part)
            rows.append(
                {
                    "candidate_id": f"candidate_{index}",
                    "file_name": filename_match.group(1).strip() if filename_match else f"candidate_{index}.txt",
                    "resume_text": part,
                }
            )
        return DataFrame(rows)
"""


CANDIDATE_CONTEXT_CODE = """
from __future__ import annotations

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import HandleInput
from lfx.schema.data import Data
from lfx.schema.message import Message
from lfx.template.field.base import Output


class CandidateContextFormatterComponent(Component):
    display_name = "Candidate Context Formatter"
    description = "Convert a loop item into resume text for extraction."
    icon = "file-text"
    name = "CandidateContextFormatterComponent"

    inputs = [
        HandleInput(name="candidate_row", display_name="Candidate Row", input_types=["Data"], required=True),
    ]

    outputs = [
        Output(display_name="Candidate Message", name="message_output", method="build_message"),
    ]

    def build_message(self) -> Message:
        row = self.candidate_row
        payload = row.data if isinstance(row, Data) else row
        resume_text = payload.get("resume_text", "")
        candidate_id = payload.get("candidate_id", "")
        file_name = payload.get("file_name", "")
        return Message(
            text=f"candidate_id: {candidate_id}\\nfile_name: {file_name}\\n\\nresume_text:\\n{resume_text}"
        )
"""


HARD_FILTER_CODE = """
from __future__ import annotations

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import HandleInput
from lfx.schema.data import Data
from lfx.template.field.base import Output


def _unwrap(value):
    if isinstance(value, Data):
        return value.data
    return value


def _norm_list(value):
    if not value:
        return []
    if isinstance(value, str):
        return [value.strip().lower()] if value.strip() else []
    return [str(item).strip().lower() for item in value if str(item).strip()]


class HardRequirementEvaluatorComponent(Component):
    display_name = "Hard Requirement Evaluator"
    description = "Apply deterministic screening rules for hard requirements."
    icon = "shield-check"
    name = "HardRequirementEvaluatorComponent"

    inputs = [
        HandleInput(name="job_profile", display_name="Job Profile", input_types=["Data"], required=True),
        HandleInput(name="candidate_profile", display_name="Candidate Profile", input_types=["Data"], required=True),
    ]

    outputs = [
        Output(display_name="Hard Filter Decision", name="decision_output", method="evaluate"),
    ]

    def evaluate(self) -> Data:
        job = _unwrap(self.job_profile) or {}
        candidate = _unwrap(self.candidate_profile) or {}

        failures = []
        evidence = []

        candidate_skills = set(_norm_list(candidate.get("skills")))
        required_skills = set(_norm_list(job.get("required_skills")))
        missing_skills = sorted(required_skills - candidate_skills)
        if missing_skills:
            failures.append(f"Missing required skills: {', '.join(missing_skills)}")
        else:
            if required_skills:
                evidence.append("Required skills present in candidate profile.")

        required_years = int(job.get("required_years_experience") or 0)
        candidate_years = int(candidate.get("years_experience") or 0)
        if candidate_years < required_years:
            failures.append(
                f"Years of experience below minimum: candidate={candidate_years}, required={required_years}"
            )
        elif required_years:
            evidence.append(f"Experience threshold met: {candidate_years} years.")

        required_auth = _norm_list(job.get("required_work_authorization"))
        candidate_auth = " ".join(_norm_list(candidate.get("work_authorization")))
        if required_auth and not any(item in candidate_auth for item in required_auth):
            failures.append("Required work authorization not found.")
        elif required_auth:
            evidence.append("Work authorization requirement appears satisfied.")

        required_location = _norm_list(job.get("required_location_constraints"))
        candidate_location = " ".join(_norm_list(candidate.get("current_location")))
        if required_location and not any(item in candidate_location for item in required_location):
            failures.append("Location constraint not clearly satisfied.")
        elif required_location:
            evidence.append("Location constraint appears satisfied.")

        required_certs = set(_norm_list(job.get("required_certifications")))
        candidate_certs = set(_norm_list(candidate.get("certifications")))
        missing_certs = sorted(required_certs - candidate_certs)
        if missing_certs:
            failures.append(f"Missing required certifications: {', '.join(missing_certs)}")
        elif required_certs:
            evidence.append("Required certifications present.")

        passes = len(failures) == 0
        return Data(
            data={
                "candidate_id": candidate.get("candidate_id"),
                "name": candidate.get("name"),
                "passes_hard_requirements": passes,
                "hard_requirement_failures": failures,
                "hard_requirement_evidence": evidence,
            }
        )
"""


FIT_CONTEXT_CODE = """
from __future__ import annotations

import json

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import HandleInput
from lfx.schema.data import Data
from lfx.schema.message import Message
from lfx.template.field.base import Output


def _unwrap(value):
    if isinstance(value, Data):
        return value.data
    return value


class FitContextFormatterComponent(Component):
    display_name = "Fit Context Formatter"
    description = "Build a single message for fit scoring."
    icon = "braces"
    name = "FitContextFormatterComponent"

    inputs = [
        HandleInput(name="job_profile", display_name="Job Profile", input_types=["Data"], required=True),
        HandleInput(name="candidate_profile", display_name="Candidate Profile", input_types=["Data"], required=True),
        HandleInput(name="hard_filter", display_name="Hard Filter", input_types=["Data"], required=True),
    ]

    outputs = [
        Output(display_name="Fit Message", name="message_output", method="build_message"),
    ]

    def build_message(self) -> Message:
        payload = {
            "job_profile": _unwrap(self.job_profile),
            "candidate_profile": _unwrap(self.candidate_profile),
            "hard_filter": _unwrap(self.hard_filter),
        }
        return Message(text=json.dumps(payload, indent=2))
"""


RESULT_MERGER_CODE = """
from __future__ import annotations

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import HandleInput
from lfx.schema.data import Data
from lfx.template.field.base import Output


def _unwrap(value):
    if isinstance(value, Data):
        return value.data
    return value


class CandidateResultMergerComponent(Component):
    display_name = "Candidate Result Merger"
    description = "Merge extraction, hard filter, and fit outputs for one candidate."
    icon = "merge"
    name = "CandidateResultMergerComponent"

    inputs = [
        HandleInput(name="candidate_profile", display_name="Candidate Profile", input_types=["Data"], required=True),
        HandleInput(name="hard_filter", display_name="Hard Filter", input_types=["Data"], required=True),
        HandleInput(name="fit_assessment", display_name="Fit Assessment", input_types=["Data"], required=True),
    ]

    outputs = [
        Output(display_name="Candidate Result", name="result_output", method="merge"),
    ]

    def merge(self) -> Data:
        candidate = _unwrap(self.candidate_profile) or {}
        hard_filter = _unwrap(self.hard_filter) or {}
        fit = _unwrap(self.fit_assessment) or {}
        merged = {}
        merged.update(candidate)
        merged.update(hard_filter)
        merged.update(fit)
        return Data(data=merged)
"""


QUALIFYING_FILTER_CODE = """
from __future__ import annotations

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import HandleInput
from lfx.schema.dataframe import DataFrame
from lfx.template.field.base import Output


class QualifyingCandidateFilterComponent(Component):
    display_name = "Qualifying Candidate Filter"
    description = "Keep only candidates who passed hard requirements."
    icon = "filter"
    name = "QualifyingCandidateFilterComponent"

    inputs = [
        HandleInput(name="candidate_results", display_name="Candidate Results", input_types=["DataFrame"], required=True),
    ]

    outputs = [
        Output(display_name="Qualifying Candidates", name="dataframe_output", method="filter_candidates"),
    ]

    def filter_candidates(self) -> DataFrame:
        rows = self.candidate_results.to_dict(orient="records")
        filtered = [row for row in rows if row.get("passes_hard_requirements") is True]
        return DataFrame(filtered)
"""


TOP_K_CODE = """
from __future__ import annotations

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import HandleInput
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.template.field.base import Output


def _unwrap(value):
    if isinstance(value, Data):
        return value.data
    return value


class TopKRankerComponent(Component):
    display_name = "Top-K Ranker"
    description = "Sort qualifying candidates by fit score and apply top-k."
    icon = "list-ordered"
    name = "TopKRankerComponent"

    inputs = [
        HandleInput(name="qualifying_candidates", display_name="Qualifying Candidates", input_types=["DataFrame"], required=True),
        HandleInput(name="job_profile", display_name="Job Profile", input_types=["Data"], required=True),
    ]

    outputs = [
        Output(display_name="Top Candidates", name="dataframe_output", method="rank_candidates"),
    ]

    def rank_candidates(self) -> DataFrame:
        rows = self.qualifying_candidates.to_dict(orient="records")
        rows.sort(key=lambda row: float(row.get("fit_score") or 0.0), reverse=True)
        job = _unwrap(self.job_profile) or {}
        top_k = int(job.get("top_k") or 3)
        ranked = []
        for rank, row in enumerate(rows[:top_k], start=1):
            enriched = dict(row)
            enriched["rank"] = rank
            ranked.append(enriched)
        return DataFrame(ranked)
"""


SUMMARY_CONTEXT_CODE = """
from __future__ import annotations

import json

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import HandleInput
from lfx.schema.message import Message
from lfx.template.field.base import Output


class SummaryContextFormatterComponent(Component):
    display_name = "Summary Context Formatter"
    description = "Build the shortlist summary payload."
    icon = "file-json"
    name = "SummaryContextFormatterComponent"

    inputs = [
        HandleInput(name="top_candidates", display_name="Top Candidates", input_types=["DataFrame"], required=True),
    ]

    outputs = [
        Output(display_name="Summary Message", name="message_output", method="build_message"),
    ]

    def build_message(self) -> Message:
        rows = self.top_candidates.to_dict(orient="records")
        return Message(text=json.dumps({"top_k_recommended": rows}, indent=2))
"""


FINAL_FORMATTER_CODE = """
from __future__ import annotations

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import HandleInput
from lfx.schema.data import Data
from lfx.schema.message import Message
from lfx.template.field.base import Output


class FinalFormatterComponent(Component):
    display_name = "Final Formatter"
    description = "Assemble the final hire screening response."
    icon = "package"
    name = "FinalFormatterComponent"

    inputs = [
        HandleInput(name="qualifying_candidates", display_name="Qualifying Candidates", input_types=["DataFrame"], required=True),
        HandleInput(name="top_candidates", display_name="Top Candidates", input_types=["DataFrame"], required=True),
        HandleInput(name="summary_message", display_name="Summary Message", input_types=["Message"], required=True),
    ]

    outputs = [
        Output(display_name="Final Output", name="data_output", method="build_output"),
    ]

    def build_output(self) -> Data:
        qualifying = self.qualifying_candidates.to_dict(orient="records")
        top_candidates = self.top_candidates.to_dict(orient="records")
        summary_message = self.summary_message
        summary = summary_message.text if isinstance(summary_message, Message) else str(summary_message)
        return Data(
            data={
                "qualifying_candidates": qualifying,
                "top_k_recommended": top_candidates,
                "recommended_candidate_summary": summary,
            }
        )
"""


def build_flow():
    backup = load_backup()
    file_base = find_node(backup, "File")
    prompt_base = find_node(backup, "Prompt")
    loop_base = find_node(backup, "LoopComponent")
    agent_base = find_node(backup, "Agent")
    chat_base = find_node(backup, "ChatOutput")

    nodes = []

    jd_file = file_node(file_base, "File-JD001", {"x": 0, "y": 0}, "JD File", "\n\n", advanced_mode=True, markdown=True)
    cv_file = file_node(
        file_base,
        "File-CV001",
        {"x": 0, "y": 420},
        "CV Files",
        "\n\n===FILE_BOUNDARY===\n\n",
        advanced_mode=True,
        markdown=True,
    )
    jd_prompt = prompt_node(prompt_base, "Prompt-JD001", {"x": 360, "y": -220}, "JD Extraction Prompt", JD_PROMPT)
    candidate_prompt = prompt_node(
        prompt_base, "Prompt-CAND001", {"x": 1650, "y": 200}, "Candidate Extraction Prompt", CANDIDATE_PROMPT
    )
    fit_prompt = prompt_node(prompt_base, "Prompt-FIT001", {"x": 2940, "y": 200}, "Fit Scoring Prompt", FIT_PROMPT)
    summary_prompt = prompt_node(
        prompt_base, "Prompt-SUM001", {"x": 4760, "y": 160}, "Recommendation Summary Prompt", SUMMARY_PROMPT
    )

    jd_schema = [
        {"name": "role_title", "description": "Job title", "type": "str", "multiple": "False"},
        {"name": "role_family", "description": "Job family", "type": "str", "multiple": "False"},
        {"name": "required_skills", "description": "Required skills", "type": "str", "multiple": "True"},
        {"name": "preferred_skills", "description": "Preferred skills", "type": "str", "multiple": "True"},
        {"name": "required_years_experience", "description": "Minimum years of experience", "type": "int", "multiple": "False"},
        {"name": "required_education", "description": "Required education", "type": "str", "multiple": "True"},
        {"name": "required_certifications", "description": "Required certifications", "type": "str", "multiple": "True"},
        {"name": "required_location_constraints", "description": "Required location constraints", "type": "str", "multiple": "True"},
        {"name": "required_work_authorization", "description": "Required work authorization", "type": "str", "multiple": "True"},
        {"name": "required_industry_experience", "description": "Required industry experience", "type": "str", "multiple": "True"},
        {"name": "responsibilities", "description": "Responsibilities", "type": "str", "multiple": "True"},
        {"name": "fit_dimensions", "description": "Fit dimensions", "type": "str", "multiple": "True"},
        {"name": "top_k", "description": "Recommended shortlist size", "type": "int", "multiple": "False"},
    ]
    candidate_schema = [
        {"name": "candidate_id", "description": "Candidate identifier", "type": "str", "multiple": "False"},
        {"name": "name", "description": "Candidate name", "type": "str", "multiple": "False"},
        {"name": "email", "description": "Candidate email", "type": "str", "multiple": "False"},
        {"name": "phone", "description": "Candidate phone", "type": "str", "multiple": "False"},
        {"name": "current_location", "description": "Current location", "type": "str", "multiple": "False"},
        {"name": "work_authorization", "description": "Work authorization", "type": "str", "multiple": "False"},
        {"name": "skills", "description": "Skills", "type": "str", "multiple": "True"},
        {"name": "education", "description": "Education", "type": "str", "multiple": "True"},
        {"name": "certifications", "description": "Certifications", "type": "str", "multiple": "True"},
        {"name": "years_experience", "description": "Years of experience", "type": "int", "multiple": "False"},
        {"name": "titles", "description": "Titles held", "type": "str", "multiple": "True"},
        {"name": "companies", "description": "Companies worked at", "type": "str", "multiple": "True"},
        {"name": "industry_experience", "description": "Industry experience", "type": "str", "multiple": "True"},
        {"name": "summary", "description": "Candidate summary", "type": "str", "multiple": "False"},
        {"name": "evidence", "description": "Structured evidence snippets", "type": "dict", "multiple": "False"},
    ]
    fit_schema = [
        {"name": "candidate_id", "description": "Candidate identifier", "type": "str", "multiple": "False"},
        {"name": "fit_score", "description": "Overall fit score from 0 to 100", "type": "float", "multiple": "False"},
        {"name": "dimension_scores", "description": "Dimension scores", "type": "dict", "multiple": "False"},
        {"name": "strengths", "description": "Strengths", "type": "str", "multiple": "True"},
        {"name": "gaps", "description": "Gaps", "type": "str", "multiple": "True"},
        {"name": "fit_rationale", "description": "Fit rationale", "type": "str", "multiple": "False"},
    ]

    table_schema = [
        {
            "default": "field",
            "description": "Specify the name of the output field.",
            "display_name": "Name",
            "edit_mode": "inline",
            "formatter": "text",
            "name": "name",
            "type": "str",
        },
        {
            "default": "description of field",
            "description": "Describe the purpose of the output field.",
            "display_name": "Description",
            "edit_mode": "popover",
            "formatter": "text",
            "name": "description",
            "type": "str",
        },
        {
            "default": "str",
            "description": "Indicate the data type of the output field (e.g., str, int, float, bool, dict).",
            "display_name": "Type",
            "edit_mode": "inline",
            "formatter": "text",
            "name": "type",
            "options": ["str", "int", "float", "bool", "dict"],
            "type": "str",
        },
        {
            "default": "False",
            "description": "Set to True if this output field should be a list of the specified type.",
            "display_name": "As List",
            "edit_mode": "inline",
            "formatter": "text",
            "name": "multiple",
            "type": "boolean",
        },
    ]
    vertex_structured_code = (COMPONENTS_DIR / "vertex_ai_structured_output.py").read_text().strip()

    def vertex_structured_node(node_id, position, display_name, schema_name, output_schema):
        return custom_component_node(
            node_id,
            position,
            "VertexAIStructuredOutputComponent",
            display_name,
            "Generate structured data using Vertex AI chat models without trustcall.",
            "braces",
            [
                file_input(
                    "credentials",
                    "Credentials",
                    "JSON credentials file. Leave empty to fallback to environment variables",
                    file_types=["json"],
                ),
                text_input("model_name", "Model Name", "gemini-2.5-flash", advanced=False),
                str_input("project", "Project", "", "The project ID.", advanced=True),
                str_input("location", "Location", "us-central1", advanced=True),
                int_input("max_output_tokens", "Max Output Tokens", 0, advanced=True),
                int_input("max_retries", "Max Retries", 1, advanced=True),
                float_input("temperature", "Temperature", 0.0, advanced=False),
                int_input("top_k", "Top K", 0, advanced=True),
                float_input("top_p", "Top P", 0.95, advanced=True),
                multiline_input(
                    "input_value",
                    "Input Message",
                    "",
                    "The input message to the language model.",
                    required=True,
                    tool_mode=True,
                ),
                multiline_input(
                    "system_prompt",
                    "Format Instructions",
                    STRUCTURED_SYSTEM,
                    "The instructions to the language model for formatting the output.",
                    advanced=True,
                    required=True,
                ),
                text_input("schema_name", "Schema Name", schema_name, advanced=True),
                table_input(
                    "output_schema",
                    "Output Schema",
                    output_schema,
                    table_schema,
                    "Define the structure and data types for the model's output.",
                    required=True,
                ),
                str_input(
                    "method",
                    "Structured Output Method",
                    "with_structured_output",
                    "Reserved for future native JSON-schema mode. Current implementation uses LangChain ChatVertexAI.with_structured_output.",
                    advanced=True,
                ),
            ],
            [
                output_spec("structured_output", "Structured Output", "build_structured_output", ["Data"]),
                output_spec("dataframe_output", "Structured Output", "build_structured_dataframe", ["DataFrame"]),
            ],
            vertex_structured_code,
            ["Data", "DataFrame"],
            component_name="VertexAIStructuredOutput",
        )

    jd_structured = vertex_structured_node(
        "StructuredOutput-JD001",
        {"x": 360, "y": 0},
        "JD Structured Output",
        "JobRequirementProfile",
        jd_schema,
    )
    candidate_structured = vertex_structured_node(
        "StructuredOutput-CAND001",
        {"x": 1980, "y": 420},
        "Candidate Structured Output",
        "CandidateProfile",
        candidate_schema,
    )
    fit_structured = vertex_structured_node(
        "StructuredOutput-FIT001",
        {"x": 3270, "y": 420},
        "Fit Structured Output",
        "FitAssessment",
        fit_schema,
    )

    splitter = custom_component_node(
        "ResumeSplitter-001",
        {"x": 360, "y": 420},
        "ResumeSplitterComponent",
        "Resume Splitter",
        "Split concatenated resume uploads into one candidate row per file.",
        "split",
        [
            handle_input("input_value", "Resume Files", ["Message"], "Concatenated resume text."),
            text_input("separator", "Separator", "\n\n===FILE_BOUNDARY===\n\n", "Boundary token between files."),
        ],
        [output_spec("dataframe_output", "Candidate DataFrame", "build_dataframe", ["DataFrame"])],
        RESUME_SPLITTER_CODE.strip(),
        ["DataFrame"],
    )

    loop = loop_node(loop_base, "Loop-CAND001", {"x": 960, "y": 420}, "Candidate Loop")

    candidate_context = custom_component_node(
        "CandidateContext-001",
        {"x": 1320, "y": 420},
        "CandidateContextFormatterComponent",
        "Candidate Context Formatter",
        "Build the candidate extraction message from the loop row.",
        "file-text",
        [handle_input("candidate_row", "Candidate Row", ["Data"], "Single candidate record from the loop.")],
        [output_spec("message_output", "Candidate Message", "build_message", ["Message"])],
        CANDIDATE_CONTEXT_CODE.strip(),
        ["Message"],
    )

    hard_filter = custom_component_node(
        "HardFilter-001",
        {"x": 2310, "y": 420},
        "HardRequirementEvaluatorComponent",
        "Hard Requirement Evaluator",
        "Apply deterministic hard requirement checks.",
        "shield-check",
        [
            handle_input("job_profile", "Job Profile", ["Data"], "Structured job requirements."),
            handle_input("candidate_profile", "Candidate Profile", ["Data"], "Structured candidate profile."),
        ],
        [output_spec("decision_output", "Hard Filter Decision", "evaluate", ["Data"])],
        HARD_FILTER_CODE.strip(),
        ["Data"],
    )

    fit_context = custom_component_node(
        "FitContext-001",
        {"x": 2640, "y": 420},
        "FitContextFormatterComponent",
        "Fit Context Formatter",
        "Combine JD, candidate, and hard filter outputs for fit scoring.",
        "braces",
        [
            handle_input("job_profile", "Job Profile", ["Data"], "Structured job requirements."),
            handle_input("candidate_profile", "Candidate Profile", ["Data"], "Structured candidate profile."),
            handle_input("hard_filter", "Hard Filter", ["Data"], "Hard filter decision."),
        ],
        [output_spec("message_output", "Fit Message", "build_message", ["Message"])],
        FIT_CONTEXT_CODE.strip(),
        ["Message"],
    )

    merger = custom_component_node(
        "ResultMerger-001",
        {"x": 3600, "y": 420},
        "CandidateResultMergerComponent",
        "Candidate Result Merger",
        "Merge candidate profile, hard filter, and fit assessment.",
        "merge",
        [
            handle_input("candidate_profile", "Candidate Profile", ["Data"], "Structured candidate profile."),
            handle_input("hard_filter", "Hard Filter", ["Data"], "Hard filter decision."),
            handle_input("fit_assessment", "Fit Assessment", ["Data"], "Fit scoring output."),
        ],
        [output_spec("result_output", "Candidate Result", "merge", ["Data"])],
        RESULT_MERGER_CODE.strip(),
        ["Data"],
    )

    qualifying_filter = custom_component_node(
        "QualifyingFilter-001",
        {"x": 4200, "y": 420},
        "QualifyingCandidateFilterComponent",
        "Qualifying Candidate Filter",
        "Keep only candidates who passed hard requirements.",
        "filter",
        [handle_input("candidate_results", "Candidate Results", ["DataFrame"], "All merged candidate results.")],
        [output_spec("dataframe_output", "Qualifying Candidates", "filter_candidates", ["DataFrame"])],
        QUALIFYING_FILTER_CODE.strip(),
        ["DataFrame"],
    )

    top_k = custom_component_node(
        "TopK-001",
        {"x": 4530, "y": 420},
        "TopKRankerComponent",
        "Top-K Ranker",
        "Rank qualifying candidates by fit score and apply top-k.",
        "list-ordered",
        [
            handle_input("qualifying_candidates", "Qualifying Candidates", ["DataFrame"], "Qualifying candidates."),
            handle_input("job_profile", "Job Profile", ["Data"], "Structured job requirements."),
        ],
        [output_spec("dataframe_output", "Top Candidates", "rank_candidates", ["DataFrame"])],
        TOP_K_CODE.strip(),
        ["DataFrame"],
    )

    summary_context = custom_component_node(
        "SummaryContext-001",
        {"x": 4860, "y": 420},
        "SummaryContextFormatterComponent",
        "Summary Context Formatter",
        "Build the top-k recommendation payload for summarization.",
        "file-json",
        [handle_input("top_candidates", "Top Candidates", ["DataFrame"], "Ranked top candidates.")],
        [output_spec("message_output", "Summary Message", "build_message", ["Message"])],
        SUMMARY_CONTEXT_CODE.strip(),
        ["Message"],
    )

    summary_agent = agent_node(agent_base, "Agent-SUM001", {"x": 5190, "y": 420}, "Recommendation Summary Agent", SUMMARY_PROMPT)

    final_formatter = custom_component_node(
        "FinalFormatter-001",
        {"x": 5520, "y": 420},
        "FinalFormatterComponent",
        "Final Formatter",
        "Assemble the final response object.",
        "package",
        [
            handle_input("qualifying_candidates", "Qualifying Candidates", ["DataFrame"], "All candidates passing hard requirements."),
            handle_input("top_candidates", "Top Candidates", ["DataFrame"], "Ranked top candidates."),
            handle_input("summary_message", "Summary Message", ["Message"], "Generated shortlist summary."),
        ],
        [output_spec("data_output", "Final Output", "build_output", ["Data"])],
        FINAL_FORMATTER_CODE.strip(),
        ["Data"],
    )

    chat_output = chat_output_node(chat_base, "ChatOutput-001", {"x": 5850, "y": 420})

    nodes.extend(
        [
            jd_file,
            cv_file,
            jd_prompt,
            jd_structured,
            splitter,
            loop,
            candidate_prompt,
            candidate_context,
            candidate_structured,
            hard_filter,
            fit_prompt,
            fit_context,
            fit_structured,
            merger,
            qualifying_filter,
            top_k,
            summary_prompt,
            summary_context,
            summary_agent,
            final_formatter,
            chat_output,
        ]
    )

    def out(node, name):
        for item in node["data"]["node"]["outputs"]:
            if item["name"] == name:
                return item
        raise KeyError((node["id"], name))

    edges = [
        edge(jd_file, out(jd_file, "message"), jd_structured, "input_value"),
        edge(jd_prompt, out(jd_prompt, "prompt"), jd_structured, "system_prompt"),
        edge(cv_file, out(cv_file, "message"), splitter, "input_value"),
        edge(splitter, out(splitter, "dataframe_output"), loop, "data"),
        edge(loop, out(loop, "item"), candidate_context, "candidate_row"),
        edge(candidate_context, out(candidate_context, "message_output"), candidate_structured, "input_value"),
        edge(candidate_prompt, out(candidate_prompt, "prompt"), candidate_structured, "system_prompt"),
        edge(jd_structured, out(jd_structured, "structured_output"), hard_filter, "job_profile"),
        edge(candidate_structured, out(candidate_structured, "structured_output"), hard_filter, "candidate_profile"),
        edge(jd_structured, out(jd_structured, "structured_output"), fit_context, "job_profile"),
        edge(candidate_structured, out(candidate_structured, "structured_output"), fit_context, "candidate_profile"),
        edge(hard_filter, out(hard_filter, "decision_output"), fit_context, "hard_filter"),
        edge(fit_context, out(fit_context, "message_output"), fit_structured, "input_value"),
        edge(fit_prompt, out(fit_prompt, "prompt"), fit_structured, "system_prompt"),
        edge(candidate_structured, out(candidate_structured, "structured_output"), merger, "candidate_profile"),
        edge(hard_filter, out(hard_filter, "decision_output"), merger, "hard_filter"),
        edge(fit_structured, out(fit_structured, "structured_output"), merger, "fit_assessment"),
        edge(merger, out(merger, "result_output"), loop, "item", loop_target=True, loop_output_types=["Data", "Message"]),
        edge(loop, out(loop, "done"), qualifying_filter, "candidate_results"),
        edge(qualifying_filter, out(qualifying_filter, "dataframe_output"), top_k, "qualifying_candidates"),
        edge(jd_structured, out(jd_structured, "structured_output"), top_k, "job_profile"),
        edge(top_k, out(top_k, "dataframe_output"), summary_context, "top_candidates"),
        edge(summary_context, out(summary_context, "message_output"), summary_agent, "input_value"),
        edge(summary_prompt, out(summary_prompt, "prompt"), summary_agent, "system_prompt"),
        edge(qualifying_filter, out(qualifying_filter, "dataframe_output"), final_formatter, "qualifying_candidates"),
        edge(top_k, out(top_k, "dataframe_output"), final_formatter, "top_candidates"),
        edge(summary_agent, out(summary_agent, "response"), final_formatter, "summary_message"),
        edge(final_formatter, out(final_formatter, "data_output"), chat_output, "input_value"),
    ]

    flow = {
        "name": "Hire Agent Preliminary Screening",
        "description": "Screen uploaded resumes against a job description using deterministic hard filters and LLM-assisted fit scoring.",
        "endpoint_name": None,
        "id": FLOW_ID,
        "is_component": False,
        "last_tested_version": "1.8.4",
        "locked": False,
        "tags": ["hiring", "screening", "langflow"],
        "data": {
            "nodes": nodes,
            "edges": edges,
            "viewport": {"x": 151.0, "y": 60.0, "zoom": 0.45},
        },
    }
    return flow


if __name__ == "__main__":
    flow = build_flow()
    OUTPUT.write_text(json.dumps(flow, indent=2))
    print(OUTPUT)
