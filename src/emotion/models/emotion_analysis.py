from dataclasses import dataclass
from typing import List

@dataclass
class EmotionAnalysis:
    """情感分析结果"""
    emotion_state: str      # 情感状态（happy/neutral/sad/angry）
    intensity: float        # 情感强度（0-1）
    reason: str            # 分析原因
    keywords: List[str]    # 情感关键词
    eq_score: float        # 情绪商数（0-1） 