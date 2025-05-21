from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from ..models.emotion_analysis import EmotionAnalysis
from .emotion_analyzer import EmotionAnalyzer
from config.emotion_config import EmotionConfig

class EmotionManager:
    """情感管理器：管理情感状态和用户行为"""
    def __init__(self, config: EmotionConfig):
        self.config = config
        self.mongo_client = MongoClient()
        self.db = self.mongo_client['chatbot_db']
        self.emotion_collection = self.db['emotion_states']
        self.behavior_collection = self.db['user_behaviors']
        self.analyzer = EmotionAnalyzer()
        self.emotion_states = config.emotion_states
        self.update_params = config.update_params
        self.expressions = config.expressions
        
    def update_emotion(self, 
                      user_id: str,
                      conversation: str,
                      timestamp: datetime) -> EmotionAnalysis:
        """更新情感状态"""
        # 获取用户行为数据
        user_behavior = self._get_user_behavior(user_id, timestamp)
        
        # 分析对话内容和用户行为
        analysis = self.analyzer.analyze_conversation(conversation, user_behavior)
        
        # 获取当前情感状态
        current_emotion = self._get_current_emotion(user_id)
        
        # 计算新的情感状态
        new_emotion = self._calculate_new_emotion(current_emotion, analysis)
        
        # 更新情感状态
        self._update_emotion_state(user_id, new_emotion, timestamp)
        
        # 更新用户行为
        self._update_user_behavior(user_id, timestamp)
        
        return new_emotion
        
    def _get_user_behavior(self, user_id: str, timestamp: datetime) -> Dict[str, Any]:
        """获取用户行为数据"""
        # 获取最近24小时的行为数据
        start_time = timestamp - timedelta(days=1)
        behaviors = list(self.behavior_collection.find({
            'user_id': user_id,
            'timestamp': {'$gte': start_time}
        }))
        
        if not behaviors:
            return {
                'conversation_frequency': 0,
                'avg_duration': 0,
                'avg_interval': 0,
                'time_of_day': self._get_time_of_day(timestamp),
                'conversation_cycle': 'unknown'
            }
            
        # 计算行为指标
        total_duration = sum(b['duration'] for b in behaviors)
        total_intervals = sum(b['interval'] for b in behaviors)
        frequency = len(behaviors)
        
        return {
            'conversation_frequency': frequency,
            'avg_duration': total_duration / frequency if frequency > 0 else 0,
            'avg_interval': total_intervals / frequency if frequency > 0 else 0,
            'time_of_day': self._get_time_of_day(timestamp),
            'conversation_cycle': self._get_conversation_cycle(behaviors)
        }
        
    def _get_current_emotion(self, user_id: str) -> EmotionAnalysis:
        """获取当前情感状态"""
        emotion_doc = self.emotion_collection.find_one({'user_id': user_id})
        if not emotion_doc:
            return EmotionAnalysis(
                emotion_state='neutral',
                intensity=0.5,
                reason='初始状态',
                keywords=[],
                eq_score=0.5
            )
            
        return EmotionAnalysis(
            emotion_state=emotion_doc['emotion_state'],
            intensity=emotion_doc['intensity'],
            reason=emotion_doc['reason'],
            keywords=emotion_doc['keywords'],
            eq_score=emotion_doc['eq_score']
        )
        
    def _calculate_new_emotion(self, 
                             current: EmotionAnalysis,
                             new: EmotionAnalysis) -> EmotionAnalysis:
        """计算新的情感状态"""
        # 应用情感衰减
        decayed_intensity = current.intensity * (1 - self.update_params.decay_rate)
        
        # 计算新的情感强度
        new_intensity = (decayed_intensity + new.intensity) / 2
        
        # 根据情绪商数调整情感状态
        if new.eq_score > 0.7:  # 高情绪商数
            # 倾向于保持积极情感
            if current.emotion_state in ['happy', 'neutral']:
                new_emotion = current.emotion_state
            else:
                new_emotion = 'neutral'
        elif new.eq_score < 0.3:  # 低情绪商数
            # 倾向于保持消极情感
            if current.emotion_state in ['sad', 'angry']:
                new_emotion = current.emotion_state
            else:
                new_emotion = 'neutral'
        else:
            new_emotion = new.emotion_state
            
        return EmotionAnalysis(
            emotion_state=new_emotion,
            intensity=new_intensity,
            reason=new.reason,
            keywords=new.keywords,
            eq_score=new.eq_score
        )
        
    def _update_emotion_state(self, 
                            user_id: str,
                            emotion: EmotionAnalysis,
                            timestamp: datetime) -> None:
        """更新情感状态"""
        self.emotion_collection.update_one(
            {'user_id': user_id},
            {
                '$set': {
                    'emotion_state': emotion.emotion_state,
                    'intensity': emotion.intensity,
                    'reason': emotion.reason,
                    'keywords': emotion.keywords,
                    'eq_score': emotion.eq_score,
                    'timestamp': timestamp
                }
            },
            upsert=True
        )
        
    def _update_user_behavior(self, user_id: str, timestamp: datetime) -> None:
        """更新用户行为"""
        # 获取上一次行为记录
        last_behavior = self.behavior_collection.find_one(
            {'user_id': user_id},
            sort=[('timestamp', -1)]
        )
        
        if last_behavior:
            # 计算时间间隔
            interval = (timestamp - last_behavior['timestamp']).total_seconds()
        else:
            interval = 0
            
        # 创建新的行为记录
        behavior_record = {
            'user_id': user_id,
            'timestamp': timestamp,
            'interval': interval,
            'duration': 0  # 将在对话结束时更新
        }
        
        self.behavior_collection.insert_one(behavior_record)
        
    def _get_time_of_day(self, timestamp: datetime) -> str:
        """获取时间段"""
        hour = timestamp.hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 22:
            return 'night'
        else:
            return 'late_night'
            
    def _get_conversation_cycle(self, behaviors: List[Dict[str, Any]]) -> str:
        """获取对话周期"""
        if not behaviors:
            return 'unknown'
            
        # 计算平均间隔
        intervals = [b['interval'] for b in behaviors]
        avg_interval = sum(intervals) / len(intervals)
        
        if avg_interval < 3600:  # 1小时内
            return 'frequent'
        elif avg_interval < 86400:  # 24小时内
            return 'daily'
        else:
            return 'occasional'
            
    def get_emotion_expression(self, emotion_state: str) -> str:
        """获取情感表达"""
        if emotion_state not in self.expressions:
            return "我现在很平静。"
        return self.expressions[emotion_state][0]  # 返回第一个表达方式
        
    def get_emotion_state(self, user_id: str = "default") -> str:
        """获取当前情感状态"""
        emotion_doc = self.emotion_collection.find_one({'user_id': user_id})
        if not emotion_doc:
            return 'neutral'
        return emotion_doc['emotion_state']
        
    def get_emotion_intensity(self, user_id: str = "default") -> float:
        """获取当前情感强度"""
        emotion_doc = self.emotion_collection.find_one({'user_id': user_id})
        if not emotion_doc:
            return 0.5
        return emotion_doc['intensity'] 