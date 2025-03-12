import pysynth
import pysynth_b
import pysynth_s
import pysynth_e
import wave
import numpy as np

# メインメロディ
melody1 = [
    ('c4', 4), ('e4', 4), ('g4', 4), ('c5', 4),
    ('a4', 4), ('g4', 4), ('f4', 4), ('e4', 4),
]

# サブメロディ（少し高い音で演奏）
melody2 = [
    ('c5', 4), ('g4', 4), ('e4', 4), ('c4', 4),
    ('f4', 4), ('e4', 4), ('d4', 4), ('c4', 4),
]

# ドラムパターン
# バスドラム（低い音）とスネア（高い音）を模倣
drums = [
    ('c2', 16), ('r', 16), ('c2', 16), ('r', 16),  # バスドラム
    ('e3', 16), ('r', 16), ('r', 16), ('r', 16),   # スネア
    ('c2', 16), ('r', 16), ('c2', 16), ('r', 16),  # バスドラム
    ('e3', 16), ('e3', 32), ('e3', 32), ('r', 16), # スネア
]

# ハイハット的なパターン
hihat = [
    ('a5', 16), ('r', 16), ('a5', 16), ('r', 16),
    ('a5', 16), ('r', 16), ('a5', 16), ('r', 16),
] * 2  # パターンを2回繰り返し

# 各音源でメロディを生成
print("フルート/オルガン音源で生成中...")
pysynth.make_wav(melody1, fn="melody1_flute.wav", bpm=120, boost=1.5)
pysynth.make_wav(melody2, fn="melody2_flute.wav", bpm=120, boost=1.5)

print("\nピアノ音源で生成中...")
pysynth_b.make_wav(melody1, fn="melody1_piano.wav", bpm=120, boost=1.5)
pysynth_b.make_wav(melody2, fn="melody2_piano.wav", bpm=120, boost=1.5)

print("\n弦楽器音源で生成中...")
pysynth_s.make_wav(melody1, fn="melody1_string.wav", bpm=120, boost=1.5)
pysynth_s.make_wav(melody2, fn="melody2_string.wav", bpm=120, boost=1.5)

print("\nFMピアノ音源で生成中...")
pysynth_e.make_wav(melody1, fn="melody1_fm.wav", bpm=120, boost=1.5)
pysynth_e.make_wav(melody2, fn="melody2_fm.wav", bpm=120, boost=1.5)

print("\nドラムパターン生成中...")
# スタッカート（短い音）で打楽器っぽく
pysynth_s.make_wav(drums, fn="drums.wav", bpm=120, boost=2.0, pause=0.1)
pysynth_s.make_wav(hihat, fn="hihat.wav", bpm=120, boost=1.0, pause=0.1)

def mix_wav_files(file1, file2, output_file, vol1=0.7, vol2=0.7):
    # 1つ目のファイルを読み込み
    with wave.open(file1, 'rb') as wav1:
        params1 = wav1.getparams()
        frames1 = wav1.readframes(params1.nframes)
        audio1 = np.frombuffer(frames1, dtype=np.int16).astype(np.float32)
    
    # 2つ目のファイルを読み込み
    with wave.open(file2, 'rb') as wav2:
        params2 = wav2.getparams()
        frames2 = wav2.readframes(params2.nframes)
        audio2 = np.frombuffer(frames2, dtype=np.int16).astype(np.float32)
    
    # 両方の音源を同じ長さにする
    max_length = max(len(audio1), len(audio2))
    if len(audio1) < max_length:
        audio1 = np.pad(audio1, (0, max_length - len(audio1)))
    if len(audio2) < max_length:
        audio2 = np.pad(audio2, (0, max_length - len(audio2)))
    
    # ステレオ配列を作成
    stereo = np.zeros((max_length, 2), dtype=np.float32)
    
    # 左右のチャンネルに音を配置（音量を適度に調整）
    stereo[:, 0] = audio1 * vol1  # 左チャンネル
    stereo[:, 1] = audio2 * vol2  # 右チャンネル
    
    # int16に変換（クリッピング防止）
    stereo = np.clip(stereo, -32768, 32767).astype(np.int16)
    
    # ステレオWAVファイルとして保存
    with wave.open(output_file, 'wb') as wav_out:
        wav_out.setnchannels(2)
        wav_out.setsampwidth(2)
        wav_out.setframerate(44100)
        wav_out.writeframes(stereo.tobytes())

def mix_multiple_wav(files, output_file, volumes):
    """複数のWAVファイルをミックス"""
    audio_data = []
    max_length = 0
    
    # すべてのファイルを読み込み
    for file in files:
        with wave.open(file, 'rb') as wav:
            params = wav.getparams()
            frames = wav.readframes(params.nframes)
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
            audio_data.append(audio)
            max_length = max(max_length, len(audio))
    
    # すべての音源を同じ長さにする
    for i in range(len(audio_data)):
        if len(audio_data[i]) < max_length:
            audio_data[i] = np.pad(audio_data[i], (0, max_length - len(audio_data[i])))
    
    # 音源をミックス
    mixed = np.zeros(max_length, dtype=np.float32)
    for audio, vol in zip(audio_data, volumes):
        mixed += audio * vol
    
    # クリッピング防止
    mixed = np.clip(mixed, -32768, 32767).astype(np.int16)
    
    # WAVファイルとして保存
    with wave.open(output_file, 'wb') as wav_out:
        wav_out.setnchannels(1)
        wav_out.setsampwidth(2)
        wav_out.setframerate(44100)
        wav_out.writeframes(mixed.tobytes())

# 各音源のステレオミックスを作成
print("\nステレオミックスを作成中...")
mix_wav_files('melody1_flute.wav', 'melody2_flute.wav', 'stereo_mix_flute.wav')
mix_wav_files('melody1_piano.wav', 'melody2_piano.wav', 'stereo_mix_piano.wav')
mix_wav_files('melody1_string.wav', 'melody2_string.wav', 'stereo_mix_string.wav')
mix_wav_files('melody1_fm.wav', 'melody2_fm.wav', 'stereo_mix_fm.wav')

# ドラムパターンをミックス
print("\nドラムパターンをミックス中...")
mix_multiple_wav(['drums.wav', 'hihat.wav'], 'drums_mixed.wav', [0.8, 0.4])

# メロディとドラムをミックスした完全版を作成
print("\n最終ミックスを作成中...")
for instrument in ['flute', 'piano', 'string', 'fm']:
    mix_wav_files(f'stereo_mix_{instrument}.wav', 'drums_mixed.wav', 
                 f'final_mix_{instrument}.wav', 0.7, 0.5) 