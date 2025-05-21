from typing import Dict, Any, List
from dataclasses import dataclass

# 情感表达模板
EMOTION_EXPRESSIONS = {
    'happy': [
        "我感到非常开心！",
        "这真让人高兴。",
        "今天的心情特别棒！"
    ],
    'excited': [
        "太棒了，我好激动！",
        "这真令人振奋！",
        "我充满了期待和热情。"
    ],
    'content': [
        "我很满足现在的状态。",
        "一切都很舒适、安心。",
        "我觉得很平静。"
    ],
    'sad': [
        "我有点难过。",
        "心情有些低落。",
        "有些事情让我感到失落。"
    ],
    'angry': [
        "我有点生气。",
        "这让我很不满。",
        "我感到愤怒。"
    ],
    'anxious': [
        "我有些担心。",
        "有点紧张和不安。",
        "我感到焦虑。"
    ],
    'neutral': [
        "我现在很平静。",
        "一切如常。",
        "没有特别的情绪波动。"
    ],
    'curious': [
        "我对这个很感兴趣！",
        "让我来探索一下。",
        "我很好奇。"
    ]
}

# 情感更新参数
EMOTION_UPDATE_PARAMS = {
    # 情感分析参数
    'analysis': {
        'max_tokens': 2000,  # 最大token数
        'temperature': 0.7,  # 温度参数
        'top_k': 3,  # 返回最可能的k个情感
        'confidence_threshold': 0.6  # 置信度阈值
    },
    
    # 情感转换参数
    'transition': {
        'min_duration': 60,  # 最小持续时间（秒）
        'max_duration': 300,  # 最大持续时间（秒）
        'transition_probability': 0.3,  # 转换概率
        'intensity_change': 0.2  # 强度变化
    },
    
    # 情感衰减参数
    'decay': {
        'base_rate': 0.1,  # 基础衰减率
        'intensity_factor': 0.2,  # 强度因子
        'time_factor': 0.1,  # 时间因子
        'min_intensity': 0.1  # 最小强度
    },
    
    # 情感触发参数
    'trigger': {
        'keyword_weight': 0.4,  # 关键词权重
        'context_weight': 0.3,  # 上下文权重
        'history_weight': 0.3,  # 历史权重
        'min_trigger_score': 0.6  # 最小触发分数
    }
}

# 情感状态定义
EMOTION_STATES = {
    # 积极情感
    'happy': {
        'name': '开心',
        'intensity_range': (0.6, 1.0),
        'keywords': ['开心', '快乐', '高兴', '喜悦', '兴奋', '愉快', '欢乐'],
        'triggers': ['成功', '赞美', '礼物', '好消息', '有趣的事']
    },
    'excited': {
        'name': '兴奋',
        'intensity_range': (0.7, 1.0),
        'keywords': ['兴奋', '激动', '热情', '振奋', '充满活力'],
        'triggers': ['新发现', '挑战', '冒险', '突破']
    },
    'content': {
        'name': '满足',
        'intensity_range': (0.4, 0.8),
        'keywords': ['满足', '满意', '舒适', '安心', '平静'],
        'triggers': ['完成任务', '达成目标', '获得认可']
    },
    
    # 消极情感
    'sad': {
        'name': '悲伤',
        'intensity_range': (0.4, 0.8),
        'keywords': ['悲伤', '难过', '伤心', '失落', '沮丧'],
        'triggers': ['失败', '失去', '离别', '失望']
    },
    'angry': {
        'name': '愤怒',
        'intensity_range': (0.6, 1.0),
        'keywords': ['愤怒', '生气', '恼火', '不满', '烦躁'],
        'triggers': ['不公平', '被冒犯', '阻碍', '背叛']
    },
    'anxious': {
        'name': '焦虑',
        'intensity_range': (0.5, 0.9),
        'keywords': ['焦虑', '担心', '紧张', '不安', '恐惧'],
        'triggers': ['未知', '压力', '危险', '不确定性']
    },
    
    # 中性情感
    'neutral': {
        'name': '平静',
        'intensity_range': (0.0, 0.3),
        'keywords': ['平静', '中性', '一般', '普通'],
        'triggers': ['日常对话', '例行事务']
    },
    'curious': {
        'name': '好奇',
        'intensity_range': (0.3, 0.7),
        'keywords': ['好奇', '感兴趣', '探索', '求知'],
        'triggers': ['新事物', '未知领域', '有趣话题']
    }
}

