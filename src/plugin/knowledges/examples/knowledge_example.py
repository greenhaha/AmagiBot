from pymongo import MongoClient
from ...llm.core.llm_manager import LLMManager
from ..knowledge_manager import KnowledgeManager

def main():
    # 初始化MongoDB客户端
    mongo_client = MongoClient('mongodb://localhost:27017/')
    
    # 初始化LLM管理器
    llm_manager = LLMManager()
    
    # 创建知识库管理器
    knowledge_manager = KnowledgeManager(mongo_client, llm_manager)
    
    # 从文件学习知识
    print("开始学习知识...")
    results = knowledge_manager.learn_from_files()
    print("\n学习结果：")
    print(f"总文件数: {results['total_files']}")
    print(f"处理文件数: {results['processed_files']}")
    print(f"总块数: {results['total_chunks']}")
    print(f"成功处理块数: {results['successful_chunks']}")
    if results['errors']:
        print("\n错误信息：")
        for error in results['errors']:
            print(f"- {error}")
            
    # 获取知识库统计信息
    stats = knowledge_manager.get_knowledge_stats("system")
    print("\n知识库统计：")
    print(f"总知识数: {stats['total_knowledge']}")
    print("各类型知识数量：")
    for category, count in stats['category_counts'].items():
        print(f"- {category}: {count}")
        
    # 示例查询
    queries = [
        "Python的主要特点是什么？",
        "Python适合哪些应用领域？",
        "学习Python有什么建议？"
    ]
    
    print("\n知识查询示例：")
    for query in queries:
        print(f"\n查询: {query}")
        knowledge = knowledge_manager.get_knowledge(query, "system")
        for item in knowledge:
            print(f"\n内容: {item['content']}")
            print(f"类别: {item['metadata']['category']}")
            print(f"关键点: {', '.join(item['metadata']['key_points'])}")
            print(f"强度: {item['strength']:.2f}")

if __name__ == "__main__":
    main() 