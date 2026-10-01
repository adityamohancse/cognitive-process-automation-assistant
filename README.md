# IT Support Automation Assistant

A hands-on Cognitive Process Automation demo for a fictional enterprise client. The solution uses IBM watsonx Assistant for guided actions and policy answers, a FastAPI mock ticket service, and an optional Python client using the IBM watsonx Assistant v2 SDK.

> **Plan check first:** IBM documentation currently says the Assistant v2 runtime API requires Plus or higher, while plan availability and UI entitlements can vary. Verify the current Lite/free-tier limits in your IBM Cloud account before relying on `/chat`. The Assistant UI/action build and this local mock-ticket integration can still be demonstrated independently.

## 1. What the client needs

| Process step | Assistant action | API/integration | Business benefit |
|---|---|---|---|
| Password reset | Collect employee ID, security answer, confirmation | `POST /create-ticket` with `ticket_type=password_reset` | Reduces repetitive service-desk contacts while retaining identity checks |
| Laptop request | Collect employee ID, department, laptop type, justification, confirmation | `POST /create-ticket` with `ticket_type=laptop_request` | Standardizes request intake and approval routing |
| Access request | Collect system and manager, confirm | `POST /create-ticket` with `ticket_type=access_request` | Produces complete, traceable access requests |
| Policy questions | Conversational search over VPN, equipment leave, and security policy documents | watsonx Assistant search/knowledge source | Gives consistent answers with source-grounded content |
| Escalation | Detect frustration or two failed attempts, summarize and hand off | Human-agent handoff or webhook; local summary model in `app/main.py` | Preserves context and reduces agent after-call discovery time |

## 2. Architecture

```text
Employee
   |
   v
watsonx Assistant (Actions + conversational search)
   |                         |
   | custom extension         | optional v2 runtime API
   v                         v
FastAPI /create-ticket  FastAPI /chat
   |                         |
   v                         v
Mock ticket store       IBM AssistantV2 SDK
                              |
                              v
                       watsonx Assistant environment

Human agent receives: issue + completed steps + sentiment + ticket number
```

## 3. Prerequisites and account setup

