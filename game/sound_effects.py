import pygame
import numpy as np
from pathlib import Path

# 効果音ディレクトリ
sfx_dir = Path("sfx")
sfx_dir.mkdir(exist_ok=True)

# 効果音キャッシュ
sound_cache = {}

def create_sound_effect(effect_type, volume=0.7):
    """8ビット風の効果音を生成する
    effect_type: 効果音の種類 ('dash', 'shot', 'hit', 'menu_move', 'menu_select')
    volume: 音量 (0.0〜1.0)
    """
    sample_rate = 44100
    
    if effect_type == "dash":
        # ダッシュ音（高速上昇する短い音）
        duration = 0.15
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 周波数（急速に上昇）
        freq_start = 200
        freq_end = 800
        freq = np.exp(np.linspace(np.log(freq_start), np.log(freq_end), len(t)))
        
        # 矩形波生成
        wave = np.sign(np.sin(2 * np.pi * np.cumsum(freq) / sample_rate) + 0.5)
        
        # エンベロープ（急速な立ち上がりと減衰）
        envelope = np.exp(-15 * t)
        wave = wave * envelope * volume
        
    elif effect_type == "shot":
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
        
    elif effect_type == "menu_move":
        # メニュー移動音（短い高音のビープ）
        duration = 0.05
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 単純な矩形波
        freq = 1200
        wave = np.sign(np.sin(2 * np.pi * freq * t) + 0.5)
        
        # シンプルなエンベロープ
        envelope = np.exp(-30 * t)
        wave = wave * envelope * volume
        
    elif effect_type == "menu_select":
        # 選択決定音（ピンポン風の2音）
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

def get_sound(effect_type, force_new=False):
    """効果音を取得（キャッシュがあればそれを使用）"""
    global sound_cache
    
    if force_new or effect_type not in sound_cache:
        sound_cache[effect_type] = create_sound_effect(effect_type)
    
    return sound_cache[effect_type]

def play_sound(effect_type, volume=0.7):
    """効果音を再生"""
    sound = get_sound(effect_type)
    if sound:
        sound.set_volume(volume)
        sound.play()

# 初期化関数
def initialize_sounds():
    """全効果音を事前に生成してキャッシュ"""
    effects = ["dash", "shot", "hit", "menu_move", "menu_select"]
    for effect in effects:
        get_sound(effect)
    
    print("効果音初期化完了")

# Pygameが初期化されている場合のみ実行
if pygame.mixer.get_init():
    initialize_sounds() 