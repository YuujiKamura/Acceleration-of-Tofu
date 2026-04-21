import pygame
import numpy as np
from array import array
import os
import wave

# assetsフォルダの作成
assets_dir = "assets/sounds"
os.makedirs(assets_dir, exist_ok=True)

pygame.mixer.init(frequency=44100, size=-16, channels=1)

def save_samples_to_wav(samples, filename, sample_rate=44100):
    """サンプルデータをWAVファイルとして保存"""
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # モノラル
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())

def generate_sweep_sound(start_freq, end_freq, duration, volume=0.5):
    """周波数が変化する効果音を生成"""
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    for i in range(len(samples)):
        t = i / sample_rate
        freq = start_freq + (end_freq - start_freq) * (t / duration)
        period = sample_rate / freq
        
        if (i % int(period)) < (int(period) / 4):
            samples[i] = int(32767 * volume)
        else:
            samples[i] = int(-32767 * volume)
    
    return samples

def generate_buster_sound():
    """バスター（ショット）音を生成"""
    duration = 0.15
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    freq = 1200
    volume = 0.7
    
    for i in range(len(samples)):
        t = i / sample_rate
        decay = np.exp(-t * 8)
        current_freq = freq * (1 + t * 2)
        period = sample_rate / current_freq
        
        if (i % int(period)) < (int(period) / 2):
            samples[i] = int(32767 * volume * decay)
        else:
            samples[i] = int(-32767 * volume * decay)
    
    return samples

def generate_damage_sound():
    """ダメージ音を生成（うねうねした下降音）"""
    duration = 0.3
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    base_freq = 800
    volume = 0.7
    
    for i in range(len(samples)):
        t = i / sample_rate
        # 基本周波数を下降させる
        current_freq = base_freq * (1 - t * 0.7)
        # うねり（ビブラート）を加える
        vibrato = np.sin(2 * np.pi * 30 * t) * 50
        period = sample_rate / (current_freq + vibrato)
        
        # 時間経過で音量を減衰
        decay = np.exp(-t * 4)
        
        if (i % int(period)) < (int(period) / 2):
            samples[i] = int(32767 * volume * decay)
        else:
            samples[i] = int(-32767 * volume * decay)
    
    return samples

def generate_1up_sound():
    """1UP音を生成（上昇する短い音の連続）"""
    duration = 0.4
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    volume = 0.6
    notes = [(600, 0.1), (800, 0.1), (1000, 0.1), (1200, 0.1)]
    
    for note_freq, note_duration in notes:
        start_idx = int(sample_rate * notes.index((note_freq, note_duration)) * note_duration)
        end_idx = int(start_idx + sample_rate * note_duration)
        
        for i in range(start_idx, min(end_idx, len(samples))):
            t = (i - start_idx) / sample_rate
            period = sample_rate / note_freq
            
            if (i % int(period)) < (int(period) / 4):
                samples[i] = int(32767 * volume)
            else:
                samples[i] = int(-32767 * volume)
    
    return samples

def generate_item_sound():
    """アイテム取得音を生成（短い上昇音）"""
    duration = 0.15
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    start_freq = 500
    end_freq = 1300
    volume = 0.5
    
    for i in range(len(samples)):
        t = i / sample_rate
        # 指数関数的な周波数上昇
        freq = start_freq + (end_freq - start_freq) * (t / duration) ** 2
        period = sample_rate / freq
        
        # 時間経過で音量をやや減衰
        decay = 1 - (t / duration) * 0.3
        
        if (i % int(period)) < (int(period) / 3):
            samples[i] = int(32767 * volume * decay)
        else:
            samples[i] = int(-32767 * volume * decay)
    
    return samples

def generate_charge_sound():
    """チャージ音を生成（徐々に上昇する音）"""
    duration = 1.0
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    base_freq = 300
    volume = 0.5
    
    for i in range(len(samples)):
        t = i / sample_rate
        # 周波数を徐々に上昇させる
        freq = base_freq + (t ** 2) * 1000
        # うねりを加える（チャージ感を出す）
        wobble = np.sin(2 * np.pi * 30 * t) * (t * 100)
        period = sample_rate / (freq + wobble)
        
        # 音量も徐々に大きくする
        volume_mod = 0.3 + (t ** 0.5) * 0.7
        
        if (i % int(period)) < (int(period) / 4):
            samples[i] = int(32767 * volume * volume_mod)
        else:
            samples[i] = int(-32767 * volume * volume_mod)
    
    return samples

