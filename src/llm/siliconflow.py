import os
import json
import requests
from typing import List, Dict, Any, Optional
from .base import BaseLLM
from config.dialogue_config import LLM_MODELS

class SiliconFlow(BaseLLM):
    """SiliconFlow API实现类"""
    
    def __init__(self):
        """初始化SiliconFlow客户端"""
        self.api_key = os.getenv('SILICONFLOW_API_KEY')
        self.api_base = os.getenv('SILICONFLOW_API_BASE', 'https://api.siliconflow.cn/v1')
        self.model_name = os.getenv('SILICONFLOW_MODEL_NAME', 'Pro/deepseek-ai/DeepSeek-V3')
        self.timeout = int(os.getenv('SILICONFLOW_TIMEOUT', '30'))
        
        # 设置机器人性格特征
        self.personality_traits = {
            'friendly': 0.8,      # 友好程度
            'professional': 0.7,  # 专业程度
            'humorous': 0.5,      # 幽默程度
            'empathetic': 0.8,    # 同理心
            'creative': 0.6,      # 创造力
            'analytical': 0.7,    # 分析能力
            'patient': 0.8,       # 耐心程度
            'curious': 0.6        # 好奇心
        }
        
        # 验证配置
        if not self.api_key:
            raise ValueError("SiliconFlow API密钥必须配置")
            
        # 设置请求头
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # 检查可用模型
        try:
            available_models = self.get_available_models()
            print("\n可用的模型列表：")
            for model in available_models:
                print(f"- {model}")
            
            if self.model_name not in available_models:
                print(f"\n警告：指定的模型 '{self.model_name}' 不在可用模型列表中")
                if available_models:
                    self.model_name = available_models[0]
                    print(f"已自动切换到第一个可用模型：{self.model_name}")
        except Exception as e:
            print(f"\n警告：无法获取可用模型列表：{str(e)}")
        
        print(f"\n初始化SiliconFlow客户端：")
        print(f"API Base: {self.api_base}")
        print(f"Model: {self.model_name}")
        print(f"Timeout: {self.timeout}")
    
    def chat(self, 
            messages: List[Dict[str, str]], 
            temperature: float = 0.7,
            max_tokens: int = 2000,
            stream: bool = False) -> Dict[str, Any]:
        """
        发送聊天请求
        
        Args:
            messages: 消息历史列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            stream: 是否使用流式响应
            
        Returns:
            API响应结果
        """
        try:
            # 构建请求数据
            data = {
                'model': self.model_name,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'stream': stream
            }
            
            print(f"\n发送API请求：")
            print(f"URL: {self.api_base}/chat/completions")
            
            # 发送请求
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            # 打印响应状态和内容
            print(f"\nAPI响应：")
            print(f"Status Code: {response.status_code}")
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 处理流式响应
            if stream:
                return self._handle_stream_response(result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"\nAPI请求失败：")
            print(f"Error: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise Exception(f"SiliconFlow API请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"SiliconFlow API响应解析失败: {str(e)}")
        except Exception as e:
            raise Exception(f"SiliconFlow API调用出错: {str(e)}")
    
    def _handle_stream_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理流式响应
        
        Args:
            response: 原始响应数据
            
        Returns:
            处理后的响应数据
        """
        try:
            # 这里需要根据SiliconFlow的具体流式响应格式进行处理
            # 示例实现，实际使用时需要根据API文档调整
            return {
                'choices': [{
                    'message': {
                        'content': response.get('content', ''),
                        'role': 'assistant'
                    }
                }]
            }
        except Exception as e:
            raise Exception(f"处理流式响应失败: {str(e)}")
    
    def get_embeddings(self, text: str) -> List[float]:
        """
        获取文本的嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            文本的嵌入向量
        """
        try:
            # 构建请求数据
            data = {
                'model': f"{self.model_name}-embedding",
                'input': text
            }
            
            # 发送请求
            response = requests.post(
                f"{self.api_base}/embeddings",
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            return result.get('data', [{}])[0].get('embedding', [])
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取嵌入向量失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"解析嵌入向量响应失败: {str(e)}")
        except Exception as e:
            raise Exception(f"获取嵌入向量出错: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            可用模型列表
        """
        try:
            # 发送请求
            response = requests.get(
                f"{self.api_base}/models",
                headers=self.headers,
                timeout=self.timeout
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            return [model['id'] for model in result.get('data', [])]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取模型列表失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"解析模型列表响应失败: {str(e)}")
        except Exception as e:
            raise Exception(f"获取模型列表出错: {str(e)}") 