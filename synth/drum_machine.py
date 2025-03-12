import pygame
import numpy as np
import os
import time
from scipy.signal import butter, filtfilt
import urllib.request
import zipfile
import io
import threading
from pathlib import Path
import json
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT  # 定数をインポート
import wave
import struct
from scipy import signal

# Pygameの初期化
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# 画面サイズ
WIDTH, HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT  # constants.pyの値を使用
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("シンプルドラムマシン")

# 色の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (150, 150, 150)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
PURPLE = (150, 50, 255)
YELLOW = (255, 255, 50)
ORANGE = (255, 165, 0)

# フォント設定
try:
    # 日本語対応フォント設定を試みる
    available_fonts = pygame.font.get_fonts()
    japanese_fonts = ['yugothic', 'msgothic', 'meiryo', 'msmincho', 'yumincho']
    
    # 使用可能な日本語フォントを探す
    selected_font = None
    for jp_font in japanese_fonts:
        if any(jp_font in available_font.lower() for available_font in available_fonts):
            selected_font = jp_font
            break
    
    if selected_font:
        font = pygame.font.SysFont(selected_font, 24)
        small_font = pygame.font.SysFont(selected_font, 16)
        large_font = pygame.font.SysFont(selected_font, 32)
        print(f"日本語フォント初期化完了: {selected_font}")
    else:
        # システムに日本語フォントがない場合はデフォルトフォントを使用
        print("日本語フォントが見つかりません。代替方法を試みます。")
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 16)
        large_font = pygame.font.Font(None, 32)
except Exception as e:
    print(f"フォント初期化エラー: {e}")
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 16)
    large_font = pygame.font.Font(None, 32)

# サンプルファイルのダウンロードパス
sample_dir = Path("drum_samples")
sample_dir.mkdir(exist_ok=True)

# サンプルダウンロード用のURL
sample_urls = {
    "bass_exp": "https://freesound.org/data/previews/171/171104_2394245-lq.mp3",
    "beam": "https://freesound.org/data/previews/387/387186_7255534-lq.mp3",
    "shield": "https://freesound.org/data/previews/208/208871_1915595-lq.mp3",
    "alert": "https://freesound.org/data/previews/411/411462_5121236-lq.mp3",
    "explosion": "https://freesound.org/data/previews/412/412068_7865607-lq.mp3"
}

# ダウンロード状態
download_status = {
    "in_progress": False,
    "completed": False,
    "message": ""
}

# BGM再生用のグローバル変数を追加
bgm_pattern = None
bgm_tempo = 120
bgm_is_playing = False

# ドラム音をダウンロードする関数
def download_drum_samples():
    download_status["in_progress"] = True
    download_status["message"] = "サンプルをダウンロード中..."
    
    try:
        for sound_type, url in sample_urls.items():
            file_path = sample_dir / f"{sound_type}.mp3"
            if not file_path.exists():
                urllib.request.urlretrieve(url, file_path)
        
        download_status["completed"] = True
        download_status["message"] = "サンプルのダウンロードが完了しました"
    except Exception as e:
        download_status["message"] = f"ダウンロードエラー: {e}"
    finally:
        download_status["in_progress"] = False

# バックグラウンドでダウンロードを開始
def start_download_thread():
    thread = threading.Thread(target=download_drum_samples)
    thread.daemon = True
    thread.start()

