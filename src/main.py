import os
import json
import logging
from typing import Dict, Any, Optional, List
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

from src.llm.base import BaseLLM
from src.dialogue import DialogueSystem
from src.memory.core.memory_manager import MemoryManager
from src.emotion import EmotionManager, EmotionAnalyzer
from src.config.dialogue_config import DialogueConfig
from src.config.memory_config import MemoryConfig
from src.config.emotion_config import EmotionConfig

def main(llm: Optional[BaseLLM] = None):
    """
    主程序入口
    
    Args:
        llm: LLM模型实例
    """
    if llm is None:
        raise ValueError("LLM模型实例不能为空")
    
    # 加载配置
    dialogue_config = DialogueConfig()
    memory_config = MemoryConfig()
    emotion_config = EmotionConfig()
    
    # 初始化系统组件
    memory_manager = MemoryManager(memory_config)
    emotion_manager = EmotionManager(emotion_config)
    emotion_analyzer = EmotionAnalyzer()
    
    # 初始化对话系统
    dialogue_system = DialogueSystem(
        llm=llm,
        emotion_manager=emotion_manager,
        emotion_analyzer=emotion_analyzer,
        memory_manager=memory_manager
    )
    
    # 获取机器人名称
    bot_name = os.getenv('BOT_NAME', '女仆天城')
    print(f"\n{bot_name}已启动，输入'quit'退出对话")
    
    # 初始化对话历史
    messages: List[Dict[str, str]] = []
    
    # 获取最大历史记录数
    max_history = dialogue_config.max_history
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n主人: ").strip()
            
            # 检查是否退出
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n再见！")
                break
            
            # 检查是否清空历史
            if user_input.lower() in ['clear', 'clear history', '清空历史']:
                messages.clear()
                memory_manager.clear_memory()
                print("\n对话历史已清空")
                continue
            print("更新记忆")
            # 1. 更新记忆
            memory_manager.add_memory(
                content=user_input,
                user_id="user_input",
                metadata={
                    "type": "user_input",
                    "timestamp": datetime.now().isoformat(),
                    "context": "user_message"
                }
            )
            memory_context = memory_manager.get_memory_context(
                query=user_input,
                user_id="user_input"
            )
            # 2. 更新情感状态
            emotion_state = emotion_manager.get_emotion_state()
            emotion_intensity = emotion_manager.get_emotion_intensity()
            # 3. 生成回复
            response = dialogue_system.generate_response(
                user_input=user_input,
                model_name=dialogue_config.model_name,
                personality_traits=llm.personality_traits,
                emotion_state=emotion_state,
                emotion_intensity=emotion_intensity,
                memory_context=memory_context
            )
            # 4. 更新记忆
            memory_manager.add_memory(
                content=response,
                user_id="assistant_response",
                metadata={
                    "type": "assistant_response",
                    "timestamp": datetime.now().isoformat(),
                    "context": "assistant_message"
                }
            )
            
            # 5. 打印天城回复
            print(f"\n天城: {response}")
            
            # 6. 更新对话历史
            messages.append({
                "role": "user",
                "content": user_input
            })
            messages.append({
                "role": "assistant",
                "content": response
            })
            
            # 保持历史记录在限制范围内
            if len(messages) > max_history * 2:
                messages = messages[-max_history * 2:]
            
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"\n错误：{str(e)}")
            continue

if __name__ == "__main__":
    main() 