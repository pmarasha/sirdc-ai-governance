# SIRDC AI POLICY v1.0 (Draft)

## Section 1 — Purpose
This policy governs the use, development, procurement, and deployment of
Artificial Intelligence systems across all SIRDC institutes.

## Section 2 — Scope
Applies to all staff, contractors, and researchers who design, build,
purchase, or operate AI systems.

## Section 3 — Risk Classification
All AI systems MUST be assigned one of four tiers:
- Prohibited: social scoring, mass surveillance, manipulation of minors.
- High: medical diagnosis, HR screening, biometric identification,
  safety-critical systems, credit/eligibility decisions.
- Limited: chatbots, content generation, internal recommendation engines.
- Minimal: spam filters, internal search, productivity tools.

## Section 4 — Data Protection
4.1 Personal data (names, IDs, salaries, medical records, biometrics)
    MUST NOT be sent to any public LLM (e.g., ChatGPT, Gemini).
4.2 Confidential research data MUST NOT be sent to any public LLM
    unless approved in writing by the AI Review Board.
4.3 Anonymised or synthetic data may be used with public LLMs.
4.4 Any use of personal data for model training requires:
    (a) explicit consent, OR
    (b) irreversible anonymisation, AND
    (c) AI Review Board approval.

## Section 5 — Human Oversight
5.1 All High-risk systems MUST have a named human-in-the-loop reviewer.
5.2 All High-risk decisions MUST be logged with reviewer name and timestamp.
5.3 Prohibited systems MUST NOT be developed or deployed under any
    circumstances.

## Section 6 — Review Cadence
6.1 High-risk systems: review every 6 months.
6.2 Limited-risk systems: review every 12 months.
6.3 Minimal-risk systems: review every 12 months.
6.4 Overdue reviews MUST be escalated to the institute lead within 7 days.

## Section 7 — Transparency
7.1 Every AI system MUST be registered in the SIRDC AI Inventory.
7.2 Users MUST be informed when they are interacting with an AI system.
7.3 Model cards MUST be produced for all High-risk systems.

## Section 8 — Incident Reporting
8.1 Any harm, bias, or unexpected behaviour from an AI system MUST be
    reported within 24 hours to the AI Governance Lead.
8.2 Incidents MUST be logged in the dashboard.

## Section 9 — Procurement
9.1 Third-party AI tools MUST undergo a governance review before purchase.
9.2 Vendors MUST provide documentation of their training data and
    data retention practices.

## Section 10 — Enforcement
Violations may result in suspension of the AI system, retraining
requirements, or disciplinary action.