# Scout AI Recruit Technical Specification

## 1. Purpose

Scout AI Recruit is a Langflow-based preliminary hiring screen that evaluates uploaded candidate CVs against an uploaded job description. The system is designed for recruiter-side triage, not final hiring decisions.

The project produces three primary outputs:

- `qualifying_candidates`: candidates that pass deterministic hard requirements
- `top_k_recommended`: ranked shortlist from the qualifying pool
- `recommended_candidate_summary`: recruiter-facing generative summary of the shortlisted candidates

## 2. Project Artifacts

Core project files:

- [Hire Agent Preliminary Screening.json](/Users/mengshangjun/Documents/cmu/14789/project/Hire%20Agent%20Preliminary%20Screening.json): importable Langflow flow
- [generate_hire_langflow.py](/Users/mengshangjun/Documents/cmu/14789/project/generate_hire_langflow.py): generator for the Langflow flow JSON
- [components/vertex_ai_structured_output.py](/Users/mengshangjun/Documents/cmu/14789/project/components/vertex_ai_structured_output.py): Vertex AI structured output kernel
- [components/vertex_ai.py](/Users/mengshangjun/Documents/cmu/14789/project/components/vertex_ai.py): Vertex AI model component source
- [components/structured_ouput.py](/Users/mengshangjun/Documents/cmu/14789/project/components/structured_ouput.py): original generic structured output component
- [gui.py](/Users/mengshangjun/Documents/cmu/14789/project/gui.py): Streamlit client for file upload and flow execution

## 3. Functional Scope

### 3.1 Inputs

- One job description file
- One or more candidate CV files
- Optional recruiter instruction text for the run

### 3.2 Outputs

- Full list of candidates that satisfy hard requirements
- Ranked top-k recommendation set
- Natural-language summary of the recommendation set

### 3.3 Non-goals

- Final hiring recommendation
- Background checks
- External enrichment from LinkedIn, GitHub, or web search
- Interview scheduling or ATS writeback

## 4. Design Principles

- Hard requirements must be deterministic and auditable.
- LLMs should be used for extraction and fit reasoning, not binary screening logic that can be implemented as rules.
- The job description and CVs must be normalized into structured profiles before any comparison.
- All ranking decisions should preserve evidence and rationale.
- The shortlist summary must only describe the returned candidates, not invent missing data.

## 5. System Overview

The system consists of four major stages:

1. Job description ingestion and normalization
2. Candidate resume ingestion and per-candidate screening
3. Aggregation, qualification filtering, and ranking
4. Shortlist summarization and API/UI presentation

At runtime:

1. The client uploads source files to Langflow `/api/v2/files`.
2. The flow receives uploaded file paths through `tweaks` targeting the two `Read File` nodes.
3. The flow parses, extracts, filters, scores, and summarizes.
4. The client renders either structured JSON output or plain text fallback.

## 6. Runtime Architecture

### 6.1 Flow Name

`Hire Agent Preliminary Screening`

### 6.2 Node Inventory

The current generated flow contains 21 nodes and 28 edges.

Nodes:

1. `File-JD001` (`JD File`)
2. `File-CV001` (`CV Files`)
3. `Prompt-JD001` (`JD Extraction Prompt`)
4. `StructuredOutput-JD001` (`JD Structured Output`)
5. `ResumeSplitter-001` (`Resume Splitter`)
6. `Loop-CAND001` (`Candidate Loop`)
7. `Prompt-CAND001` (`Candidate Extraction Prompt`)
8. `CandidateContext-001` (`Candidate Context Formatter`)
9. `StructuredOutput-CAND001` (`Candidate Structured Output`)
10. `HardFilter-001` (`Hard Requirement Evaluator`)
11. `Prompt-FIT001` (`Fit Scoring Prompt`)
12. `FitContext-001` (`Fit Context Formatter`)
13. `StructuredOutput-FIT001` (`Fit Structured Output`)
14. `ResultMerger-001` (`Candidate Result Merger`)
15. `QualifyingFilter-001` (`Qualifying Candidate Filter`)
16. `TopK-001` (`Top-K Ranker`)
17. `Prompt-SUM001` (`Recommendation Summary Prompt`)
18. `SummaryContext-001` (`Summary Context Formatter`)
19. `Agent-SUM001` (`Recommendation Summary Agent`)
20. `FinalFormatter-001` (`Final Formatter`)
21. `ChatOutput-001` (`Chat Output`)

