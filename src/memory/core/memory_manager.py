from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from .memory_encoder import MemoryEncoder
from .memory_retriever import MemoryRetriever
from ..models.memory_encoding import MemoryEncoding
from config.memory_config import MemoryConfig
import numpy as np

class MemoryManager:
    """记忆管理器：管理记忆的存储和更新"""
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.mongo_client = MongoClient()
        self.db = self.mongo_client['chatbot_db']
        self.memory_collection = self.db['memories']
        self.encoder = MemoryEncoder()
        self.retriever = MemoryRetriever(self.mongo_client)
        
    def add_memory(self,
                  content: str,
                  user_id: str,
                  metadata: Dict[str, Any]) -> None:
        """添加新记忆"""
        # 编码记忆内容
        memory_encoding = self.encoder.encode_memory(content, metadata)
        
        # 准备存储数据
        memory_doc = {
            'user_id': user_id,
            'content': content,
            'embedding': memory_encoding.embedding.tolist(),
            'strength': memory_encoding.strength,
            'memory_type': memory_encoding.memory_type,
            'key_points': memory_encoding.key_points,
            'metadata': metadata,
            'timestamp': datetime.now()
        }
        
        # 存储到数据库
        self.memory_collection.insert_one(memory_doc)
        
    def update_memory(self,
                     memory_id: str,
                     new_content: str,
                     new_metadata: Dict[str, Any]) -> None:
        """更新现有记忆"""
        # 编码新的记忆内容
        memory_encoding = self.encoder.encode_memory(new_content, new_metadata)
        
        # 更新数据库记录
        self.memory_collection.update_one(
            {'_id': memory_id},
            {
                '$set': {
                    'content': new_content,
                    'embedding': memory_encoding.embedding.tolist(),
                    'strength': memory_encoding.strength,
                    'memory_type': memory_encoding.memory_type,
                    'key_points': memory_encoding.key_points,
                    'metadata': new_metadata,
                    'updated_at': datetime.now()
                }
            }
        )
        
    def get_memory_context(self,
                          query: str,
                          user_id: str,
                          context_window: int = 5) -> str:
        """获取记忆上下文"""
        # 编码查询内容
        query_encoding = self.encoder.encode_memory(
            query,
            {'is_query': True}
        )
        
        # 检索相关记忆
        return self.retriever.get_memory_context(
            query=query,
            query_embedding=query_encoding.embedding,
            user_id=user_id,
            context_window=context_window
        )
        
    def consolidate_memories(self, user_id: str) -> None:
        """整合记忆"""
        # 获取所有记忆
        memories = list(self.memory_collection.find({'user_id': user_id}))
        
        # 按记忆类型分组
        memory_groups = {}
        for memory in memories:
            memory_type = memory['memory_type']
            if memory_type not in memory_groups:
                memory_groups[memory_type] = []
            memory_groups[memory_type].append(memory)
            
        # 对每种类型的记忆进行整合
        for memory_type, memories in memory_groups.items():
            self._consolidate_memory_group(memories)
            
    def _consolidate_memory_group(self, memories: List[Dict[str, Any]]) -> None:
        """整合同一类型的记忆组"""
        if len(memories) < 2:
            return
            
        # 按时间排序
        memories.sort(key=lambda x: x['timestamp'])
        
        # 合并相似的记忆
        i = 0
        while i < len(memories) - 1:
            current = memories[i]
            next_memory = memories[i + 1]
            
            # 计算相似度
            similarity = self.retriever._cosine_similarity(
                np.array(current['embedding']),
                np.array(next_memory['embedding'])
            )
            
            if similarity > 0.8:  # 相似度阈值
                # 合并记忆
                merged_content = f"{current['content']}\n{next_memory['content']}"
                merged_metadata = {
                    **current['metadata'],
                    'merged_from': [current['_id'], next_memory['_id']]
                }
                
                # 更新当前记忆
                self.update_memory(
                    current['_id'],
                    merged_content,
                    merged_metadata
                )
                
                # 删除下一个记忆
                self.memory_collection.delete_one({'_id': next_memory['_id']})
                memories.pop(i + 1)
            else:
                i += 1
                
    def clear_memories(self, user_id: str) -> None:
        """清除用户的所有记忆"""
        self.memory_collection.delete_many({'user_id': user_id})
        
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取记忆统计信息"""
        # 获取记忆总数
        total_memories = self.memory_collection.count_documents({'user_id': user_id})
        
        # 获取各类型记忆数量
        memory_types = self.memory_collection.distinct('memory_type', {'user_id': user_id})
        type_counts = {
            memory_type: self.memory_collection.count_documents({
                'user_id': user_id,
                'memory_type': memory_type
            })
            for memory_type in memory_types
        }
        
        # 获取最近记忆时间
        latest_memory = self.memory_collection.find_one(
            {'user_id': user_id},
            sort=[('timestamp', -1)]
        )
        
        return {
            'total_memories': total_memories,
            'type_counts': type_counts,
            'latest_memory_time': latest_memory['timestamp'] if latest_memory else None
        } 