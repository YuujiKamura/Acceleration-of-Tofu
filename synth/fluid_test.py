import os
import urllib.request
import fluidsynth
import time
import numpy as np
import soundfile as sf

# SoundFontファイルのダウンロード
soundfont_url = "https://musical-artifacts.com/artifacts/files/general-user-gs-soundfont-v1.471.sf2"
soundfont_path = "general-user-gs.sf2"

if not os.path.exists(soundfont_path):
    print("SoundFontをダウンロード中...")
    urllib.request.urlretrieve(soundfont_url, soundfont_path)
    print("ダウンロード完了")

# FluidSynthの初期化
fs = fluidsynth.Synth()
fs.start()

# SoundFontのロード
sfid = fs.sfload(soundfont_path)
fs.program_select(0, sfid, 0, 0)

# メロディの定義（ノート番号, 時間（秒）, ベロシティ）
melody = [
    # ピアノパート（チャンネル0）
    (0, 60, 1.0, 100),  # ド
    (0, 64, 1.0, 100),  # ミ
    (0, 67, 1.0, 100),  # ソ
    (0, 72, 1.0, 100),  # ド（高）
]

# ドラムパート（チャンネル9は通常ドラム用）
drums = [
    # バスドラム
    (9, 36, 0.5, 100),
    (9, 36, 0.5, 100),
    # スネア
    (9, 38, 0.5, 100),
    (9, 38, 0.5, 100),
]

# 音楽の生成
print("音楽を生成中...")

# サンプリングレートとバッファサイズの設定
sample_rate = 44100
buffer_size = int(sample_rate * 8)  # 8秒分のバッファ
audio_buffer = np.zeros(buffer_size, dtype=np.float32)

# メロディの再生とキャプチャ
for channel, note, duration, velocity in melody:
    fs.noteon(channel, note, velocity)
    time.sleep(duration)
    fs.noteoff(channel, note)

# ドラムパートの再生
for channel, note, duration, velocity in drums:
    fs.noteon(channel, note, velocity)
    time.sleep(duration)
    fs.noteoff(channel, note)

# 音声データの保存
print("WAVファイルを保存中...")
sf.write('fluid_output.wav', audio_buffer, sample_rate)

# 後片付け
fs.delete()
print("完了！") 