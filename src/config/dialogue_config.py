from typing import Dict, Any, List
from dataclasses import dataclass

# LLM模型配置
LLM_MODELS = {
    'siliconflow': {
        'name': 'Pro/deepseek-ai/DeepSeek-V3',
        'type': 'siliconflow',
        'api_key_env': 'SILICONFLOW_API_KEY',
        'temperature': 0.7,
        'max_tokens': 2000
    },
    'chatgpt': {
        'name': 'gpt-3.5-turbo',
        'type': 'openai',
        'api_key_env': 'OPENAI_API_KEY',
        'temperature': 0.7,
        'max_tokens': 2000
    },
    'deepseek': {
        'name': 'deepseek-chat',
        'type': 'deepseek',
        'api_key_env': 'DEEPSEEK_API_KEY',
        'temperature': 0.7,
        'max_tokens': 2000
    },
    'qianwen': {
        'name': 'qianwen-chat',
        'type': 'qwen',
        'api_key_env': 'QIANWEN_API_KEY',
        'temperature': 0.7,
        'max_tokens': 2000
    }
}

# 默认模型
DEFAULT_MODEL = 'deepseek'

# 模型选择规则
MODEL_SELECTION_RULES = {
    'general': {
        'model': 'siliconflow',
        'keywords': ['你好', '请问', '谢谢']
    },
    'creative': {
        'model': 'chatgpt',
        'keywords': ['创意', '想象', '故事']
    },
    'technical': {
        'model': 'deepseek',
        'keywords': ['技术', '代码', '算法']
    }
}

@dataclass
class DialogueConfig:
    """对话系统配置"""
    
    # 模型配置
    model_name: str = LLM_MODELS['siliconflow']['name']
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # 提示词配置
    system_prompt: str = """你是一个智能助手，具有独特的性格特征和情感状态。
请始终保持友好、专业的态度，并以自然、连贯的方式回应用户的输入。"""
    
    # 对话配置
    max_history: int = 10
    stop_sequences: List[str] = None
    
    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = ['用户：', '助手：']
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'DialogueConfig':
        """从字典创建配置"""
        return cls(
            model_name=config.get('model_name', cls.model_name),
            temperature=config.get('temperature', cls.temperature),
            max_tokens=config.get('max_tokens', cls.max_tokens),
            system_prompt=config.get('system_prompt', cls.system_prompt),
            max_history=config.get('max_history', cls.max_history),
            stop_sequences=config.get('stop_sequences', cls.stop_sequences)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'model_name': self.model_name,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'system_prompt': self.system_prompt,
            'max_history': self.max_history,
            'stop_sequences': self.stop_sequences
        } 