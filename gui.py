import os
import json
import uuid
from urllib.parse import urlparse

import requests
import streamlit as st

LANGFLOW_RUN_URL = "http://localhost:7860/api/v1/run/4ac79b81-26b2-4501-910d-e4805cf3b98e"
API_KEY = os.getenv("LANGFLOW_API_KEY", "")
JD_COMPONENT_ID = "File-JD001"
CV_COMPONENT_ID = "File-CV001"


def get_langflow_base_url(run_url: str) -> str:
    parsed = urlparse(run_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def upload_langflow_file(uploaded_file, headers: dict[str, str], base_url: str) -> str:
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }
    response = requests.post(
        f"{base_url}/api/v2/files",
        headers=headers,
        files=files,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    if "path" not in data:
        msg = f"Upload response missing file path: {data}"
        raise ValueError(msg)
    return data["path"]


def extract_answer(data: dict) -> str:
    try:
        return data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
    except (KeyError, IndexError, TypeError):
        return str(data)


def parse_answer_payload(answer: str):
    if not isinstance(answer, str):
        return None

    cleaned = answer.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def render_candidate_card(candidate: dict, rank: int | None = None):
    title = candidate.get("name") or candidate.get("candidate_id") or "Candidate"
    fit_score = candidate.get("fit_score")
    strengths = candidate.get("strengths") or []
    gaps = candidate.get("gaps") or []
    summary = candidate.get("summary") or candidate.get("fit_rationale") or ""

    label = f"#{rank} {title}" if rank is not None else title
    with st.container(border=True):
        cols = st.columns([4, 1])
        with cols[0]:
            st.markdown(f"### {label}")
        with cols[1]:
            if fit_score is not None:
                st.metric("Fit", f"{fit_score}")

        if summary:
            st.write(summary)

        if strengths:
            st.markdown("**Strengths**")
            for item in strengths:
                st.write(f"- {item}")

        if gaps:
            st.markdown("**Gaps**")
            for item in gaps:
                st.write(f"- {item}")


def render_structured_output(result: dict):
    summary = result.get("recommended_candidate_summary")
    top_candidates = result.get("top_k_recommended") or []
    qualifying_candidates = result.get("qualifying_candidates") or []

    summary_col, metrics_col = st.columns([3, 2])
    with summary_col:
        st.subheader("Shortlist Summary")
        if summary:
            st.write(summary)
        else:
            st.caption("No summary returned.")
    with metrics_col:
        st.subheader("Overview")
        st.metric("Qualifying Candidates", len(qualifying_candidates))
        st.metric("Recommended", len(top_candidates))

    st.subheader("Top Recommended Candidates")
    if top_candidates:
        for index, candidate in enumerate(top_candidates, start=1):
            render_candidate_card(candidate, rank=candidate.get("rank") or index)
    else:
        st.info("No recommended candidates were returned.")

    st.subheader("Qualifying Candidate Pool")
    if qualifying_candidates:
        table_rows = []
        for candidate in qualifying_candidates:
            table_rows.append(
                {
                    "name": candidate.get("name"),
                    "candidate_id": candidate.get("candidate_id"),
                    "fit_score": candidate.get("fit_score"),
                    "passes_hard_requirements": candidate.get("passes_hard_requirements"),
                    "fit_rationale": candidate.get("fit_rationale"),
                }
            )
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No qualifying candidates were returned.")


st.set_page_config(page_title="Hire Agent", page_icon="🤖", layout="centered")

st.title("Hire Agent")
st.write("Upload one job description, one or more CVs, and run the Langflow screening flow.")

if not API_KEY:
    st.warning("Set LANGFLOW_API_KEY before running the app.")

job_description = st.file_uploader(
    "Job description",
    type=["pdf", "docx", "txt", "md"],
    accept_multiple_files=False,
)
candidate_cvs = st.file_uploader(
    "Candidate CVs",
    type=["pdf", "docx", "txt", "md"],
    accept_multiple_files=True,
)
user_input = st.text_area("Instruction", value="Screen these candidates against the job description.")

if st.button("Run screening"):
    if not user_input.strip():
        st.warning("Please enter an instruction.")
    elif job_description is None:
        st.warning("Please upload a job description.")
    elif not candidate_cvs:
        st.warning("Please upload at least one CV.")
    else:
        headers = {
            "accept": "application/json",
            "x-api-key": API_KEY,
        }
        base_url = get_langflow_base_url(LANGFLOW_RUN_URL)

        try:
            with st.spinner("Uploading files to Langflow..."):
                jd_path = upload_langflow_file(job_description, headers, base_url)
                cv_paths = [upload_langflow_file(candidate_cv, headers, base_url) for candidate_cv in candidate_cvs]

            payload = {
                "output_type": "chat",
                "input_type": "text",
                "input_value": user_input,
                "session_id": str(uuid.uuid4()),
                "tweaks": {
                    JD_COMPONENT_ID: {
                        "path": [jd_path],
                    },
                    CV_COMPONENT_ID: {
                        "path": cv_paths,
                    },
                },
            }

            with st.spinner("Running agent..."):
                run_headers = {
                    "Content-Type": "application/json",
                    "x-api-key": API_KEY,
                }
                response = requests.post(LANGFLOW_RUN_URL, json=payload, headers=run_headers, timeout=180)
                response.raise_for_status()
                data = response.json()

            answer = extract_answer(data)
            parsed_answer = parse_answer_payload(answer)

            if isinstance(parsed_answer, dict):
                render_structured_output(parsed_answer)
            else:
                st.subheader("Agent Response")
                st.write(answer)

            with st.expander("Raw response"):
                st.json(data)

        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {e}")
        except ValueError as e:
            st.error(f"Failed to parse JSON response: {e}")