# ドラムマシン風の打楽器音を生成する関数
def create_drum_sound(sound_type, volume=0.7, quality="high"):
    """物理モデリングを用いたドラム音源の生成"""
    sample_rate = 44100
    
    if sound_type == "bass_exp":  # キック音
        duration = 0.15
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # メンブレンの振動（基本波形）
        freq_start = 150
        freq_end = 35
        freq = np.exp(np.linspace(np.log(freq_start), np.log(freq_end), len(t)))
        membrane = np.sin(2 * np.pi * np.cumsum(freq) / sample_rate)
        
        # ボディ共鳴（倍音）
        body = 0.5 * np.sin(2 * np.pi * freq * 1.5 * t) + 0.25 * np.sin(2 * np.pi * freq * 2 * t)
        
        # アタックノイズ（スティック音）
        noise = np.random.uniform(-1, 1, len(t))
        noise_env = np.exp(-80 * t)
        
        # 非線形歪み（メンブレンの張力による）
        membrane_nl = np.tanh(3 * membrane)
        
        # 合成
        wave = membrane_nl + 0.3 * body + 0.2 * noise * noise_env
        
        # 2段エンベロープ（アタックと減衰を個別に制御）
        env_attack = 1 - np.exp(-200 * t)  # 鋭いアタック
        env_decay = np.exp(-25 * t)  # ゆっくりとした減衰
        envelope = env_attack * env_decay
        
        wave = wave * envelope * volume * 2.0
        
    elif sound_type == "beam":  # スネア音
        duration = 0.2
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # メンブレン振動
        freq = 180
        membrane = np.sin(2 * np.pi * freq * t)
        
        # スナッピー（金属線）のシミュレーション
        snappy_freqs = np.linspace(2000, 4000, 8)  # 複数の高周波
        snappy = np.zeros_like(t)
        for f in snappy_freqs:
            snappy += np.random.uniform(0.1, 0.2) * np.sin(2 * np.pi * f * t)
        
        # ノイズ成分（スナッピーの振動）
        noise = np.random.uniform(-1, 1, len(t))
        
        # バンドパスフィルター（スネアらしい周波数帯域を強調）
        b1, a1 = butter(2, [900/sample_rate*2, 2000/sample_rate*2], btype='band')
        filtered_noise = filtfilt(b1, a1, noise)
        
        # 非線形歪み
        membrane_nl = np.tanh(2 * membrane)
        
        # 合成
        wave = 0.5 * membrane_nl + 0.3 * snappy + 0.4 * filtered_noise
        
        # エンベロープ（アタックと2段階の減衰）
        env_attack = 1 - np.exp(-300 * t)
        env_decay1 = np.exp(-15 * t)  # メンブレン用
        env_decay2 = np.exp(-10 * t)  # スナッピー用
        envelope = env_attack * (0.6 * env_decay1 + 0.4 * env_decay2)
        
        wave = wave * envelope * volume * 1.8
        
    elif sound_type == "shield":  # ハイハット（クローズ）
        duration = 0.1
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 金属板の振動シミュレーション
        freqs = np.array([6000, 7500, 9000, 10500, 12000])
        phases = np.random.uniform(0, 2*np.pi, len(freqs))
        cymbal = np.zeros_like(t)
        for i, f in enumerate(freqs):
            cymbal += np.sin(2 * np.pi * f * t + phases[i])
        
        # 非線形結合（シンバルの特徴的な倍音）
        cymbal_nl = np.tanh(cymbal)
        
        # 高周波ノイズ
        noise = np.random.uniform(-1, 1, len(t))
        b, a = butter(6, 7000/sample_rate*2, btype='high')
        filtered_noise = filtfilt(b, a, noise)
        
        # 合成
        wave = 0.6 * cymbal_nl + 0.4 * filtered_noise
        
        # 急峻なエンベロープ
        envelope = np.exp(-70 * t)
        envelope[:int(0.001 * sample_rate)] = 1.0
        
        wave = wave * envelope * volume * 0.8
        
    elif sound_type == "alert":  # 警告音
        duration = 0.4
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # より落ち着いた基本周波数
        freq_start = 330  # E4音
        freq_end = 440    # A4音
        freq = np.exp(np.linspace(np.log(freq_start), np.log(freq_end), len(t)))
        wave = np.sin(2 * np.pi * np.cumsum(freq) / sample_rate)
        
        # 倍音を追加（より柔らかい音色に）
        wave += 0.3 * np.sin(3 * np.pi * np.cumsum(freq) / sample_rate)
        wave += 0.15 * np.sin(4 * np.pi * np.cumsum(freq) / sample_rate)
        
        # よりゆっくりとした変調
        mod_freq = 8  # 8Hzのパルス
        modulation = 0.8 + 0.2 * np.sin(2 * np.pi * mod_freq * t)
        wave = wave * modulation
        
        # なめらかなエンベロープ
        envelope = (1 - np.exp(-5 * t)) * np.exp(-2 * t)
        wave = wave * envelope * volume * 0.8
        
    elif sound_type == "explosion":  # 爆発音（より控えめに）
        duration = 0.4
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # ノイズベース（より柔らかく）
        noise = np.random.uniform(-1, 1, len(t))
        
        # 低周波フィルタリング（より穏やかな轟音）
        b, a = signal.butter(4, 150/sample_rate*2, btype='low')
        low_noise = signal.filtfilt(b, a, noise)
        
        # 中周波フィルタリング（より柔らかい破裂音）
        b2, a2 = signal.butter(4, [150/sample_rate*2, 1000/sample_rate*2], btype='band')
        mid_noise = signal.filtfilt(b2, a2, noise)
        
        # 高周波成分を抑える
        b3, a3 = signal.butter(4, 2000/sample_rate*2, btype='high')
        high_noise = signal.filtfilt(b3, a3, noise)
        
        # 各成分のエンベロープ（よりゆっくりと）
        env_low = np.exp(-3 * t)
        env_mid = np.exp(-6 * t)
        env_high = np.exp(-15 * t)
        
        # 合成（低音をより強調）
        wave = (0.7 * low_noise * env_low + 
                0.2 * mid_noise * env_mid +
                0.05 * high_noise * env_high)
        
        # 全体のエンベロープ（よりなめらか）
        envelope = (1 - np.exp(-30 * t)) * np.exp(-2 * t)
        wave = wave * envelope * volume * 0.7
    
    else:
        # デフォルト音（使用されない）
        duration = 0.1
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave = np.sin(2 * np.pi * 440 * t) * volume
    
    # 波形の品質向上処理
    # 1. DCオフセット除去
    wave = wave - np.mean(wave)
    
    # 2. ノーマライズ
    max_val = np.max(np.abs(wave))
    if max_val > 0:
        wave = wave / max_val
    
    # 3. ソフトクリッピング（ドラム音用に調整）
    wave = np.tanh(wave * 1.5)  # より自然なクリッピング
    
    # 4. 高品質なリサンプリング
    if quality == "high":
        # アンチエイリアシングフィルタ
        nyq = sample_rate / 2
        b, a = butter(3, 18000/nyq, btype='low')  # より自然なロールオフ
        wave = filtfilt(b, a, wave)
    
    # ステレオ化（より自然な定位）
    stereo = np.zeros((len(wave), 2), dtype=np.float32)
    if sound_type == "bass_exp":  # キックは中央よりやや左
        stereo[:, 0] = wave * 1.1
        stereo[:, 1] = wave * 0.9
    elif sound_type == "beam":  # スネアは左
        stereo[:, 0] = wave * 1.2
        stereo[:, 1] = wave * 0.8
    elif sound_type == "shield":  # ハイハットは右
        stereo[:, 0] = wave * 0.7
        stereo[:, 1] = wave * 1.3
    elif sound_type == "alert":  # 警告音は左右に振る
        pan = np.sin(2 * np.pi * 2 * t)  # 2Hzでパンニング
        stereo[:, 0] = wave * (1 + pan) * 0.5
        stereo[:, 1] = wave * (1 - pan) * 0.5
    else:  # その他は適度に振り分け
        stereo[:, 0] = wave * 1.05
        stereo[:, 1] = wave * 0.95
    
    # 最終的なクリッピング
    stereo = np.clip(stereo, -0.98, 0.98)
    
    # PyGame用のサウンドオブジェクトに変換
    try:
        sound = pygame.sndarray.make_sound(stereo)
        return sound
    except Exception as e:
        print(f"音声生成エラー: {e}")
        return None

