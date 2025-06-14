#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雷🐷🐷聊天机器人测试文件
用于测试已训练好的模型的聊天效果
"""

from model_train import OpenAIChatBot
import json

# 从配置文件读取API密钥
try:
    from config import OPENAI_API_KEY
    API_KEY = OPENAI_API_KEY
except ImportError:
    print("❌ 未找到config.py文件！")
    print("请复制config_template.py为config.py并填入您的API密钥")
    exit(1)

# 已训练好的模型ID
TRAINED_MODEL_ID = "ft:gpt-3.5-turbo-0125:personal::BiA2Eytr"

def test_chat():
    """测试聊天功能"""
    # 创建聊天机器人实例
    bot = OpenAIChatBot(API_KEY)
    bot.fine_tuned_model_id = TRAINED_MODEL_ID
    
    print(f"🤖 使用模型: {TRAINED_MODEL_ID}")
    print("🧪 开始测试聊天效果...")
    
    # 测试不同场景
    test_cases = [
        {
            "group": "当年三人分",
            "history": ["寻常摆渡: 来不来我的世界"],
            "friend": "寻常摆渡"
        },
        {
            "group": "挑衅大帝衰微之夜", 
            "history": ["杜预: 太愚蠢了"],
            "friend": "杜预"
        },
        {
            "group": "当年三人分",
            "history": ["神仙传: 你太愚蠢了"],
            "friend": "神仙传"
        },
        {
            "group": "当年三人分",
            "history": ["格里戈里·拉斯普京: 雷猪猪快来玩游戏"],
            "friend": "格里戈里·拉斯普京"
        },
        {
            "group": "未知群组",
            "history": ["某人: 在吗"],
            "friend": None
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- 测试场景 {i} ---")
        response = bot.chat(case["group"], case["history"], case["friend"])
        print(f"群组: {case['group']}")
        print(f"对话对象: {case['friend'] or '未知'}")
        print(f"历史: {case['history']}")
        print(f"雷🐷🐷: {response}")
        print("-" * 50)

def interactive_chat():
    """交互式聊天"""
    bot = OpenAIChatBot(API_KEY)
    bot.fine_tuned_model_id = TRAINED_MODEL_ID
    
    print("🎯 进入交互式聊天模式")
    print("输入 'quit' 或 'exit' 退出")
    print("输入格式: 群组名|朋友名|消息内容")
    print("例如: 当年三人分|寻常摆渡|来不来我的世界")
    print("-" * 50)
    
    conversation_history = []
    
    while True:
        try:
            user_input = input("\n输入: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            if not user_input:
                continue
            
            # 解析输入
            parts = user_input.split('|')
            if len(parts) >= 3:
                group = parts[0].strip()
                friend = parts[1].strip() if parts[1].strip() else None
                message = parts[2].strip()
                
                # 构建对话历史
                if friend:
                    history_line = f"{friend}: {message}"
                else:
                    history_line = f"某人: {message}"
                
                conversation_history.append(history_line)
                
                # 保持最近5轮对话
                if len(conversation_history) > 5:
                    conversation_history = conversation_history[-5:]
                
            else:
                # 简单输入，使用默认设置
                group = "测试群组"
                friend = None
                message = user_input
                conversation_history = [f"某人: {message}"]
            
            # 生成回复
            response = bot.chat(group, conversation_history, friend)
            
            if response:
                print(f"雷🐷🐷: {response}")
                # 将回复也加入历史
                conversation_history.append(f"雷🐷🐷: {response}")
            else:
                print("❌ 生成回复失败")
                
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 出错了: {e}")

def test_specific_friends():
    """测试与特定朋友的对话模式"""
    bot = OpenAIChatBot(API_KEY)
    bot.fine_tuned_model_id = TRAINED_MODEL_ID
    
    print("🎯 测试与特定朋友的对话模式")
    
    # 读取聊天模式数据
    try:
        with open('chat_patterns_final.json', 'r', encoding='utf-8') as f:
            chat_patterns = json.load(f)
    except FileNotFoundError:
        print("❌ 未找到聊天模式文件")
        return
    
    # 选择几个互动较多的朋友进行测试
    top_friends = sorted(chat_patterns.items(), 
                        key=lambda x: x[1]['interaction_count'], 
                        reverse=True)[:3]
    
    print(f"选择互动最多的3个朋友进行测试...")
    
    for friend_name, pattern in top_friends:
        print(f"\n=== 与 {friend_name} 的对话测试 ===")
        print(f"互动次数: {pattern['interaction_count']}")
        print(f"平均回复长度: {pattern['avg_response_length']:.1f}")
        
        # 模拟不同类型的对话
        test_messages = [
            "在吗",
            "来玩游戏吗",
            "你在干什么",
            "愚蠢",
            "太愚蠢了"
        ]
        
        for msg in test_messages:
            history = [f"{friend_name}: {msg}"]
            response = bot.chat("测试群组", history, friend_name)
            print(f"{friend_name}: {msg}")
            print(f"雷🐷🐷: {response}")
            print("-" * 30)

if __name__ == "__main__":
    print("🤖 雷🐷🐷聊天机器人测试系统")
    print("=" * 50)
    
    print("选择测试模式:")
    print("1. 预设场景测试")
    print("2. 交互式聊天")
    print("3. 特定朋友对话测试")
    print("4. 全部测试")
    
    try:
        choice = input("请选择 (1-4): ").strip()
        
        if choice == "1":
            test_chat()
        elif choice == "2":
            interactive_chat()
        elif choice == "3":
            test_specific_friends()
        elif choice == "4":
            print("🚀 开始全部测试...")
            test_chat()
            print("\n" + "="*50)
            test_specific_friends()
            print("\n🎯 如需交互式聊天，请重新运行并选择模式2")
        else:
            print("❌ 无效选择，默认运行预设场景测试")
            test_chat()
            
    except KeyboardInterrupt:
        print("\n👋 再见！")
    except Exception as e:
        print(f"❌ 出错了: {e}")
