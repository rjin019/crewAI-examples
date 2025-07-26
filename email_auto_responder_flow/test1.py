import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from crewai import Agent, Crew, Task, Process
from langchain_openai import ChatOpenAI
import yaml
import os

os.environ["OPENAI_API_KEY"] = "REMOVED_SECRETproj-JueprMFyYfl0QuhT9qcQ9cFV-WDEK4amR1pO8r8wXcDzfGFGyT8JO9SGrgqA5ojyn-QUe_YaB3T3BlbkFJIZ4EHstMoppu6aYLqHdQNOlen5SyML2sZOWyEf09eRvylnNPR4UARn1y-c-_N7-1Z1b7LI9qQA"

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def gmail_authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('email_auto_responder_flow/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def list_messages(service, max_results=10):
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])
    return messages

def get_message(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
    headers = msg.get('payload', {}).get('headers', [])
    email_data = {}
    for header in headers:
        if header['name'] == 'From':
            email_data['sender'] = header['value']
        elif header['name'] == 'Subject':
            email_data['subject'] = header['value']
        elif header['name'] == 'Date':
            email_data['date'] = header['value']
    email_data['id'] = msg_id
    return email_data

agent_yaml_path = "email_auto_responder_flow/src/email_auto_responder_flow/crews/email_filter_crew/config/agents.yaml"
task_yaml_path = "email_auto_responder_flow/src/email_auto_responder_flow/crews/email_filter_crew/config/tasks.yaml"

def load_agents_and_tasks(agent_yaml_path, task_yaml_path, llm):
    with open(agent_yaml_path, "r") as f:
        agent_conf = yaml.safe_load(f)
    with open(task_yaml_path, "r") as f:
        task_conf = yaml.safe_load(f)

    agents = {}
    for name, conf in agent_conf.items():
        agents[name] = Agent(
            role=conf["role"],
            goal=conf["goal"],
            backstory=conf["backstory"],
            llm=llm,
            tools=[],
            verbose=True
        )
    
    tasks = []
    for name, conf in task_conf.items():
        agent_name = conf["agent"]
        tasks.append(Task(
            description=conf["description"],
            expected_output=conf["expected_output"],
            agent=agents[agent_name]
        ))
    
    return agents, tasks

from email.mime.text import MIMEText
import base64

def send_message(service, to, subject, body_text):
    message = MIMEText(body_text)
    message['to'] = to
    message['subject'] = subject
    raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
    send_result = service.users().messages().send(userId="me", body=raw_message).execute()
    print(f"sent")
    return send_result

import time
from datetime import datetime

def start_monitoring(interval_hours=24):
    service = gmail_authenticate()
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    agents, tasks = load_agents_and_tasks(agent_yaml_path, task_yaml_path, llm)
    
    print(f"🚀 Starting email monitoring (checking every {interval_hours} hours)...")
    
    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⏰ [{current_time}] Checking for new emails...")
        
        process_new_emails(service, llm, agents, tasks)
        
        # Sleep until next run
        print(f"⏳ Next check in {interval_hours} hours...")
        time.sleep(interval_hours * 3600)  # Convert hours to seconds

def process_new_emails(service, llm, agents, tasks):
    messages = list_messages(service, max_results=10)
    emails = [get_message(service, msg['id']) for msg in messages]

    # Phase 1: Email Filter
    print("📥 Processing emails:")
    for i, email in enumerate(emails, 1):
        print(f"{i}. {email['subject']} (from: {email['sender']})")

    crew_filter = Crew(
        agents=[agents["email_filter_agent"]],
        tasks=[tasks[0]],
        process=Process.sequential,
        verbose=True,
    )
    filter_result = crew_filter.kickoff(inputs={"emails": emails})

    # 兼容输出：string / tuple / dict
    if isinstance(filter_result, tuple):
        filter_result = filter_result[0]
    elif isinstance(filter_result, str):
        import json
        filter_result = json.loads(filter_result)

    print("\n🔍 Filter Result:")
    print(filter_result)

    # Phase 2: Email Action Analyzer
    crew_action = Crew(
        agents=[agents["email_action_agent"]],
        tasks=[tasks[1]],
        process=Process.sequential,
        verbose=True,
    )
    action_result = crew_action.kickoff(inputs={"emails": filter_result})
    if isinstance(action_result, tuple):
        action_result = action_result[0]
    elif isinstance(action_result, str):
        import json
        action_result = json.loads(action_result)

    print("\n📋 Action Result:")
    print(action_result)

    # Phase 3: Email Writer
    crew_writer = Crew(
        agents=[agents["email_response_writer"]],
        tasks=[tasks[2]],
        process=Process.sequential,
        verbose=True,
    )
    writer_result = crew_writer.kickoff(inputs={"emails": action_result})
    if isinstance(writer_result, tuple):
        writer_result = writer_result[0]
    elif isinstance(writer_result, str):
        import json
        writer_result = json.loads(writer_result)

    print("\n✉️ Writer Result:")
    print(writer_result)

    # Phase 4: Send Replies
    for reply in writer_result:
        try:
            # 处理格式
            if isinstance(reply, tuple):
                reply = reply[0]
            elif isinstance(reply, str):
                import json
                reply = json.loads(reply)

            send_message(
                service,
                to=reply["to"],
                subject=reply["subject"],
                body_text=reply["body"]
            )
            print(f"✅ Sent reply to: {reply['to']}")
        except Exception as e:
            print(f"❌ Failed to send reply to {reply.get('to', 'UNKNOWN')}: {e}")

if __name__ == "__main__":
    start_monitoring(interval_hours=24)