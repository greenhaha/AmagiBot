from pymongo import MongoClient
from ..sources.conversation_source import ConversationMemorySource
from ..sources.knowledge_source import KnowledgeMemorySource
from ..core.multi_source_manager import MultiSourceMemoryManager

def main():
    # 初始化MongoDB客户端
    mongo_client = MongoClient('mongodb://localhost:27017/')
    
    # 创建记忆源
    conversation_source = ConversationMemorySource(mongo_client)
    knowledge_source = KnowledgeMemorySource(mongo_client)
    
    # 创建多源记忆管理器
    memory_manager = MultiSourceMemoryManager()
    
    # 注册记忆源
    memory_manager.register_source(conversation_source)
    memory_manager.register_source(knowledge_source)
    
    # 示例用户ID
    user_id = "user123"
    
    # 添加对话记忆
    memory_manager.add_memory(
        content="用户说他喜欢Python编程",
        user_id=user_id,
        source_name="conversation",
        metadata={
            'importance': 0.8,
            'emotional_intensity': 0.6,
            'context': '用户偏好'
        }
    )
    
    # 添加知识记忆
    memory_manager.add_memory(
        content="Python是一种高级编程语言，以其简洁的语法和丰富的库而闻名",
        user_id=user_id,
        source_name="knowledge",
        metadata={
            'knowledge_type': 'domain',
            'confidence': 0.9,
            'category': 'programming'
        }
    )
    
    # 查询记忆
    memories = memory_manager.get_memories(
        query="Python编程",
        user_id=user_id,
        limit=5
    )
    
    print("查询结果:")
    for memory in memories:
        print(f"来源: {memory.metadata.get('source', 'unknown')}")
        print(f"内容: {memory.content}")
        print(f"强度: {memory.strength}")
        print(f"类型: {memory.memory_type}")
        print("---")
        
    # 获取记忆统计信息
    stats = memory_manager.get_memory_stats(user_id)
    print("\n记忆统计:")
    print(f"总记忆数: {stats['overall']['total_memories']}")
    print("各类型记忆数量:")
    for memory_type, count in stats['overall']['type_counts'].items():
        print(f"- {memory_type}: {count}")
        
    # 整合记忆
    print("\n开始整合记忆...")
    memory_manager.consolidate_memories(user_id)
    
    # 再次获取统计信息
    updated_stats = memory_manager.get_memory_stats(user_id)
    print("\n整合后的记忆统计:")
    print(f"总记忆数: {updated_stats['overall']['total_memories']}")
    print("各类型记忆数量:")
    for memory_type, count in updated_stats['overall']['type_counts'].items():
        print(f"- {memory_type}: {count}")

if __name__ == "__main__":
    main() 