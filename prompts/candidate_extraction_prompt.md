Extract a normalized candidate profile from the resume text.

You are not limited to an explicit `Skills` section. You must gather candidate skills from all evidence in the resume, including:

- experience bullets
- project descriptions
- responsibilities
- tools and technologies mentioned under roles
- certifications
- education, coursework, and research only when they clearly indicate hands-on use

Rules:

- Use only evidence present in the resume.
- Do not invent qualifications, employers, titles, or technologies that are not supported by the text.
- Treat technologies, tools, frameworks, programming languages, cloud platforms, databases, and methods mentioned in work or project experience as skills, even if they are not listed in a dedicated skills section.
- If a candidate describes having built, implemented, maintained, analyzed, deployed, migrated, optimized, or led work using a tool or technology, include that tool or technology in `skills`.
- Prefer normalized canonical names in `skills`.
  - Example: `Google Cloud Platform` -> `GCP`
  - Example: `Amazon Web Services` -> `AWS`
  - Example: `Postgres` -> `PostgreSQL`
- Do not add a skill based only on vague adjacent context.
  - Example: if a team used Kubernetes but the candidate’s contribution does not mention it, do not add `Kubernetes`.
- Estimate `years_experience` conservatively if a direct value is not stated.
- Keep `evidence` short, quote-like, and tied to the actual supporting text.
- If the resume includes multiple spellings or aliases for the same skill, normalize them to one canonical skill entry but preserve supporting evidence.
- Extract `summary` as a short recruiter-readable snapshot of the candidate’s background.

Extraction guidance for `skills`:

- Include explicit skills listed in a skills section.
- Also include implicit skills demonstrated through actual work, project, or research descriptions.
- Prioritize skills with direct action evidence over generic exposure.
- Prefer precision over recall when evidence is weak, but do not miss clearly demonstrated technologies from experience bullets.

Return a normalized candidate profile from the full resume, not only from a dedicated skills section.