# ドラム音をロードする関数
def load_drum_sounds(quality="high"):
    sounds = {}
    sound_types = ["bass_exp", "beam", "shield", "alert", "explosion", "crystal", "piano_tone", "bell"]
    
    for sound_type in sound_types:
        # WAVファイルの存在確認
        wav_path = Path("drum_samples") / f"{sound_type}.wav"
        if wav_path.exists():
            try:
                sounds[sound_type] = pygame.mixer.Sound(str(wav_path))
                print(f"WAVファイルを読み込みました: {sound_type}")
                continue
            except Exception as e:
                print(f"WAVファイルの読み込みに失敗: {sound_type} - {e}")
        
        # WAVファイルがない場合は生成
        if sound_type in ["alert", "explosion"]:
            sounds[sound_type] = create_drum_sound(sound_type, volume=0.7, quality=quality)
            print(f"音を生成しました: {sound_type}")
        elif sound_type == "crystal":
            sounds[sound_type] = create_piano_sound(880, volume=0.5, quality=quality)  # 高音のクリスタル音
        elif sound_type == "piano_tone":
            sounds[sound_type] = create_piano_sound(440, volume=0.7, quality=quality)  # 中音域のピアノ音
        elif sound_type == "bell":
            sounds[sound_type] = create_piano_sound(660, volume=0.6, quality=quality)  # ベル音
        else:
            sounds[sound_type] = None
            print(f"未対応の音源タイプ: {sound_type}")
    
    return sounds

# ボタンクラス
class Button:
    def __init__(self, x, y, width, height, text, color, action=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = color
        self.hover_color = tuple(min(c + 30, 255) for c in color)
        self.action = action
        self.is_hovered = False
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height), border_radius=5)
        pygame.draw.rect(surface, WHITE, (self.x, self.y, self.width, self.height), width=2, border_radius=5)
        
        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        surface.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            self.is_hovered = self.x <= mouse_x <= self.x + self.width and self.y <= mouse_y <= self.y + self.height
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左クリック
                mouse_x, mouse_y = event.pos
                if self.x <= mouse_x <= self.x + self.width and self.y <= mouse_y <= self.y + self.height:
                    return True
        return False