### 6.3 Execution Stages

#### Stage A: Job Description Extraction

- `File-JD001` reads the uploaded JD file.
- `Prompt-JD001` provides extraction instructions.
- `StructuredOutput-JD001` converts JD text into `JobRequirementProfile`.

#### Stage B: Resume Fan-out and Candidate Normalization

- `File-CV001` reads uploaded CV files.
- `ResumeSplitter-001` splits the combined file content into one candidate record per file.
- `Loop-CAND001` iterates over candidate records.
- `CandidateContext-001` formats each record for structured extraction.
- `Prompt-CAND001` provides candidate extraction instructions.
- `StructuredOutput-CAND001` produces `CandidateProfile`.

#### Stage C: Deterministic Screening and Fit Scoring

- `HardFilter-001` compares `CandidateProfile` against `JobRequirementProfile`.
- `FitContext-001` combines job profile, candidate profile, and hard filter decision.
- `Prompt-FIT001` provides fit scoring instructions.
- `StructuredOutput-FIT001` produces `FitAssessment`.
- `ResultMerger-001` merges extraction, filtering, and fit outputs for the current candidate.
- `Loop-CAND001` collects the merged candidate records.

#### Stage D: Ranking and Summary

- `QualifyingFilter-001` keeps only candidates with `passes_hard_requirements = true`.
- `TopK-001` sorts qualifying candidates by `fit_score` and truncates to `top_k`.
- `SummaryContext-001` prepares the shortlisted candidates as a summarization payload.
- `Prompt-SUM001` provides summary instructions.
- `Agent-SUM001` generates recruiter-facing narrative output.
- `FinalFormatter-001` assembles the final response object.
- `ChatOutput-001` publishes the result.

## 7. Data Contracts

### 7.1 JobRequirementProfile

```json
{
  "role_title": "str",
  "role_family": "str",
  "required_skills": ["str"],
  "preferred_skills": ["str"],
  "required_years_experience": "int",
  "required_education": ["str"],
  "required_certifications": ["str"],
  "required_location_constraints": ["str"],
  "required_work_authorization": ["str"],
  "required_industry_experience": ["str"],
  "responsibilities": ["str"],
  "fit_dimensions": ["str"],
  "top_k": "int"
}
```

### 7.2 CandidateProfile

```json
{
  "candidate_id": "str",
  "name": "str",
  "email": "str",
  "phone": "str",
  "current_location": "str",
  "work_authorization": "str",
  "skills": ["str"],
  "education": ["str"],
  "certifications": ["str"],
  "years_experience": "int",
  "titles": ["str"],
  "companies": ["str"],
  "industry_experience": ["str"],
  "summary": "str",
  "evidence": {
    "skills": ["str"],
    "experience": ["str"],
    "education": ["str"]
  }
}
```

### 7.3 HardFilterDecision

```json
{
  "candidate_id": "str",
  "name": "str",
  "passes_hard_requirements": "bool",
  "hard_requirement_failures": ["str"],
  "hard_requirement_evidence": ["str"]
}
```

### 7.4 FitAssessment

```json
{
  "candidate_id": "str",
  "fit_score": "float",
  "dimension_scores": {
    "skills_alignment": "float",
    "relevant_experience": "float",
    "industry_fit": "float",
    "seniority_fit": "float",
    "education_fit": "float"
  },
  "strengths": ["str"],
  "gaps": ["str"],
  "fit_rationale": "str"
}
```

### 7.5 Final Output

```json
{
  "qualifying_candidates": [
    {
      "candidate_id": "str",
      "name": "str",
      "passes_hard_requirements": "bool",
      "fit_score": "float",
      "hard_requirement_evidence": ["str"],
      "fit_rationale": "str"
    }
  ],
  "top_k_recommended": [
    {
      "rank": "int",
      "candidate_id": "str",
      "name": "str",
      "fit_score": "float",
      "strengths": ["str"],
      "gaps": ["str"],
      "summary": "str"
    }
  ],
  "recommended_candidate_summary": "str"
}
```

