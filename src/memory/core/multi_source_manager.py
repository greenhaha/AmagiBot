from typing import List, Dict, Any, Optional
from datetime import datetime
from ..sources.base import MemorySource
from ..models.memory_encoding import MemoryEncoding

class MultiSourceMemoryManager:
    """多源记忆管理器：整合和管理不同来源的记忆"""
    def __init__(self):
        self.sources: Dict[str, MemorySource] = {}
        
    def register_source(self, source: MemorySource) -> None:
        """注册记忆源"""
        source_name = source.get_source_name()
        self.sources[source_name] = source
        
    def get_memories(self,
                    query: str,
                    user_id: str,
                    source_names: Optional[List[str]] = None,
                    limit: int = 10,
                    time_range: Optional[tuple[datetime, datetime]] = None) -> List[MemoryEncoding]:
        """从多个源获取记忆"""
        all_memories = []
        
        # 确定要查询的源
        sources_to_query = (
            [self.sources[name] for name in source_names if name in self.sources]
            if source_names
            else list(self.sources.values())
        )
        
        # 从每个源获取记忆
        for source in sources_to_query:
            memories = source.get_memories(
                query=query,
                user_id=user_id,
                limit=limit,
                time_range=time_range
            )
            all_memories.extend(memories)
            
        # 按记忆强度排序
        all_memories.sort(key=lambda x: x.strength, reverse=True)
        
        # 返回前limit个记忆
        return all_memories[:limit]
        
    def add_memory(self,
                  content: str,
                  user_id: str,
                  source_name: str,
                  metadata: Dict[str, Any]) -> None:
        """向指定源添加记忆"""
        if source_name not in self.sources:
            raise ValueError(f"未知的记忆源: {source_name}")
            
        self.sources[source_name].add_memory(
            content=content,
            user_id=user_id,
            metadata=metadata
        )
        
    def update_memory(self,
                     memory_id: str,
                     new_content: str,
                     source_name: str,
                     new_metadata: Dict[str, Any]) -> None:
        """更新指定源的记忆"""
        if source_name not in self.sources:
            raise ValueError(f"未知的记忆源: {source_name}")
            
        self.sources[source_name].update_memory(
            memory_id=memory_id,
            new_content=new_content,
            new_metadata=new_metadata
        )
        
    def delete_memory(self, memory_id: str, source_name: str) -> None:
        """删除指定源的记忆"""
        if source_name not in self.sources:
            raise ValueError(f"未知的记忆源: {source_name}")
            
        self.sources[source_name].delete_memory(memory_id)
        
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取所有源的记忆统计信息"""
        stats = {}
        
        for source_name, source in self.sources.items():
            source_stats = source.get_memory_stats(user_id)
            stats[source_name] = source_stats
            
        # 计算总体统计信息
        total_memories = sum(
            source_stats['total_memories']
            for source_stats in stats.values()
        )
        
        # 合并所有类型的计数
        all_type_counts = {}
        for source_stats in stats.values():
            for memory_type, count in source_stats['type_counts'].items():
                all_type_counts[memory_type] = all_type_counts.get(memory_type, 0) + count
                
        # 获取最新的记忆时间
        latest_memory_time = max(
            (source_stats['latest_memory_time'] for source_stats in stats.values()
             if source_stats['latest_memory_time'] is not None),
            default=None
        )
        
        stats['overall'] = {
            'total_memories': total_memories,
            'type_counts': all_type_counts,
            'latest_memory_time': latest_memory_time
        }
        
        return stats
        
    def consolidate_memories(self, user_id: str) -> None:
        """整合所有源的记忆"""
        # 获取所有记忆
        all_memories = self.get_memories(
            query="",
            user_id=user_id,
            limit=1000  # 获取足够多的记忆以进行整合
        )
        
        # 按类型分组
        memory_groups = {}
        for memory in all_memories:
            memory_type = memory.memory_type
            if memory_type not in memory_groups:
                memory_groups[memory_type] = []
            memory_groups[memory_type].append(memory)
            
        # 对每组记忆进行整合
        for memory_type, memories in memory_groups.items():
            self._consolidate_memory_group(memories, user_id)
            
    def _consolidate_memory_group(self,
                                memories: List[MemoryEncoding],
                                user_id: str) -> None:
        """整合一组相似记忆"""
        if len(memories) <= 1:
            return
            
        # 按强度排序
        memories.sort(key=lambda x: x.strength, reverse=True)
        
        # 合并相似记忆
        i = 0
        while i < len(memories) - 1:
            current = memories[i]
            next_memory = memories[i + 1]
            
            # 如果记忆相似度超过阈值，合并它们
            if self._calculate_similarity(current, next_memory) > 0.8:
                # 合并内容
                merged_content = f"{current.content}\n{next_memory.content}"
                
                # 合并元数据
                merged_metadata = {
                    **current.metadata,
                    **next_memory.metadata,
                    'merged_from': [
                        current.metadata.get('id'),
                        next_memory.metadata.get('id')
                    ]
                }
                
                # 更新当前记忆
                self.update_memory(
                    memory_id=current.metadata['id'],
                    new_content=merged_content,
                    source_name=current.metadata['source'],
                    new_metadata=merged_metadata
                )
                
                # 删除下一个记忆
                self.delete_memory(
                    memory_id=next_memory.metadata['id'],
                    source_name=next_memory.metadata['source']
                )
                
                # 从列表中移除已合并的记忆
                memories.pop(i + 1)
            else:
                i += 1
                
    def _calculate_similarity(self,
                            memory1: MemoryEncoding,
                            memory2: MemoryEncoding) -> float:
        """计算两个记忆之间的相似度"""
        # 使用余弦相似度
        dot_product = sum(a * b for a, b in zip(memory1.embedding, memory2.embedding))
        norm1 = sum(a * a for a in memory1.embedding) ** 0.5
        norm2 = sum(b * b for b in memory2.embedding) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2) 