def generate_stage_clear():
    """ステージクリア音を生成（ファンファーレ）"""
    duration = 1.5
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    # ファンファーレの音階とタイミング
    notes = [
        (400, 0.0, 0.2),   # ド
        (500, 0.2, 0.2),   # ミ
        (600, 0.4, 0.2),   # ソ
        (800, 0.6, 0.9)    # ドー（長め）
    ]
    
    volume = 0.6
    for freq, start, note_duration in notes:
        start_idx = int(start * sample_rate)
        end_idx = int((start + note_duration) * sample_rate)
        
        for i in range(start_idx, min(end_idx, len(samples))):
            t = (i - start_idx) / sample_rate
            # ビブラートを加える
            vibrato = np.sin(2 * np.pi * 8 * t) * 20
            period = sample_rate / (freq + vibrato)
            
            # 音の減衰
            decay = 1.0 if t < note_duration * 0.8 else 1.0 - ((t - note_duration * 0.8) / (note_duration * 0.2))
            
            if (i % int(period)) < (int(period) / 3):
                samples[i] = int(32767 * volume * decay)
            else:
                samples[i] = int(-32767 * volume * decay)
    
    return samples

def generate_boss_appear():
    """ボス登場音を生成（不気味な下降音）"""
    duration = 1.2
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    volume = 0.7
    base_freqs = [800, 600, 400, 200]  # 段階的に下降
    
    for i in range(len(samples)):
        t = i / sample_rate
        section = int(t * 4)  # 4段階に分ける
        if section >= len(base_freqs):
            section = len(base_freqs) - 1
            
        freq = base_freqs[section]
        # 不気味な揺らぎを加える
        wobble = np.sin(2 * np.pi * 15 * t) * 30
        period = sample_rate / (freq + wobble)
        
        # パルス幅を変調（不気味さを増す）
        duty = 0.3 + np.sin(2 * np.pi * 2 * t) * 0.1
        
        if (i % int(period)) < (int(period) * duty):
            samples[i] = int(32767 * volume)
        else:
            samples[i] = int(-32767 * volume)
    
    return samples

# 効果音の生成と保存
print("効果音ファイルを生成中...")

# 基本アクション音
jump_samples = generate_sweep_sound(400, 1200, 0.15, volume=0.4)
save_samples_to_wav(jump_samples, f"{assets_dir}/jump.wav")
print("保存完了: jump.wav")

land_samples = generate_sweep_sound(300, 150, 0.1, volume=0.5)
save_samples_to_wav(land_samples, f"{assets_dir}/land.wav")
print("保存完了: land.wav")

buster_samples = generate_buster_sound()
save_samples_to_wav(buster_samples, f"{assets_dir}/buster.wav")
print("保存完了: buster.wav")

# イベント音
damage_samples = generate_damage_sound()
save_samples_to_wav(damage_samples, f"{assets_dir}/damage.wav")
print("保存完了: damage.wav")

oneup_samples = generate_1up_sound()
save_samples_to_wav(oneup_samples, f"{assets_dir}/1up.wav")
print("保存完了: 1up.wav")

item_samples = generate_item_sound()
save_samples_to_wav(item_samples, f"{assets_dir}/item.wav")
print("保存完了: item.wav")

# 特殊効果音
charge_samples = generate_charge_sound()
save_samples_to_wav(charge_samples, f"{assets_dir}/charge.wav")
print("保存完了: charge.wav")

clear_samples = generate_stage_clear()
save_samples_to_wav(clear_samples, f"{assets_dir}/stage_clear.wav")
print("保存完了: stage_clear.wav")

boss_samples = generate_boss_appear()
save_samples_to_wav(boss_samples, f"{assets_dir}/boss_appear.wav")
print("保存完了: boss_appear.wav")

print("\nすべての効果音を assets/sounds フォルダに保存しました！") 