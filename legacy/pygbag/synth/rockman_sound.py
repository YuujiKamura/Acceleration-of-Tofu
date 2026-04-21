import pygame
import numpy as np
from array import array
import time

pygame.mixer.init(frequency=44100, size=-16, channels=1)

def generate_sweep_sound(start_freq, end_freq, duration, volume=0.5):
    """周波数が変化する効果音を生成"""
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    for i in range(len(samples)):
        # 時間に応じて周波数を変化
        t = i / sample_rate
        freq = start_freq + (end_freq - start_freq) * (t / duration)
        period = sample_rate / freq
        
        # 矩形波生成
        if (i % int(period)) < (int(period) / 4):  # デューティ比25%
            samples[i] = int(32767 * volume)
        else:
            samples[i] = int(-32767 * volume)
    
    return pygame.mixer.Sound(samples)

def generate_buster_sound():
    """バスター（ショット）音を生成"""
    duration = 0.15
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    freq = 1200  # 基本周波数
    volume = 0.7
    
    for i in range(len(samples)):
        t = i / sample_rate
        # 時間経過で音量を減衰
        decay = np.exp(-t * 8)
        # 周波数を少し上昇させる
        current_freq = freq * (1 + t * 2)
        period = sample_rate / current_freq
        
        if (i % int(period)) < (int(period) / 2):
            samples[i] = int(32767 * volume * decay)
        else:
            samples[i] = int(-32767 * volume * decay)
    
    return pygame.mixer.Sound(samples)

# 効果音の生成
jump_sound = generate_sweep_sound(400, 1200, 0.15, volume=0.4)  # ジャンプ音
land_sound = generate_sweep_sound(300, 150, 0.1, volume=0.5)    # 着地音
buster_sound = generate_buster_sound()                          # バスター音

print("ロックマン風効果音のデモ開始...")

# ジャンプ→バスター→着地のデモ
for _ in range(2):
    print("ジャンプ！")
    jump_sound.play()
    time.sleep(0.3)
    
    print("バスター発射！")
    buster_sound.play()
    time.sleep(0.3)
    
    print("着地！")
    land_sound.play()
    time.sleep(0.5)

print("\nデモ完了！") 