import pygame
import numpy as np
from array import array
import time

pygame.mixer.init(frequency=44100, size=-16, channels=1)

def generate_drum_hit(freq=50, duration=0.1, volume=0.8):
    """ファミコン風のドラム音を生成"""
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    # 基本の矩形波を生成
    period = int(sample_rate / freq)
    base_amplitude = 32767 * volume
    
    # エンベロープ（急速な減衰）を適用
    for i in range(len(samples)):
        # 時間経過による音量減衰
        decay = np.exp(-i / (sample_rate * 0.02))  # 0.02秒で減衰
        
        if (i % period) < (period / 2):
            samples[i] = int(base_amplitude * decay)
        else:
            samples[i] = int(-base_amplitude * decay)
    
    return pygame.mixer.Sound(samples)

print("ファミコン風ドラム音のテスト開始...")

# ドラムパターン（秒単位の間隔）
pattern = [0.2, 0.2, 0.2, 0.2]  # ドンドンドンドン

# ドラム音を生成
drum_sound = generate_drum_hit()

# パターンを3回繰り返す
for _ in range(3):
    print("ドンドンドンドン...")
    for interval in pattern:
        drum_sound.play()
        time.sleep(interval)
    time.sleep(0.4)  # パターン間の休止

print("\nテスト完了！") 