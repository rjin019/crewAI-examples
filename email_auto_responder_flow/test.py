#!/usr/bin/env python3
"""
 Testing, Integration Testing
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# testing
class EmailProcessor:
    def __init__(self):
        self.service = None
        
    def classify_email(self, email):
        subject = email.get('subject', '').lower()
        sender = email.get('sender', '').lower()
        
        # category
        if any(spam_word in subject for spam_word in ['giveaway', 'limited time', 'deal', 'offer']):
            return 'spam'
        elif 'reservation' in subject:
            return 'reservations'
        elif 'meeting' in subject or 'invite' in subject:
            return 'meeting'
        elif 'support' in subject or 'help' in subject:
            return 'support_request'
        elif any(domain in sender for domain in ['.edu', '.gov']):
            return 'primary'
        else:
            return 'news'
    
    def needs_reply(self, category):
        """判断是否需要回复"""
        reply_categories = ['primary', 'meeting', 'support_request']
        return category in reply_categories
    
    def generate_reply(self, email, category):
        """autoreply"""
        if category == 'meeting':
            return "Thank you for the meeting invitation. I'll check my schedule and get back to you."
        elif category == 'support_request':
            return "Thank you for contacting us. We've received your request and will respond within 24 hours."
        elif category == 'primary':
            return "Thank you for your email. I'll review it and respond accordingly."
        else:
            return ""

# ===== UNIT TESTING =====
class TestEmailProcessor(unittest.TestCase):
    """Unit Testing"""
    
    def setUp(self):
        """prepare testing"""
        self.processor = EmailProcessor()
    
    def test_classify_spam_email(self):
        """test spam"""
        email = {'subject': 'Limited time offer!', 'sender': 'spam@example.com'}
        result = self.processor.classify_email(email)
        self.assertEqual(result, 'spam')
    
    def test_classify_meeting_email(self):
        """test meeting"""
        email = {'subject': 'Meeting invitation for tomorrow', 'sender': 'colleague@company.com'}
        result = self.processor.classify_email(email)
        self.assertEqual(result, 'meeting')
    
    def test_classify_reservation_email(self):
        """test reservation"""
        email = {'subject': 'Hotel reservation confirmation', 'sender': 'hotel@booking.com'}
        result = self.processor.classify_email(email)
        self.assertEqual(result, 'reservations')
    
    def test_needs_reply_logic(self):
        """test draft"""
        self.assertTrue(self.processor.needs_reply('meeting'))
        self.assertTrue(self.processor.needs_reply('support_request'))
        self.assertFalse(self.processor.needs_reply('spam'))
        self.assertFalse(self.processor.needs_reply('news'))
    
    def test_generate_reply_content(self):
        """test support"""
        email = {'subject': 'Need help', 'sender': 'user@example.com'}
        reply = self.processor.generate_reply(email, 'support_request')
        self.assertIn('Thank you for contacting us', reply)
        self.assertIn('24 hours', reply)













def run_simple_tests():
    """简单的测试执行函数"""
    print("🧪 开始运行邮件处理系统测试...")
    print("=" * 50)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加单元测试
    test_suite.addTest(unittest.makeSuite(TestEmailProcessor))
    print("")
    
 
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("\n" + "=" * 50)
    print(f"Test")
    print(f"{result.testsRun} ")
    print(f"G: {len(result.failures)} ")
    print(f"F: {len(result.errors)} 个")
    print(f"%: {((result.testsRun - len(result.failures) - len(result.errors))/result.testsRun*100):.1f}%")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_simple_tests()
    
    if success:
        print("\nPass")
        sys.exit(0)
    else:
        print("\nWrong")
        sys.exit(1)