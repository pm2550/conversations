import json
import tiktoken

def count_tokens_in_jsonl(filename):
    """计算JSONL文件中的token数量"""
    # 使用GPT-3.5-turbo的编码器
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    total_tokens = 0
    total_samples = 0
    
    print(f"📊 正在分析文件: {filename}")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        sample = json.loads(line)
                        sample_tokens = 0
                        
                        # 计算每个消息的token数
                        if 'messages' in sample:
                            for message in sample['messages']:
                                content = message.get('content', '')
                                tokens = len(encoding.encode(content))
                                sample_tokens += tokens
                        
                        total_tokens += sample_tokens
                        total_samples += 1
                        
                        # 显示前几个样本的详细信息
                        if line_num <= 5:
                            print(f"  样本 {line_num}: {sample_tokens} tokens")
                            if 'messages' in sample:
                                for i, msg in enumerate(sample['messages']):
                                    msg_tokens = len(encoding.encode(msg.get('content', '')))
                                    role = msg.get('role', 'unknown')
                                    content_preview = msg.get('content', '')[:50] + "..." if len(msg.get('content', '')) > 50 else msg.get('content', '')
                                    print(f"    {role}: {msg_tokens} tokens - {content_preview}")
                        
                    except json.JSONDecodeError as e:
                        print(f"⚠️ 第{line_num}行JSON解析错误: {e}")
                        continue
                        
    except FileNotFoundError:
        print(f"❌ 找不到文件: {filename}")
        return None, None
    except Exception as e:
        print(f"❌ 处理文件时出错: {e}")
        return None, None
    
    return total_tokens, total_samples

def estimate_training_cost(total_tokens):
    """估算训练成本"""
    # OpenAI GPT-3.5-turbo微调价格 (2024年价格)
    training_cost_per_1k_tokens = 0.008  # $0.008 per 1K tokens
    
    cost = (total_tokens / 1000) * training_cost_per_1k_tokens
    return cost

def main():
    print("🔢 Token计数器 - 分析训练数据")
    print("=" * 50)
    
    filename = "deepseek_data_final.jsonl"
    total_tokens, total_samples = count_tokens_in_jsonl(filename)
    
    if total_tokens is not None:
        print(f"\n📈 统计结果:")
        print(f"总样本数: {total_samples:,}")
        print(f"总Token数: {total_tokens:,}")
        print(f"平均每样本Token数: {total_tokens/total_samples:.1f}")
        
        # 估算成本
        cost = estimate_training_cost(total_tokens)
        print(f"\n💰 估算训练成本:")
        print(f"GPT-3.5-turbo微调: ${cost:.2f} USD")
        
        # 文件大小信息
        import os
        file_size = os.path.getsize(filename) / (1024 * 1024)  # MB
        print(f"\n📁 文件信息:")
        print(f"文件大小: {file_size:.1f} MB")
        print(f"Token密度: {total_tokens/file_size:.0f} tokens/MB")
        
        # OpenAI限制检查
        print(f"\n⚠️ OpenAI限制检查:")
        if total_samples < 10:
            print("❌ 样本数量不足！OpenAI要求至少10个训练样本")
        elif total_samples > 100000:
            print("⚠️ 样本数量过多！建议控制在10万以内")
        else:
            print("✅ 样本数量符合要求")
            
        if total_tokens > 50000000:  # 50M tokens
            print("⚠️ Token数量较大，训练时间可能很长")
        else:
            print("✅ Token数量合理")
    
    else:
        print("❌ 无法分析文件")

if __name__ == "__main__":
    main() 