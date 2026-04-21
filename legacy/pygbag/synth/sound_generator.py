import pygame
import numpy as np
import os

# 初期化
pygame.mixer.init(frequency=44100, size=-16, channels=2)
pygame.init()

# 保存先ディレクトリの確保
sound_dir = "assets/sounds"
os.makedirs(sound_dir, exist_ok=True)

def mono_to_stereo(mono_data):
    """モノラルデータをステレオに変換"""
    stereo_data = np.column_stack((mono_data, mono_data))
    return stereo_data

def generate_laser_sound():
    """レーザー音（ビーム武器用）を生成"""
    sample_rate = 44100
    duration = 0.2  # 秒
    frequency = 1000  # Hz
    
    # サイン波を使用
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # 周波数を上げていく
    freq = np.linspace(frequency, frequency * 3, len(t))
    # サイン波生成
    tone = np.sin(2 * np.pi * freq * t)
    # フェードアウト
    fade = np.linspace(1.0, 0.0, len(t))
    tone = tone * fade
    # 音量調整
    tone = (tone * 32767).astype(np.int16)
    
    # ステレオに変換
    stereo_tone = mono_to_stereo(tone)
    
    # バイト配列に変換
    byte_array = pygame.sndarray.make_sound(stereo_tone)
    return byte_array

def generate_special_sound():
    """スペシャル技の効果音を生成"""
    sample_rate = 44100
    duration = 0.6  # 秒
    
    # サイン波用の時間配列
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 複数の周波数を混ぜた音
    tone1 = np.sin(2 * np.pi * 880 * t)  # 高い音
    tone2 = np.sin(2 * np.pi * 440 * t)  # 中間の音
    tone3 = np.sin(2 * np.pi * 220 * t)  # 低い音
    
    # 時間に応じた重み付け
    w1 = np.linspace(0.1, 1.0, len(t))  # 徐々に大きく
    w2 = np.concatenate((np.linspace(0, 1, len(t)//2), np.linspace(1, 0, len(t)//2)))  # 上昇して下降
    w3 = np.linspace(1.0, 0.1, len(t))  # 徐々に小さく
    
    # 重み付けを適用
    tone = (tone1 * w1 + tone2 * w2 + tone3 * w3) / 3
    
    # ビブラート効果（揺らぎ）
    vibrato = np.sin(2 * np.pi * 8 * t) * 0.1
    tone = tone * (1 + vibrato)
    
    # 音量調整
    tone = (tone * 32767 * 0.5).astype(np.int16)
    
    # ステレオに変換
    stereo_tone = mono_to_stereo(tone)
    
    # バイト配列に変換
    byte_array = pygame.sndarray.make_sound(stereo_tone)
    return byte_array

def generate_hit_sound():
    """ヒット音を生成"""
    sample_rate = 44100
    duration = 0.15  # 秒
    
    # サイン波用の時間配列
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # ノイズ成分
    noise = np.random.uniform(-1, 1, len(t))
    
    # 減衰する正弦波
    decay = np.exp(-t * 30)
    tone = np.sin(2 * np.pi * 150 * t) * decay
    
    # ノイズと波形を合成
    mixed = tone * 0.7 + noise * 0.3 * decay
    
    # 音量調整
    mixed = (mixed * 32767 * 0.8).astype(np.int16)
    
    # ステレオに変換
    stereo_tone = mono_to_stereo(mixed)
    
    # バイト配列に変換
    byte_array = pygame.sndarray.make_sound(stereo_tone)
    return byte_array

def generate_shield_sound():
    """シールド音を生成"""
    sample_rate = 44100
    duration = 0.3  # 秒
    
    # サイン波用の時間配列
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 高い音から低い音への変化
    freq = np.linspace(1200, 300, len(t))
    tone = np.sin(2 * np.pi * freq * t)
    
    # パルス効果
    pulse = np.sin(2 * np.pi * 20 * t) * 0.5 + 0.5
    tone = tone * pulse
    
    # フェード効果
    fade_in = np.linspace(0, 1, int(len(t) * 0.1))
    fade_out = np.linspace(1, 0, int(len(t) * 0.4))
    fade_middle = np.ones(len(t) - len(fade_in) - len(fade_out))
    fade = np.concatenate((fade_in, fade_middle, fade_out))
    
    # フェードを適用
    tone = tone * fade
    
    # 音量調整
    tone = (tone * 32767 * 0.7).astype(np.int16)
    
    # ステレオに変換
    stereo_tone = mono_to_stereo(tone)
    
    # バイト配列に変換
    byte_array = pygame.sndarray.make_sound(stereo_tone)
    return byte_array

def generate_hyper_sound():
    """ハイパーモード発動音を生成"""
    sample_rate = 44100
    duration = 1.0  # 秒
    
    # サイン波用の時間配列
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 上昇音
    freq_up = np.linspace(200, 1200, int(len(t) * 0.5))
    freq_sustained = np.ones(len(t) - len(freq_up)) * 1200
    freq = np.concatenate((freq_up, freq_sustained))
    
    # サイン波生成
    tone1 = np.sin(2 * np.pi * freq * t)
    tone2 = np.sin(2 * np.pi * freq * 1.5 * t)  # 1.5倍の周波数で和音
    
    # パルス効果を追加
    pulse = np.sin(2 * np.pi * 15 * t) * 0.5 + 0.5
    
    # 音を合成
    mixed = (tone1 * 0.7 + tone2 * 0.3) * pulse
    
    # フェード効果
    fade_in = np.linspace(0, 1, int(len(t) * 0.1))
    fade_out = np.linspace(1, 0, int(len(t) * 0.3))
    fade_middle = np.ones(len(t) - len(fade_in) - len(fade_out))
    fade = np.concatenate((fade_in, fade_middle, fade_out))
    
    # フェードを適用
    mixed = mixed * fade
    
    # 音量調整
    mixed = (mixed * 32767 * 0.7).astype(np.int16)
    
    # ステレオに変換
    stereo_tone = mono_to_stereo(mixed)
    
    # バイト配列に変換
    byte_array = pygame.sndarray.make_sound(stereo_tone)
    return byte_array

def generate_menu_sound():
    """メニュー選択音を生成"""
    sample_rate = 44100
    duration = 0.1  # 秒
    
    # サイン波用の時間配列
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 低音から高音へ
    freq = np.linspace(400, 800, len(t))
    tone = np.sin(2 * np.pi * freq * t)
    
    # フェードアウト
    fade = np.exp(-t * 10)
    tone = tone * fade
    
    # 音量調整
    tone = (tone * 32767 * 0.5).astype(np.int16)
    
    # ステレオに変換
    stereo_tone = mono_to_stereo(tone)
    
    # バイト配列に変換
    byte_array = pygame.sndarray.make_sound(stereo_tone)
    return byte_array

# 効果音を生成して保存
sounds = {
    "shot": generate_laser_sound(),
    "special": generate_special_sound(),
    "hit": generate_hit_sound(),
    "shield": generate_shield_sound(),
    "hyper": generate_hyper_sound(),
    "menu": generate_menu_sound()
}

# 効果音を保存
for name, sound in sounds.items():
    file_path = os.path.join(sound_dir, f"{name}.wav")
    try:
        sound.save(file_path)
        print(f"{name}効果音をファイル {file_path} に保存しました。")
    except Exception as e:
        print(f"エラー: {name}効果音の保存失敗 - {e}")

print("効果音生成完了")
pygame.quit() 