1. Create or use an IBM Cloud account at [cloud.ibm.com](https://cloud.ibm.com/).
2. Open the IBM Cloud catalog and search for **watsonx Assistant**. Select the current available Lite/free option if shown.
3. Create an Assistant and an environment. IBM may label the product and menu differently as the service evolves; verify the current plan, region, quotas, and trial expiration in the service page.
4. Record the service URL, assistant ID, environment ID, and API key only in `.env`; never commit secrets.
5. In the assistant editor, create the four actions described below. UI labels can change, so look for the current equivalents of **Actions**, **Integrations**, **Search/knowledge**, **Extensions**, **Preview**, and **Human agent/handoff**.
6. Install Python 3.10+ and run the local service:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

## 4. Two-to-three day build plan

### Day 1: process design and Assistant UI

1. Convert the process definition above into a short requirements summary: actors are employees, service desk agents, and approvers; systems are watsonx Assistant and the ticket API; controls are identity validation, confirmation, auditability, and escalation.
2. Open the Assistant editor and select the current **Actions** area. Choose the current equivalent of **Create action** for each of the four actions. If the UI offers a starter/template, use it; otherwise create blank actions. IBM can rename these controls, so verify the labels in your tenant.
3. For each action, add steps in this order: **Ask/collect**, **Validate** (or a condition), **Confirm**, **Use an extension** (after Day 2), and **Message/report result**. In the action's variables, use names such as `employee_id`, `department`, `laptop_type`, `justification`, `system_name`, and `manager_name`.
4. Add a general fallback. On the first failure, ask the user to rephrase or choose a supported value. On the second failure, offer human help and preserve the summary. The exact fallback control may be under **Settings**, **Behavior**, or the action editor in your tenant.
5. Add interruption handling so a user can ask a related question and return to the unfinished action. Look for the current equivalent of **Allow interruptions**, **Handle interruptions**, or a global search/answer setting.

**Suggested UI navigation (verify current labels):** IBM Cloud console → watsonx Assistant service → open Assistant → select the development environment → **Actions** → create/edit action → add steps → **Preview**. For knowledge, use the current **Search**, **Knowledge**, or **Data sources** area associated with the Assistant, then return to **Preview** and test source-grounded answers. For extension setup, use **Integrations** → **Extensions** → **Build custom extension**; IBM’s current documentation specifically describes this path and requires an OpenAPI 3.0 JSON document.

### Day 2: search, extension, and local integration

1. In the current Assistant UI, locate the search or knowledge-source configuration. Upload the three original policy files in `policies/`. If PDF is required, export each Markdown file to PDF without changing its text.
2. Test policy questions with citations/source snippets if the current experience supports them.
3. Start the local FastAPI service and expose it through a reachable HTTPS URL for a real custom extension test. For local-only testing, use the endpoint directly.
4. Import `openapi.json` from the Assistant **Integrations** area. IBM’s current custom-extension documentation says the import must be OpenAPI 3.0 JSON, with absolute server URLs and a clear operation summary.
5. In the action editor, add a custom-extension step for `createTicket`, map collected variables into the request body, and map `ticket_id`, `status`, and `next_step` into response variables.

### Day 3: testing and stakeholder demo

1. Run the ten conversations in `docs/test-conversations.md`.
2. Record actual results in the table; do not mark a test passed until you run it in your own environment.
3. Prepare the non-technical demo script below.
4. Explain Orchestrate as a design note only unless you have access to an Orchestrate tenant and its current ADK/API.

## 5. Assistant action blueprints

### Password reset

- Trigger examples: “I forgot my password”, “reset my account”.
- Collect `employee_id`; validate a simple enterprise format such as `E12345` or `e12345`.
- Collect `security_answer`; never display or log the expected answer.
- Confirm: “Reset access for employee E12345 and create a service ticket?”
- Call `createTicket` with `ticket_type=password_reset`, employee ID, and `identity_verified=true`.
- Success message includes the ticket number and expected service-desk next step.
- Do not claim the password was reset; this demo creates a reset ticket.

### Laptop request

- Collect and validate `employee_id`, `department`, `laptop_type`, and `justification`.
- Suggested laptop types: `standard`, `developer`, `power_user`; allow a current UI equivalent or free text with a review route.
- Confirm the complete request.
- Call `createTicket` with `approval_required=true` and `route_to=IT procurement approval`.

### Access request

- Collect `employee_id`, `system_name`, and `manager_name`.
- Confirm scope and manager.
- Call `createTicket` with `approval_required=true` and `route_to=system owner`.

### Escalation

- Trigger when the user explicitly asks for a person, uses clear frustration language, or the assistant reaches two failed attempts.
- Provide a short summary: issue, completed steps, missing information, and sentiment.
- Present the summary to the human-agent integration if available. In this local project, the `/chat` response can return the summary when escalation is requested.

## 6. FastAPI service and SDK client

`app/main.py` exposes:

- `GET /health`
- `POST /create-ticket`: mock ticket creation for the custom extension
- `POST /chat`: sends a message to watsonx Assistant v2 when configured

The `/chat` request is:

```json
{"message":"I need a laptop","session_id":null}
```

The response contains Assistant text, returned session ID, and raw response data. The service creates a new Assistant session when `session_id` is absent.

The local ticket endpoint is intentionally a mock. It stores tickets in memory and is not production-safe: restart loses tickets, there is no authentication, and identity validation is illustrative only.

## 7. Conversational search policy documents

Upload:

- `policies/vpn-policy.md`
- `policies/it-equipment-leave-policy.md`
- `policies/security-policy.md`

They are original sample text for a fictional client, not IBM policy. Replace them with approved client documents before a real deployment.

## 8. Stakeholder requirements summary

The client wants employees to self-serve common IT requests, capture complete request data, answer policy questions from approved documents, and escalate safely when automation is insufficient. The first release should prioritize low-risk ticket creation rather than directly changing passwords or entitlements. Success measures should be agreed with the Automation Project Manager; examples are completion rate, valid-ticket rate, escalation rate, average handling time, and answer-grounding feedback.

## 9. Demo script

**Audience:** client stakeholder and Automation Project Manager.

1. “An employee starts with a natural-language request instead of learning a service-desk form.”
2. Demonstrate a laptop request. Show the assistant collecting only missing fields, summarizing them, asking for confirmation, and returning a ticket number.
3. Ask “Can I use VPN from a hotel?” Show the answer coming from the uploaded policy source.
4. Enter an invalid employee ID and show a helpful correction.
5. Say “I’m frustrated; connect me to a person.” Show the escalation summary with issue, completed steps, and sentiment.
6. Explain that the demo creates mock tickets. In production, the same contract could call an ITSM platform or an RPA workflow after security, authentication, and approval controls are finalized.

## 10. Watsonx Orchestrate design note

**Hands-on in this repository:** Assistant action design, policy-source preparation, FastAPI ticket contract, OpenAPI extension document, optional Assistant v2 client, and test conversations.

**Design-only unless separately provisioned:** expose this capability in watsonx Orchestrate as a skill/agent. A future implementation could package the ticket operation as an Orchestrate skill, register the Assistant as a collaborator/agent using the current Orchestrate API or ADK, and let an Orchestrate agent route work to the specialized Assistant. Verify the current Orchestrate tenant, ADK version, registration API, authentication, and catalog workflow before implementation. Do not describe this demo as completed Orchestrate integration.

This is also where RPA collaboration fits: an RPA bot could consume the approved ticket event to update an ITSM record or provision a laptop, while the cognitive layer handles intent, missing information, policy grounding, and human escalation.

## 11. Testing

See `docs/test-conversations.md`. Replace the expected status with observed results after running each case. The tests cover happy paths, validation, interruption, policy search, explicit escalation, and two-failure escalation.

## 12. Resume bullets with real-result placeholders

- Accomplished **[X]% reduction in [manual intake time / incomplete requests]**, as measured by **[your comparison method and sample size]**, by designing a watsonx Assistant IT-support workflow with guided collection, confirmation, policy search, and a FastAPI ticket extension.
- Accomplished **[X]% [successful completion / grounded-answer rate] across [N] test conversations**, as measured by **[your test log or evaluation rubric]**, by implementing Assistant v2 session messaging, input validation, escalation summaries, and repeatable end-to-end test scenarios.

Replace every bracketed value with results you actually measured. Do not claim IDCP, IBM Consulting Advantage, Orchestrate, or production deployment experience unless you complete and can explain it.

## 13. Interview questions and strong answers

### 1. How did you convert the process into a cognitive solution?

I separated deterministic controls from conversational work. The assistant gathers and validates fields, confirms the request, and calls a typed ticket API; it does not directly reset a password or grant access. Policy questions use approved documents, and uncertainty or frustration routes to a human with context.

### 2. Why use Actions instead of one large prompt?

Actions make the process explicit and testable: each step has a purpose, input, validation, confirmation, and fallback. That gives stakeholders traceability and makes it easier to change one process without destabilizing the others.

### 3. How did you use Watson APIs?

The Python client uses `IAMAuthenticator` and `AssistantV2` to create a session and send stateful messages. Configuration is environment-based. Because IBM’s current API documentation may restrict v2 runtime access to Plus or higher, I verify the account entitlement before presenting the integration as available on Lite.

### 4. How would you secure the ticket integration?

Use HTTPS, an API key or OAuth mechanism supported by the current custom-extension importer, server-side authentication and authorization, input validation, audit logging without sensitive answers, rate limits, and a real ITSM identity model. The repository endpoint is a deliberately unauthenticated mock for learning only.

### 5. What happens when the assistant fails?

The first failure gives a targeted rephrase or supported-value prompt. A second failure, clear frustration, or a direct request for a person triggers escalation. The human receives the issue, completed steps, missing fields, ticket number if created, and sentiment.

### 6. How is this Agent Assist or User Assist?

User Assist is the employee-facing guided self-service experience. Agent Assist is the context package and recommended next step delivered to the human agent. The pattern reduces repeated questioning without pretending that a mock handoff is a production contact-center integration.

### 7. Where could RPA collaborate?

After approval, RPA could update an ITSM system, create procurement tasks, or execute a controlled provisioning step. The Assistant should remain responsible for conversation and intake; the bot should be idempotent, auditable, and governed by approvals.

### 8. How would you work with the client and project manager?

I would agree the process boundary, risk controls, approved policy sources, success measures, and escalation ownership first. I would demo happy and failure paths, maintain a decision log, obtain sign-off on the API contract, and report measured test outcomes rather than generic AI claims.

## 14. Files

```text
app/main.py
app/watson_client.py
requirements.txt
.env.example
openapi.json
policies/*.md
docs/test-conversations.md
```
