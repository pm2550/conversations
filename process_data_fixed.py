import re, json
from datetime import datetime
from collections import defaultdict

def load_blocks(path, gap_minutes=30):
    """加载聊天记录并按时间间隔分组 - 修复多行消息格式"""
    lines = [l.rstrip() for l in open(path, encoding='utf-8')]  # 保留空行，只去除右侧空白
    blocks, cur = [], []
    prev_ts = None
    current_group = None
    current_chat = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 检查是否是消息分组或对象标识
        if line.startswith('消息分组:'):
            current_group = line[5:]
            i += 1
            continue
        elif line.startswith('消息对象:'):
            current_chat = line[5:]
            i += 1
            continue
        elif line.startswith('====') or '消息记录' in line or not line:
            i += 1
            continue
        elif line.startswith('系统消息'):
            i += 1
            continue
        
        # 🔧 修复时间戳和消息解析逻辑
        # 检查是否是时间戳行
        timestamp_pattern = r'^(\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2})\s+'
        ts_match = re.match(timestamp_pattern, line)
        
        if ts_match:
            timestamp = ts_match.group(1)
            rest = line[ts_match.end():]
            
            # 匹配用户信息：发言者(ID)
            user_match = re.match(r'(.+?)\((\d+)\)\s*$', rest)
            if user_match:
                username = user_match.group(1).strip()
                user_id = user_match.group(2)
                
                # 🔧 关键修复：读取下一行(们)作为消息内容
                message_lines = []
                j = i + 1
                
                # 继续读取直到遇到下一个时间戳行或文件结束
                while j < len(lines):
                    next_line = lines[j].strip()
                    
                    # 如果遇到下一个时间戳行，停止
                    if re.match(timestamp_pattern, next_line):
                        break
                    # 如果遇到分组/对象标识，停止
                    if (next_line.startswith('消息分组:') or 
                        next_line.startswith('消息对象:') or 
                        next_line.startswith('====') or
                        next_line.startswith('系统消息')):
                        break
                    
                    # 添加消息行（包括空行）
                    message_lines.append(lines[j].rstrip())
                    j += 1
                
                # 合并消息内容
                message = '\n'.join(message_lines).strip()
                
                # 调试前几个解析结果
                if len(blocks) < 2:
                    print(f"调试解析: 时间戳='{timestamp}', 用户名='{username}', ID={user_id}")
                    print(f"  消息内容: '{message}' (长度: {len(message)})")
                
                # 处理时间和分组
                try:
                    dt = datetime.fromisoformat(timestamp)
                    if prev_ts and (dt - prev_ts).total_seconds() > gap_minutes*60:
                        if cur:
                            blocks.append((current_group, current_chat, cur))
                        cur = []
                    cur.append((user_id, username, message))
                    prev_ts = dt
                except:
                    pass
                
                # 跳到消息结束位置
                i = j
                continue
        
        i += 1
    
    if cur:
        blocks.append((current_group, current_chat, cur))
    return blocks

def make_enhanced_samples(blocks, target='3159852227', window=3):
    """创建增强的训练样本，包含群组信息和对话者关系"""
    samples = []
    user_interactions = defaultdict(list)  # 记录目标用户与每个人的对话
    
    # 用户名解析已修复，不再需要映射表
    print("✅ 使用修复后的用户名解析")
    
    for group_name, chat_name, blk in blocks:
        # 提取目标用户与其他用户的对话模式
        for i, (uid, username, text) in enumerate(blk):
            if uid == target and text.strip():  # 目标用户的发言
                # 获取上下文
                ctx = blk[max(0, i-window):i]
                
                # 分析对话对象
                conversation_partners = set()
                for c_uid, c_username, c_text in ctx:
                    if c_uid != target:
                        # 直接使用解析出的用户名
                        conversation_partners.add((c_uid, c_username))
                
                # 构建messages格式的训练样本
                messages = []
                
                # 系统消息，包含群组和角色信息
                system_content = f"你是雷🐷🐷，一个喜欢说'dds'、'愚蠢'、'丢大师'等词汇的QQ群聊天用户。你在群组'{chat_name or '未知群组'}'中聊天。"
                messages.append({"role": "system", "content": system_content})
                
                # 添加对话历史作为用户消息
                if ctx:
                    context_msgs = []
                    for c_uid, c_username, c_text in ctx:
                        if c_text.strip():
                            # 直接使用解析出的用户名
                            context_msgs.append(f"{c_username}: {c_text}")
                    
                    if context_msgs:
                        user_content = "对话历史:\n" + "\n".join(context_msgs) + "\n\n请以雷🐷🐷的身份回复："
                        messages.append({"role": "user", "content": user_content})
                
                # 助手回复（目标用户的实际回复）
                messages.append({"role": "assistant", "content": text})
                
                # 创建样本
                sample = {
                    "messages": messages,
                    "metadata": {
                        "group": group_name,
                        "chat": chat_name,
                        "partners": list(conversation_partners),
                        "timestamp": blk[i][0] if i < len(blk) else None
                    }
                }
                samples.append(sample)
                
                # 记录与特定用户的互动模式
                for partner_id, partner_name in conversation_partners:
                    user_interactions[partner_name].append({
                        "context": context_msgs if 'context_msgs' in locals() else [],
                        "response": text,
                        "group": chat_name
                    })
    
    return samples, user_interactions