## 8. Custom Components

Project-specific custom components currently used in the generated flow:

- `ResumeSplitterComponent`
- `CandidateContextFormatterComponent`
- `VertexAIStructuredOutput`
- `HardRequirementEvaluatorComponent`
- `FitContextFormatterComponent`
- `CandidateResultMergerComponent`
- `QualifyingCandidateFilterComponent`
- `TopKRankerComponent`
- `SummaryContextFormatterComponent`
- `FinalFormatterComponent`

## 9. Vertex AI Structured Output Kernel

### 9.1 Motivation

The original generic structured output block relied on:

- `trustcall.create_extractor(...)`
- `llm.with_structured_output(...)`

This produced unstable behavior with `gemini-2.5-flash` in the current Langflow setup. The project now includes a Vertex-specific structured output kernel to remove the `trustcall` dependency and align the structured extraction path with the Vertex AI model configuration used elsewhere in the project.

### 9.2 Current Kernel

Implementation:

- [components/vertex_ai_structured_output.py](/Users/mengshangjun/Documents/cmu/14789/project/components/vertex_ai_structured_output.py)

Responsibilities:

- build `ChatVertexAI` with project, location, credentials, and sampling parameters
- compile the table schema into a Pydantic model
- wrap the schema inside an outer `objects: list[...]` container
- invoke `with_structured_output(...)`
- normalize outputs into Langflow `Data` or `DataFrame`

### 9.3 Current Limitation

In the current Langflow import path, prompt-to-custom-component connections targeting `system_prompt` may be dropped as invalid even though the field exists in the component template. The technical workaround is to keep instruction text directly in the node default values when necessary.

## 10. Screening Logic

### 10.1 Deterministic Hard Filter

The hard requirement evaluator currently checks:

- missing required skills
- minimum years of experience
- required work authorization
- required location constraints
- required certifications

The hard filter produces explicit failures and supporting evidence. A candidate only enters the ranking pool if all active hard checks pass.

### 10.2 Fit Scoring

Fit scoring is LLM-assisted and should only evaluate candidates relative to:

- skills alignment
- relevant experience
- industry fit
- seniority fit
- education fit

If a candidate fails hard requirements, the fit stage may still produce output for traceability, but downstream qualification filtering removes the candidate from the ranked pool.

## 11. API and Client Integration

### 11.1 File Uploads

The Streamlit client uploads source files to:

- `POST /api/v2/files`

The returned `path` values are sent into the flow through `tweaks`.

### 11.2 Flow Invocation

The client runs the flow with:

- `POST /api/v1/run/<flow_id>`

The current UI uses the two file component IDs:

- `File-JD001`
- `File-CV001`

### 11.3 UI Behavior

The Streamlit client:

- uploads JD and CV files
- injects uploaded file paths into Langflow
- runs the flow
- attempts to parse the response as structured JSON
- renders shortlist cards, metrics, and candidate tables when structured output is returned
- falls back to plain text otherwise

## 12. Operational Assumptions

- Langflow is running locally and reachable from the Streamlit app.
- The configured flow ID exists and matches the generated flow.
- `LANGFLOW_API_KEY` is available in the environment.
- Vertex AI credentials are provided either through the component file input or the runtime environment.

## 13. Risks and Open Issues

- Langflow import behavior for custom component prompt handles is inconsistent.
- The Vertex AI structured output kernel is syntax-checked locally but not fully validated against every installed Langflow environment.
- The recommendation summary agent remains generative and can still vary between runs.
- The flow currently avoids external enrichment, which limits validation against candidate public profiles.

## 14. Future Work

- Replace prompt-edge dependence with baked-in node defaults or a more robust custom input contract.
- Add native Vertex/Gemini JSON schema mode if direct API support is preferable to `with_structured_output`.
- Add role-specific configurable hard filters and weights.
- Add evaluation fixtures and regression tests for extraction and ranking quality.
- Add persistence or ATS integration if the project moves beyond prototype stage.