# ビートグリッドクラス
class BeatGrid:
    def __init__(self, x, y, width, height, rows, cols, cell_color=DARK_GRAY, active_color=RED):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rows = rows
        self.cols = cols
        self.cell_width = width // cols
        self.cell_height = height // rows
        self.cell_color = cell_color
        self.active_color = active_color
        self.grid = [[False for _ in range(cols)] for _ in range(rows)]
        # 色のリストを拡張
        self.active_colors = [
            RED,        # 低音爆発
            BLUE,       # ビーム
            GREEN,      # シールド
            YELLOW,     # 警告
            PURPLE,     # 爆発
            (200, 200, 255),  # クリスタル（薄い青）
            (255, 200, 200),  # ピアノ（薄い赤）
            (255, 255, 200),  # ベル（薄い黄）
        ]
        
    def draw(self, surface, current_beat=None):
        # グリッド背景
        pygame.draw.rect(surface, DARK_GRAY, (self.x, self.y, self.width, self.height))
        
        # セル
        for row in range(self.rows):
            for col in range(self.cols):
                cell_x = self.x + col * self.cell_width
                cell_y = self.y + row * self.cell_height
                
                # セル色決定 (4拍子のグリッド色を変える)
                if col % 4 == 0:
                    bg_color = LIGHT_GRAY if not self.grid[row][col] else self.active_colors[row % len(self.active_colors)]
                else:
                    bg_color = GRAY if not self.grid[row][col] else self.active_colors[row % len(self.active_colors)]
                
                # 現在の再生位置を強調
                if current_beat is not None and col == current_beat:
                    if self.grid[row][col]:
                        # アクティブなセルを再生中
                        border_color = WHITE
                        border_width = 3
                    else:
                        # 非アクティブなセルを再生中
                        border_color = GREEN
                        border_width = 2
                else:
                    # 通常のセル
                    border_color = DARK_GRAY
                    border_width = 1
                
                # セル描画
                pygame.draw.rect(surface, bg_color, (cell_x, cell_y, self.cell_width, self.cell_height))
                pygame.draw.rect(surface, border_color, (cell_x, cell_y, self.cell_width, self.cell_height), border_width)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左クリック
                mouse_x, mouse_y = event.pos
                
                # クリック位置がグリッド内かチェック
                if (self.x <= mouse_x < self.x + self.width and 
                    self.y <= mouse_y < self.y + self.height):
                    
                    # クリックされたセルを特定
                    col = (mouse_x - self.x) // self.cell_width
                    row = (mouse_y - self.y) // self.cell_height
                    
                    # セルの状態を切り替え
                    self.grid[row][col] = not self.grid[row][col]
                    return (row, col)
        
        return None
    
    def get_active_cells(self, col):
        """指定した列のアクティブなセル（行）のリストを返す"""
        if col < 0 or col >= self.cols:
            return []
        
        return [row for row in range(self.rows) if self.grid[row][col]]
    
    def clear(self):
        """グリッドをクリア"""
        self.grid = [[False for _ in range(self.cols)] for _ in range(self.rows)]
    
    def fill_pattern(self, pattern_type):
        """基本的なパターンをグリッドに設定"""
        self.clear()
        
        if pattern_type == "basic":
            # 基本的な8ビートパターン
            for col in range(self.cols):
                if col % 8 == 0:  # 1拍目
                    self.grid[0][col] = True  # 低音爆発
                if col % 8 == 4:  # 5拍目
                    self.grid[1][col] = True  # ビーム
                if col % 4 == 0:  # 1,5拍目
                    self.grid[2][col] = True  # シールド
                if col % 2 == 0:  # 偶数拍
                    self.grid[3][col] = True  # 警告
                if col % 8 == 6:  # 7拍目
                    self.grid[4][col] = True  # 爆発
                if col % 4 == 2:  # 3,7拍目
                    self.grid[5][col] = True  # クリスタル
                if col % 8 == 2:  # 3拍目
                    self.grid[6][col] = True  # ピアノ
                if col % 8 == 0:  # 1拍目
                    self.grid[7][col] = True  # ベル
        
        elif pattern_type == "rock":
            # 攻撃パターン
            for col in range(self.cols):
                if col % 8 == 0 or col % 8 == 6:  # 1,7拍目
                    self.grid[0][col] = True  # 低音爆発
                if col % 8 == 2 or col % 8 == 5:  # 3,6拍目
                    self.grid[1][col] = True  # ビーム
                if col % 4 == 0:  # 1,5拍目
                    self.grid[4][col] = True  # 爆発
                if col % 2 == 1:  # 奇数拍
                    self.grid[2][col] = True  # シールド
                if col % 8 == 4:  # 5拍目
                    self.grid[5][col] = True  # クリスタル
                if col % 4 == 2:  # 3,7拍目
                    self.grid[6][col] = True  # ピアノ
                if col % 8 == 0:  # 1拍目
                    self.grid[7][col] = True  # ベル
        
        elif pattern_type == "disco":
            # 警告パターン
            for col in range(self.cols):
                if col % 4 == 0:  # 1拍目
                    self.grid[3][col] = True  # 警告
                if col % 8 == 2 or col % 8 == 6:  # 3,7拍目
                    self.grid[1][col] = True  # ビーム
                if col % 4 == 2:  # 3拍目
                    self.grid[2][col] = True  # シールド
                if col % 8 == 4:  # 5拍目
                    self.grid[4][col] = True  # 爆発
                if col % 2 == 0:  # 偶数拍
                    self.grid[5][col] = True  # クリスタル
                if col % 4 == 0:  # 1,5拍目
                    self.grid[6][col] = True  # ピアノ
                if col % 8 == 0:  # 1拍目
                    self.grid[7][col] = True  # ベル
    
    def save_pattern(self):
        """現在のパターンを保存"""
        global bgm_pattern, bgm_tempo
        bgm_pattern = [row[:] for row in self.grid]  # グリッドの深いコピー
        
        # パターンをJSONファイルとして保存
        data = {
            "pattern": bgm_pattern,
            "tempo": bgm_tempo  # 現在のテンポを保存
        }
        
        # BGMフォルダを作成
        bgm_dir = Path("bgm")
        bgm_dir.mkdir(exist_ok=True)
        
        # JSONファイルに保存
        try:
            with open(bgm_dir / "current_pattern.json", "w") as f:
                json.dump(data, f)
            
            # WAVファイルとしても保存（現在のテンポを使用）
            drum_sounds = load_drum_sounds(quality="high")
            drum_types = ["bass_exp", "beam", "shield", "alert", "explosion", "crystal", "piano_tone", "bell"]
            export_pattern_to_wav(self.grid, bgm_tempo, drum_sounds, drum_types)
            
            return True
        except Exception as e:
            print(f"パターン保存エラー: {e}")
            return False
    
    def load_pattern(self, pattern):
        """保存されたパターンを読み込み"""
        if pattern and len(pattern) == self.rows and len(pattern[0]) == self.cols:
            self.grid = [row[:] for row in pattern]
            return True
        return False

