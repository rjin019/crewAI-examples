# Email Auto Responder API Documentation

## Overview
This system is designed to monitor Gmail inbox, classify incoming emails, determine whether a reply is needed, and automatically generate and send appropriate replies using CrewAI agents and OpenAI LLM.

---

## Authentication
OAuth2 is used for Gmail API authentication. Click the API platform setup to get the API autorization from OAuth2.0, and then down load the credentials.JSON file and the platform key for using the email auto responder.

- **API Platform Setup**: `[https://www.googleapis.com/auth/gmail.readonly](https://console.developers.google.com/?hl=zh-cn)`
- **Token File**
- **Credentials File**

---

## Functionality （**Functions as Endpoints**）

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
  2. Run CrewAI classification and filtering agents sequentially
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
1. **filter_emails** — Classifies email based on 7 categories(spam/purchase/reservation/meeting/supportrequest/news/primary).
2. **action_required_emails** — Checks if a reply is needed.
3. **draft_responses** — Generates email content if needed.

---
## Agent and Task Matching

| Agent Name              | Role | task                    |
| ----------------------- | --------| ------------------------     |
| email\_filter\_agent    | filter emails based on 7 categories | `filter_emails`          |
| email\_action\_agent    | determine email's type from email-filter, processing the need auto reply emails| `action_required_emails` |
| email\_response\_writer | drafting emails passed by email-action | `draft_responses`        |


---
## Example Email Object

```json
{
  {'date': 'Wed, 23 Jul 2025 19:19:35 +0000',
  'subject': 'Summer updates incoming—Check out what’s new on Handshake!',
  'sender': 'Handshake <handshake@g.joinhandshake.com>',
  'id': '19838ba29f790bdd',
  'snippet': ''}
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

## Example Full Output
<img width="1103" height="1803" alt="Clip_2025-07-25_19-59-06" src="https://github.com/user-attachments/assets/0151a9e9-3cd0-4905-9667-1756fc49ed12" />  
<img width="926" height="2045" alt="Clip_2025-07-25_19-59-55" src="https://github.com/user-attachments/assets/661a3989-cd6b-4be0-8876-7a467bffc986" />  

<img width="1107" height="1410" alt="Clip_2025-07-25_20-00-36" src="https://github.com/user-attachments/assets/6dd25940-196f-4070-b80a-70d9dcb26e0e" />  

---

## License
This system is part of a student research/automation demo project. Use responsibly with rate limits and privacy in mind.  
Since this is a student project, I didn't add up the "send authorization" from Gmail yet(but I will test it until it's stable and then add it up) because it will cause the uncontrolled behavior in my mailbox.  


---

**Author**: Christan Jin  
**Last Updated**: July 2025
