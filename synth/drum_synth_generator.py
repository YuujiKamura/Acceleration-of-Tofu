import pysynth
import os
from pathlib import Path

# 音声ファイルを保存するディレクトリを作成
SAMPLES_DIR = Path("drum_samples")
SAMPLES_DIR.mkdir(exist_ok=True)

# より豊かな音色定義（音域調整版）
drum_patterns = {
    "bass_exp": [
        # さらに低い基音
        ('a0', 8),      # 超低音基音
        ('a1', 8),      # 1オクターブ上
        ('e1', 8),      # 5度上
        ('c#1', 8),     # 3度上
        # サブ低音レイヤー
        ('a0', 16),     # 基音重ね
        ('e1', 16),     # 5度重ね
        # アタック音（明瞭さ用）
        ('a3', 32),     # 高域アタック
        ('e3', 32),     # 5度アタック
        # 倍音成分
        ('a2', 16),     # 2オクターブ上
    ],
    "beam": [
        # メイン音色（より透明感のある音に）
        ('e6', 8),      # 基音
        ('e7', 8),      # 1オクターブ上
        ('b6', 8),      # 5度上
        ('g#6', 8),     # 3度上
        # クリアな高域強調
        ('e7', 16),     # 1オクターブ上（再度）
        ('b6', 16),     # 5度（再度）
        # 柔らかい低域
        ('e5', 32),     # 1オクターブ下
        ('b5', 32),     # 低い5度
        # クリアなフェードアウト
        ('c7', 32),
        ('g6', 32),
    ],
    "shield": [
        # メイン音色（より透明感を追加）
        ('c6', 8),      # 基音
        ('c7', 8),      # 1オクターブ上
        ('g6', 8),      # 5度上
        ('e6', 8),      # 3度上
        # クリアな高域
        ('c7', 16),     # 1オクターブ上（再度）
        ('g6', 16),     # 5度（再度）
        # 柔らかい低域サポート
        ('c5', 32),     # 1オクターブ下
        ('g5', 32),     # 低い5度
        # 透明感のあるフェードアウト
        ('e6', 32),
        ('b6', 32),
    ],
    "crystal": [        # 新規: 透き通るような音色
        ('e7', 4),      # 高い基音
        ('b6', 4),      # 5度下
        ('e6', 8),      # オクターブ下
        ('b6', 8),      # 5度
        ('e7', 16),     # 基音重ね
        ('b7', 32),     # 高い5度
        ('e6', 32),     # 低いオクターブ
    ],
    "piano_tone": [     # 新規: ピアノ的な音色
        ('c4', 4),      # 中央のC
        ('c5', 8),      # 1オクターブ上
        ('g4', 8),      # 5度上
        ('e4', 8),      # 3度上
        ('c3', 16),     # 1オクターブ下
        ('g3', 16),     # 低い5度
        ('c5', 32),     # 高いアタック
    ],
    "bell": [           # 新規: ベル的な透明な音色
        ('a6', 4),      # 高い基音
        ('e7', 8),      # 5度上
        ('a7', 16),     # オクターブ上
        ('c7', 16),     # 短3度上
        ('e6', 32),     # オクターブ下
        ('b6', 32),     # 5度
    ]
}

def generate_drum_samples():
    """ドラム音色のWAVファイルを生成"""
    print("高品質ドラム音源を生成中...")
    
    for sound_name, pattern in drum_patterns.items():
        output_file = SAMPLES_DIR / f"{sound_name}.wav"
        print(f"生成中: {output_file}")
        # 音質パラメータ調整
        pysynth.make_wav(
            pattern,
            fn=str(output_file),
            bpm=960,    # 高速テンポ（音の重なり用）
            boost=1.8,  # 音量ブースト増加
            repeat=3    # 音を3回重ねてより豊かに
        )

if __name__ == "__main__":
    generate_drum_samples()
    print("音源生成完了！") 