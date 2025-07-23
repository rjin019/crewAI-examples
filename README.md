# Email Auto Responder API Documentation

## Overview
This system is designed to monitor Gmail inbox, classify incoming emails, determine whether a reply is needed, and automatically generate and send appropriate replies using CrewAI agents and OpenAI LLM.

---

## Authentication
OAuth2 is used for Gmail API authentication.

- **Scopes Used**: `https://www.googleapis.com/auth/gmail.readonly`
- **Token File**: `token.json`
- **Credentials File**: `credentials.json`

---

## Endpoints / Functions

### `gmail_authenticate()`
**Purpose**: Authenticate with Gmail and return a service object.
- **Returns**: `Resource` — Gmail API service instance.

---

### `list_messages(service, max_results=10)`
**Purpose**: Fetches a list of recent email message IDs.
- **Parameters**:
  - `service`: Gmail API service object.
  - `max_results` *(int)*: Number of messages to fetch.
- **Returns**: `List[Dict]` — List of message metadata with ID.

---

### `get_message(service, msg_id)`
**Purpose**: Retrieves metadata for a specific email.
- **Parameters**:
  - `service`: Gmail API service object.
  - `msg_id` *(str)*: Gmail message ID.
- **Returns**: `Dict` containing `id`, `subject`, `sender`, `date`.

---

### `load_agents_and_tasks(agent_yaml_path, task_yaml_path, llm)`
**Purpose**: Loads agent and task configurations from YAML files.
- **Parameters**:
  - `agent_yaml_path`: Path to agent YAML file.
  - `task_yaml_path`: Path to task YAML file.
  - `llm`: Language model instance (e.g., `ChatOpenAI`)
- **Returns**: Tuple of `(agents_dict, tasks_list)`

---

### `send_message(service, to, subject, body_text)`
**Purpose**: Sends a reply email using the Gmail API.
- **Parameters**:
  - `service`: Gmail API service.
  - `to`: Recipient email.
  - `subject`: Email subject.
  - `body_text`: Email body.
- **Returns**: Send result as dictionary.

---

### `start_monitoring(interval_hours=24)`
**Purpose**: Starts periodic email checking and auto-response every N hours.
- **Parameters**:
  - `interval_hours` *(int)*: Interval in hours between checks.
- **Behavior**: Calls `process_new_emails()` in a loop.

---

### `process_new_emails(service, llm, agents, tasks)`
**Purpose**: Core logic to handle email classification and auto-reply.
- **Steps**:
  1. Fetch latest emails
  2. Run CrewAI classification and filtering agents
  3. If needed, run writer agent
  4. Send replies via Gmail
- **Returns**: `None` (side effects only)

---

## YAML Configuration

### `agents.yaml`
Defines the roles and personas of each agent:
- `email_filter_agent`: Classifies email categories
- `email_action_agent`: Determines reply necessity
- `email_response_writer`: Generates email replies

---

### `tasks.yaml`
Three core tasks:
1. **filter_emails** — Classifies email and flags.
2. **action_required_emails** — Checks if a reply is needed.
3. **draft_responses** — Generates email content if needed.

---

## Example Email Object

```json
{
  "id": "19829b64f2e3ffec",
  "subject": "Meeting Reminder",
  "sender": "Team Lead <lead@company.com>",
  "date": "Mon, 1 Jul 2025 10:00:00 -0700",
  "snippet": "Don't forget our meeting today..."
}
```

---

## Example CrewAI Result

```json
[
  {
    "id": "19829b64f2e3ffec",
    "subject": "Meeting Reminder",
    "category": "meeting",
    "needs_auto_reply": true,
    "sender": "lead@company.com"
  },
  ...
]
```

---

## Error Handling

| Error Type           | Description                                   |
|----------------------|-----------------------------------------------|
| GmailAuthError       | Gmail authentication failed                   |
| CrewExecutionError   | CrewAI failed during one or more tasks        |
| NoReplyNeededError   | All emails marked as no action needed         |
| APIQuotaExceeded     | Gmail API daily usage limit exceeded          |

---

## License
This system is part of a student research/automation demo project. Use responsibly with rate limits and privacy in mind.

---

**Author**: Christan Jin  
**Last Updated**: July 2025
