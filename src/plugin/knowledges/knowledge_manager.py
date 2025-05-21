from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime
from pymongo import MongoClient
from ..memory.core.multi_source_manager import MultiSourceManager
from ..memory.sources.knowledge_source import KnowledgeMemorySource
from ..llm.core.llm_manager import LLMManager

class KnowledgeManager:
    """知识库管理器：管理知识库的学习和检索"""
    def __init__(self, mongo_client: MongoClient, llm_manager: LLMManager):
        self.mongo_client = mongo_client
        self.llm_manager = llm_manager
        self.db = mongo_client['chatbot_db']
        self.collection = self.db['knowledge_base']
        
        # 初始化记忆管理器
        self.memory_manager = MultiSourceManager()
        self.knowledge_source = KnowledgeMemorySource(mongo_client)
        self.memory_manager.register_source(self.knowledge_source)
        
        # 加载配置
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载知识库配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'model_name': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 2000,
            'knowledge_dir': 'data',
            'file_extensions': ['.txt'],
            'chunk_size': 1000,
            'overlap': 200
        }
        
    def learn_from_files(self, user_id: str = "system") -> Dict[str, Any]:
        """从文件学习知识"""
        knowledge_dir = os.path.join(os.path.dirname(__file__), self.config['knowledge_dir'])
        if not os.path.exists(knowledge_dir):
            raise FileNotFoundError(f"知识库目录不存在: {knowledge_dir}")
            
        results = {
            'total_files': 0,
            'processed_files': 0,
            'total_chunks': 0,
            'successful_chunks': 0,
            'errors': []
        }
        
        # 遍历知识库目录
        for root, _, files in os.walk(knowledge_dir):
            for file in files:
                if any(file.endswith(ext) for ext in self.config['file_extensions']):
                    results['total_files'] += 1
                    file_path = os.path.join(root, file)
                    
                    try:
                        # 读取文件内容
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # 分块处理
                        chunks = self._split_content(content)
                        results['total_chunks'] += len(chunks)
                        
                        # 处理每个块
                        for chunk in chunks:
                            try:
                                # 使用LLM处理知识
                                processed_knowledge = self._process_knowledge(chunk)
                                
                                # 存储到知识库
                                self._store_knowledge(
                                    content=processed_knowledge['content'],
                                    metadata={
                                        'source_file': file_path,
                                        'category': processed_knowledge['category'],
                                        'key_points': processed_knowledge['key_points'],
                                        'confidence': processed_knowledge['confidence']
                                    },
                                    user_id=user_id
                                )
                                
                                results['successful_chunks'] += 1
                            except Exception as e:
                                results['errors'].append(f"处理块时出错: {str(e)}")
                                
                        results['processed_files'] += 1
                    except Exception as e:
                        results['errors'].append(f"处理文件 {file} 时出错: {str(e)}")
                        
        return results
        
    def _split_content(self, content: str) -> List[str]:
        """将内容分割成块"""
        chunks = []
        chunk_size = self.config['chunk_size']
        overlap = self.config['overlap']
        
        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk = content[start:end]
            chunks.append(chunk)
            start = end - overlap
            
        return chunks
        
    def _process_knowledge(self, content: str) -> Dict[str, Any]:
        """使用LLM处理知识内容"""
        prompt = f"""请分析以下知识内容，并提取关键信息：
        
{content}

请以JSON格式返回以下信息：
1. 处理后的内容（保持原意但更清晰）
2. 知识类别
3. 关键点列表
4. 可信度（0-1之间）

格式示例：
{{
    "content": "处理后的内容",
    "category": "知识类别",
    "key_points": ["关键点1", "关键点2"],
    "confidence": 0.9
}}"""

        response = self.llm_manager.generate_response(
            prompt=prompt,
            model_name=self.config['model_name'],
            temperature=self.config['temperature'],
            max_tokens=self.config['max_tokens']
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果LLM返回的不是有效的JSON，进行简单处理
            return {
                'content': content,
                'category': 'general',
                'key_points': [],
                'confidence': 0.5
            }
            
    def _store_knowledge(self,
                        content: str,
                        metadata: Dict[str, Any],
                        user_id: str) -> None:
        """存储知识到数据库"""
        # 存储到知识库集合
        self.collection.insert_one({
            'content': content,
            'metadata': metadata,
            'user_id': user_id,
            'created_at': datetime.now()
        })
        
        # 同时存储到记忆系统
        self.memory_manager.add_memory(
            content=content,
            user_id=user_id,
            source_name='knowledge',
            metadata=metadata
        )
        
    def get_knowledge(self,
                     query: str,
                     user_id: str,
                     limit: int = 5) -> List[Dict[str, Any]]:
        """检索知识"""
        # 从记忆系统检索
        memories = self.memory_manager.get_memories(
            query=query,
            user_id=user_id,
            source_names=['knowledge'],
            limit=limit
        )
        
        # 转换为知识格式
        return [
            {
                'content': memory.content,
                'metadata': memory.metadata,
                'strength': memory.strength
            }
            for memory in memories
        ]
        
    def get_knowledge_stats(self, user_id: str) -> Dict[str, Any]:
        """获取知识库统计信息"""
        # 获取知识总数
        total_knowledge = self.collection.count_documents({'user_id': user_id})
        
        # 获取各类型知识数量
        categories = self.collection.distinct('metadata.category', {'user_id': user_id})
        category_counts = {
            category: self.collection.count_documents({
                'user_id': user_id,
                'metadata.category': category
            })
            for category in categories
        }
        
        # 获取最近更新时间
        latest_update = self.collection.find_one(
            {'user_id': user_id},
            sort=[('created_at', -1)]
        )
        
        return {
            'total_knowledge': total_knowledge,
            'category_counts': category_counts,
            'latest_update': latest_update['created_at'] if latest_update else None
        } 