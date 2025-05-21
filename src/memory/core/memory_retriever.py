from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
from pymongo import MongoClient
from .memory_analyzer import MemoryAnalyzer
from config.memory_config import MEMORY_PARAMS
from ..models.memory_encoding import MemoryEncoding

class MemoryRetriever:
    """记忆检索器：从记忆中检索相关信息"""
    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client['chatbot_db']
        self.memory_collection = self.db['memories']
        self.memory_manager = MemoryAnalyzer()
        self.memory_params = MEMORY_PARAMS
        
    def get_context(self, user_id: str, current_input: str) -> List[str]:
        """获取对话上下文"""
        # 获取短期记忆上下文
        stm_context = self._get_stm_context(user_id)
        
        # 获取长期记忆上下文
        ltm_context = self._get_ltm_context(user_id, current_input)
        
        # 合并上下文
        return stm_context + ltm_context
        
    def _get_stm_context(self, user_id: str) -> List[str]:
        """获取短期记忆上下文"""
        # 获取最近的短期记忆
        recent_memories = self.memory_manager.stm_collection.find(
            {'user_id': user_id},
            sort=[('timestamp', -1)],
            limit=self.memory_params['context_window']
        )
        
        return [memory['content'] for memory in recent_memories]
        
    def _get_ltm_context(self, user_id: str, current_input: str) -> List[str]:
        """获取长期记忆上下文"""
        # 分析当前输入
        analysis = self.memory_manager.analyzer.analyze_conversation(current_input)
        
        # 根据关键点检索相关长期记忆
        relevant_memories = []
        for key_point in analysis.key_points:
            memories = self.memory_manager.ltm_collection.find({
                'user_id': user_id,
                'key_points': {'$in': [key_point]}
            }).sort([('importance_score', -1)])
            
            relevant_memories.extend([memory['content'] for memory in memories])
            
        # 如果没有找到相关记忆，返回重要性最高的记忆
        if not relevant_memories:
            important_memories = self.memory_manager.ltm_collection.find(
                {'user_id': user_id},
                sort=[('importance_score', -1)],
                limit=self.memory_params['context_window']
            )
            relevant_memories = [memory['content'] for memory in important_memories]
            
        return relevant_memories
        
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户历史记录"""
        # 获取短期记忆
        stm_memories = list(self.memory_manager.stm_collection.find(
            {'user_id': user_id},
            sort=[('timestamp', -1)],
            limit=limit
        ))
        
        # 获取长期记忆
        ltm_memories = list(self.memory_manager.ltm_collection.find(
            {'user_id': user_id},
            sort=[('timestamp', -1)],
            limit=limit
        ))
        
        # 合并并格式化记忆
        all_memories = []
        for memory in stm_memories + ltm_memories:
            all_memories.append({
                'content': memory['content'],
                'timestamp': memory['timestamp'],
                'type': 'stm' if 'occurrence_count' in memory else 'ltm',
                'importance_score': memory.get('importance_score', 0.0),
                'key_points': memory.get('key_points', [])
            })
            
        # 按时间排序
        all_memories.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_memories[:limit]
        
    def retrieve_memories(self,
                         query: str,
                         query_embedding: np.ndarray,
                         user_id: str,
                         top_k: int = 5,
                         memory_types: Optional[List[str]] = None,
                         time_range: Optional[Tuple[datetime, datetime]] = None) -> List[Dict[str, Any]]:
        """检索相关记忆"""
        # 构建查询条件
        query_conditions = {
            'user_id': user_id
        }
        
        # 添加记忆类型过滤
        if memory_types:
            query_conditions['memory_type'] = {'$in': memory_types}
            
        # 添加时间范围过滤
        if time_range:
            start_time, end_time = time_range
            query_conditions['timestamp'] = {
                '$gte': start_time,
                '$lte': end_time
            }
            
        # 获取所有符合条件的记忆
        memories = list(self.memory_collection.find(query_conditions))
        
        if not memories:
            return []
            
        # 计算相似度分数
        scored_memories = []
        for memory in memories:
            # 计算余弦相似度
            similarity = self._cosine_similarity(
                query_embedding,
                np.array(memory['embedding'])
            )
            
            # 应用记忆强度衰减
            time_decay = self._calculate_time_decay(memory['timestamp'])
            strength = memory['strength'] * (1 - time_decay)
            
            # 计算最终分数
            final_score = similarity * strength
            
            scored_memories.append({
                'memory': memory,
                'score': final_score
            })
            
        # 按分数排序并返回前k个结果
        scored_memories.sort(key=lambda x: x['score'], reverse=True)
        return [item['memory'] for item in scored_memories[:top_k]]
        
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
    def _calculate_time_decay(self, timestamp: datetime) -> float:
        """计算时间衰减"""
        now = datetime.now()
        time_diff = now - timestamp
        
        # 使用指数衰减函数
        decay_rate = 0.1  # 衰减率
        days = time_diff.days
        return 1 - np.exp(-decay_rate * days)
        
    def get_memory_context(self,
                          query: str,
                          query_embedding: np.ndarray,
                          user_id: str,
                          context_window: int = 5) -> str:
        """获取记忆上下文"""
        # 检索相关记忆
        memories = self.retrieve_memories(
            query=query,
            query_embedding=query_embedding,
            user_id=user_id,
            top_k=context_window
        )
        
        if not memories:
            return ""
            
        # 构建上下文
        context_parts = []
        for memory in memories:
            # 添加关键信息点
            if memory.get('key_points'):
                context_parts.extend(memory['key_points'])
            else:
                context_parts.append(memory['content'])
                
        return "\n".join(context_parts) 