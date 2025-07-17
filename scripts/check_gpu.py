#!/usr/bin/env python3
"""
Скрипт для перевірки GPU та CUDA підтримки для Whisper транскрибації
"""

import torch
import sys

def check_gpu():
    print("🔍 Checking GPU and CUDA support...")
    print("=" * 50)
    
    # Перевіряємо PyTorch версію
    print(f"📦 PyTorch version: {torch.__version__}")
    
    # Перевіряємо CUDA доступність
    cuda_available = torch.cuda.is_available()
    print(f"⚡ CUDA available: {cuda_available}")
    
    if cuda_available:
        # Інформація про GPU
        gpu_count = torch.cuda.device_count()
        print(f"🎮 Number of GPUs: {gpu_count}")
        
        for i in range(gpu_count):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
            print(f"🎮 GPU {i}: {gpu_name}")
            print(f"💾 GPU {i} Memory: {gpu_memory:.1f} GB")
        
        # Поточний GPU
        current_device = torch.cuda.current_device()
        print(f"🎯 Current GPU: {current_device}")
        
        # Тест GPU
        print("\n🧪 Testing GPU with simple tensor operation...")
        try:
            x = torch.randn(1000, 1000).cuda()
            y = torch.randn(1000, 1000).cuda()
            z = torch.mm(x, y)
            print("✅ GPU test successful!")
        except Exception as e:
            print(f"❌ GPU test failed: {e}")
            return False
    else:
        print("⚠️  CUDA not available. You can still use CPU for transcription, but it will be slower.")
        print("💡 To enable GPU support, install PyTorch with CUDA:")
        print("   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118")
    
    print("\n" + "=" * 50)
    
    # Рекомендації для Whisper
    print("📋 Whisper Model Recommendations:")
    if cuda_available:
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"💾 Your GPU has {gpu_memory:.1f} GB memory")
        
        if gpu_memory >= 8:
            print("✅ Recommended: large model (best quality)")
        elif gpu_memory >= 4:
            print("✅ Recommended: medium model (good quality)")
        elif gpu_memory >= 2:
            print("✅ Recommended: small model (balanced)")
        else:
            print("✅ Recommended: base model (fast)")
    else:
        print("✅ Recommended: base model (CPU mode)")
    
    return cuda_available

if __name__ == "__main__":
    check_gpu() 