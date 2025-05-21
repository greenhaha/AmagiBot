from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from ..models.emotion_analysis import EmotionAnalysis
from config.emotion_config import EMOTION_STATES, PERSONALITY_TRAITS
from src.llm.siliconflow import SiliconFlow
from src.llm.base import BaseLLM

class EmotionReasoner:
    """情感推理器：进行情感推理和情绪商数调整"""
    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm or SiliconFlow()
        self.emotion_states = EMOTION_STATES
        self.personality_traits = PERSONALITY_TRAITS
        
    def reason_emotion(self,
                      current_emotion: EmotionAnalysis,
                      conversation_history: List[str],
                      personality: Dict[str, float]) -> Tuple[EmotionAnalysis, float]:
        """进行情感推理"""
        # 创建推理提示词
        prompt = self._create_reasoning_prompt(
            current_emotion,
            conversation_history,
            personality
        )
        
        # 构建消息列表
        messages = [
            {
                "role": "system",
                "content": "你是一个情感推理专家，请分析对话历史和当前情感状态，进行情感推理。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # 使用LLM进行推理
        response = self.llm.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        if not response or 'choices' not in response or not response['choices']:
            # 如果LLM推理失败，使用基于规则的简单推理
            return self._simple_reasoning(
                current_emotion,
                conversation_history,
                personality
            )
            
        try:
            # 解析LLM返回的JSON结果
            result = json.loads(response['choices'][0]['message']['content'])
            
            # 创建新的情感分析结果
            new_emotion = EmotionAnalysis(
                emotion_state=result.get('emotion_state', current_emotion.emotion_state),
                intensity=result.get('intensity', current_emotion.intensity),
                reason=result.get('reason', ''),
                keywords=result.get('keywords', current_emotion.keywords),
                eq_score=result.get('eq_score', current_emotion.eq_score)
            )
            
            # 获取情绪商数调整值
            eq_adjustment = result.get('eq_adjustment', 0.0)
            
            return new_emotion, eq_adjustment
            
        except json.JSONDecodeError:
            return self._simple_reasoning(
                current_emotion,
                conversation_history,
                personality
            )
            
    def _create_reasoning_prompt(self,
                               current_emotion: EmotionAnalysis,
                               conversation_history: List[str],
                               personality: Dict[str, float]) -> str:
        """创建推理提示词"""
        return f"""请分析以下对话历史和当前情感状态，进行情感推理。

当前情感状态：
- 情感：{current_emotion.emotion_state}
- 强度：{current_emotion.intensity}
- 原因：{current_emotion.reason}
- 关键词：{', '.join(current_emotion.keywords)}
- 情绪商数：{current_emotion.eq_score}

性格特征：
{', '.join([f'{k}: {v:.2f}' for k, v in personality.items()])}

最近对话历史：
{chr(10).join(conversation_history[-5:])}

请考虑以下因素：
1. 对话的情感发展
2. 性格特征的影响
3. 情绪商数的变化
4. 情感状态的合理性

请以JSON格式返回推理结果：
{{
    "emotion_state": "happy/neutral/sad/angry",
    "intensity": 0-1的分数,
    "reason": "推理原因",
    "keywords": ["关键词1", "关键词2", ...],
    "eq_score": 0-1的情绪商数,
    "eq_adjustment": -0.1到0.1的调整值
}}"""

    def _simple_reasoning(self,
                         current_emotion: EmotionAnalysis,
                         conversation_history: List[str],
                         personality: Dict[str, float]) -> Tuple[EmotionAnalysis, float]:
        """基于规则的简单推理"""
        # 分析最近对话的情感倾向
        emotion_scores = self._analyze_conversation_emotion(conversation_history[-5:])
        
        # 根据性格特征调整情感
        adjusted_emotion = self._adjust_emotion_by_personality(
            current_emotion,
            emotion_scores,
            personality
        )
        
        # 计算情绪商数调整值
        eq_adjustment = self._calculate_eq_adjustment(
            current_emotion,
            adjusted_emotion,
            personality
        )
        
        return adjusted_emotion, eq_adjustment
        
    def _analyze_conversation_emotion(self, conversations: List[str]) -> Dict[str, float]:
        """分析对话情感倾向"""
        emotion_scores = {state: 0.0 for state in self.emotion_states.keys()}
        
        for conversation in conversations:
            for state, config in self.emotion_states.items():
                score = sum(1 for keyword in config['keywords'] if keyword in conversation)
                emotion_scores[state] += score / len(config['keywords'])
                
        # 归一化分数
        total = sum(emotion_scores.values())
        if total > 0:
            emotion_scores = {k: v/total for k, v in emotion_scores.items()}
            
        return emotion_scores
        
    def _adjust_emotion_by_personality(self,
                                     current_emotion: EmotionAnalysis,
                                     emotion_scores: Dict[str, float],
                                     personality: Dict[str, float]) -> EmotionAnalysis:
        """根据性格特征调整情感"""
        # 计算性格特征对情感的影响
        personality_impact = {
            'humor': 0.1,      # 幽默感增加积极情感
            'seriousness': -0.1,  # 严肃性增加消极情感
            'empathy': 0.05,   # 同理心增加情感强度
            'creativity': 0.05  # 创造力增加情感变化
        }
        
        # 应用性格特征影响
        adjusted_intensity = current_emotion.intensity
        for trait, weight in personality.items():
            adjusted_intensity += personality_impact.get(trait, 0) * weight
            
        # 确保强度在有效范围内
        adjusted_intensity = max(0.0, min(1.0, adjusted_intensity))
        
        # 选择最显著的情感状态
        max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        return EmotionAnalysis(
            emotion_state=max_emotion[0],
            intensity=adjusted_intensity,
            reason=f"基于对话分析和性格特征调整",
            keywords=current_emotion.keywords,
            eq_score=current_emotion.eq_score
        )
        
    def _calculate_eq_adjustment(self,
                               current_emotion: EmotionAnalysis,
                               new_emotion: EmotionAnalysis,
                               personality: Dict[str, float]) -> float:
        """计算情绪商数调整值"""
        # 基础调整值
        base_adjustment = 0.0
        
        # 根据情感变化调整
        if new_emotion.emotion_state != current_emotion.emotion_state:
            if new_emotion.emotion_state in ['happy', 'neutral']:
                base_adjustment += 0.05
            else:
                base_adjustment -= 0.05
                
        # 根据情感强度调整
        intensity_diff = new_emotion.intensity - current_emotion.intensity
        base_adjustment += intensity_diff * 0.1
        
        # 根据性格特征调整
        personality_adjustment = 0.0
        for trait, weight in personality.items():
            if trait == 'empathy':
                personality_adjustment += weight * 0.1
            elif trait == 'seriousness':
                personality_adjustment -= weight * 0.05
                
        # 合并调整值
        total_adjustment = base_adjustment + personality_adjustment
        
        # 确保调整值在合理范围内
        return max(-0.1, min(0.1, total_adjustment)) 