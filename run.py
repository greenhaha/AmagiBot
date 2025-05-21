#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

def load_environment():
    """加载环境变量"""
    # 加载.env文件
    load_dotenv()
    
    # 获取LLM模型类型
    llm_type = os.getenv('LLM_TYPE', 'chatgpt').lower()
    
    # 验证必要的环境变量
    required_vars = {
        'chatgpt': ['OPENAI_API_KEY', 'OPENAI_API_BASE'],
        'deepseek': ['DEEPSEEK_API_KEY', 'DEEPSEEK_API_BASE'],
        'qianwen': ['QIANWEN_API_KEY', 'QIANWEN_API_BASE'],
        'siliconflow': ['SILICONFLOW_API_KEY', 'SILICONFLOW_API_BASE']
    }
    
    # 检查当前模型所需的必要环境变量
    if llm_type not in required_vars:
        print(f"错误：不支持的LLM类型 - {llm_type}")
        print("支持的LLM类型：chatgpt, deepseek, qianwen, siliconflow")
        sys.exit(1)
        
    missing_vars = [var for var in required_vars[llm_type] if not os.getenv(var)]
    if missing_vars:
        print(f"错误：缺少必要的环境变量：{', '.join(missing_vars)}")
        print(f"请检查.env文件是否正确配置了{llm_type}所需的API密钥和基础URL")
        sys.exit(1)
    
    return llm_type

def check_environment():
    """检查环境配置"""
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("错误：需要Python 3.8或更高版本")
        sys.exit(1)
        
    # 检查MongoDB
    try:
        import pymongo
        client = pymongo.MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
        client.server_info()
    except Exception as e:
        print("错误：MongoDB连接失败，请确保MongoDB已启动")
        sys.exit(1)

def install_dependencies():
    """安装依赖"""
    print("正在安装依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"错误：依赖安装失败 - {str(e)}")
        sys.exit(1)

def create_directories():
    """创建必要的目录"""
    directories = [
        "logs",
        "data",
        "src/config",
        "src/plugin/knowledges/data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def initialize_llm(llm_type):
    """初始化LLM模型"""
    print(f"正在初始化{llm_type}模型...")
    try:
        if llm_type == 'chatgpt':
            from src.llm.chatgpt import ChatGPT
            return ChatGPT()
        elif llm_type == 'deepseek':
            from src.llm.deepseek import DeepSeek
            return DeepSeek()
        elif llm_type == 'qianwen':
            from src.llm.qianwen import QianWen
            return QianWen()
        elif llm_type == 'siliconflow':
            from src.llm.siliconflow import SiliconFlow
            return SiliconFlow()
    except Exception as e:
        print(f"错误：{llm_type}模型初始化失败 - {str(e)}")
        sys.exit(1)

def main():
    """主函数"""
    print("正在启动聊天机器人...")
    
    # 创建目录
    create_directories()
    
    # 加载环境变量
    llm_type = load_environment()
    
    # 检查环境
    check_environment()
    
    # 安装依赖
    install_dependencies()
    
    # 初始化LLM模型
    llm = initialize_llm(llm_type)
    
    # 启动机器人
    print(f"\n正在启动聊天机器人（使用{llm_type}模型）...")
    try:
        from src.main import main as start_bot
        start_bot(llm)
    except ImportError as e:
        print(f"错误：导入失败 - {str(e)}")
        print("请确保所有必要的Python包都已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"错误：启动失败 - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 