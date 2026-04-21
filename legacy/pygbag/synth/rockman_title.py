import pygame
import numpy as np
from array import array
import wave

pygame.mixer.init(frequency=44100, size=-16, channels=1)

# BGMの基本設定
BPM = 145
BEATS_PER_BAR = 4  # 4/4拍子
SAMPLE_RATE = 44100

def bpm_to_sec(beats):
    """拍数を秒数に変換"""
    return beats * (60.0 / BPM)

def bar_to_sec(bars):
    """小節数を秒数に変換"""
    return bpm_to_sec(bars * BEATS_PER_BAR)

def save_samples_to_wav(samples, filename, sample_rate=44100):
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())

def generate_note(freq, duration, volume=0.5, duty=0.25):
    """単音を生成"""
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    period = sample_rate / freq
    for i in range(len(samples)):
        if (i % int(period)) < (int(period) * duty):
            samples[i] = int(32767 * volume)
        else:
            samples[i] = int(-32767 * volume)
    
    return samples

def generate_drum_hit(freq, duration, volume=0.7):
    """ドラム音を生成（急速な減衰付き）"""
    sample_rate = 44100
    samples = array('h', [0] * int(sample_rate * duration))
    
    period = sample_rate / freq
    for i in range(len(samples)):
        t = i / sample_rate
        # 急速な減衰
        decay = np.exp(-t * 30)
        if (i % int(period)) < (int(period) * 0.5):
            samples[i] = int(32767 * volume * decay)
        else:
            samples[i] = int(-32767 * volume * decay)
    
    return samples

def mix_samples(*sample_arrays):
    """複数の音をミックス"""
    max_length = max(len(arr) for arr in sample_arrays)
    mixed = array('h', [0] * max_length)
    
    for samples in sample_arrays:
        for i in range(len(samples)):
            mixed[i] = max(min(mixed[i] + samples[i], 32767), -32767)
    
    return mixed

