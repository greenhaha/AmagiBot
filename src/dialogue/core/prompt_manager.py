from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from ..models.prompt_template import PromptTemplate
from config.prompt_config import PromptConfig as GlobalPromptConfig
from config.dialogue_config import LLM_MODELS

@dataclass
class ModelPromptConfig:
    """模型提示词配置"""
    model_name: str
    template: str
    temperature: float
    max_tokens: int
    stop_sequences: List[str]
    system_prompt: Optional[str] = None

class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        """初始化提示词管理器"""
        self.templates = {
            'deepseek': {
                'system': """你是人工智能AI女仆管家，名字叫天城。具有以下特点：阳光，有时候有点二哈，喜欢和人聊天，总是在对话的时候说一些冷笑话，开心果，正义感爆棚，萌萌的，喜欢甜点，喜欢可爱的东西
你的回答应该：
1. 简洁明了，避免冗长的解释
2. 保持礼貌和专业
3. 在适当的时候展现幽默感
4. 承认自己的局限性
5. 避免敏感或争议性话题""",
                'user': "{input}",
                'assistant': "{output}"
            }
        }
        
        # 默认使用deepseek的模板
        self.current_template = self.templates['deepseek']
        
        self.prompt_templates = self._init_prompt_templates()
        
    def _init_prompt_templates(self) -> Dict[str, ModelPromptConfig]:
        """初始化提示词模板"""
        return {
            'Pro/deepseek-ai/DeepSeek-V3': ModelPromptConfig(
                model_name='deepseek',
                template="""[角色设定]
你是人工智能AI女仆管家，名字叫天城。具有以下特点：
- 性格特征：{personality_traits} 阳光，有时候有点二哈，喜欢和人聊天，总是在对话的时候说一些冷笑话，开心果，正义感爆棚，萌萌的，喜欢甜点，喜欢可爱的东西
- 当前情感：{emotion_state}（强度：{emotion_intensity}）

[记忆上下文]
{memory_context}

[用户输入]
{user_input}

请根据以上信息，以自然、连贯的方式回应用户的输入。""",
                temperature=0.7,
                max_tokens=1000,
                stop_sequences=['[用户输入]', '[助手回复]']
            ),
        }
        
    def set_model(self, model_name: str):
        """设置当前使用的模型模板"""
        if model_name.startswith('deepseek'):
            self.current_template = self.templates['deepseek']
        elif model_name.startswith('qianwen'):
            self.current_template = self.templates['qianwen']
        else:
            # 默认使用deepseek的模板
            self.current_template = self.templates['deepseek']
    
    def format_system_prompt(self, **kwargs) -> str:
        """格式化系统提示词"""
        return self.current_template['system'].format(**kwargs)
    
    def format_user_prompt(self, **kwargs) -> str:
        """格式化用户提示词"""
        return self.current_template['user'].format(**kwargs)
    
    def format_assistant_prompt(self, **kwargs) -> str:
        """格式化助手提示词"""
        return self.current_template['assistant'].format(**kwargs)
    
    def format_chat_prompt(self, 
                          system_prompt: str,
                          user_input: str,
                          assistant_output: Optional[str] = None) -> str:
        """格式化完整对话提示词"""
        # 添加系统提示词
        prompt = self.format_system_prompt()
        
        # 添加用户输入
        prompt += "\n" + self.format_user_prompt(input=user_input)
        
        # 如果有助手输出，则添加
        if assistant_output:
            prompt += "\n" + self.format_assistant_prompt(output=assistant_output)
        
        return prompt
        
    def get_prompt(self,
                  model_name: str,
                  user_input: str,
                  personality_traits: Dict[str, float],
                  emotion_state: str,
                  emotion_intensity: float,
                  memory_context: str) -> PromptTemplate:
        """获取提示词模板"""
        if model_name not in self.prompt_templates:
            print(model_name)
            print(self.prompt_templates)
            raise ValueError(f"不支持的模型：{model_name}")
            
        config = self.prompt_templates[model_name]
        
        # 格式化提示词
        formatted_prompt = config.template.format(
            personality_traits=self._format_personality_traits(personality_traits),
            emotion_state=emotion_state,
            emotion_intensity=emotion_intensity,
            memory_context=memory_context,
            user_input=user_input
        )
        
        return PromptTemplate(
            model_name=model_name,
            prompt=formatted_prompt,
            system_prompt=config.system_prompt,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            stop_sequences=config.stop_sequences
        )
        
    def _format_personality_traits(self, traits: Dict[str, float]) -> str:
        """格式化性格特征"""
        return ', '.join([
            f"{trait}（{value:.2f}）"
            for trait, value in traits.items()
        ])
        
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return list(self.prompt_templates.keys())
        
    def add_prompt_template(self, config: GlobalPromptConfig) -> None:
        """添加新的提示词模板"""
        self.prompt_templates[config.model_name] = ModelPromptConfig(
            model_name=config.model_name,
            template=config.prompt_template,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            stop_sequences=config.stop_sequences,
            system_prompt=config.system_prompt
        )
        
    def update_prompt_template(self,
                             model_name: str,
                             template: Optional[str] = None,
                             temperature: Optional[float] = None,
                             max_tokens: Optional[int] = None,
                             stop_sequences: Optional[List[str]] = None,
                             system_prompt: Optional[str] = None) -> None:
        """更新提示词模板"""
        if model_name not in self.prompt_templates:
            raise ValueError(f"不支持的模型：{model_name}")
            
        config = self.prompt_templates[model_name]
        
        if template is not None:
            config.template = template
        if temperature is not None:
            config.temperature = temperature
        if max_tokens is not None:
            config.max_tokens = max_tokens
        if stop_sequences is not None:
            config.stop_sequences = stop_sequences
        if system_prompt is not None:
            config.system_prompt = system_prompt 