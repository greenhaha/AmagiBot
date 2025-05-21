from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from .base import MemorySource
from ..models.memory_encoding import MemoryEncoding
from ..core.memory_encoder import MemoryEncoder

class ConversationMemorySource(MemorySource):
    """对话记忆源：管理对话相关的记忆"""
    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client['chatbot_db']
        self.collection = self.db['conversation_memories']
        self.encoder = MemoryEncoder()
        
    def get_source_name(self) -> str:
        return "conversation"
        
    def get_memories(self,
                    query: str,
                    user_id: str,
                    limit: int = 10,
                    time_range: Optional[tuple[datetime, datetime]] = None) -> List[MemoryEncoding]:
        """获取对话记忆"""
        # 构建查询条件
        query_conditions = {'user_id': user_id}
        if time_range:
            start_time, end_time = time_range
            query_conditions['timestamp'] = {
                '$gte': start_time,
                '$lte': end_time
            }
            
        # 获取记忆
        memories = list(self.collection.find(
            query_conditions,
            sort=[('timestamp', -1)],
            limit=limit
        ))
        
        # 转换为MemoryEncoding对象
        return [
            MemoryEncoding(
                content=memory['content'],
                embedding=memory['embedding'],
                strength=memory['strength'],
                memory_type=memory['memory_type'],
                key_points=memory['key_points'],
                metadata=memory['metadata']
            )
            for memory in memories
        ]
        
    def add_memory(self,
                  content: str,
                  user_id: str,
                  metadata: Dict[str, Any]) -> None:
        """添加对话记忆"""
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
        self.collection.insert_one(memory_doc)
        
    def update_memory(self,
                     memory_id: str,
                     new_content: str,
                     new_metadata: Dict[str, Any]) -> None:
        """更新对话记忆"""
        # 编码新的记忆内容
        memory_encoding = self.encoder.encode_memory(new_content, new_metadata)
        
        # 更新数据库记录
        self.collection.update_one(
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
        
    def delete_memory(self, memory_id: str) -> None:
        """删除对话记忆"""
        self.collection.delete_one({'_id': memory_id})
        
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取对话记忆统计信息"""
        # 获取记忆总数
        total_memories = self.collection.count_documents({'user_id': user_id})
        
        # 获取各类型记忆数量
        memory_types = self.collection.distinct('memory_type', {'user_id': user_id})
        type_counts = {
            memory_type: self.collection.count_documents({
                'user_id': user_id,
                'memory_type': memory_type
            })
            for memory_type in memory_types
        }
        
        # 获取最近记忆时间
        latest_memory = self.collection.find_one(
            {'user_id': user_id},
            sort=[('timestamp', -1)]
        )
        
        return {
            'total_memories': total_memories,
            'type_counts': type_counts,
            'latest_memory_time': latest_memory['timestamp'] if latest_memory else None
        } 