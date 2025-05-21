from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class PromptConfig:
    """提示词配置"""
    
    # 系统提示词
    system_prompt: str = """你是一个智能助手，具有独特的性格特征和情感状态。
请始终保持友好、专业的态度，并以自然、连贯的方式回应用户的输入。"""
    
    # 情感提示词
    emotion_prompt: str = """请根据当前的情感状态和强度，调整你的回复风格。
情感状态：{emotion_state}
情感强度：{emotion_intensity}"""
    
    # 记忆提示词
    memory_prompt: str = """请参考以下相关记忆来生成回复：
{memory_context}"""
    
    # 性格提示词
    personality_prompt: str = """请根据以下性格特征来调整你的回复风格：
{personality_traits}"""
    
    # 提示词模板
    prompt_template: str = """{system_prompt}

{emotion_prompt}

{memory_prompt}

{personality_prompt}

用户输入：{user_input}

请生成回复："""
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'PromptConfig':
        """从字典创建配置"""
        return cls(
            system_prompt=config.get('system_prompt', cls.system_prompt),
            emotion_prompt=config.get('emotion_prompt', cls.emotion_prompt),
            memory_prompt=config.get('memory_prompt', cls.memory_prompt),
            personality_prompt=config.get('personality_prompt', cls.personality_prompt),
            prompt_template=config.get('prompt_template', cls.prompt_template)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'system_prompt': self.system_prompt,
            'emotion_prompt': self.emotion_prompt,
            'memory_prompt': self.memory_prompt,
            'personality_prompt': self.personality_prompt,
            'prompt_template': self.prompt_template
        }
    
    def format_prompt(self, 
                     user_input: str,
                     emotion_state: str = None,
                     emotion_intensity: float = None,
                     memory_context: str = None,
                     personality_traits: Dict[str, float] = None) -> str:
        """格式化提示词"""
        # 准备情感提示词
        emotion_prompt = ""
        if emotion_state and emotion_intensity is not None:
            emotion_prompt = self.emotion_prompt.format(
                emotion_state=emotion_state,
                emotion_intensity=emotion_intensity
            )
        
        # 准备记忆提示词
        memory_prompt = ""
        if memory_context:
            memory_prompt = self.memory_prompt.format(
                memory_context=memory_context
            )
        
        # 准备性格提示词
        personality_prompt = ""
        if personality_traits:
            personality_prompt = self.personality_prompt.format(
                personality_traits=personality_traits
            )
        
        # 格式化完整提示词
        return self.prompt_template.format(
            system_prompt=self.system_prompt,
            emotion_prompt=emotion_prompt,
            memory_prompt=memory_prompt,
            personality_prompt=personality_prompt,
            user_input=user_input
        ) 