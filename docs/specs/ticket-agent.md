# Nimbus Ticket Agent specification

**Status:** Design only. Implement the behavior in M9/M10 and its evaluation
suite in M12. The catalog source of truth is
[`data/tickets/topics.yaml`](../../data/tickets/topics.yaml).

## A1. User flow

1. Offer **“Still need help?”** after an abstention or thumbs-down. A direct
   user request to open a ticket starts the same flow. A guest is told
   **“Please log in to open a ticket”** and cannot create a draft.
2. For an authenticated user, show three topic chips, **“None of these”**, and
   an always-available **Other** option. “None of these” reveals the other
   three catalog topics; no separate browse screen is needed.
3. After topic selection, fetch the form definition from the YAML catalog; do
   not ask an LLM to design form fields. Pre-fill only fields explicitly
   stated in this conversation.
4. Let the user edit the draft. The agent may ask at most two follow-up
   questions for missing required values. If the flow exceeds a limit or
   fails, fall back to all topic choices and an empty form.
5. The user reviews and clicks **Confirm**. The server validates and submits
   the ticket, then routes it using the topic's queue (or region-specific
   billing queue).

## A2. Agent tools and boundaries

The LLM may select tools; application code validates every name, argument,
result, and state transition. Tool calls and corresponding server events are
documented here; tools never bypass the authoritative service layer.

| Tool | Contract |
| --- | --- |
| `list_topics(exclude)` | Return catalog topics other than the supplied valid IDs. |
| `present_topic_options(topic_ids, reasons)` | Every ID must exist in the catalog; emit SSE `topic_options`. |
| `get_form_schema(topic_id)` | Return base, locked, and topic-specific field definitions from the catalog. |
| `fill_form(topic_id, values)` | Validate fields; take region/email from verified claims; save a draft in Redis; return missing/invalid fields and emit SSE `form_draft`. |
| `ask_missing_field(field, question)` | Ask one focused question for a missing required field; maximum two calls per ticket flow. |
| `search_docs(query)` | Use RAG retrieval with the same authenticated access filter as ordinary search. |
| `get_my_tickets()` | Return only tickets owned by the user identified by the token. |

There is deliberately **no submit tool**. Submission occurs only through
`POST /tickets/{id}/confirm` after explicit user confirmation and fresh server
validation.

## A3. Rules and validation

- `user_id`, `region`, and `email` are read from the verified token, never
  accepted as LLM-authored identity. A payload that tries to override a locked
  field, particularly a different region, receives HTTP 422.
- Pre-fill is extractive, not inferential: every value must have been stated in
  the conversation. If it was not stated, leave it empty. Do not turn guesses,
  implications, or general knowledge into field values.
- Reject a card number or secret in any user-entered field with the exact
  message: **“Please don't include card numbers or keys.”** Do not persist the
  rejected value in the draft, logs, or metrics.
- Maximums per flow: 8 agent steps, 2 missing-field questions, and 2 topic
  rounds. On a limit or tool failure, offer all topics and an empty form.
- Supported field types are only `text`, `textarea`, and `select`. Enforce each
  catalog `required`, `max_length`, and `options` constraint on the server.
- The user can edit any unlocked value before confirmation. Locked region and
  email values are shown read-only and cannot be changed by the browser.
- Topic selection and draft creation do not submit a ticket or trigger an
  external action.

**Better to have / out of scope:** date fields, conditional fields, uploads,
and region-specific help text.

## A4. Topic catalog

`data/tickets/topics.yaml` is the versioned, human-maintained catalog. It
contains six unique topic IDs. Shared required fields are `subject` and
`description`; `region` and `email` are locked identity fields. Each topic
provides its display text, category, queue, optional notice, and at most two
additional fields. Billing tickets route to `billing-R1` or `billing-R2` based
on the authenticated region. Topic and field definitions come from the
catalog—not an LLM.

## A5. Ticket persistence (M9 design)

The M9 schema change adds these columns to `tickets`:

- `topic_id TEXT` — selected catalog topic ID.
- `queue TEXT` — server-resolved routing queue.
- `fields JSONB NOT NULL DEFAULT '{}'` — validated topic form data, excluding
  duplicate identity values where practical.

Keep existing ticket category/status behavior compatible. Validate the topic
ID and queue from the catalog on confirmation; never trust a queue supplied by
the model or browser. The migration and rollback are implementation work for
M9, not part of this design-only change.

## M12 acceptance direction

The ticket-agent suite uses about 30 tasks, balanced between should/shouldn't
cases, and a simulated user with an opening message plus hidden facts. The
simulator answers only what is asked, otherwise says “I don't know,” and is
limited to eight turns. Each trial receives isolated state. The final M12 run
uses three trials per agent task and reports pass@1 and pass^3; safety graders
must verify that the agent never submits a ticket itself.
