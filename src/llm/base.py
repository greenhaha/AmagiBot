from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseLLM(ABC):
    """LLM基类，定义所有LLM实现必须实现的接口"""
    
    @abstractmethod
    def chat(self, 
            messages: List[Dict[str, str]], 
            temperature: float = 0.7,
            max_tokens: int = 2000,
            stream: bool = False) -> Dict[str, Any]:
        """
        发送聊天请求
        
        Args:
            messages: 消息历史列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            stream: 是否使用流式响应
            
        Returns:
            API响应结果
        """
        pass
    
    @abstractmethod
    def get_embeddings(self, text: str) -> List[float]:
        """
        获取文本的嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            文本的嵌入向量
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            可用模型列表
        """
        pass 