def analyze_chat_patterns(user_interactions):
    """分析用户对不同朋友的聊天模式"""
    patterns = {}
    for friend, interactions in user_interactions.items():
        if len(interactions) >= 3:  # 至少要有3次互动才分析
            responses = [inter["response"] for inter in interactions]
            
            # 分析特征
            avg_length = sum(len(r) for r in responses) / len(responses)
            emoji_count = sum(r.count('[') + r.count('🐷') + r.count('愚蠢') for r in responses)
            
            patterns[friend] = {
                "interaction_count": len(interactions),
                "avg_response_length": avg_length,
                "emoji_usage": emoji_count / len(responses),
                "common_words": extract_common_words(responses),
                "groups": list(set(inter["group"] for inter in interactions))
            }
    
    return patterns

def extract_common_words(responses):
    """提取常用词汇"""
    words = []
    for response in responses:
        # 简单的词汇提取
        words.extend([w for w in response if len(w) > 1])
    
    from collections import Counter
    return Counter(words).most_common(5)

# 🔧 修复并处理数据
print("正在处理聊天记录...")

all_samples = []
all_interactions = defaultdict(list)

for filename in ['1.txt', '2.txt']:
    print(f"处理文件: {filename}")
    blocks = load_blocks(filename)
    print(f"  从 {filename} 解析出 {len(blocks)} 个对话块")
    
    samples, interactions = make_enhanced_samples(blocks)
    all_samples.extend(samples)
    
    # 合并互动数据
    for friend, friend_interactions in interactions.items():
        all_interactions[friend].extend(friend_interactions)

print(f"\n📊 数据统计:")
print(f"总共生成了 {len(all_samples)} 个训练样本")

# 验证样本质量
if all_samples:
    sample = all_samples[0]
    print(f"\n📝 第一个训练样本预览:")
    print(f"系统消息: {sample['messages'][0]['content']}")
    if len(sample['messages']) > 1:
        print(f"用户消息: {sample['messages'][1]['content'][:100]}...")
    if len(sample['messages']) > 2:
        print(f"助手回复: {sample['messages'][2]['content'][:50]}...")
else:
    print("\n❌ 没有生成任何训练样本")

# 分析聊天模式
patterns = analyze_chat_patterns(all_interactions)
print(f"\n👥 发现与 {len(patterns)} 个朋友的聊天模式")

# 显示主要对话伙伴
if patterns:
    sorted_friends = sorted(patterns.items(), key=lambda x: x[1]['interaction_count'], reverse=True)
    print("主要对话伙伴:")
    for friend, data in sorted_friends[:5]:
        print(f"  - {friend}: {data['interaction_count']}次互动")

# 保存训练数据  
with open('deepseek_data_final.jsonl', 'w', encoding='utf-8') as fout:
    for sample in all_samples:
        # 只保存训练需要的字段，使用messages格式
        training_sample = {
            "messages": sample["messages"]
        }
        fout.write(json.dumps(training_sample, ensure_ascii=False) + '\n')

# 保存分析结果
with open('chat_patterns_final.json', 'w', encoding='utf-8') as f:
    json.dump(patterns, f, ensure_ascii=False, indent=2)

print("\n✅ 数据处理完成！")
print("生成文件:")
print("- deepseek_data_final.jsonl: 最终修复的训练数据")
print("- chat_patterns_final.json: 聊天模式分析")
print("\n🎯 目标用户(雷🐷🐷)的训练样本已准备就绪！") 