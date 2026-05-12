# RealESRGAN 增强技能

## 功能
使用本地安装的 RealESRGAN (ncnn-vulkan) 对图像进行超分辨率增强。

## 文件位置
- 工具：`C:\realesrgan\realesrgan-ncnn-vulkan.exe`
- 包装器：`C:\realesrgan\realesrgan_wrapper.py`
- 依赖：`C:\realesrgan\vcomp140.dll`

## 使用方式

### 1. 通过 @ops 调用

```
@ops enhance_realesrgan --input=输入.jpg --output=输出.jpg --model=realesr-general
```

### 2. 命令行工具

```bash
C:\realesrgan\realesrgan-ncnn-vulkan.exe -i 输入.jpg -o 输出.jpg -n realesr-general -s 2
```

### 3. Python 包装器

```python
from realesrgan_wrapper import enhance_image

enhance_image(
    input_path='输入.jpg',
    output_path='输出.jpg',
    model_name='realesr-general',  # realesr-animevideov3, realesr-general, realesr-natural
    scale=2
)
```

## 可用模型

| 模型名称 | 适用场景 |
|---------|---------|
| `realesr-animevideov3` | 动漫/二次元 |
| `realesr-general-x4v3` | 通用场景 (4 倍放大) |
| `realesr-general` | 通用场景 |
| `realesr-natural` | 自然场景 |
| `realesr-cup-cake` | 食物 |

## 参数说明

- `-i`: 输入图像路径
- `-o`: 输出图像路径
- `-n`: 模型名称
- `-s`: 放大倍率 (2 或 4)

## 审计日志

所有图像增强操作将被记录到 `audit_queue.json`，供 @sentinel 审核。
