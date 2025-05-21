from typing import Dict, Any, Optional, List
from datetime import datetime
from src.memory.core.multi_source_manager import MultiSourceMemoryManager
from src.emotion import EmotionManager, EmotionAnalyzer
from src.llm.base import BaseLLM
from src.dialogue.core.prompt_manager import PromptManager

class DialogueProcessor:
    """对话处理器：整合记忆系统和情感系统处理对话"""
    def __init__(self,
                 memory_manager: MultiSourceMemoryManager,
                 emotion_manager: EmotionManager,
                 emotion_analyzer: EmotionAnalyzer,
                 llm: BaseLLM):
        self.memory_manager = memory_manager
        self.emotion_manager = emotion_manager
        self.emotion_analyzer = emotion_analyzer
        self.llm = llm
        self.prompt_manager = PromptManager()
        
    def process_dialogue(self,
                        user_id: str,
                        user_input: str,
                        personality_traits: Dict[str, float],
                        model_name: str = "siliconflow") -> str:
        """处理对话并生成回复"""
        # 1. 分析用户输入的情感
        emotion_analysis = self.emotion_analyzer.analyze_emotion(user_input)
        
        # 2. 更新情感状态
        self.emotion_manager.update_emotion_state(
            user_id=user_id,
            emotion_state=emotion_analysis.emotion_state,
            intensity=emotion_analysis.intensity,
            metadata={
                'trigger': user_input,
                'analysis_method': 'llm',
                'confidence': emotion_analysis.confidence
            }
        )
        
        # 3. 获取当前情感状态
        current_emotion = self.emotion_manager.get_emotion_state(user_id)
        
        # 4. 从记忆系统检索相关记忆
        memories = self.memory_manager.get_memories(
            query=user_input,
            user_id=user_id,
            limit=5
        )
        
        # 5. 构建记忆上下文
        memory_context = self._build_memory_context(memories)
        
        # 6. 构建情感上下文
        emotion_context = self._build_emotion_context(current_emotion)
        
        # 7. 构建系统提示
        system_prompt = self._build_system_prompt(
            personality_traits=personality_traits,
            emotion_context=emotion_context,
            memory_context=memory_context
        )
        
        # 8. 生成回复
        response = self.process_input(
            user_input=user_input,
            model_name=model_name,
            personality_traits=personality_traits,
            emotion_state=emotion_analysis.emotion_state,
            emotion_intensity=emotion_analysis.intensity,
            memory_context=memory_context
        )
        
        # 9. 存储对话记忆
        self._store_dialogue_memory(
            user_id=user_id,
            user_input=user_input,
            response=response,
            emotion_state=current_emotion,
            metadata={
                'emotion_analysis': emotion_analysis.dict(),
                'memory_context': memory_context,
                'personality_traits': personality_traits
            }
        )
        
        return response
        
    def process_input(self,
                     user_input: str,
                     model_name: str,
                     personality_traits: Dict[str, float],
                     emotion_state: str,
                     emotion_intensity: float,
                     memory_context: str) -> str:
        """处理用户输入并生成回复"""
        # 获取提示词模板
        prompt_template = self.prompt_manager.get_prompt(
            model_name=model_name,
            user_input=user_input,
            personality_traits=personality_traits,
            emotion_state=emotion_state,
            emotion_intensity=emotion_intensity,
            memory_context=memory_context
        )
        
        # 构建消息列表
        messages = [
            {
                "role": "system",
                "content": prompt_template.system_prompt or ""
            },
            {
                "role": "user",
                "content": prompt_template.prompt
            }
        ]
        
        # 调用LLM生成回复
        response = self.llm.chat(
            messages=messages,
            temperature=prompt_template.temperature,
            max_tokens=prompt_template.max_tokens
        )
        
        # 从响应中提取内容
        if response and 'choices' in response and len(response['choices']) > 0:
            return response['choices'][0]['message']['content']
        else:
            return "抱歉，我暂时无法生成回复。"
        
    def _build_memory_context(self, memories: List[Any]) -> str:
        """构建记忆上下文"""
        if not memories:
            return "没有相关的历史记忆。"
            
        context_parts = ["相关历史记忆："]
        for memory in memories:
            context_parts.append(f"- {memory.content}")
            if memory.key_points:
                context_parts.append(f"  关键点：{', '.join(memory.key_points)}")
                
        return "\n".join(context_parts)
        
    def _build_emotion_context(self, emotion_state: Dict[str, Any]) -> str:
        """构建情感上下文"""
        context_parts = ["当前情感状态："]
        context_parts.append(f"- 主要情感：{emotion_state['primary_emotion']}")
        context_parts.append(f"- 情感强度：{emotion_state['intensity']:.2f}")
        if emotion_state['secondary_emotions']:
            context_parts.append(f"- 次要情感：{', '.join(emotion_state['secondary_emotions'])}")
            
        return "\n".join(context_parts)
        
    def _build_system_prompt(self,
                           personality_traits: Dict[str, float],
                           emotion_context: str,
                           memory_context: str) -> str:
        """构建系统提示"""
        prompt_parts = [
            "你是一个具有情感和记忆能力的AI助手。",
            "请根据以下信息生成回复：",
            "",
            "性格特征：",
        ]
        
        # 添加性格特征
        for trait, value in personality_traits.items():
            prompt_parts.append(f"- {trait}: {value:.2f}")
            
        # 添加情感和记忆上下文
        prompt_parts.extend([
            "",
            emotion_context,
            "",
            memory_context,
            "",
            "请确保你的回复：",
            "1. 符合你的性格特征",
            "2. 考虑当前的情感状态",
            "3. 适当引用相关的历史记忆",
            "4. 保持自然和连贯的对话风格"
        ])
        
        return "\n".join(prompt_parts)
        
    def _store_dialogue_memory(self,
                             user_id: str,
                             user_input: str,
                             response: str,
                             emotion_state: Dict[str, Any],
                             metadata: Dict[str, Any]) -> None:
        """存储对话记忆"""
        # 存储用户输入
        self.memory_manager.add_memory(
            content=user_input,
            user_id=user_id,
            source_name="conversation",
            metadata={
                **metadata,
                'type': 'user_input',
                'emotion_state': emotion_state
            }
        )
        
        # 存储AI回复
        self.memory_manager.add_memory(
            content=response,
            user_id=user_id,
            source_name="conversation",
            metadata={
                **metadata,
                'type': 'ai_response',
                'emotion_state': emotion_state
            }
        ) 