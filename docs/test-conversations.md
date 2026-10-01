# Test conversations

Run these in the Assistant preview and record the actual result in the final column. Expected outcomes are acceptance criteria, not pre-existing results.

| # | Scenario and conversation | Expected result | Actual result |
|---:|---|---|---|
| 1 | User: “I need a laptop.” Assistant asks fields. User: `E12345`, Finance, standard, “replacement for damaged device.” User confirms. | Complete laptop request; ticket is `PENDING_APPROVAL`. | [record] |
| 2 | User: “Reset my password.” User enters `E12345`, answers the configured fictional security question, confirms. | Identity is verified and reset ticket is created; assistant does not claim direct password change. | [record] |
| 3 | User: “Give me access to SAP. My manager is Priya Shah.” User supplies `E12345` and confirms. | Access ticket contains system and manager and routes to approval/system owner. | [record] |
| 4 | User: “Can I use VPN from a hotel?” | Search answer cites or clearly grounds the response in the VPN policy. | [record] |
| 5 | User starts laptop request, then asks: “What is the travel equipment rule?” | Assistant answers policy question and returns to the unfinished laptop request. | [record] |
| 6 | User enters `123` for employee ID. | Assistant explains the expected format and asks again; no ticket is created. | [record] |
| 7 | User requests laptop but refuses justification. | Assistant explains why justification is needed and offers human help after repeated refusal. | [record] |
| 8 | User says: “This is useless. Connect me to a person.” | Immediate handoff with issue, collected fields, and frustrated sentiment. | [record] |
| 9 | User gives two unsupported answers during access request. | Second failure triggers escalation; summary includes missing system or manager data. | [record] |
| 10 | User asks: “How do I report a stolen laptop?” | Search answer uses the equipment/security policy and recommends immediate reporting. | [record] |

## Result rubric

- **Pass:** expected intent, collection, validation, integration result, and escalation behavior all occur.
- **Partial:** useful answer but one required control or field mapping is missing.
- **Fail:** wrong action, fabricated policy answer, ticket without required fields, or escalation without context.
