from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from ..models.memory_encoding import MemoryEncoding

class MemoryEncoder:
    """记忆编码器：将对话内容编码为向量表示"""
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.encoding_dim = self.model.get_sentence_embedding_dimension()
        
    def encode_memory(self, 
                     content: str,
                     metadata: Dict[str, Any]) -> MemoryEncoding:
        """编码记忆内容"""
        # 生成文本嵌入
        embedding = self.model.encode(content)
        
        # 计算记忆强度
        strength = self._calculate_memory_strength(content, metadata)
        
        # 计算记忆类型
        memory_type = self._determine_memory_type(content, metadata)
        
        # 提取关键信息
        key_points = self._extract_key_points(content)
        
        return MemoryEncoding(
            content=content,
            embedding=embedding,
            strength=strength,
            memory_type=memory_type,
            key_points=key_points,
            metadata=metadata
        )
        
    def _calculate_memory_strength(self, 
                                 content: str,
                                 metadata: Dict[str, Any]) -> float:
        """计算记忆强度"""
        # 基础强度
        base_strength = 0.5
        
        # 根据内容长度调整
        content_length = len(content)
        if content_length > 100:
            base_strength += 0.1
        elif content_length < 20:
            base_strength -= 0.1
            
        # 根据情感强度调整
        emotion_intensity = metadata.get('emotion_intensity', 0.5)
        base_strength += (emotion_intensity - 0.5) * 0.2
        
        # 根据重要性调整
        importance = metadata.get('importance', 0.5)
        base_strength += (importance - 0.5) * 0.2
        
        # 根据时间衰减调整
        time_decay = metadata.get('time_decay', 0.0)
        base_strength *= (1 - time_decay)
        
        return max(0.0, min(1.0, base_strength))
        
    def _determine_memory_type(self,
                             content: str,
                             metadata: Dict[str, Any]) -> str:
        """确定记忆类型"""
        # 根据内容特征和元数据确定记忆类型
        if metadata.get('is_explicit', False):
            return 'explicit'  # 显性记忆
            
        if metadata.get('is_procedural', False):
            return 'procedural'  # 程序性记忆
            
        if metadata.get('is_episodic', False):
            return 'episodic'  # 情景记忆
            
        if metadata.get('is_semantic', False):
            return 'semantic'  # 语义记忆
            
        # 默认返回语义记忆
        return 'semantic'
        
    def _extract_key_points(self, content: str) -> List[str]:
        """提取关键信息点"""
        # 简单实现：按句子分割并选择重要句子
        sentences = content.split('。')
        key_points = []
        
        for sentence in sentences:
            if len(sentence.strip()) > 0:
                # 检查是否包含重要关键词
                if any(keyword in sentence for keyword in ['重要', '关键', '必须', '一定']):
                    key_points.append(sentence.strip())
                    
        return key_points
        
    def encode_batch(self, 
                    contents: List[str],
                    metadata_list: List[Dict[str, Any]]) -> List[MemoryEncoding]:
        """批量编码记忆内容"""
        return [
            self.encode_memory(content, metadata)
            for content, metadata in zip(contents, metadata_list)
        ] 