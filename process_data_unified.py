#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的聊天记录处理脚本
- 取消群组信息
- 建立ID到名字的映射关系
- 统一使用最常用的名字
"""

import re, json
from datetime import datetime
from collections import defaultdict, Counter

def load_blocks(path, gap_minutes=30):
    """加载聊天记录并按时间间隔分组 - 不包含群组信息"""
    lines = [l.rstrip() for l in open(path, encoding='utf-8')]
    blocks, cur = [], []
    prev_ts = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过群组和对象信息
        if (line.startswith('消息分组:') or line.startswith('消息对象:') or 
            line.startswith('====') or '消息记录' in line or not line or
            line.startswith('系统消息')):
            i += 1
            continue
        
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
                
                # 读取消息内容
                message_lines = []
                j = i + 1
                
                while j < len(lines):
                    next_line = lines[j].strip()
                    
                    if re.match(timestamp_pattern, next_line):
                        break
                    if (next_line.startswith('消息分组:') or 
                        next_line.startswith('消息对象:') or 
                        next_line.startswith('====') or
                        next_line.startswith('系统消息')):
                        break
                    
                    message_lines.append(lines[j].rstrip())
                    j += 1
                
                message = '\n'.join(message_lines).strip()
                
                # 处理时间分组
                try:
                    dt = datetime.fromisoformat(timestamp)
                    if prev_ts and (dt - prev_ts).total_seconds() > gap_minutes*60:
                        if cur:
                            blocks.append(cur)
                        cur = []
                    cur.append((user_id, username, message))
                    prev_ts = dt
                except:
                    pass
                
                i = j
                continue
        
        i += 1
    
    if cur:
        blocks.append(cur)
    return blocks

def build_user_mapping(blocks):
    """构建用户ID到统一名字的映射关系"""
    # 统计每个ID使用的所有名字及其频率
    id_names = defaultdict(Counter)
    
    for blk in blocks:
        for user_id, username, message in blk:
            if username and user_id:
                id_names[user_id][username] += 1
    
    # 为每个ID选择最常用的名字
    user_mapping = {}
    for user_id, name_counts in id_names.items():
        most_common_name = name_counts.most_common(1)[0][0]
        user_mapping[user_id] = most_common_name
        
        # 如果一个ID有多个名字，打印出来查看
        if len(name_counts) > 1:
            print(f"用户ID {user_id} 有多个名字: {dict(name_counts)} -> 统一为: {most_common_name}")
    
    return user_mapping

def make_unified_samples(blocks, user_mapping, target='3159852227', window=3):
    """创建统一的训练样本，不包含群组信息"""
    samples = []
    user_interactions = defaultdict(list)
    
    for blk in blocks:
        for i, (uid, username, text) in enumerate(blk):
            if uid == target and text.strip():  # 目标用户的发言
                # 获取上下文
                ctx = blk[max(0, i-window):i]
                
                # 分析对话对象
                conversation_partners = set()
                for c_uid, c_username, c_text in ctx:
                    if c_uid != target and c_uid in user_mapping:
                        unified_name = user_mapping[c_uid]
                        conversation_partners.add((c_uid, unified_name))
                
                # 构建messages格式的训练样本
                messages = []
                
                # 系统消息，不包含群组信息
                system_content = "你是雷🐷🐷，一个喜欢说'dds'、'愚蠢'、'丢大师'等词汇的QQ群聊天用户。"
                messages.append({"role": "system", "content": system_content})
                
                # 添加对话历史作为用户消息
                if ctx:
                    context_msgs = []
                    for c_uid, c_username, c_text in ctx:
                        if c_text.strip() and c_uid in user_mapping:
                            # 使用统一的名字
                            unified_name = user_mapping[c_uid]
                            context_msgs.append(f"{unified_name}: {c_text}")
                    
                    if context_msgs:
                        user_content = "对话历史:\n" + "\n".join(context_msgs) + "\n\n请以雷🐷🐷的身份回复："
                        messages.append({"role": "user", "content": user_content})
                
                # 助手回复（目标用户的实际回复）
                messages.append({"role": "assistant", "content": text})
                
                # 创建样本
                sample = {
                    "messages": messages,
                    "metadata": {
                        "partners": list(conversation_partners),
                        "timestamp": blk[i][0] if i < len(blk) else None
                    }
                }
                samples.append(sample)
                
                # 记录与特定用户的互动模式
                for partner_id, partner_name in conversation_partners:
                    user_interactions[partner_name].append({
                        "context": context_msgs if 'context_msgs' in locals() else [],
                        "response": text
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
                "common_words": extract_common_words(responses)
            }
    
    return patterns

def extract_common_words(responses):
    """提取常用词汇"""
    words = []
    for response in responses:
        words.extend([w for w in response if len(w) > 1])
    
    return Counter(words).most_common(5)

# 主处理流程
if __name__ == "__main__":
    print("正在处理聊天记录...")

    all_blocks = []
    for filename in ['1.txt', '2.txt']:
        print(f"处理文件: {filename}")
        blocks = load_blocks(filename)
        print(f"  从 {filename} 解析出 {len(blocks)} 个对话块")
        all_blocks.extend(blocks)

    print(f"\n总共解析出 {len(all_blocks)} 个对话块")

    # 构建用户映射
    print("\n构建用户ID到名字的映射关系...")
    user_mapping = build_user_mapping(all_blocks)
    print(f"发现 {len(user_mapping)} 个用户")

    # 显示目标用户的名字
    target_user_id = '3159852227'
    if target_user_id in user_mapping:
        print(f"目标用户(ID: {target_user_id})的统一名字: {user_mapping[target_user_id]}")
    else:
        print(f"❌ 未找到目标用户ID: {target_user_id}")

    # 生成训练样本
    print("\n生成训练样本...")
    all_samples, all_interactions = make_unified_samples(all_blocks, user_mapping)

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

    # 分析聊天模式
    patterns = analyze_chat_patterns(all_interactions)
    print(f"\n👥 发现与 {len(patterns)} 个朋友的聊天模式")

    # 显示主要对话伙伴
    if patterns:
        sorted_friends = sorted(patterns.items(), key=lambda x: x[1]['interaction_count'], reverse=True)
        print("主要对话伙伴:")
        for friend, data in sorted_friends[:5]:
            print(f"  - {friend}: {data['interaction_count']}次互动")

    # 保存用户映射关系
    with open('user_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(user_mapping, f, ensure_ascii=False, indent=2)

    # 保存训练数据  
    with open('deepseek_data_unified.jsonl', 'w', encoding='utf-8') as fout:
        for sample in all_samples:
            training_sample = {
                "messages": sample["messages"]
            }
            fout.write(json.dumps(training_sample, ensure_ascii=False) + '\n')

    # 保存分析结果
    with open('chat_patterns_unified.json', 'w', encoding='utf-8') as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)

    print("\n✅ 数据处理完成！")
    print("生成文件:")
    print("- user_mapping.json: 用户ID到统一名字的映射关系")
    print("- deepseek_data_unified.jsonl: 统一后的训练数据（无群组信息）")
    print("- chat_patterns_unified.json: 聊天模式分析")
    print(f"\n🎯 目标用户({user_mapping.get(target_user_id, '未知')})的训练样本已准备就绪！") 