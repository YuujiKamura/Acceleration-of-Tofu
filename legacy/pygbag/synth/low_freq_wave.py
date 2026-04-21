import pygame
import numpy as np
from array import array
import time

pygame.mixer.init(frequency=44100, size=-16, channels=1)

def generate_square_wave(freq, duration, volume=0.5):
    """低周波の矩形波を生成"""
    sample_rate = 44100
    period = int(sample_rate / freq)
    samples = array('h', [0] * int(sample_rate * duration))
    
    amplitude = 32767 * volume  # 16-bit
    
    for i in range(len(samples)):
        if (i % period) < (period / 2):
            samples[i] = int(amplitude)
        else:
            samples[i] = int(-amplitude)
    
    return pygame.mixer.Sound(samples)

# 超低周波のテスト（20Hz～60Hz）
LOW_FREQS = [
    (20, "20Hz - 超低音域の底"),
    (30, "30Hz - 重低音"),
    (40, "40Hz - オルガンの最低音域"),
    (50, "50Hz - 電源ハム周波数"),
    (60, "60Hz - 低音の可聴域")
]

print("低周波矩形波のテスト開始...")

for freq, desc in LOW_FREQS:
    print(f"\n{desc}を再生中...")
    sound = generate_square_wave(freq, duration=2.0, volume=0.8)
    sound.play()
    time.sleep(2.5)  # 2秒再生 + 0.5秒休止

print("\nテスト完了！") 