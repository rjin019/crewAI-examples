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

















# ===== INTEGRATION TESTING (集成测试) =====
class TestEmailWorkflow(unittest.TestCase):
    """Integration Testing - 测试模块间交互"""
    
    def setUp(self):
        self.processor = EmailProcessor()
    
    def test_complete_email_processing_workflow(self):
        """测试完整的邮件处理流程"""
        # 输入邮件
        email = {
            'subject': 'Meeting request for project discussion',
            'sender': 'manager@company.com',
            'id': '12345'
        }
        
        # 步骤1: 分类
        category = self.processor.classify_email(email)
        self.assertEqual(category, 'meeting')
        
        # 步骤2: 判断是否需要回复
        should_reply = self.processor.needs_reply(category)
        self.assertTrue(should_reply)
        
        # 步骤3: 生成回复
        if should_reply:
            reply = self.processor.generate_reply(email, category)
            self.assertIsNotNone(reply)
            self.assertTrue(len(reply) > 0)
    
    def test_spam_email_workflow(self):
        """测试垃圾邮件完整流程"""
        email = {
            'subject': 'Win big prizes - limited time!',
            'sender': 'promo@spam.com',
            'id': '54321'
        }
        
        category = self.processor.classify_email(email)
        should_reply = self.processor.needs_reply(category)
        
        # 垃圾邮件不应该回复
        self.assertEqual(category, 'spam')
        self.assertFalse(should_reply)

# # ===== BLACK-BOX TESTING (黑盒测试) =====
# class TestBlackBoxEmailProcessing(unittest.TestCase):
#     """Black-box Testing - 基于输入输出的测试，不考虑内部实现"""
    
#     def setUp(self):
#         self.processor = EmailProcessor()
    
#     def test_various_input_combinations(self):
#         """测试各种输入组合"""
#         test_cases = [
#             # (input_email, expected_category, should_reply)
#             ({'subject': 'Giveaway alert!', 'sender': 'ads@promo.com'}, 'spam', False),
#             ({'subject': 'Hotel reservation #123', 'sender': 'hotel@booking.com'}, 'reservations', False),
#             ({'subject': 'Team meeting tomorrow', 'sender': 'boss@company.com'}, 'meeting', True),
#             ({'subject': 'Help with login issue', 'sender': 'user@client.com'}, 'support_request', True),
#             ({'subject': 'Research update', 'sender': 'prof@university.edu'}, 'primary', True),
#         ]
        
#         for email, expected_category, expected_reply in test_cases:
#             with self.subTest(email=email['subject']):
#                 category = self.processor.classify_email(email)
#                 needs_reply = self.processor.needs_reply(category)
                
#                 self.assertEqual(category, expected_category)
#                 self.assertEqual(needs_reply, expected_reply)

# # ===== COVERAGE-BASED TESTING (覆盖率测试) =====
# class TestBranchCoverage(unittest.TestCase):
#     """Branch Coverage Testing - 确保每个分支都被测试到"""
    
#     def setUp(self):
#         self.processor = EmailProcessor()
    
#     def test_all_classification_branches(self):
#         """测试所有分类分支"""
#         # 确保每个if-elif分支都被执行
#         test_emails = [
#             ({'subject': 'limited time offer', 'sender': 'spam@test.com'}, 'spam'),
#             ({'subject': 'reservation confirmation', 'sender': 'hotel@test.com'}, 'reservations'),
#             ({'subject': 'meeting invite', 'sender': 'colleague@test.com'}, 'meeting'),
#             ({'subject': 'support needed', 'sender': 'user@test.com'}, 'support_request'),
#             ({'subject': 'academic paper', 'sender': 'researcher@university.edu'}, 'primary'),
#             ({'subject': 'newsletter', 'sender': 'news@website.com'}, 'news'),  # 默认分支
#         ]
        
#         for email, expected in test_emails:
#             result = self.processor.classify_email(email)
#             self.assertEqual(result, expected, f"Failed for email: {email}")

# ===== 简单的测试运行器 =====
def run_simple_tests():
    """简单的测试执行函数"""
    print("🧪 开始运行邮件处理系统测试...")
    print("=" * 50)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加单元测试
    test_suite.addTest(unittest.makeSuite(TestEmailProcessor))
    print("✅ 单元测试已添加")
    
    # 添加集成测试  
    test_suite.addTest(unittest.makeSuite(TestEmailWorkflow))
    print("✅ 集成测试已添加")
    
    # 添加黑盒测试
    test_suite.addTest(unittest.makeSuite(TestBlackBoxEmailProcessing))
    print("✅ 黑盒测试已添加")
    
    # 添加覆盖率测试
    test_suite.addTest(unittest.makeSuite(TestBranchCoverage))
    print("✅ 分支覆盖率测试已添加")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果摘要
    print("\n" + "=" * 50)
    print(f"🎯 测试结果摘要:")
    print(f"   总共运行: {result.testsRun} 个测试")
    print(f"   失败: {len(result.failures)} 个")
    print(f"   错误: {len(result.errors)} 个")
    print(f"   成功率: {((result.testsRun - len(result.failures) - len(result.errors))/result.testsRun*100):.1f}%")
    
    return result.wasSuccessful()

# ===== 主函数 =====
if __name__ == '__main__':
    # 运行所有测试
    success = run_simple_tests()
    
    if success:
        print("\n🎉 所有测试通过！系统可以部署。")
        sys.exit(0)
    else:
        print("\n❌ 有测试失败，请检查代码。")
        sys.exit(1)