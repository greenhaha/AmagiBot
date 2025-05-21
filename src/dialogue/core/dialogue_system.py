from typing import List, Dict, Any, Optional
from .prompt_manager import PromptManager
from .dialogue_processor import DialogueProcessor
from ..models.prompt_template import PromptTemplate
from config.prompt_config import PromptConfig
from src.llm.siliconflow import SiliconFlow
from src.llm.base import BaseLLM
from src.emotion import EmotionManager, EmotionAnalyzer
from src.memory.core.multi_source_manager import MultiSourceMemoryManager

class DialogueSystem:
    """对话系统：处理用户输入并生成回复"""
    def __init__(self, 
                 llm: Optional[BaseLLM] = None,
                 emotion_manager: Optional[EmotionManager] = None,
                 emotion_analyzer: Optional[EmotionAnalyzer] = None,
                 memory_manager: Optional[MultiSourceMemoryManager] = None):
        self.prompt_manager = PromptManager()
        self.llm = llm or SiliconFlow()
        self.emotion_manager = emotion_manager
        self.emotion_analyzer = emotion_analyzer
        self.memory_manager = memory_manager
        self.dialogue_processor = DialogueProcessor(
            memory_manager=self.memory_manager,
            llm=self.llm,
            emotion_manager=self.emotion_manager,
            emotion_analyzer=self.emotion_analyzer
        )
        
    def generate_response(self,
                         user_input: str,
                         model_name: str,
                         personality_traits: Dict[str, float],
                         emotion_state: str,
                         emotion_intensity: float,
                         memory_context: str) -> str:
        """生成回复"""
        # 使用对话处理器处理用户输入
        response = self.dialogue_processor.process_input(
            user_input=user_input,
            model_name=model_name,
            personality_traits=personality_traits,
            emotion_state=emotion_state,
            emotion_intensity=emotion_intensity,
            memory_context=memory_context
        )
        
        return response
        
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return self.prompt_manager.get_supported_models()
        
    def add_prompt_template(self, config: PromptConfig) -> None:
        """添加新的提示词模板"""
        self.prompt_manager.add_prompt_template(config)
        
    def update_prompt_template(self,
                             model_name: str,
                             template: Optional[str] = None,
                             temperature: Optional[float] = None,
                             max_tokens: Optional[int] = None,
                             stop_sequences: Optional[List[str]] = None,
                             system_prompt: Optional[str] = None) -> None:
        """更新提示词模板"""
        self.prompt_manager.update_prompt_template(
            model_name=model_name,
            template=template,
            temperature=temperature,
            max_tokens=max_tokens,
            stop_sequences=stop_sequences,
            system_prompt=system_prompt
        ) 