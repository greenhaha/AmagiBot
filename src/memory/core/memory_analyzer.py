from typing import Dict, Any, List, Optional
import json
from ..models.memory_analysis import MemoryAnalysis
from config.memory_config import MEMORY_ANALYSIS_PROMPT, IMPORTANCE_KEYWORDS
from src.llm.siliconflow import SiliconFlow
from src.llm.base import BaseLLM

class MemoryAnalyzer:
    """记忆分析器：分析对话内容的重要性"""
    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm or SiliconFlow()
        self.importance_keywords = IMPORTANCE_KEYWORDS
        
    def analyze_conversation(self, conversation: str) -> MemoryAnalysis:
        """分析对话内容"""
        # 使用LLM分析对话内容
        prompt = MEMORY_ANALYSIS_PROMPT.format(conversation=conversation)
        
        # 构建消息列表
        messages = [
            {
                "role": "system",
                "content": "你是一个记忆分析专家，请分析对话内容的重要性，判断是否应该存储在长期记忆中。"
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
            return self._simple_analysis(conversation)
            
        try:
            # 解析LLM返回的JSON结果
            result = json.loads(response['choices'][0]['message']['content'])
            return MemoryAnalysis(
                should_store_in_ltm=result.get('should_store_in_ltm', False),
                reason=result.get('reason', ''),
                importance_score=result.get('importance_score', 0.0),
                key_points=result.get('key_points', [])
            )
        except json.JSONDecodeError:
            # 如果JSON解析失败，使用基于关键词的简单分析
            return self._simple_analysis(conversation)
            
    def _simple_analysis(self, conversation: str) -> MemoryAnalysis:
        """基于关键词的简单分析"""
        # 检查是否包含重要关键词
        has_importance_keywords = any(keyword in conversation for keyword in self.importance_keywords)
        
        # 计算关键词出现次数
        keyword_count = sum(1 for keyword in self.importance_keywords if keyword in conversation)
        
        # 根据关键词出现次数计算重要性分数
        importance_score = min(1.0, keyword_count * 0.2)
        
        return MemoryAnalysis(
            should_store_in_ltm=has_importance_keywords,
            reason="包含重要关键词" if has_importance_keywords else "未检测到重要信息",
            importance_score=importance_score,
            key_points=[conversation] if has_importance_keywords else []
        ) 