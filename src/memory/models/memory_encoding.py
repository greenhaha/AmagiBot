from dataclasses import dataclass
from typing import List, Dict, Any
import numpy as np

@dataclass
class MemoryEncoding:
    """记忆编码数据模型"""
    content: str                    # 记忆内容
    embedding: np.ndarray          # 向量嵌入
    strength: float                # 记忆强度
    memory_type: str               # 记忆类型
    key_points: List[str]          # 关键信息点
    metadata: Dict[str, Any]       # 元数据 