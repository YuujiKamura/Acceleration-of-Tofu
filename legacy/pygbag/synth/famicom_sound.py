import pygame
import numpy as np
from array import array
import time

pygame.mixer.init(frequency=44100, size=-16, channels=1)

def generate_famicom_wave(freq, duration, duty_cycle=0.5, volume=0.5):
    """ファミコン風の矩形波を生成
    duty_cycle: デューティ比（0.125, 0.25, 0.5, 0.75のいずれか）
    """
    sample_rate = 44100
    period = int(sample_rate / freq)
    samples = array('h', [0] * int(sample_rate * duration))
    
    amplitude = 32767 * volume  # 16-bit
    duty_point = int(period * duty_cycle)
    
    for i in range(len(samples)):
        if (i % period) < duty_point:
            samples[i] = int(amplitude)
        else:
            samples[i] = int(-amplitude)
    
    return pygame.mixer.Sound(samples)

# ファミコンの音階（Hz）
NOTES = {
    'A3': 220.00,  # ラ
    'C4': 261.63,  # ド
    'E4': 329.63,  # ミ
    'G4': 392.00,  # ソ
    'A4': 440.00,  # ラ
}

# ファミコンのデューティ比
DUTY_CYCLES = [
    (0.125, "デューティ比12.5% - 細い音"),
    (0.25,  "デューティ比25% - 主旋律向き"),
    (0.5,   "デューティ比50% - 基本の音"),
    (0.75,  "デューティ比75% - 太い音")
]

print("ファミコン風サウンドのテスト開始...")

# メロディパターン
melody = [
    ('A3', 0.2),
    ('C4', 0.2),
    ('E4', 0.2),
    ('G4', 0.2),
    ('A4', 0.4)
]

# 各デューティ比でメロディを再生
for duty, desc in DUTY_CYCLES:
    print(f"\n{desc}")
    for note, duration in melody:
        sound = generate_famicom_wave(NOTES[note], duration, duty_cycle=duty, volume=0.5)
        sound.play()
        time.sleep(duration + 0.05)  # 少し間を開ける
    time.sleep(0.5)  # パターン間の休止

print("\nテスト完了！") 