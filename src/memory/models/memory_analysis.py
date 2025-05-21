from dataclasses import dataclass
from typing import List

@dataclass
class MemoryAnalysis:
    """记忆分析结果"""
    should_store_in_ltm: bool  # 是否应该存储在长期记忆中
    reason: str               # 分析原因
    importance_score: float   # 重要性分数（0-1）
    key_points: List[str]    # 关键点列表 