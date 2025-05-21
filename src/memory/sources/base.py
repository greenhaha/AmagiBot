from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models.memory_encoding import MemoryEncoding

class MemorySource(ABC):
    """记忆源基类：定义记忆源的基本接口"""
    
    @abstractmethod
    def get_source_name(self) -> str:
        """获取记忆源名称"""
        pass
        
    @abstractmethod
    def get_memories(self,
                    query: str,
                    user_id: str,
                    limit: int = 10,
                    time_range: Optional[tuple[datetime, datetime]] = None) -> List[MemoryEncoding]:
        """获取记忆"""
        pass
        
    @abstractmethod
    def add_memory(self,
                  content: str,
                  user_id: str,
                  metadata: Dict[str, Any]) -> None:
        """添加记忆"""
        pass
        
    @abstractmethod
    def update_memory(self,
                     memory_id: str,
                     new_content: str,
                     new_metadata: Dict[str, Any]) -> None:
        """更新记忆"""
        pass
        
    @abstractmethod
    def delete_memory(self, memory_id: str) -> None:
        """删除记忆"""
        pass
        
    @abstractmethod
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取记忆统计信息"""
        pass 