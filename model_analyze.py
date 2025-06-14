# 高级数据处理和优化
def create_persona_aware_samples():
    """创建感知个性的训练样本"""
    print("创建个性化训练样本...")
    
    # 加载原始样本
    samples = []
    with open('deepseek_data.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            samples.append(json.loads(line))
    
    # 分析目标用户(雷🐷🐷)的语言特征
    target_responses = [s['completion'] for s in samples]
    
    # 特征分析
    features = {
        "常用词汇": ["dds", "愚蠢", "🐷", "太愚蠢了"],
        "常用表达": ["呼哈哈", "丢大师", "皮肤全是愚蠢"],  
        "语言风格": "简短、直接、带有游戏用语",
        "表情使用": "常用🐷和[表情]",
        "平均长度": sum(len(r) for r in target_responses) / len(target_responses)
    }
    
    print("语言特征分析:")
    for key, value in features.items():
        print(f"  {key}: {value}")
    
    # 创建增强样本
    enhanced_samples = []
    for sample in samples:
        # 基础样本
        enhanced_samples.append(sample)
        
        # 如果是多人对话，创建针对性变体
        prompt = sample['prompt']
        if '对话历史:' in prompt:
            # 提取对话参与者
            history_part = prompt.split('对话历史:')[1].split('雷🐷🐷:')[0]
            speakers = list(set([line.split(':')[0] for line in history_part.split('\n') if ':' in line]))
            
            # 为每个主要对话者创建个性化提示
            for speaker in speakers[:2]:  # 限制前2个主要对话者
                if speaker.strip() and speaker != '雷🐷🐷':
                    persona_prompt = prompt.replace(
                        '雷🐷🐷: ', 
                        f'雷🐷🐷 对 {speaker}: '
                    )
                    enhanced_samples.append({
                        'prompt': persona_prompt,
                        'completion': sample['completion']
                    })
    
    # 保存增强样本
    with open('enhanced_deepseek_data.jsonl', 'w', encoding='utf-8') as f:
        for sample in enhanced_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    print(f"原始样本: {len(samples)}")
    print(f"增强样本: {len(enhanced_samples)}")
    print("已保存到 enhanced_deepseek_data.jsonl")
    
    return enhanced_samples

def analyze_conversation_styles():
    """分析不同群组的对话风格差异"""
    print("分析对话风格...")
    
    with open('chat_patterns.json', 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    
    # 按互动频率排序
    sorted_friends = sorted(patterns.items(), 
                           key=lambda x: x[1]['interaction_count'], 
                           reverse=True)
    
    print("主要聊天对象分析:")
    print("-" * 60)
    for friend, data in sorted_friends[:10]:  # 显示前10个
        print(f"朋友: {friend}")
        print(f"  互动次数: {data['interaction_count']}")
        print(f"  平均回复长度: {data['avg_response_length']:.1f}字符")
        print(f"  表情使用频率: {data['emoji_usage']:.2f}")
        print(f"  常用词汇: {data['common_words'][:3]}")
        print(f"  活跃群组: {data['groups']}")
        print("-" * 30)

# 运行分析
if __name__ == "__main__":
    create_persona_aware_samples()
    analyze_conversation_styles()
    
    print("\n使用建议:")
    print("1. 使用 enhanced_deepseek_data.jsonl 进行训练以获得更好效果")
    print("2. 可以根据chat_patterns.json调整不同朋友的对话策略")
    print("3. 建议训练时增加epoch数到6-8轮以充分学习个性特征")
