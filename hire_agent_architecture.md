# Hire Agent Langflow Architecture

## Why not reuse the current flow directly

The existing [HR Recruiting (Backup).json](/Users/mengshangjun/Documents/cmu/14789/project/HR%20Recruiting%20%28Backup%29.json) is a support-quality workflow:

- the first prompt evaluates customer support interactions
- the first structured schema is for `Interaction ID`, `Issue resolved`, `Critical alert`
- the downstream loop classifies text chunks rather than screening resumes

That means the current graph shape is not the right abstraction for hiring. The correct move is a clean rebuild with a few reusable component types rather than trying to retarget the current prompts.

## Target product behavior

Inputs:

- one uploaded job description
- one or more uploaded candidate CVs

Outputs:

- `qualifying_candidates`: candidates who satisfy hard requirements
- `top_k_recommended`: ranked subset of qualifying candidates by fit score
- `recommended_candidate_summary`: generative summary of the recommended candidates

## Design principles

- Keep hard-requirement filtering deterministic and auditable.
- Use LLMs for extraction and fit reasoning, not for binary gating when a rule can do the job.
- Normalize both JD and CVs into structured profiles before any comparison.
- Score only candidates who pass hard filters.
- Keep evidence with every decision so recruiters can inspect why a candidate passed or failed.

## Proposed Langflow graph

### 1. Inputs

`JD File Input` (`File`)
- Single job description upload.
- `advanced_mode=true`
- `markdown=true` if parsing PDFs reliably helps.

`CV File Input` (`File`)
- Multi-file CV upload.
- `advanced_mode=true`
- keep uploaded files separate.

### 2. Job requirement extraction

`JD Extraction Prompt` (`Prompt`)
- Instructs the model to extract normalized hiring requirements from the JD.

`JD Structured Output` (`StructuredOutput`)
- Produces `JobRequirementProfile`.

Schema:

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

### 3. CV fan-out

`Resume File Splitter` (`Custom Python Component`)
- Input: uploaded CV file bundle.
- Output: `DataFrame`, one row per uploaded CV.
- Each row should contain:
  - `candidate_id`
  - `file_name`
  - `resume_text`

This component is the key missing piece in the current backup flow. Chunking text is not enough; the screening loop has to iterate per resume, not per text chunk.

### 4. Per-candidate screening loop

`Candidate Loop` (`LoopComponent`)
- Iterates over one CV at a time.

Inside the loop:

`Candidate Extract Prompt` (`Prompt`)
- Instructs the model to extract candidate facts only from the CV.

`Candidate Structured Output` (`StructuredOutput`)
- Produces `CandidateProfile`.

Schema:

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

`Hard Requirement Evaluator` (`Custom Python Component`)
- Inputs:
  - `JobRequirementProfile`
  - `CandidateProfile`
- Output: `HardFilterDecision`

Rules:

- reject if missing any must-have skill
- reject if below minimum years of experience
- reject if missing required work authorization
- reject if location constraints fail
- optionally reject on required degree or certifications

Schema:

```json
{
  "candidate_id": "str",
  "passes_hard_requirements": "bool",
  "hard_requirement_failures": ["str"],
  "hard_requirement_evidence": ["str"]
}
```

`Fit Scoring Prompt` (`Prompt`)
- Used only after hard requirements are evaluated.
- Prompts the model to assess preference fit across weighted dimensions.

`Fit Scoring Structured Output` (`StructuredOutput`)
- Inputs:
  - `JobRequirementProfile`
  - `CandidateProfile`
  - `HardFilterDecision`
- Output: `FitAssessment`

Schema:

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

### 5. Post-loop aggregation

`Candidate Result Merger` (`Custom Python Component`)
- Joins `CandidateProfile`, `HardFilterDecision`, and `FitAssessment` for each candidate.

`Qualifying Candidate Filter` (`Custom Python Component`)
- Keeps only candidates with `passes_hard_requirements=true`.

`Top-K Ranker` (`Custom Python Component`)
- Sorts qualifying candidates by `fit_score`.
- Applies `top_k` from the JD profile, or a configured default.

### 6. Final generative summary