# 情感转换规则
EMOTION_TRANSITION_RULES = {
    # 积极情感转换
    'happy': {
        'excited': 0.3,  # 开心可能转换为兴奋
        'content': 0.4,  # 开心可能转换为满足
        'neutral': 0.2   # 开心可能转换为平静
    },
    'excited': {
        'happy': 0.3,    # 兴奋可能转换为开心
        'content': 0.3,  # 兴奋可能转换为满足
        'neutral': 0.2   # 兴奋可能转换为平静
    },
    'content': {
        'happy': 0.2,    # 满足可能转换为开心
        'neutral': 0.4   # 满足可能转换为平静
    },
    
    # 消极情感转换
    'sad': {
        'angry': 0.2,    # 悲伤可能转换为愤怒
        'anxious': 0.2,  # 悲伤可能转换为焦虑
        'neutral': 0.3   # 悲伤可能转换为平静
    },
    'angry': {
        'sad': 0.2,      # 愤怒可能转换为悲伤
        'anxious': 0.2,  # 愤怒可能转换为焦虑
        'neutral': 0.3   # 愤怒可能转换为平静
    },
    'anxious': {
        'sad': 0.2,      # 焦虑可能转换为悲伤
        'angry': 0.2,    # 焦虑可能转换为愤怒
        'neutral': 0.3   # 焦虑可能转换为平静
    },
    
    # 中性情感转换
    'neutral': {
        'happy': 0.2,    # 平静可能转换为开心
        'curious': 0.3,  # 平静可能转换为好奇
        'sad': 0.1,      # 平静可能转换为悲伤
        'anxious': 0.1   # 平静可能转换为焦虑
    },
    'curious': {
        'excited': 0.3,  # 好奇可能转换为兴奋
        'happy': 0.2,    # 好奇可能转换为开心
        'neutral': 0.3   # 好奇可能转换为平静
    }
}

@dataclass
class EmotionConfig:
    """情感系统配置"""
    
    # 情感状态
    emotion_states: Dict[str, Dict[str, Any]] = None
    
    # 情感转换规则
    transition_rules: Dict[str, Dict[str, float]] = None
    
    # 情感更新参数
    update_params: Dict[str, Dict[str, Any]] = None
    
    # 情感表达模板
    expressions: Dict[str, List[str]] = None
    
    # 情感强度衰减率（每秒）
    decay_rate: float = 0.1
    
    # 情感触发阈值
    trigger_threshold: float = 0.6
    
    # 情感持续时间（秒）
    emotion_duration: int = 300
    
    def __post_init__(self):
        if self.emotion_states is None:
            self.emotion_states = EMOTION_STATES
        if self.transition_rules is None:
            self.transition_rules = EMOTION_TRANSITION_RULES
        if self.update_params is None:
            self.update_params = EMOTION_UPDATE_PARAMS
        if self.expressions is None:
            self.expressions = EMOTION_EXPRESSIONS
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'EmotionConfig':
        """从字典创建配置"""
        return cls(
            emotion_states=config.get('emotion_states', cls.emotion_states),
            transition_rules=config.get('transition_rules', cls.transition_rules),
            update_params=config.get('update_params', cls.update_params),
            expressions=config.get('expressions', cls.expressions),
            decay_rate=config.get('decay_rate', cls.decay_rate),
            trigger_threshold=config.get('trigger_threshold', cls.trigger_threshold),
            emotion_duration=config.get('emotion_duration', cls.emotion_duration)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'emotion_states': self.emotion_states,
            'transition_rules': self.transition_rules,
            'update_params': self.update_params,
            'expressions': self.expressions,
            'decay_rate': self.decay_rate,
            'trigger_threshold': self.trigger_threshold,
            'emotion_duration': self.emotion_duration
        } 