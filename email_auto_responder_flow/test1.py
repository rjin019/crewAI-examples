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

def process_new_emails(service, llm, agents, tasks):
    messages = list_messages(service, max_results=10)
    
    emails = []
    for msg in messages:
        email = get_message(service, msg['id'])
        email['snippet'] = ''  # Optional: Fetch full content if needed
        emails.append(email)
    
    print("New Emails to Process:")
    for i, email in enumerate(emails, 1):
        print(f"{i}. {email['subject']} (from: {email['sender']})")
    
    # Kick off CrewAI processing
    inputs = {"emails": emails}
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    
    try:
        result = crew.kickoff(inputs=inputs)
        print("\n=== Processing Result ===")
        print(result)
        return result
    except Exception as e:
        print(f"Error processing emails: {e}")
        return None

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

import re

def extract_email(sender_str):
    match = re.search(r'<(.*?)>', sender_str)
    if match:
        return match.group(1)
    return sender_str.strip()  # fallback

def main():
    service = gmail_authenticate()
    messages = list_messages(service, max_results=10)
    llm = ChatOpenAI(model="gpt-3.5-turbo")

    agents, tasks = load_agents_and_tasks(agent_yaml_path, task_yaml_path, llm)

    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    
    emails = []
    messages = list_messages(service, max_results=10)
    for msg in messages:
        full_msg = get_message(service, msg["id"])
        headers = full_msg["payload"]["headers"]
        sender = extract_email(email["sender"])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        snippet = full_msg.get("snippet", "")
        email_summary = {
            "id": msg['id'],
            "sender": sender,
            "subject": subject,
            "snippet": snippet
        }
        emails.append(email_summary)

    
    print("Email Info:")
    for i, email in enumerate(emails, 1):
        print(f"{i}. {email['subject']} (from: {email['sender']}")
    
    inputs = {"emails": emails}
    
    try:
        result = crew.kickoff(inputs=inputs)
        print("\n=== result ===")
        print(result)

        for i, email in enumerate(emails):
            reply_text = result[i]['draft']
            to_sender = extract_email(email["sender"])
            subject = "Re: " + email['subject']
            send_message(service, to=to_sender, subject=subject, body_text=reply_text)


    except Exception as e:
        print(f"fault: {e}")
        print("check errors")

if __name__ == '__main__':
    #main()
    start_monitoring(interval_hours=24)