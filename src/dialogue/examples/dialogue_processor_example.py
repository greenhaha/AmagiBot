from pymongo import MongoClient
from src.memory.core.multi_source_manager import MultiSourceMemoryManager
from src.memory.sources.conversation_source import ConversationMemorySource
from src.memory.sources.knowledge_source import KnowledgeMemorySource
from src.emotion.core.emotion_manager import EmotionManager
from src.emotion.core.emotion_analyzer import EmotionAnalyzer
from src.llm.siliconflow import LLMManager
from ..core.dialogue_processor import DialogueProcessor

def main():
    # 初始化MongoDB客户端
    mongo_client = MongoClient('mongodb://localhost:27017/')
    
    # 初始化记忆系统
    memory_manager = MultiSourceMemoryManager()
    conversation_source = ConversationMemorySource(mongo_client)
    knowledge_source = KnowledgeMemorySource(mongo_client)
    memory_manager.register_source(conversation_source)
    memory_manager.register_source(knowledge_source)
    
    # 初始化情感系统
    emotion_manager = EmotionManager(mongo_client)
    emotion_analyzer = EmotionAnalyzer()
    
    # 初始化LLM管理器
    llm_manager = LLMManager()
    
    # 创建对话处理器
    dialogue_processor = DialogueProcessor(
        memory_manager=memory_manager,
        emotion_manager=emotion_manager,
        emotion_analyzer=emotion_analyzer,
        llm_manager=llm_manager
    )
    
    # 示例用户ID和性格特征
    user_id = "user123"
    personality_traits = {
        "友好度": 0.8,
        "专业度": 0.7,
        "幽默感": 0.6,
        "同理心": 0.9
    }
    
    # 示例对话
    dialogue_examples = [
        "你好，我想了解一下Python编程",
        "Python有什么特点？",
        "我最近在学习Python，感觉有点困难",
        "能给我一些学习建议吗？"
    ]
    
    print("开始对话示例：\n")
    
    for user_input in dialogue_examples:
        print(f"用户: {user_input}")
        
        # 处理对话并生成回复
        response = dialogue_processor.process_dialogue(
            user_id=user_id,
            user_input=user_input,
            personality_traits=personality_traits
        )
        
        print(f"AI: {response}\n")
        
    # 获取对话统计信息
    memory_stats = memory_manager.get_memory_stats(user_id)
    emotion_stats = emotion_manager.get_emotion_stats(user_id)
    
    print("\n对话统计信息：")
    print(f"总对话数: {memory_stats['conversation']['total_memories']}")
    print(f"情感状态: {emotion_stats['current_emotion']}")
    print(f"情感强度: {emotion_stats['intensity']:.2f}")

if __name__ == "__main__":
    main() 