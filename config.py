# MongoDB配置
MONGO_CONFIG = {
    'host': 'localhost',
    'port': 27017,
    'db_name': 'chatbot_db',
    'stm_collection': 'stm_conversations',  # 短期记忆集合
    'ltm_collection': 'ltm_conversations'   # 长期记忆集合
}

# 记忆系统配置
MEMORY_CONFIG = {
    'stm_size': 10,          # 短期记忆容量
    'ltm_threshold': 3,      # 提升为长期记忆的阈值（出现次数）
    'context_window': 5,     # 上下文窗口大小
    'memory_decay': 0.1,     # 记忆衰减率
    'importance_keywords': [  # 重要关键词（出现这些词的内容更容易进入长期记忆）
        '重要', '记住', '关键', '必须', '一定',
        '永远', '永远记住', '不要忘记'
    ]
}

# LLM配置
LLM_CONFIG = {
    'models': {
        'gpt-3.5': {
            'type': 'openai',
            'name': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 2000,
            'api_key_env': 'OPENAI_API_KEY'
        },
        'gpt-4': {
            'type': 'openai',
            'name': 'gpt-4',
            'temperature': 0.7,
            'max_tokens': 2000,
            'api_key_env': 'OPENAI_API_KEY'
        },
        'deepseek': {
            'type': 'deepseek',
            'name': 'deepseek-chat',
            'temperature': 0.7,
            'max_tokens': 2000,
            'api_key_env': 'DEEPSEEK_API_KEY'
        },
        'qwen': {
            'type': 'qwen',
            'name': 'qwen-turbo',
            'temperature': 0.7,
            'max_tokens': 2000,
            'api_key_env': 'QWEN_API_KEY'
        }
    },
    'default_model': 'gpt-3.5',
    'model_selection_rules': {
        'creative': {
            'model': 'gpt-4',
            'keywords': ['想象', '创意', '故事', '创作', '艺术']
        },
        'precise': {
            'model': 'deepseek',
            'keywords': ['解释', '分析', '计算', '证明', '定义']
        },
        'casual': {
            'model': 'qwen',
            'keywords': ['聊天', '闲聊', '日常', '生活']
        }
    }
}

# 对话系统配置
DIALOGUE_CONFIG = {
    'prompt_templates': {
        'default': """你是一个名为"天成"的AI助手。请根据以下信息生成回复：
用户ID: {user_id}
当前情绪: {emotion}
性格特征: {personality}
对话历史: {context}

用户输入: {user_input}""",
        
        'creative': """你是一个富有创造力的AI助手"天成"。请根据以下信息生成富有想象力的回复：
用户ID: {user_id}
当前情绪: {emotion}
性格特征: {personality}
对话历史: {context}

用户输入: {user_input}""",
        
        'precise': """你是一个严谨的AI助手"天成"。请根据以下信息生成准确、专业的回复：
用户ID: {user_id}
当前情绪: {emotion}
性格特征: {personality}
对话历史: {context}

用户输入: {user_input}"""
    },
    'memory_analysis_prompt': """请分析以下对话内容，判断是否应该存储在长期记忆中。
考虑以下因素：
1. 信息的重要性
2. 是否包含关键信息
3. 是否值得长期保存
4. 是否具有普遍参考价值

对话内容：
{conversation}

请以JSON格式返回分析结果：
{
    "should_store_in_ltm": true/false,
    "reason": "分析原因",
    "importance_score": 0-1的分数,
    "key_points": ["关键点1", "关键点2", ...]
}"""
} 