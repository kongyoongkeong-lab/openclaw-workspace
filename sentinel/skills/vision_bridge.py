#!/usr/bin/env python3
"""
Moondream Vision Accessor
用于访问本地 Ollama API 进行图像识别
"""
import requests
import base64
import json
import time
from typing import Dict, Optional, List, Any
from PIL import Image


class MoondreamVision:
    """Moondream 视觉访问器类"""
    
    def __init__(
        self,
        api_url: str = "http://localhost:11434",  # Ollama 默认端口
        model: str = "moondream:latest",
        max_retries: int = 3,
        retry_delay: float = 2.0,
        timeout: int = 30
    ):
        """
        初始化 Moondream 视觉访问器
        
        Args:
            api_url: Ollama API 地址 (默认 http://localhost:11434)
            model: 使用的模型 (moondream:latest)
            max_retries: 最大重试次数
            retry_delay: 重试间隔 (秒)
            timeout: 请求超时时间 (秒)
        """
        self.api_url = api_url.rstrip('/')
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.session = requests.Session()
        
    def encode_image_to_base64(self, image_path: str) -> str:
        """
        将图像文件转换为 Base64
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            Base64 编码的图像数据
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不是有效图像
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 验证是否为有效图像
            try:
                Image.open(image_path)
            except Exception as e:
                raise ValueError(f"无法打开图像：{e}")
            
            # 转换为 Base64
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return base64_data
            
        except FileNotFoundError:
            raise FileNotFoundError(f"图像文件不存在：{image_path}")
        except Exception as e:
            raise RuntimeError(f"图像转换失败：{e}")
    
    def _make_request_with_retry(self, prompt: str, image_data: bytes) -> Dict:
        """
        带重试机制的请求
        
        Args:
            prompt: 图像描述提示
            image_data: Base64 编码的图像数据
            
        Returns:
            API 响应
            
        Raises:
            requests.exceptions.RequestException: 请求失败
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "base64": image_data,
            "stream": False
        }
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    f"{self.api_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"错误：HTTP {response.status_code}")
                    return {"response": f"错误：HTTP {response.status_code}"}
                    
            except requests.exceptions.RequestException as e:
                print(f"请求错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    print(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError(f"请求失败：{e}")
                    
        return {"response": "请求超时"}
    
    def describe_image(self, image_path: str, prompt: str = "描述这张图片") -> str:
        """
        描述图像内容
        
        Args:
            image_path: 图像文件路径
            prompt: 自定义提示
            
        Returns:
            图像描述文本
        """
        try:
            # 读取并编码图像
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 使用 Moondream 分析
            response = self._make_request_with_retry(prompt, image_data)
            
            if "response" in response:
                return response["response"]
            
            return response.get("response", "无响应")
            
        except Exception as e:
            print(f"图像分析错误：{e}")
            return f"错误：{e}"
    
    def identify_objects(self, image_path: str, max_objects: int = 5) -> List[str]:
        """
        识别图像中的物体
        
        Args:
            image_path: 图像文件路径
            max_objects: 最大物体数量
            
        Returns:
            物体列表
        """
        prompt = f"识别这张图片中的所有物体，最多{max_objects}个"
        
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            response = self._make_request_with_retry(prompt, image_data)
            
            if "response" in response:
                return response["response"].split('\n')[:max_objects]
            
            return []
            
        except Exception as e:
            print(f"物体识别错误：{e}")
            return []
    
    def answer_question(self, image_path: str, question: str) -> str:
        """
        回答关于图像的特定问题
        
        Args:
            image_path: 图像文件路径
            question: 问题
            
        Returns:
            答案
        """
        prompt = question
        
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            response = self._make_request_with_retry(prompt, image_data)
            
            if "response" in response:
                return response["response"]
            
            return "无响应"
            
        except Exception as e:
            print(f"问题回答错误：{e}")
            return f"错误：{e}"
    
    def get_image_info(self, image_path: str) -> Dict:
        """
        获取图像基本信息
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            图像信息字典
        """
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                info = {
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "format": img.format,
                    "size": f"{img.width}x{img.height}"
                }
                return info
                
        except Exception as e:
            print(f"图像信息获取错误：{e}")
            return {"error": str(e)}


def main():
    """示例用法"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法：vision_bridge.py <图像路径> [问题]")
        print("示例:")
        print("  vision_bridge.py image.jpg")
        print("  vision_bridge.py image.jpg '这是什么？'")
        print("  vision_bridge.py image.jpg 识别物体")
        sys.exit(1)
    
    image_path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else "描述这张图片"
    
    # 创建访问器
    vision = MoondreamVision()
    
    # 获取图像信息
    print(f"获取图像信息：{image_path}")
    info = vision.get_image_info(image_path)
    print(json.dumps(info, indent=2))
    
    print("")
    
    # 描述图像
    print(f"描述图像...")
    print("-" * 80)
    description = vision.describe_image(image_path)
    print(description)
    print("-" * 80)
    
    # 如果指定了问题
    if question != "描述这张图片":
        print(f"\n回答问题：{question}")
        print("-" * 80)
        answer = vision.answer_question(image_path, question)
        print(answer)
        print("-" * 80)


if __name__ == "__main__":
    main()
