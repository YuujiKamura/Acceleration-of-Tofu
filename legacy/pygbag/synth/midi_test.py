from midiutil import MIDIFile

# MIDIファイルの作成（1トラック）
midi = MIDIFile(1)

# トラックの初期化
track = 0
time = 0
midi.addTrackName(track, time, "Sample Track")
midi.addTempo(track, time, 120)

# メロディの定義（音程, 開始時間, 長さ）
melody = [
    (60, 0, 1),   # ド (C4)
    (64, 1, 1),   # ミ (E4)
    (67, 2, 1),   # ソ (G4)
    (72, 3, 1),   # ド (C5)
    (71, 4, 1),   # シ (B4)
    (67, 5, 1),   # ソ (G4)
    (64, 6, 1),   # ミ (E4)
    (60, 7, 1),   # ド (C4)
]

# メロディの追加
channel = 0
volume = 100
for pitch, t, duration in melody:
    midi.addNote(track, channel, pitch, t, duration, volume)

# ドラムパートの追加（チャンネル9は通常ドラム用）
drum_track = 0
drum_channel = 9
for t in range(0, 8, 2):
    # バスドラム
    midi.addNote(drum_track, drum_channel, 36, t, 1, volume)
    # スネア
    midi.addNote(drum_track, drum_channel, 38, t + 1, 1, volume)
    # ハイハット
    midi.addNote(drum_track, drum_channel, 42, t, 0.5, volume)
    midi.addNote(drum_track, drum_channel, 42, t + 0.5, 0.5, volume)
    midi.addNote(drum_track, drum_channel, 42, t + 1, 0.5, volume)
    midi.addNote(drum_track, drum_channel, 42, t + 1.5, 0.5, volume)

# MIDIファイルの保存
with open("output.mid", "wb") as output_file:
    midi.writeFile(output_file)

print("MIDIファイルを生成しました: output.mid") 