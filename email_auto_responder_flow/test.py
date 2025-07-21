import os
import time
import schedule
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from crewai import Agent, Crew, Task, Process
from langchain_openai import ChatOpenAI
import yaml
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

os.environ["OPENAI_API_KEY"] = "REMOVED_SECRETproj-JueprMFyYfl0QuhT9qcQ9cFV-WDEK4amR1pO8r8wXcDzfGFGyT8JO9SGrgqA5ojyn-QUe_YaB3T3BlbkFJIZ4EHstMoppu6aYLqHdQNOlen5SyML2sZOWyEf09eRvylnNPR4UARn1y-c-_N7-1Z1b7LI9qQA"

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
PROCESSED_EMAILS_FILE = 'processed_emails.json'

class EmailMonitor:
    def __init__(self):
        self.service = None
        self.crew = None
        self.processed_emails = self.load_processed_emails()
        
    def load_processed_emails(self):
        """加载已处理的邮件ID"""
        if os.path.exists(PROCESSED_EMAILS_FILE):
            with open(PROCESSED_EMAILS_FILE, 'r') as f:
                return set(json.load(f))
        return set()
    
    def save_processed_emails(self):
        """保存已处理的邮件ID"""
        with open(PROCESSED_EMAILS_FILE, 'w') as f:
            json.dump(list(self.processed_emails), f)
    
    def gmail_authenticate(self):
        """Gmail认证"""
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
    
    def get_new_messages(self, max_results=10):
        """获取新邮件（未处理的）"""
        if not self.service:
            self.service = self.gmail_authenticate()
            
        results = self.service.users().messages().list(userId='me', maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        # 过滤出未处理的邮件
        new_messages = [msg for msg in messages if msg['id'] not in self.processed_emails]
        return new_messages
    
    def get_message_details(self, msg_id):
        """获取邮件详情"""
        msg = self.service.users().messages().get(
            userId='me', 
            id=msg_id, 
            format='metadata', 
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()
        
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
        email_data['snippet'] = ''
        return email_data
    
    def initialize_crew(self):
        """初始化CrewAI"""
        agent_yaml_path = "email_auto_responder_flow/src/email_auto_responder_flow/crews/email_filter_crew/config/agents.yaml"
        task_yaml_path = "email_auto_responder_flow/src/email_auto_responder_flow/crews/email_filter_crew/config/tasks.yaml"
        
        with open(agent_yaml_path, "r") as f:
            agent_conf = yaml.safe_load(f)
        with open(task_yaml_path, "r") as f:
            task_conf = yaml.safe_load(f)
        
        llm = ChatOpenAI(model="gpt-3.5-turbo")
        
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
        
        self.crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )
    
    def process_new_emails(self):
        """处理新邮件"""
        try:
            logger.info("正在检查新邮件...")
            new_messages = self.get_new_messages()
            
            if not new_messages:
                logger.info("没有新邮件")
                return
            
            logger.info(f"发现 {len(new_messages)} 封新邮件")
            
            # 获取邮件详情
            emails = []
            for msg in new_messages:
                email_data = self.get_message_details(msg['id'])
                emails.append(email_data)
                logger.info(f"新邮件: {email_data['subject']} (from: {email_data['sender']})")
            
            # 如果crew未初始化，先初始化
            if not self.crew:
                self.initialize_crew()
            
            # 处理邮件
            inputs = {"emails": emails}
            result = self.crew.kickoff(inputs=inputs)
            
            # 记录处理结果
            logger.info("邮件处理完成")
            logger.info(f"处理结果: {result}")
            
            # 将处理过的邮件ID添加到已处理列表
            for msg in new_messages:
                self.processed_emails.add(msg['id'])
            
            # 保存已处理的邮件ID
            self.save_processed_emails()
            
        except Exception as e:
            logger.error(f"处理邮件时出错: {e}")
    
    def start_monitoring(self, interval_minutes=5):
        """开始监控邮件"""
        logger.info(f"开始邮件监控，检查间隔: {interval_minutes} 分钟")
        
        # 设置定时任务
        schedule.every(interval_minutes).minutes.do(self.process_new_emails)
        
        # 立即执行一次
        self.process_new_emails()
        
        # 持续运行
        while True:
            schedule.run_pending()
            time.sleep(1)

# 使用示例
if __name__ == '__main__':
    monitor = EmailMonitor()
    
    # 开始监控，每5分钟检查一次
    monitor.start_monitoring(interval_minutes=5)