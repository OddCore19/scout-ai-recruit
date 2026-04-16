# Hire Agent Prototype

Prototype Langflow workflow and Streamlit client for preliminary hiring screening.

## Contents

- `Hire Agent Preliminary Screening.json`: importable Langflow flow
- `components/`: custom Langflow components
- `gui.py`: Streamlit UI for JD/CV upload and flow execution
- `generate_hire_langflow.py`: regenerates the flow JSON

## Run locally

1. Start Langflow locally.
2. Export your API key:

```bash
export LANGFLOW_API_KEY="your_api_key"
```

3. Run the Streamlit app:

```bash
streamlit run gui.py
```

## Notes

- The Streamlit client expects the flow endpoint configured in `gui.py`.
- File uploads use Langflow `/api/v2/files`, then pass file paths through flow `tweaks`.