def generate_rockman_title():
    """ロックマンタイトルBGMを生成"""
    total_bars = 8  # 全8小節
    total_duration = bar_to_sec(total_bars)
    samples = array('h', [0] * int(SAMPLE_RATE * total_duration))
    
    # 音階の周波数（オクターブを追加）
    notes = {
        'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61,
        'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
        'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
        'G4': 392.00, 'A4': 440.00, 'B4': 493.88, 'C5': 523.25,
        'D5': 587.33, 'E5': 659.26  # E5を追加
    }
    
    # イントロ部分（2小節）
    intro_melody = [
        # 1小節目前半: テッテレテッテレ（8分音符）
        (notes['E4'], bar_to_sec(0), bpm_to_sec(0.25)),          # テッ
        (notes['G4'], bar_to_sec(0) + bpm_to_sec(0.25), bpm_to_sec(0.25)),  # テ
        (notes['A4'], bar_to_sec(0) + bpm_to_sec(0.5), bpm_to_sec(0.25)),   # レ
        
        (notes['E4'], bar_to_sec(0) + bpm_to_sec(1.0), bpm_to_sec(0.25)),   # テッ
        (notes['G4'], bar_to_sec(0) + bpm_to_sec(1.25), bpm_to_sec(0.25)),  # テ
        (notes['A4'], bar_to_sec(0) + bpm_to_sec(1.5), bpm_to_sec(0.25)),   # レ
        
        # 1小節目後半: てってってって（16分音符）
        (notes['E4'], bar_to_sec(0) + bpm_to_sec(2.0), bpm_to_sec(0.125)),   # て
        (notes['G4'], bar_to_sec(0) + bpm_to_sec(2.25), bpm_to_sec(0.125)),  # っ
        (notes['E4'], bar_to_sec(0) + bpm_to_sec(2.5), bpm_to_sec(0.125)),   # て
        (notes['G4'], bar_to_sec(0) + bpm_to_sec(2.75), bpm_to_sec(0.125)),  # っ
        (notes['E4'], bar_to_sec(0) + bpm_to_sec(3.0), bpm_to_sec(0.125)),   # て
        (notes['G4'], bar_to_sec(0) + bpm_to_sec(3.25), bpm_to_sec(0.125)),  # っ
        (notes['E4'], bar_to_sec(0) + bpm_to_sec(3.5), bpm_to_sec(0.125)),   # て
        (notes['G4'], bar_to_sec(0) + bpm_to_sec(3.75), bpm_to_sec(0.125)),  # っ
        
        # 2小節目前半: テケテケテケテケ（16分音符）
        (notes['A4'], bar_to_sec(1), bpm_to_sec(0.125)),          # テ
        (notes['C5'], bar_to_sec(1) + bpm_to_sec(0.25), bpm_to_sec(0.125)),  # ケ
        (notes['A4'], bar_to_sec(1) + bpm_to_sec(0.5), bpm_to_sec(0.125)),   # テ
        (notes['C5'], bar_to_sec(1) + bpm_to_sec(0.75), bpm_to_sec(0.125)),  # ケ
        (notes['A4'], bar_to_sec(1) + bpm_to_sec(1.0), bpm_to_sec(0.125)),   # テ
        (notes['C5'], bar_to_sec(1) + bpm_to_sec(1.25), bpm_to_sec(0.125)),  # ケ
        (notes['A4'], bar_to_sec(1) + bpm_to_sec(1.5), bpm_to_sec(0.125)),   # テ
        (notes['C5'], bar_to_sec(1) + bpm_to_sec(1.75), bpm_to_sec(0.125)),  # ケ
        
        # 2小節目後半: デーン（長め）
        (notes['E5'], bar_to_sec(1) + bpm_to_sec(2.0), bpm_to_sec(2.0)),     # デーン
    ]
    
    # メインメロディ（6小節）
    main_melody = []
    # 最初のフレーズ（2小節）
    phrase1 = [
        (notes['C4'], bar_to_sec(2), bpm_to_sec(1)),
        (notes['E4'], bar_to_sec(2) + bpm_to_sec(1), bpm_to_sec(1)),
        (notes['G4'], bar_to_sec(2) + bpm_to_sec(2), bpm_to_sec(1)),
        (notes['C5'], bar_to_sec(2) + bpm_to_sec(3), bpm_to_sec(1)),
        (notes['B4'], bar_to_sec(3), bpm_to_sec(1)),
        (notes['G4'], bar_to_sec(3) + bpm_to_sec(1), bpm_to_sec(1)),
        (notes['A4'], bar_to_sec(3) + bpm_to_sec(2), bpm_to_sec(1)),
        (notes['F4'], bar_to_sec(3) + bpm_to_sec(3), bpm_to_sec(1)),
    ]
    main_melody.extend(phrase1)
    
    # 2番目のフレーズ（2小節）
    phrase2 = [
        (notes['G4'], bar_to_sec(4), bpm_to_sec(2)),
        (notes['E4'], bar_to_sec(4) + bpm_to_sec(2), bpm_to_sec(2)),
        (notes['C4'], bar_to_sec(5), bpm_to_sec(1)),
        (notes['D4'], bar_to_sec(5) + bpm_to_sec(1), bpm_to_sec(1)),
        (notes['E4'], bar_to_sec(5) + bpm_to_sec(2), bpm_to_sec(2)),
    ]
    main_melody.extend(phrase2)
    
    # 最後のフレーズ（2小節）
    phrase3 = [
        (notes['C5'], bar_to_sec(6), bpm_to_sec(2)),
        (notes['B4'], bar_to_sec(6) + bpm_to_sec(2), bpm_to_sec(1)),
        (notes['G4'], bar_to_sec(6) + bpm_to_sec(3), bpm_to_sec(1)),
        (notes['A4'], bar_to_sec(7), bpm_to_sec(2)),
        (notes['G4'], bar_to_sec(7) + bpm_to_sec(2), bpm_to_sec(2)),
    ]
    main_melody.extend(phrase3)
    
    # ベース音パターン（8分音符で刻む）
    bass_notes = []
    for bar in range(2, 8):  # イントロ2小節後から開始
        for beat in range(BEATS_PER_BAR * 2):  # 8分音符なので1小節を8等分
            time = bar_to_sec(bar) + bpm_to_sec(beat/2)
            if beat % 2 == 0:
                bass_notes.append((notes['C3'], time, bpm_to_sec(0.4)))
            else:
                bass_notes.append((notes['G3'], time, bpm_to_sec(0.4)))
    
    # ドラムパターン
    drum_pattern = []
    for bar in range(2, 8):  # イントロ2小節後から開始
        base_time = bar_to_sec(bar)
        # 1小節中の4拍
        for beat in range(BEATS_PER_BAR):
            time = base_time + bpm_to_sec(beat)
            if beat % 2 == 0:
                # キック（1,3拍目）
                drum_pattern.append((50, time, bpm_to_sec(0.25)))
            else:
                # スネア（2,4拍目）
                drum_pattern.append((150, time, bpm_to_sec(0.25)))
            # 8分音符のハイハット
            if beat < BEATS_PER_BAR - 1:  # 最後の拍以外
                drum_pattern.append((300, time + bpm_to_sec(0.5), bpm_to_sec(0.25)))
    
    # 音を生成してミックス
    melody_samples = array('h', [0] * len(samples))
    bass_samples = array('h', [0] * len(samples))
    drum_samples = array('h', [0] * len(samples))
    
    # イントロ部分を生成
    for freq, start, duration in intro_melody:
        note = generate_note(freq, duration, volume=0.4)
        start_idx = int(start * SAMPLE_RATE)
        for i in range(len(note)):
            if start_idx + i < len(melody_samples):
                melody_samples[start_idx + i] += note[i]
    
    # メインメロディを生成
    for freq, start, duration in main_melody:
        note = generate_note(freq, duration, volume=0.3)
        start_idx = int(start * SAMPLE_RATE)
        for i in range(len(note)):
            if start_idx + i < len(melody_samples):
                melody_samples[start_idx + i] += note[i]
    
    # ベース音を生成（太い音色で）
    for freq, start, duration in bass_notes:
        note = generate_note(freq, duration, volume=0.35, duty=0.5)
        start_idx = int(start * SAMPLE_RATE)
        for i in range(len(note)):
            if start_idx + i < len(bass_samples):
                bass_samples[start_idx + i] += note[i]
    
    # ドラム音を生成
    for freq, start, duration in drum_pattern:
        drum = generate_drum_hit(freq, duration, volume=0.4)
        start_idx = int(start * SAMPLE_RATE)
        for i in range(len(drum)):
            if start_idx + i < len(drum_samples):
                drum_samples[start_idx + i] += drum[i]
    
    # 全パートをミックス
    final_samples = mix_samples(melody_samples, bass_samples, drum_samples)
    return final_samples

# BGMを生成して保存
print("ロックマンタイトルBGMを生成中...")
print(f"BPM: {BPM}, 小節数: 8小節")
bgm_samples = generate_rockman_title()
save_samples_to_wav(bgm_samples, "assets/sounds/rockman_title.wav")
print("保存完了: rockman_title.wav") 