def play_bgm(drum_sounds, drum_types):
    """BGMとしてパターンを再生（グローバル変数を使用）"""
    global bgm_pattern, bgm_tempo, bgm_is_playing
    
    if not bgm_is_playing or not bgm_pattern:
        return
    
    current_time = time.time()
    beat_interval = 60 / bgm_tempo / 4  # 16分音符の間隔
    
    # 現在のビート位置を計算
    current_beat = int((current_time * bgm_tempo / 60 * 4) % 16)
    
    # アクティブなセルの音を再生
    for row in range(len(bgm_pattern)):
        if row < len(drum_types) and bgm_pattern[row][current_beat]:
            sound_type = drum_types[row]
            if sound_type in drum_sounds and drum_sounds[sound_type]:
                drum_sounds[sound_type].play()

def export_pattern_to_wav(grid, tempo, drum_sounds, drum_types, filename="bgm/current_pattern.wav"):
    """パターンをWAVファイルとして書き出す"""
    sample_rate = 44100
    beat_duration = 60.0 / tempo / 4.0  # 16分音符の長さ（秒）
    pattern_duration = beat_duration * 16  # 全パターンの長さ（秒）
    total_samples = int(pattern_duration * sample_rate)
    
    # 出力バッファ（ステレオ）
    output_buffer = np.zeros((total_samples, 2), dtype=np.float32)
    
    # 各ビートの音を合成
    for col in range(16):  # 16ビート
        start_sample = int(col * beat_duration * sample_rate)
        for row in range(len(grid)):
            if grid[row][col] and row < len(drum_types):
                sound_type = drum_types[row]
                if sound_type in drum_sounds and drum_sounds[sound_type]:
                    # PyGameのSoundオブジェクトから波形データを取得
                    sound_array = pygame.sndarray.samples(drum_sounds[sound_type])
                    sound_length = min(len(sound_array), total_samples - start_sample)
                    output_buffer[start_sample:start_sample + sound_length] += sound_array[:sound_length]
    
    # クリッピング防止のためにノーマライズ
    max_val = np.max(np.abs(output_buffer))
    if max_val > 0:
        output_buffer = output_buffer / max_val * 0.9
    
    # WAVファイルとして保存
    bgm_dir = Path("bgm")
    bgm_dir.mkdir(exist_ok=True)
    
    with wave.open(str(bgm_dir / "current_pattern.wav"), 'w') as wav_file:
        wav_file.setnchannels(2)  # ステレオ
        wav_file.setsampwidth(2)  # 16bit
        wav_file.setframerate(sample_rate)
        
        # float32からint16に変換
        wav_data = (output_buffer * 32767).astype(np.int16)
        wav_file.writeframes(wav_data.tobytes())
    
    return True

