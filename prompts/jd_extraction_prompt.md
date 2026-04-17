Extract a normalized hiring requirements profile from the job description.

Rules:

- Separate explicit hard requirements from preferred qualifications.
- Do not infer requirements that are not stated.
- Normalize equivalent skills and credentials where obvious.
- If a requirement is missing, return an empty list or null-compatible default.
- Return only information supported by the job description text.