`Recommendation Summary Prompt` (`Prompt`)
- Produces a recruiter-facing narrative over the ranked shortlist.

`Recommendation Summary Agent` (`Agent` or `VertexAiModel + Prompt`)
- Summarizes top-k recommended candidates only.

`Final Formatter` (`Custom Python Component` or `StructuredOutput`)
- Builds the final API response object.

Schema:

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

## Recommended node list

1. `JD File Input` (`File`)
2. `CV File Input` (`File`)
3. `JD Extraction Prompt` (`Prompt`)
4. `JD Structured Output` (`StructuredOutput`)
5. `Resume File Splitter` (`Custom Python`)
6. `Candidate Loop` (`LoopComponent`)
7. `Candidate Extract Prompt` (`Prompt`)
8. `Candidate Structured Output` (`StructuredOutput`)
9. `Hard Requirement Evaluator` (`Custom Python`)
10. `Fit Scoring Prompt` (`Prompt`)
11. `Fit Scoring Structured Output` (`StructuredOutput`)
12. `Candidate Result Merger` (`Custom Python`)
13. `Qualifying Candidate Filter` (`Custom Python`)
14. `Top-K Ranker` (`Custom Python`)
15. `Recommendation Summary Prompt` (`Prompt`)
16. `Recommendation Summary Agent` (`Agent`)
17. `Final Formatter` (`Custom Python` or `StructuredOutput`)
18. `Chat Output` (`ChatOutput`)

## Recommended edges

1. `JD File Input -> JD Structured Output`
2. `JD Extraction Prompt -> JD Structured Output.system_prompt`
3. `CV File Input -> Resume File Splitter`
4. `Resume File Splitter -> Candidate Loop`
5. `Candidate Loop.item -> Candidate Structured Output`
6. `Candidate Extract Prompt -> Candidate Structured Output.system_prompt`
7. `JD Structured Output -> Hard Requirement Evaluator`
8. `Candidate Structured Output -> Hard Requirement Evaluator`
9. `JD Structured Output -> Fit Scoring Structured Output`
10. `Candidate Structured Output -> Fit Scoring Structured Output`
11. `Hard Requirement Evaluator -> Fit Scoring Structured Output`
12. `Fit Scoring Prompt -> Fit Scoring Structured Output.system_prompt`
13. `Candidate Structured Output -> Candidate Result Merger`
14. `Hard Requirement Evaluator -> Candidate Result Merger`
15. `Fit Scoring Structured Output -> Candidate Result Merger`
16. `Candidate Result Merger -> Candidate Loop`
17. `Candidate Loop.done -> Qualifying Candidate Filter`
18. `Qualifying Candidate Filter -> Top-K Ranker`
19. `Top-K Ranker -> Recommendation Summary Agent`
20. `Recommendation Summary Prompt -> Recommendation Summary Agent.system_prompt`
21. `Qualifying Candidate Filter -> Final Formatter`
22. `Top-K Ranker -> Final Formatter`
23. `Recommendation Summary Agent -> Final Formatter`
24. `Final Formatter -> Chat Output`

## Prompt guidance

### JD extraction prompt

- extract only explicit requirements from the JD
- distinguish must-have from preferred
- normalize synonyms
- do not infer unavailable facts

### Candidate extraction prompt

- extract only evidence present in the CV
- normalize skills and titles
- keep evidence snippets for key claims
- do not infer unstated qualifications

### Fit scoring prompt

- score only if hard filter output is available
- explain the score using requirement-aligned evidence
- penalize missing preferred signals, not missing hard requirements already failed

### Recommendation summary prompt

- summarize only top-k candidates
- compare strengths and tradeoffs across the shortlist
- avoid absolute hiring claims

## Implementation notes

- Do not use Tavily or external search in the initial version.
- Keep enrichment optional and out of the critical path.
- The most important custom components are:
  - `Resume File Splitter`
  - `Hard Requirement Evaluator`
  - `Candidate Result Merger`
  - `Qualifying Candidate Filter`
  - `Top-K Ranker`
- If you want explainability, persist all intermediate structured outputs.

## Recommendation

Treat the current backup JSON as reference only. Build a new flow for hiring rather than editing the support-analysis graph in place.
