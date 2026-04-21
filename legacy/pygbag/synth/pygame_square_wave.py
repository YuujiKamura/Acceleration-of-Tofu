import pygame
import numpy as np
from array import array

pygame.mixer.init(frequency=44100, size=-16, channels=1)

def generate_square_wave(freq, duration, volume=0.3):
    """矩形波を生成"""
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

# 音階の周波数（Hz）
NOTES = {
    'C4': 261.63,
    'E4': 329.63,
    'G4': 392.00,
    'C5': 523.25,
    'B4': 493.88
}

# メロディの定義（音名, 長さ）
melody = [
    ('C4', 0.3),
    ('E4', 0.3),
    ('G4', 0.3),
    ('C5', 0.3),
    ('B4', 0.3),
    ('G4', 0.3),
    ('E4', 0.3),
    ('C4', 0.3)
]

print("矩形波メロディを生成中...")

# メロディの再生
for note, duration in melody:
    sound = generate_square_wave(NOTES[note], duration)
    sound.play()
    pygame.time.wait(int(duration * 1000))  # ミリ秒単位で待機

print("再生完了！") 