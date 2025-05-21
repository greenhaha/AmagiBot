from typing import Dict, Any, List
from dataclasses import dataclass

# 记忆参数配置
MEMORY_PARAMS = {
    # 记忆检索参数
    'retrieval': {
        'top_k': 5,  # 检索最相关的k条记忆
        'similarity_threshold': 0.7,  # 相似度阈值
        'max_tokens': 1000,  # 最大token数
        'temperature': 0.7,  # 温度参数
    },
    
    # 记忆分析参数
    'analysis': {
        'max_tokens': 2000,  # 最大token数
        'temperature': 0.7,  # 温度参数
        'importance_threshold': 0.6,  # 重要性阈值
    },
    
    # 记忆存储参数
    'storage': {
        'max_memories': 1000,  # 最大记忆数量
        'memory_expiration': 3600,  # 记忆过期时间（秒）
        'compression_threshold': 0.8,  # 压缩阈值
    },
    
    # 记忆更新参数
    'update': {
        'relevance_threshold': 0.6,  # 相关性阈值
        'importance_weight': 0.7,  # 重要性权重
        'recency_weight': 0.3,  # 时效性权重
    }
}

# 重要性关键词
IMPORTANCE_KEYWORDS = [
    # 时间相关
    '永远', '一直', '经常', '每天', '每周', '每月', '每年',
    '重要', '关键', '必须', '一定', '肯定', '绝对',
    
    # 情感相关
    '喜欢', '讨厌', '爱', '恨', '开心', '难过', '生气',
    '害怕', '担心', '期待', '失望', '满意', '不满',
    
    # 关系相关
    '朋友', '家人', '亲人', '爱人', '同事', '同学',
    '老师', '学生', '领导', '下属',
    
    # 事件相关
    '生日', '纪念日', '节日', '假期', '旅行', '工作',
    '学习', '考试', '比赛', '会议', '约会',
    
    # 地点相关
    '家', '学校', '公司', '医院', '餐厅', '商场',
    '公园', '景点', '城市', '国家',
    
    # 物品相关
    '礼物', '纪念品', '收藏品', '贵重物品', '重要文件',
    
    # 状态相关
    '生病', '受伤', '康复', '毕业', '结婚', '离职',
    '升职', '加薪', '获奖', '成功', '失败'
]

# 记忆分析提示词
MEMORY_ANALYSIS_PROMPT = """请分析以下对话内容，提取关键信息：

对话内容：
{conversation}

请从以下几个方面进行分析：
1. 主要话题
2. 关键信息
3. 用户意图
4. 情感倾向
5. 需要记忆的重要信息

分析结果："""

# 记忆检索提示词
MEMORY_RETRIEVAL_PROMPT = """请根据以下用户输入，从记忆中检索相关信息：

用户输入：
{user_input}

记忆库：
{memories}

请找出最相关的记忆，并说明相关性："""

@dataclass
class MemoryConfig:
    """记忆系统配置"""
    
    # 记忆配置
    max_memories: int = 1000
    memory_expiration: int = 3600  # 秒
    
    # 记忆类型
    memory_types: Dict[str, float] = None
    
    # 提示词配置
    analysis_prompt: str = MEMORY_ANALYSIS_PROMPT
    retrieval_prompt: str = MEMORY_RETRIEVAL_PROMPT
    
    # 重要性关键词
    importance_keywords: List[str] = None
    
    # 记忆参数
    memory_params: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.memory_types is None:
            self.memory_types = {
                'conversation': 1.0,
                'user_input': 0.8,
                'assistant_response': 0.8,
                'system_event': 0.5
            }
        if self.importance_keywords is None:
            self.importance_keywords = IMPORTANCE_KEYWORDS
        if self.memory_params is None:
            self.memory_params = MEMORY_PARAMS
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'MemoryConfig':
        """从字典创建配置"""
        return cls(
            max_memories=config.get('max_memories', cls.max_memories),
            memory_expiration=config.get('memory_expiration', cls.memory_expiration),
            memory_types=config.get('memory_types', cls.memory_types),
            analysis_prompt=config.get('analysis_prompt', cls.analysis_prompt),
            retrieval_prompt=config.get('retrieval_prompt', cls.retrieval_prompt),
            importance_keywords=config.get('importance_keywords', cls.importance_keywords),
            memory_params=config.get('memory_params', cls.memory_params)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'max_memories': self.max_memories,
            'memory_expiration': self.memory_expiration,
            'memory_types': self.memory_types,
            'analysis_prompt': self.analysis_prompt,
            'retrieval_prompt': self.retrieval_prompt,
            'importance_keywords': self.importance_keywords,
            'memory_params': self.memory_params
        } 