def create_piano_sound(base_freq, volume=0.7, quality="high"):
    """物理モデリングを用いた弦楽器音の生成"""
    sample_rate = 44100
    duration = 1.5  # 持続時間を短めに
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 弦の振動特性を模倣（非線形性を含む）
    wave = np.zeros_like(t)
    
    # 基本周波数とその倍音（より自然な減衰特性）
    harmonics = [1, 2, 3, 4, 5]
    # 倍音の振幅を自然な減衰に調整
    amplitudes = [1.0, 0.6, 0.3, 0.15, 0.075]
    # 各倍音の減衰時間を調整（高次倍音ほど早く減衰）
    decay_rates = [3.0, 4.0, 5.0, 6.0, 7.0]
    
    # 弦の振動の非線形性を考慮
    for h, amp, decay in zip(harmonics, amplitudes, decay_rates):
        freq = base_freq * h
        # 各倍音の初期位相をわずかにずらす
        phase = np.random.uniform(0, 0.1)
        harmonic = amp * np.sin(2 * np.pi * freq * t + phase)
        # より自然な減衰カーブ
        envelope = np.exp(-decay * t) * (1 - np.exp(-50 * t))
        wave += harmonic * envelope
    
    # 弦の初期打撃（ハンマー音）
    attack_duration = 0.004  # 4ミリ秒
    attack_samples = int(attack_duration * sample_rate)
    attack_noise = np.random.uniform(-0.5, 0.5, attack_samples)
    # より自然なハンマー音の減衰
    attack_env = np.exp(-300 * np.linspace(0, 1, attack_samples))
    wave[:attack_samples] += attack_noise * attack_env * 0.3
    
    # 弦の共鳴効果（より自然な共鳴）
    b, a = signal.butter(2, [0.1, 0.9], btype='band')
    resonance = signal.lfilter(b, a, wave)
    wave = wave + resonance * 0.2
    
    # DCオフセット除去
    wave = wave - np.mean(wave)
    
    # 波形の正規化
    wave = wave / np.max(np.abs(wave)) * 0.9
    
    # ステレオ化（より自然な空間表現）
    stereo = np.zeros((len(wave), 2), dtype=np.float32)
    # 左右の微妙な遅延差
    delay_samples = int(0.001 * sample_rate)  # 1ミリ秒
    stereo[:-delay_samples, 0] = wave[delay_samples:] * 1.0  # 左
    stereo[delay_samples:, 1] = wave[:-delay_samples] * 0.95  # 右
    
    # 最終的な音量調整
    stereo = stereo * volume
    
    try:
        sound = pygame.sndarray.make_sound(stereo)
        return sound
    except Exception as e:
        print(f"ピアノ音生成エラー: {e}")
        return None

