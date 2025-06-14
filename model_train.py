import requests, time, json

# OpenAI GPT-3.5-turbo 聊天机器人类
class OpenAIChatBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.fine_tuned_model_id = None
        self.chat_patterns = {}
        
        # 加载聊天模式分析结果
        try:
            with open('chat_patterns_final.json', 'r', encoding='utf-8') as f:
                self.chat_patterns = json.load(f)
                print(f"✅ 加载了聊天模式文件，包含 {len(self.chat_patterns)} 个朋友的数据")
        except FileNotFoundError:
            print("⚠️ 未找到聊天模式文件，将使用默认模式")
    
    def upload_training_data(self, filename="deepseek_data_final.jsonl"):
        """上传训练数据到OpenAI"""
        print(f"📤 上传训练数据文件: {filename}")
        
        try:
            with open(filename, "rb") as f:
                files = {"file": f}
                data = {"purpose": "fine-tune"}
                
                response = requests.post(
                    "https://api.openai.com/v1/files", 
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                    data=data
                )
                
            if response.status_code == 200:
                file_id = response.json()["id"]
                print(f"✅ 文件上传成功，ID: {file_id}")
                return file_id
            else:
                print(f"❌ 文件上传失败: {response.status_code} - {response.text}")
                return None
                
        except FileNotFoundError:
            print(f"❌ 找不到训练数据文件: {filename}")
            return None
        except Exception as e:
            print(f"❌ 上传过程中出错: {e}")
            return None
    
    def create_fine_tune(self, file_id, model="gpt-3.5-turbo", n_epochs=3):
        """创建OpenAI微调任务"""
        print("🚀 创建微调任务...")
        payload = {
            "training_file": file_id,
            "model": model,
            "hyperparameters": {
                "n_epochs": n_epochs
            }
        }
        
        response = requests.post(
            "https://api.openai.com/v1/fine_tuning/jobs", 
            headers=self.headers, 
            json=payload
        )
        
        if response.status_code == 200:
            ft_id = response.json()["id"]
            print(f"✅ 微调任务创建成功，ID: {ft_id}")
            return ft_id
        else:
            print(f"❌ 微调任务创建失败: {response.status_code} - {response.text}")
            return None
    
    def wait_for_completion(self, ft_id):
        """等待训练完成"""
        print("⏳ 等待训练完成...")
        check_count = 0
        
        while True:
            try:
                response = requests.get(
                    f"https://api.openai.com/v1/fine_tuning/jobs/{ft_id}", 
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    job_data = response.json()
                    status = job_data["status"]
                    
                    print(f"📊 当前状态: {status} (检查次数: {check_count + 1})")
                    
                    if status == "succeeded":
                        model_id = job_data.get("fine_tuned_model")
                        self.fine_tuned_model_id = model_id
                        print(f"🎉 训练完成！模型ID: {model_id}")
                        return model_id
                    elif status == "failed":
                        error = job_data.get("error", "未知错误")
                        print(f"❌ 训练失败: {error}")
                        return None
                    elif status in ["cancelled", "canceled"]:
                        print("⚠️ 训练被取消")
                        return None
                        
                else:
                    print(f"⚠️ 检查状态失败: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ 检查状态时出错: {e}")
            
            check_count += 1
            time.sleep(60)  # 每分钟检查一次
    
    def generate_context_prompt(self, chat_group, conversation_history, target_friend=None):
        """根据聊天对象和历史生成上下文提示"""
        system_content = f"你是雷🐷🐷，一个喜欢说'dds'、'愚蠢'、'丢大师'等词汇的QQ群聊天用户。你在群组'{chat_group or '未知群组'}'中聊天。"
        
        # 如果知道主要对话对象，添加个性化信息
        if target_friend and target_friend in self.chat_patterns:
            pattern = self.chat_patterns[target_friend]
            system_content += f" 你正在与{target_friend}对话（历史互动{pattern['interaction_count']}次）。"
        
        user_content = ""
        if conversation_history:
            user_content = "对话历史:\n" + "\n".join(conversation_history) + "\n\n请以雷🐷🐷的身份回复："
        else:
            user_content = "请以雷🐷🐷的身份开始对话："
            
        return system_content, user_content
    
    def chat(self, chat_group, conversation_history, target_friend=None, max_tokens=50):
        """智能聊天回复"""
        if not self.fine_tuned_model_id:
            print("❌ 请先完成模型微调")
            return None
        
        system_content, user_content = self.generate_context_prompt(chat_group, conversation_history, target_friend)
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": self.fine_tuned_model_id,
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.8,
                    "stop": ["\n", ":", "："]
                }
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                print(f"❌ 生成回复失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 聊天时出错: {e}")
            return None

# 从配置文件读取API密钥
try:
    from config import OPENAI_API_KEY
    API_KEY = OPENAI_API_KEY
except ImportError:
    print("❌ 未找到config.py文件！")
    print("请复制config_template.py为config.py并填入您的API密钥")
    exit(1)

bot = OpenAIChatBot(API_KEY)

# 完整的训练流程
def train_chatbot():
    """完整的训练流程"""
    print("🎯 开始训练雷🐷🐷聊天机器人 (使用GPT-3.5-turbo)...")
    
    # 1. 上传训练数据
    file_id = bot.upload_training_data("deepseek_data_final.jsonl")
    if not file_id:
        print("❌ 训练终止：文件上传失败")
        return None
    
    # 2. 创建微调任务
    ft_id = bot.create_fine_tune(file_id, model="gpt-3.5-turbo", n_epochs=3)
    if not ft_id:
        print("❌ 训练终止：微调任务创建失败")
        return None
    
    # 3. 等待训练完成
    model_id = bot.wait_for_completion(ft_id)
    if model_id:
        print("🎉 训练完成！现在可以开始聊天了")
        
        # 保存模型ID
        with open('trained_model_id.txt', 'w') as f:
            f.write(model_id)
        print(f"📝 模型ID已保存到 trained_model_id.txt")
        
        return model_id
    else:
        print("❌ 训练失败")
        return None

# 测试聊天
def test_chat():
    """测试聊天功能"""
    if not bot.fine_tuned_model_id:
        # 尝试加载保存的模型ID
        try:
            with open('trained_model_id.txt', 'r') as f:
                bot.fine_tuned_model_id = f.read().strip()
            print(f"📝 加载了保存的模型ID: {bot.fine_tuned_model_id}")
        except:
            print("❌ 请先完成模型训练")
            return
    
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
        }
    ]
    
    print("🧪 开始测试聊天效果...")
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- 测试场景 {i} ---")
        response = bot.chat(case["group"], case["history"], case["friend"])
        print(f"群组: {case['group']}")
        print(f"历史: {case['history']}")
        print(f"雷🐷🐷: {response}")
        print("-" * 50)

if __name__ == "__main__":
    print("🤖 OpenAI GPT-3.5-turbo 聊天机器人训练系统")
    print("=" * 50)
    
    # 直接开始训练
    print("🚀 自动开始训练...")
    model_id = train_chatbot()
    
    if model_id:
        print("\n🎉 训练完成！开始测试聊天效果...")
        test_chat()
    else:
        print("\n❌ 训练失败，请检查API密钥和网络连接")
