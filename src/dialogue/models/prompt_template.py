from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PromptTemplate:
    """提示词模板数据模型"""
    model_name: str                # 模型名称
    prompt: str                    # 格式化后的提示词
    system_prompt: Optional[str]   # 系统提示词
    temperature: float            # 温度参数
    max_tokens: int               # 最大token数
    stop_sequences: List[str]     # 停止序列 