from typing import cast

from pydantic import BaseModel, Field, create_model

from lfx.base.models.chat_result import get_chat_result
from lfx.custom.custom_component.component import Component
from lfx.helpers.base_model import build_model_from_schema
from lfx.inputs.inputs import MessageTextInput
from lfx.io import (
    FileInput,
    FloatInput,
    IntInput,
    MultilineInput,
    Output,
    StrInput,
    TableInput,
)
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.schema.table import EditMode


class VertexAIStructuredOutputComponent(Component):
    display_name = "Vertex AI Structured Output"
    description = "Generate structured data using Vertex AI chat models without trustcall."
    documentation: str = "https://python.langchain.com/docs/integrations/chat/google_vertex_ai_palm/"
    name = "VertexAIStructuredOutput"
    icon = "braces"

    inputs = [
        FileInput(
            name="credentials",
            display_name="Credentials",
            info="JSON credentials file. Leave empty to fallback to environment variables",
            file_types=["json"],
        ),
        MessageTextInput(name="model_name", display_name="Model Name", value="gemini-2.5-flash"),
        StrInput(name="project", display_name="Project", info="The project ID.", advanced=True),
        StrInput(name="location", display_name="Location", value="us-central1", advanced=True),
        IntInput(name="max_output_tokens", display_name="Max Output Tokens", advanced=True),
        IntInput(name="max_retries", display_name="Max Retries", value=1, advanced=True),
        FloatInput(name="temperature", value=0.0, display_name="Temperature"),
        IntInput(name="top_k", display_name="Top K", advanced=True),
        FloatInput(name="top_p", display_name="Top P", value=0.95, advanced=True),
        MultilineInput(
            name="input_value",
            display_name="Input Message",
            info="The input message to the language model.",
            tool_mode=True,
            required=True,
        ),
        MultilineInput(
            name="system_prompt",
            display_name="Format Instructions",
            info="The instructions to the language model for formatting the output.",
            value=(
                "Extract structured data from the input and return only valid JSON matching the provided schema. "
                "Do not add markdown fences, commentary, or extra keys."
            ),
            required=True,
            advanced=True,
        ),
        MessageTextInput(
            name="schema_name",
            display_name="Schema Name",
            info="Provide a name for the output data schema.",
            advanced=True,
        ),
        TableInput(
            name="output_schema",
            display_name="Output Schema",
            info="Define the structure and data types for the model's output.",
            required=True,
            table_schema=[
                {
                    "name": "name",
                    "display_name": "Name",
                    "type": "str",
                    "description": "Specify the name of the output field.",
                    "default": "field",
                    "edit_mode": EditMode.INLINE,
                },
                {
                    "name": "description",
                    "display_name": "Description",
                    "type": "str",
                    "description": "Describe the purpose of the output field.",
                    "default": "description of field",
                    "edit_mode": EditMode.POPOVER,
                },
                {
                    "name": "type",
                    "display_name": "Type",
                    "type": "str",
                    "edit_mode": EditMode.INLINE,
                    "description": "Indicate the data type of the output field (e.g., str, int, float, bool, dict).",
                    "options": ["str", "int", "float", "bool", "dict"],
                    "default": "str",
                },
                {
                    "name": "multiple",
                    "display_name": "As List",
                    "type": "boolean",
                    "description": "Set to True if this output field should be a list of the specified type.",
                    "default": "False",
                    "edit_mode": EditMode.INLINE,
                },
            ],
            value=[
                {
                    "name": "field",
                    "description": "description of field",
                    "type": "str",
                    "multiple": "False",
                }
            ],
        ),
        StrInput(
            name="method",
            display_name="Structured Output Method",
            value="with_structured_output",
            advanced=True,
            info="Reserved for future native JSON-schema mode. Current implementation uses LangChain ChatVertexAI.with_structured_output.",
        ),
    ]

    outputs = [
        Output(
            name="structured_output",
            display_name="Structured Output",
            method="build_structured_output",
        ),
        Output(
            name="dataframe_output",
            display_name="Structured Output",
            method="build_structured_dataframe",
        ),
    ]

    def build_model(self):
        try:
            from langchain_google_vertexai import ChatVertexAI
        except ImportError as e:
            msg = "Please install the langchain-google-vertexai package to use Vertex AI structured output."
            raise ImportError(msg) from e

        location = self.location or None
        if self.credentials:
            from google.cloud import aiplatform
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(self.credentials)
            project = self.project or credentials.project_id
            aiplatform.init(
                project=project,
                location=location,
                credentials=credentials,
            )
        else:
            project = self.project or None
            credentials = None

        return cast(
            "object",
            ChatVertexAI(
                credentials=credentials,
                location=location,
                project=project,
                max_output_tokens=self.max_output_tokens or None,
                max_retries=self.max_retries,
                model_name=self.model_name,
                temperature=self.temperature,
                top_k=self.top_k or None,
                top_p=self.top_p,
            ),
        )

    def _build_output_model(self):
        if not self.output_schema:
            msg = "Output schema cannot be empty"
            raise ValueError(msg)

        schema_name = self.schema_name or "OutputModel"
        output_model_ = build_model_from_schema(self.output_schema)
        return create_model(
            schema_name,
            __doc__=f"A list of {schema_name}.",
            objects=(
                list[output_model_],
                Field(
                    description=f"A list of {schema_name}.",  # type: ignore[valid-type]
                    min_length=1,
                ),
            ),
        )

    def _normalize_structured_result(self, result):
        if isinstance(result, BaseModel):
            result = result.model_dump()

        if isinstance(result, dict):
            objects = result.get("objects")
            if isinstance(objects, list):
                return objects
            return [result]

        if isinstance(result, list):
            normalized = []
            for item in result:
                if isinstance(item, BaseModel):
                    normalized.append(item.model_dump())
                else:
                    normalized.append(item)
            return normalized

        msg = f"Unexpected structured output type: {type(result).__name__}"
        raise ValueError(msg)

    def build_structured_output_base(self):
        llm = self.build_model()
        output_model = self._build_output_model()

        if not hasattr(llm, "with_structured_output"):
            msg = "Vertex AI model wrapper does not support with_structured_output."
            raise TypeError(msg)

        llm_with_structured_output = llm.with_structured_output(output_model)
        config_dict = {
            "run_name": self.display_name,
            "project_name": self.get_project_name(),
            "callbacks": self.get_langchain_callbacks(),
        }
        result = get_chat_result(
            runnable=llm_with_structured_output,
            system_message=self.system_prompt,
            input_value=self.input_value,
            config=config_dict,
        )
        return self._normalize_structured_result(result)

    def build_structured_output(self) -> Data:
        output = self.build_structured_output_base()
        if not output:
            msg = "No structured output returned"
            raise ValueError(msg)
        if len(output) == 1:
            return Data(data=output[0])
        return Data(data={"results": output})

    def build_structured_dataframe(self) -> DataFrame:
        output = self.build_structured_output_base()
        if not output:
            msg = "No structured output returned"
            raise ValueError(msg)
        return DataFrame(output)
