from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime, timedelta
from ..models.emotion_analysis import EmotionAnalysis
from config.emotion_config import EMOTION_STATES, EMOTION_UPDATE_PARAMS
from src.llm.siliconflow import SiliconFlow
from src.llm.base import BaseLLM

class EmotionAnalyzer:
    """情感分析器：分析对话内容和用户行为"""
    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm or SiliconFlow()
        self.emotion_states = EMOTION_STATES
        self.update_params = EMOTION_UPDATE_PARAMS
        
    def analyze_conversation(self, 
                           conversation: str,
                           user_behavior: Dict[str, Any]) -> EmotionAnalysis:
        """分析对话内容和用户行为"""
        # 使用LLM分析对话内容的情感倾向
        prompt = self._create_emotion_analysis_prompt(conversation, user_behavior)
        
        # 构建消息列表
        messages = [
            {
                "role": "system",
                "content": "你是一个情感分析专家，请分析对话内容和用户行为，评估情感状态和情绪商数。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # 调用LLM进行分析
        response = self.llm.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        if not response or 'choices' not in response or not response['choices']:
            # 如果LLM分析失败，使用基于关键词的简单分析
            return self._simple_analysis(conversation, user_behavior)
            
        try:
            # 解析LLM返回的JSON结果
            result = json.loads(response['choices'][0]['message']['content'])
            return EmotionAnalysis(
                emotion_state=result.get('emotion_state', 'neutral'),
                intensity=result.get('intensity', 0.5),
                reason=result.get('reason', ''),
                keywords=result.get('keywords', []),
                eq_score=result.get('eq_score', 0.5)
            )
        except json.JSONDecodeError:
            return self._simple_analysis(conversation, user_behavior)
            
    def _create_emotion_analysis_prompt(self, 
                                      conversation: str,
                                      user_behavior: Dict[str, Any]) -> str:
        """创建情感分析提示词"""
        return f"""请分析以下对话内容和用户行为，评估情感状态和情绪商数。

对话内容：
{conversation}

用户行为数据：
- 对话频率：{user_behavior.get('conversation_frequency', 0)}次/天
- 平均对话时长：{user_behavior.get('avg_duration', 0)}分钟
- 平均输入间隔：{user_behavior.get('avg_interval', 0)}秒
- 对话时间：{user_behavior.get('time_of_day', 'unknown')}
- 对话周期：{user_behavior.get('conversation_cycle', 'unknown')}

请考虑以下因素：
1. 对话内容的情感倾向
2. 用户行为模式
3. 时间特征
4. 互动频率

请以JSON格式返回分析结果：
{{
    "emotion_state": "happy/neutral/sad/angry",
    "intensity": 0-1的分数,
    "reason": "分析原因",
    "keywords": ["关键词1", "关键词2", ...],
    "eq_score": 0-1的情绪商数
}}"""

    def _simple_analysis(self, 
                        conversation: str,
                        user_behavior: Dict[str, Any]) -> EmotionAnalysis:
        """基于关键词的简单分析"""
        # 检查情感关键词
        emotion_scores = {}
        for state, config in self.emotion_states.items():
            score = sum(1 for keyword in config['keywords'] if keyword in conversation)
            emotion_scores[state] = score / len(config['keywords'])
            
        # 选择得分最高的情感状态
        max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        # 计算情绪强度
        intensity = min(1.0, max_emotion[1] * 1.5)
        
        # 计算情绪商数
        eq_score = self._calculate_eq_score(user_behavior)
        
        return EmotionAnalysis(
            emotion_state=max_emotion[0],
            intensity=intensity,
            reason="基于关键词分析",
            keywords=[k for k, v in emotion_scores.items() if v > 0],
            eq_score=eq_score
        )
        
    def _calculate_eq_score(self, user_behavior: Dict[str, Any]) -> float:
        """计算情绪商数"""
        # 基础分数
        base_score = 0.5
        
        # 根据对话频率调整
        frequency = user_behavior.get('conversation_frequency', 0)
        if 1 <= frequency <= 5:  # 适中的对话频率
            base_score += 0.1
        elif frequency > 5:  # 过高的对话频率
            base_score -= 0.1
            
        # 根据对话时长调整
        duration = user_behavior.get('avg_duration', 0)
        if 5 <= duration <= 30:  # 适中的对话时长
            base_score += 0.1
        elif duration > 30:  # 过长的对话时长
            base_score -= 0.1
            
        # 根据输入间隔调整
        interval = user_behavior.get('avg_interval', 0)
        if 1 <= interval <= 10:  # 适中的输入间隔
            base_score += 0.1
        elif interval > 10:  # 过长的输入间隔
            base_score -= 0.1
            
        # 根据时间特征调整
        time_of_day = user_behavior.get('time_of_day', '')
        if time_of_day in ['morning', 'afternoon']:  # 积极的时间段
            base_score += 0.1
        elif time_of_day in ['night', 'late_night']:  # 消极的时间段
            base_score -= 0.1
            
        return max(0.0, min(1.0, base_score)) 