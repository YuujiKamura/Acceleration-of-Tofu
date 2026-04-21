#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import numpy as np
import os
from pathlib import Path

# Pygameの初期化
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

def create_sound_effect(effect_type, volume=0.7):
    """8ビット風の効果音を生成する
    effect_type: 効果音の種類
    volume: 音量 (0.0〜1.0)
    """
    sample_rate = 44100
    
    if effect_type == "shot":
        # ショット音（短い高周波音）
        duration = 0.2
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 2つの周波数を組み合わせる
        freq1, freq2 = (1000, 1500)
        wave1 = np.sign(np.sin(2 * np.pi * freq1 * t) + 0.5)
        wave2 = np.sign(np.sin(2 * np.pi * freq2 * t) + 0.5)
        wave = (wave1 * 0.7 + wave2 * 0.3)  # ミックス
        
        # エンベロープ
        envelope = np.exp(-20 * t)
        wave = wave * envelope * volume
        
    elif effect_type == "special":
        # 特殊攻撃音（より複雑な音）
        duration = 0.4
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 周波数変調
        freq_mod = 300 + 200 * np.sin(2 * np.pi * 5 * t)
        wave = np.sign(np.sin(2 * np.pi * np.cumsum(freq_mod) / sample_rate))
        
        # エンベロープ
        envelope = np.ones_like(t)
        envelope[:int(0.05 * sample_rate)] = np.linspace(0, 1, int(0.05 * sample_rate))
        envelope[int(0.05 * sample_rate):] = np.exp(-5 * (t[int(0.05 * sample_rate):] - t[int(0.05 * sample_rate)]))
        
        wave = wave * envelope * volume
        
    elif effect_type == "hit":
        # ヒット音（低音のインパクト音）
        duration = 0.3
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # ノイズをベースにした音
        noise = np.random.uniform(-1, 1, len(t))
        
        # 低周波の矩形波でフィルタリング
        carrier = np.sign(np.sin(2 * np.pi * 80 * t) + 0.5)
        wave = noise * carrier
        
        # エンベロープ
        envelope = np.exp(-10 * t)
        envelope[:int(0.01 * sample_rate)] = 1.0  # アタック部分
        
        wave = wave * envelope * volume
        
    elif effect_type == "shield":
        # シールド発動音（迫力のある低音）
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 複数の低周波数の組み合わせ
        freq_base = 150
        wave1 = np.sign(np.sin(2 * np.pi * freq_base * t) + 0.5)
        wave2 = np.sign(np.sin(2 * np.pi * (freq_base * 1.5) * t) + 0.5)
        
        # 時間経過とともに変化する周波数
        freq_sweep = np.exp(np.linspace(np.log(200), np.log(100), len(t)))
        wave3 = np.sign(np.sin(2 * np.pi * np.cumsum(freq_sweep) / sample_rate))
        
        # ミックス
        wave = (wave1 * 0.5 + wave2 * 0.3 + wave3 * 0.2)
        
        # より複雑なエンベロープ
        envelope = np.ones_like(t)
        attack_time = int(0.05 * sample_rate)
        envelope[:attack_time] = np.linspace(0, 1, attack_time)
        envelope[attack_time:] = np.exp(-3 * (t[attack_time:] - t[attack_time]))
        
        wave = wave * envelope * volume
        
    elif effect_type == "hyper":
        # ハイパーモード発動音（上昇する強力な音）
        duration = 0.6
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 上昇する周波数
        freq_sweep = np.exp(np.linspace(np.log(200), np.log(500), len(t)))
        wave1 = np.sign(np.sin(2 * np.pi * np.cumsum(freq_sweep) / sample_rate))
        
        # パルス波の混合
        freq_pulse = 300
        duty_cycle = 0.3
        wave2 = (np.sin(2 * np.pi * freq_pulse * t) > duty_cycle).astype(float) * 2 - 1
        
        # ノイズ成分
        noise = np.random.uniform(-0.3, 0.3, len(t))
        
        # 混合
        wave = (wave1 * 0.6 + wave2 * 0.3 + noise * 0.1)
        
        # エンベロープ
        envelope = np.ones_like(t)
        attack_time = int(0.1 * sample_rate)
        decay_start = int(0.4 * sample_rate)
        envelope[:attack_time] = np.linspace(0, 1, attack_time)
        envelope[decay_start:] = np.exp(-5 * (t[decay_start:] - t[decay_start]))
        
        wave = wave * envelope * volume
        
    elif effect_type == "menu":
        # メニュー選択音（ピンポン風の2音）
        duration = 0.2
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 2つの音を連続再生
        freq1, freq2 = 800, 1200
        wave1 = np.zeros_like(t)
        wave2 = np.zeros_like(t)
        
        # 前半と後半で異なる周波数
        half_point = len(t) // 2
        wave1[:half_point] = np.sign(np.sin(2 * np.pi * freq1 * t[:half_point]) + 0.5)
        wave2[half_point:] = np.sign(np.sin(2 * np.pi * freq2 * t[half_point:]) + 0.5)
        
        wave = wave1 + wave2
        
        # エンベロープ
        envelope = np.ones_like(t)
        envelope[:half_point] = np.exp(-10 * t[:half_point])
        envelope[half_point:] = np.exp(-10 * (t[half_point:] - t[half_point]))
        
        wave = wave * envelope * volume
    
    else:
        # デフォルト：短いビープ音
        duration = 0.1
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = np.sign(np.sin(2 * np.pi * 440 * t) + 0.5) * volume
    
    # 8ビット風エフェクト処理
    # 1. 波形を8ビットに量子化
    wave = np.round(wave * 127) / 127
    
    # 2. サンプリングレートを一時的に下げる
    target_rate = 22050
    resampled_len = int(len(wave) * target_rate / sample_rate)
    wave = np.interp(
        np.linspace(0, len(wave), resampled_len),
        np.arange(len(wave)),
        wave
    )
    wave = np.repeat(wave, sample_rate // target_rate)
    
    # ステレオ化
    wave = wave.astype(np.float32)
    stereo = np.zeros((len(wave), 2), dtype=np.float32)
    stereo[:, 0] = wave  # 左チャンネル
    stereo[:, 1] = wave  # 右チャンネル
    
    # -1.0～1.0の範囲にクリップ
    stereo = np.clip(stereo, -1.0, 1.0)
    
    # PyGame用のサウンドオブジェクトに変換
    try:
        sound = pygame.sndarray.make_sound(stereo)
        return sound
    except Exception as e:
        print(f"効果音生成エラー: {e}")
        return None

def save_sound(effect_type, filename):
    """効果音を生成してファイルに保存"""
    # 効果音データを直接生成
    sample_rate = 44100
    
    if effect_type == "shot":
        # ショット音（短い高周波音）
        duration = 0.2
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 2つの周波数を組み合わせる
        freq1, freq2 = (1000, 1500)
        wave1 = np.sign(np.sin(2 * np.pi * freq1 * t) + 0.5)
        wave2 = np.sign(np.sin(2 * np.pi * freq2 * t) + 0.5)
        wave = (wave1 * 0.7 + wave2 * 0.3)  # ミックス
        
        # エンベロープ
        envelope = np.exp(-20 * t)
        wave = wave * envelope * 0.7  # volume
        
    elif effect_type == "special":
        # 特殊攻撃音（より複雑な音）
        duration = 0.4
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 周波数変調
        freq_mod = 300 + 200 * np.sin(2 * np.pi * 5 * t)
        wave = np.sign(np.sin(2 * np.pi * np.cumsum(freq_mod) / sample_rate))
        
        # エンベロープ
        envelope = np.ones_like(t)
        envelope[:int(0.05 * sample_rate)] = np.linspace(0, 1, int(0.05 * sample_rate))
        envelope[int(0.05 * sample_rate):] = np.exp(-5 * (t[int(0.05 * sample_rate):] - t[int(0.05 * sample_rate)]))
        
        wave = wave * envelope * 0.7  # volume
        
    elif effect_type == "hit":
        # ヒット音（低音のインパクト音）
        duration = 0.3
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # ノイズをベースにした音
        noise = np.random.uniform(-1, 1, len(t))
        
        # 低周波の矩形波でフィルタリング
        carrier = np.sign(np.sin(2 * np.pi * 80 * t) + 0.5)
        wave = noise * carrier
        
        # エンベロープ
        envelope = np.exp(-10 * t)
        envelope[:int(0.01 * sample_rate)] = 1.0  # アタック部分
        
        wave = wave * envelope * 0.7  # volume
        
    elif effect_type == "shield":
        # シールド発動音（迫力のある低音）
        duration = 0.5
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 複数の低周波数の組み合わせ
        freq_base = 150
        wave1 = np.sign(np.sin(2 * np.pi * freq_base * t) + 0.5)
        wave2 = np.sign(np.sin(2 * np.pi * (freq_base * 1.5) * t) + 0.5)
        
        # 時間経過とともに変化する周波数
        freq_sweep = np.exp(np.linspace(np.log(200), np.log(100), len(t)))
        wave3 = np.sign(np.sin(2 * np.pi * np.cumsum(freq_sweep) / sample_rate))
        
        # ミックス
        wave = (wave1 * 0.5 + wave2 * 0.3 + wave3 * 0.2)
        
        # より複雑なエンベロープ
        envelope = np.ones_like(t)
        attack_time = int(0.05 * sample_rate)
        envelope[:attack_time] = np.linspace(0, 1, attack_time)
        envelope[attack_time:] = np.exp(-3 * (t[attack_time:] - t[attack_time]))
        
        wave = wave * envelope * 0.7  # volume
        
    elif effect_type == "hyper":
        # ハイパーモード発動音（上昇する強力な音）
        duration = 0.6
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 上昇する周波数
        freq_sweep = np.exp(np.linspace(np.log(200), np.log(500), len(t)))
        wave1 = np.sign(np.sin(2 * np.pi * np.cumsum(freq_sweep) / sample_rate))
        
        # パルス波の混合
        freq_pulse = 300
        duty_cycle = 0.3
        wave2 = (np.sin(2 * np.pi * freq_pulse * t) > duty_cycle).astype(float) * 2 - 1
        
        # ノイズ成分
        noise = np.random.uniform(-0.3, 0.3, len(t))
        
        # 混合
        wave = (wave1 * 0.6 + wave2 * 0.3 + noise * 0.1)
        
        # エンベロープ
        envelope = np.ones_like(t)
        attack_time = int(0.1 * sample_rate)
        decay_start = int(0.4 * sample_rate)
        envelope[:attack_time] = np.linspace(0, 1, attack_time)
        envelope[decay_start:] = np.exp(-5 * (t[decay_start:] - t[decay_start]))
        
        wave = wave * envelope * 0.7  # volume
        
    elif effect_type == "menu":
        # メニュー選択音（ピンポン風の2音）
        duration = 0.2
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 2つの音を連続再生
        freq1, freq2 = 800, 1200
        wave1 = np.zeros_like(t)
        wave2 = np.zeros_like(t)
        
        # 前半と後半で異なる周波数
        half_point = len(t) // 2
        wave1[:half_point] = np.sign(np.sin(2 * np.pi * freq1 * t[:half_point]) + 0.5)
        wave2[half_point:] = np.sign(np.sin(2 * np.pi * freq2 * t[half_point:]) + 0.5)
        
        wave = wave1 + wave2
        
        # エンベロープ
        envelope = np.ones_like(t)
        envelope[:half_point] = np.exp(-10 * t[:half_point])
        envelope[half_point:] = np.exp(-10 * (t[half_point:] - t[half_point]))
        
        wave = wave * envelope * 0.7  # volume
    
    else:
        # デフォルト：短いビープ音
        duration = 0.1
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = np.sign(np.sin(2 * np.pi * 440 * t) + 0.5) * 0.7
    
    # 8ビット風エフェクト処理
    # 1. 波形を8ビットに量子化
    wave = np.round(wave * 127) / 127
    
    # 2. サンプリングレートを一時的に下げる
    target_rate = 22050
    resampled_len = int(len(wave) * target_rate / sample_rate)
    wave = np.interp(
        np.linspace(0, len(wave), resampled_len),
        np.arange(len(wave)),
        wave
    )
    wave = np.repeat(wave, sample_rate // target_rate)
    
    # -1.0～1.0の範囲にクリップ
    wave = np.clip(wave, -1.0, 1.0)
    
    # WAVファイルとして保存
    try:
        # 既存のファイルを一旦削除
        if os.path.exists(filename):
            os.remove(filename)
        
        # 16ビット整数に変換
        wave_int16 = (wave * 32767).astype(np.int16)
        
        # ステレオ化
        stereo = np.zeros((len(wave_int16), 2), dtype=np.int16)
        stereo[:, 0] = wave_int16  # 左チャンネル
        stereo[:, 1] = wave_int16  # 右チャンネル
        
        # WAVファイルとして保存
        from scipy.io import wavfile
        wavfile.write(filename, sample_rate, stereo)
        
        print(f"効果音を保存しました: {filename}")
        return True
    except Exception as e:
        print(f"効果音の保存に失敗しました ({filename}): {e}")
        return False

def main():
    """全ての効果音を生成して保存"""
    print("効果音ファイルを生成しています...")
    
    # 音声ファイルの保存先
    sound_dir = Path("assets/sounds")
    os.makedirs(sound_dir, exist_ok=True)
    
    # 生成する効果音の定義
    effects = {
        "shot": "shot.wav",
        "special": "special.wav", 
        "hit": "hit.wav",
        "shield": "shield.wav",
        "hyper": "hyper.wav",
        "menu": "menu.wav"
    }
    
    # 各効果音を生成して保存
    success_count = 0
    for effect_type, filename in effects.items():
        filepath = sound_dir / filename
        if save_sound(effect_type, str(filepath)):
            success_count += 1
    
    print(f"効果音生成完了: {success_count}/{len(effects)}個の効果音を生成しました")

if __name__ == "__main__":
    main() 