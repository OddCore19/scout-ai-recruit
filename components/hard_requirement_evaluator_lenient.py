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
        cleaned = value.strip().lower()
        return [cleaned] if cleaned else []
    return [str(item).strip().lower() for item in value if str(item).strip()]


class HardRequirementEvaluatorLenientComponent(Component):
    display_name = "Hard Requirement Evaluator (Lenient)"
    description = "Apply deterministic hard checks but treat missing candidate evidence as inconclusive, not disqualifying."
    icon = "shield"
    name = "HardRequirementEvaluatorLenient"

    inputs = [
        HandleInput(name="job_profile", display_name="Job Profile", input_types=["Data"], required=True),
        HandleInput(name="candidate_profile", display_name="Candidate Profile", input_types=["Data"], required=True),
    ]

    outputs = [
        Output(display_name="Hard Filter Decision", name="decision_output", method="evaluate"),
    ]

    def _evaluate_required_skills(self, job: dict, candidate: dict, failures: list[str], evidence: list[str], warnings: list[str]):
        required_skills = set(_norm_list(job.get("required_skills")))
        candidate_skills = set(_norm_list(candidate.get("skills")))

        if not required_skills:
            return
        if not candidate_skills:
            warnings.append("No candidate skills were extracted; required skills check treated as inconclusive.")
            return

        missing_skills = sorted(required_skills - candidate_skills)
        if missing_skills:
            failures.append(f"Missing required skills from extracted profile: {', '.join(missing_skills)}")
        else:
            evidence.append("Required skills present in extracted candidate profile.")

    def _evaluate_experience(self, job: dict, candidate: dict, failures: list[str], evidence: list[str], warnings: list[str]):
        required_years = int(job.get("required_years_experience") or 0)
        candidate_years_raw = candidate.get("years_experience")

        if required_years <= 0:
            return
        if candidate_years_raw in (None, "", 0):
            warnings.append("Years of experience were not explicitly available; experience check treated as inconclusive.")
            return

        candidate_years = int(candidate_years_raw)
        if candidate_years < required_years:
            failures.append(
                f"Years of experience below minimum: candidate={candidate_years}, required={required_years}"
            )
        else:
            evidence.append(f"Experience threshold met: {candidate_years} years.")

    def _evaluate_authorization(self, job: dict, candidate: dict, failures: list[str], evidence: list[str], warnings: list[str]):
        required_auth = _norm_list(job.get("required_work_authorization"))
        candidate_auth = " ".join(_norm_list(candidate.get("work_authorization")))

        if not required_auth:
            return
        if not candidate_auth:
            warnings.append("Work authorization was not explicitly available; authorization check treated as inconclusive.")
            return

        if any(item in candidate_auth for item in required_auth):
            evidence.append("Work authorization requirement appears satisfied.")
            return

        negative_markers = ["no", "not", "without", "unable", "require sponsorship", "needs sponsorship"]
        if any(marker in candidate_auth for marker in negative_markers):
            failures.append("Work authorization appears incompatible with job requirements.")
        else:
            warnings.append("Work authorization could not be matched confidently; treated as inconclusive.")

    def _evaluate_location(self, job: dict, candidate: dict, failures: list[str], evidence: list[str], warnings: list[str]):
        required_location = _norm_list(job.get("required_location_constraints"))
        candidate_location = " ".join(_norm_list(candidate.get("current_location")))

        if not required_location:
            return
        if not candidate_location:
            warnings.append("Candidate location was not explicitly available; location check treated as inconclusive.")
            return

        if any(item in candidate_location for item in required_location):
            evidence.append("Location constraint appears satisfied.")
        else:
            warnings.append("Candidate location does not clearly match job constraint; treated as inconclusive.")

    def _evaluate_certifications(self, job: dict, candidate: dict, failures: list[str], evidence: list[str], warnings: list[str]):
        required_certs = set(_norm_list(job.get("required_certifications")))
        candidate_certs = set(_norm_list(candidate.get("certifications")))

        if not required_certs:
            return
        if not candidate_certs:
            warnings.append("No certifications were extracted; certification check treated as inconclusive.")
            return

        missing_certs = sorted(required_certs - candidate_certs)
        if missing_certs:
            failures.append(f"Missing required certifications from extracted profile: {', '.join(missing_certs)}")
        else:
            evidence.append("Required certifications present in extracted candidate profile.")

    def evaluate(self) -> Data:
        job = _unwrap(self.job_profile) or {}
        candidate = _unwrap(self.candidate_profile) or {}

        failures: list[str] = []
        evidence: list[str] = []
        warnings: list[str] = []

        self._evaluate_required_skills(job, candidate, failures, evidence, warnings)
        self._evaluate_experience(job, candidate, failures, evidence, warnings)
        self._evaluate_authorization(job, candidate, failures, evidence, warnings)
        self._evaluate_location(job, candidate, failures, evidence, warnings)
        self._evaluate_certifications(job, candidate, failures, evidence, warnings)

        return Data(
            data={
                "candidate_id": candidate.get("candidate_id"),
                "name": candidate.get("name"),
                "passes_hard_requirements": len(failures) == 0,
                "hard_requirement_failures": failures,
                "hard_requirement_evidence": evidence,
                "hard_requirement_warnings": warnings,
            }
        )
