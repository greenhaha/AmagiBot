from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from .base import MemorySource
from ..models.memory_encoding import MemoryEncoding
from ..core.memory_encoder import MemoryEncoder

class KnowledgeMemorySource(MemorySource):
    """知识记忆源：管理知识库相关的记忆"""
    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client['chatbot_db']
        self.collection = self.db['knowledge_memories']
        self.encoder = MemoryEncoder()
        
    def get_source_name(self) -> str:
        return "knowledge"
        
    def get_memories(self,
                    query: str,
                    user_id: str,
                    limit: int = 10,
                    time_range: Optional[tuple[datetime, datetime]] = None) -> List[MemoryEncoding]:
        """获取知识记忆"""
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
            sort=[('relevance_score', -1)],
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
        """添加知识记忆"""
        # 编码记忆内容
        memory_encoding = self.encoder.encode_memory(content, metadata)
        
        # 计算相关性分数
        relevance_score = self._calculate_relevance_score(content, metadata)
        
        # 准备存储数据
        memory_doc = {
            'user_id': user_id,
            'content': content,
            'embedding': memory_encoding.embedding.tolist(),
            'strength': memory_encoding.strength,
            'memory_type': memory_encoding.memory_type,
            'key_points': memory_encoding.key_points,
            'metadata': metadata,
            'relevance_score': relevance_score,
            'timestamp': datetime.now()
        }
        
        # 存储到数据库
        self.collection.insert_one(memory_doc)
        
    def update_memory(self,
                     memory_id: str,
                     new_content: str,
                     new_metadata: Dict[str, Any]) -> None:
        """更新知识记忆"""
        # 编码新的记忆内容
        memory_encoding = self.encoder.encode_memory(new_content, new_metadata)
        
        # 计算新的相关性分数
        relevance_score = self._calculate_relevance_score(new_content, new_metadata)
        
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
                    'relevance_score': relevance_score,
                    'updated_at': datetime.now()
                }
            }
        )
        
    def delete_memory(self, memory_id: str) -> None:
        """删除知识记忆"""
        self.collection.delete_one({'_id': memory_id})
        
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取知识记忆统计信息"""
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
        
    def _calculate_relevance_score(self, content: str, metadata: Dict[str, Any]) -> float:
        """计算知识相关性分数"""
        # 基础分数
        base_score = 0.5
        
        # 根据内容长度调整
        content_length = len(content)
        if content_length > 200:
            base_score += 0.1
        elif content_length < 50:
            base_score -= 0.1
            
        # 根据知识类型调整
        knowledge_type = metadata.get('knowledge_type', 'general')
        if knowledge_type == 'domain':
            base_score += 0.2
        elif knowledge_type == 'fact':
            base_score += 0.1
            
        # 根据可信度调整
        confidence = metadata.get('confidence', 0.5)
        base_score += (confidence - 0.5) * 0.2
        
        return max(0.0, min(1.0, base_score)) 