def main():
    global bgm_tempo, bgm_is_playing  # グローバル変数を使用
    clock = pygame.time.Clock()
    running = True
    
    # サウンド品質設定
    sound_quality = "high"  # "high" または "sample"
    
    # ドラム音を読み込み
    drum_sounds = load_drum_sounds(quality=sound_quality)
    
    # 音色ラベルを変更
    drum_labels = ["低音爆発", "ビーム", "シールド", "警告", "爆発", "クリスタル", "ピアノ", "ベル"]
    drum_types = ["bass_exp", "beam", "shield", "alert", "explosion", "crystal", "piano_tone", "bell"]
    
    # ビートグリッド（行数を8に増やす）
    grid = BeatGrid(100, 100, 800, 300, 8, 16)
    
    # 保存されたパターンがある場合、読み込んでBGM再生を開始
    if bgm_pattern:
        grid.load_pattern(bgm_pattern)
        bgm_is_playing = True
        tempo = bgm_tempo
        beat_interval = 60 / tempo / 4
    else:
        tempo = 120  # デフォルトBPM
        beat_interval = 60 / tempo / 4  # 16分音符の間隔 (秒)
    
    # 再生関連のパラメータ
    is_playing = False
    current_beat = 0
    last_beat_time = 0
    
    # ボタン
    play_button = Button(100, 380, 120, 40, "再生", GREEN)
    stop_button = Button(240, 380, 120, 40, "停止", RED)
    clear_button = Button(380, 380, 120, 40, "クリア", GRAY)
    
    # パターンボタン
    basic_pattern_button = Button(520, 380, 120, 40, "通常パターン", BLUE)
    rock_pattern_button = Button(660, 380, 120, 40, "攻撃パターン", PURPLE)
    disco_pattern_button = Button(800, 380, 120, 40, "警告パターン", YELLOW)
    
    # 音質切り替えボタン
    synthetic_button = Button(100, 450, 120, 40, "合成音", GRAY)
    sample_button = Button(240, 450, 120, 40, "サンプル音", ORANGE)
    if not sample_dir.exists() or not any(sample_dir.iterdir()):
        # サンプルがなければダウンロードボタンを表示
        sample_button.text = "サンプル取得"
    
    # テンポスライダー
    tempo_min, tempo_max = 60, 200
    tempo_slider_x = 400
    tempo_slider_y = 500  # 450から500に変更（下に移動）
    tempo_slider_width, tempo_slider_height = 300, 20
    tempo_handle_radius = 10
    tempo_handle_x = tempo_slider_x + (tempo - tempo_min) / (tempo_max - tempo_min) * tempo_slider_width
    dragging_tempo = False
    
    # メッセージ表示用
    message = ""
    message_time = 0
    
    # 保存ボタンを追加
    save_button = Button(380, 450, 120, 40, "パターン保存", PURPLE)
    bgm_button = Button(520, 450, 120, 40, "BGM再生", GREEN)
    
    # 操作説明の位置も調整
    help_text1 = small_font.render("グリッドをクリックして音を配置 → 再生ボタンでループ再生", True, LIGHT_GRAY)
    help_text2 = small_font.render("スペースキーで再生/停止、Cキーでクリア", True, LIGHT_GRAY)
    screen.blit(help_text1, (100, 570))  # 520から570に変更
    screen.blit(help_text2, (100, 590))  # 540から590に変更
    
    while running:
        current_time = time.time()
        
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # グリッドのクリックイベント処理
            grid_cell = grid.handle_event(event)
            if grid_cell:
                row, col = grid_cell
                # クリックした音を再生
                if row < len(drum_types):
                    sound_type = drum_types[row]
                    if sound_type in drum_sounds and drum_sounds[sound_type]:
                        drum_sounds[sound_type].play()
            
            # ボタンのイベント処理
            if play_button.handle_event(event) and not is_playing:
                is_playing = True
                current_beat = 0
                last_beat_time = current_time
                message = "再生開始"
                message_time = current_time
            
            if stop_button.handle_event(event) and is_playing:
                is_playing = False
                message = "停止"
                message_time = current_time
            
            if clear_button.handle_event(event):
                grid.clear()
                message = "グリッドをクリアしました"
                message_time = current_time
            
            if basic_pattern_button.handle_event(event):
                grid.fill_pattern("basic")
                message = "基本パターンをロードしました"
                message_time = current_time
            
            if rock_pattern_button.handle_event(event):
                grid.fill_pattern("rock")
                message = "ロックパターンをロードしました"
                message_time = current_time
            
            if disco_pattern_button.handle_event(event):
                grid.fill_pattern("disco")
                message = "ディスコパターンをロードしました"
                message_time = current_time
            
            # 音質切り替えボタン処理
            if synthetic_button.handle_event(event) and sound_quality != "high":
                sound_quality = "high"
                drum_sounds = load_drum_sounds(quality=sound_quality)
                message = "合成音に切り替えました"
                message_time = current_time
            
            if sample_button.handle_event(event):
                if not sample_dir.exists() or not any(sample_dir.iterdir()):
                    # サンプルがなければダウンロード開始
                    if not download_status["in_progress"]:
                        start_download_thread()
                        message = "サンプルをダウンロード中..."
                        message_time = current_time
                else:
                    sound_quality = "sample"
                    drum_sounds = load_drum_sounds(quality=sound_quality)
                    message = "サンプル音に切り替えました"
                    message_time = current_time
            
            # テンポスライダー処理
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                # テンポスライダーのハンドル範囲内をクリックしたか
                if ((tempo_handle_x - tempo_handle_radius <= mouse_x <= tempo_handle_x + tempo_handle_radius) and
                    (tempo_slider_y - tempo_handle_radius <= mouse_y <= tempo_slider_y + tempo_handle_radius)):
                    dragging_tempo = True
                
                # スライダーバー自体をクリックした場合もハンドルを移動
                elif (tempo_slider_x <= mouse_x <= tempo_slider_x + tempo_slider_width and
                      tempo_slider_y - 5 <= mouse_y <= tempo_slider_y + tempo_slider_height + 5):
                    tempo_handle_x = mouse_x
                    # テンポ値の計算
                    normalized_pos = (tempo_handle_x - tempo_slider_x) / tempo_slider_width
                    tempo = int(tempo_min + normalized_pos * (tempo_max - tempo_min))
                    # ビート間隔の再計算
                    beat_interval = 60 / tempo / 4
                    # グローバルテンポを更新
                    bgm_tempo = tempo
            
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging_tempo = False
            
            elif event.type == pygame.MOUSEMOTION and dragging_tempo:
                mouse_x, _ = event.pos
                # スライダー範囲内に制限
                tempo_handle_x = max(tempo_slider_x, min(mouse_x, tempo_slider_x + tempo_slider_width))
                # テンポ値の計算
                normalized_pos = (tempo_handle_x - tempo_slider_x) / tempo_slider_width
                tempo = int(tempo_min + normalized_pos * (tempo_max - tempo_min))
                # ビート間隔の再計算
                beat_interval = 60 / tempo / 4
                # グローバルテンポを更新
                bgm_tempo = tempo
            
            # 保存ボタンの処理
            if save_button.handle_event(event):
                if grid.save_pattern():
                    message = "パターンを保存しました"
                    message_time = current_time
            
            # BGM再生ボタンの処理
            if bgm_button.handle_event(event):
                if bgm_pattern:
                    bgm_is_playing = not bgm_is_playing
                    if bgm_is_playing:
                        message = "BGM再生開始"
                        bgm_button.text = "BGM停止"
                        bgm_button.color = RED
                    else:
                        message = "BGM再生停止"
                        bgm_button.text = "BGM再生"
                        bgm_button.color = GREEN
                    message_time = current_time
                else:
                    message = "先にパターンを保存してください"
                    message_time = current_time
        
        # 再生中の場合、現在のビートを更新
        if is_playing and current_time - last_beat_time >= beat_interval:
            # 現在のビートのアクティブなセルの音を再生
            active_cells = grid.get_active_cells(current_beat)
            for row in active_cells:
                if row < len(drum_types):
                    sound_type = drum_types[row]
                    if sound_type in drum_sounds and drum_sounds[sound_type]:
                        drum_sounds[sound_type].play()
            
            # 次のビートに進む
            current_beat = (current_beat + 1) % grid.cols
            last_beat_time = current_time
        
        # BGM再生の処理
        if bgm_is_playing and bgm_pattern:
            play_bgm(drum_sounds, drum_types)
        
        # ダウンロード状態を更新
        if download_status["in_progress"] or (download_status["completed"] and current_time - message_time < 2.0):
            message = download_status["message"]
            message_time = current_time
            
            if download_status["completed"]:
                download_status["completed"] = False
                if sample_dir.exists() and any(sample_dir.iterdir()):
                    sample_button.text = "サンプル音"
                    sound_quality = "sample"
                    drum_sounds = load_drum_sounds(quality=sound_quality)
        
        # 描画処理
        screen.fill(BLACK)
        
        # タイトル
        title_text = large_font.render("シンプルドラムマシン", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 40))
        screen.blit(title_text, title_rect)
        
        # 音色ラベル
        for i, label in enumerate(drum_labels):
            label_text = font.render(label, True, WHITE)
            screen.blit(label_text, (50, 100 + i * grid.cell_height + grid.cell_height // 2 - 10))
        
        # ビートグリッド描画
        current_beat_pos = current_beat if is_playing else None
        grid.draw(screen, current_beat_pos)
        
        # ボタン描画
        play_button.draw(screen)
        stop_button.draw(screen)
        clear_button.draw(screen)
        basic_pattern_button.draw(screen)
        rock_pattern_button.draw(screen)
        disco_pattern_button.draw(screen)
        
        # 音質ボタン描画
        if sound_quality == "high":
            synthetic_button.color = BLUE
            sample_button.color = GRAY
        else:
            synthetic_button.color = GRAY
            sample_button.color = BLUE
        
        synthetic_button.draw(screen)
        sample_button.draw(screen)
        
        # テンポスライダー描画
        pygame.draw.rect(screen, GRAY, (tempo_slider_x, tempo_slider_y, tempo_slider_width, tempo_slider_height), border_radius=5)
        pygame.draw.circle(screen, WHITE, (int(tempo_handle_x), tempo_slider_y + tempo_slider_height // 2), tempo_handle_radius)
        
        # テンポ表示
        tempo_text = font.render(f"テンポ: {tempo} BPM", True, WHITE)
        screen.blit(tempo_text, (tempo_slider_x, tempo_slider_y - 30))
        
        # 音質モード表示
        quality_text = font.render(f"音質モード: {'合成音' if sound_quality == 'high' else 'サンプル音'}", True, LIGHT_GRAY)
        screen.blit(quality_text, (720, 450))
        
        # 保存・BGMボタンの描画
        save_button.draw(screen)
        bgm_button.draw(screen)
        
        # BGM状態の表示
        if bgm_pattern:
            bgm_status = "BGM: 再生中" if bgm_is_playing else "BGM: 停止中"
            bgm_text = font.render(bgm_status, True, GREEN if bgm_is_playing else WHITE)
            screen.blit(bgm_text, (520, 500))
        
        # メッセージ表示
        if current_time - message_time < 2.0 and message:
            message_text = font.render(message, True, GREEN)
            message_rect = message_text.get_rect(center=(WIDTH // 2, 570))
            screen.blit(message_text, message_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    try:
        from scipy import signal
    except ImportError:
        print("Scipyライブラリが必要です。'pip install scipy'を実行してインストールしてください。")
    
    main() 