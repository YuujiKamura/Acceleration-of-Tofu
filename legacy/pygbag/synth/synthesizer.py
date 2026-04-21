import pygame
import numpy as np
import pygame.gfxdraw
import os

# Pygameの初期化
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# 画面サイズ
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("シンプルシンセサイザー")

# 色の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)
DARK_GRAY = (50, 50, 50)
LIGHT_BLUE = (100, 200, 255)
LIGHT_GREEN = (100, 255, 200)
LIGHT_RED = (255, 100, 100)
LIGHT_YELLOW = (255, 255, 100)

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
        # デフォルトフォントを使用
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 16)
        large_font = pygame.font.Font(None, 32)
except Exception as e:
    print(f"フォント初期化エラー: {e}")
    # エラー時はデフォルトフォントを使用
    font = pygame.font.Font(None, 24)
    small_font = pygame.font.Font(None, 16)
    large_font = pygame.font.Font(None, 32)

# スライダークラス
class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, default_val, label, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_val = min_val
        self.max_val = max_val
        self.value = default_val
        self.dragging = False
        self.label = label
        self.color = color
        
        # スライダーのつまみの位置を計算
        self.handle_y = self.y + (1 - (self.value - self.min_val) / (self.max_val - self.min_val)) * self.height
        
    def draw(self, surface):
        # スライダー背景
        pygame.draw.rect(surface, DARK_GRAY, (self.x, self.y, self.width, self.height))
        
        # スライダーつまみ
        pygame.draw.rect(surface, self.color, (self.x - 10, self.handle_y - 10, self.width + 20, 20), border_radius=10)
        
        # ラベル
        label_text = font.render(self.label, True, WHITE)
        surface.blit(label_text, (self.x - 10, self.y - 30))
        
        # 値
        value_text = small_font.render(f"{self.value:.2f}", True, WHITE)
        surface.blit(value_text, (self.x - 10, self.y + self.height + 10))
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左クリック
                mouse_x, mouse_y = event.pos
                if self.x - 10 <= mouse_x <= self.x + self.width + 10 and self.y - 10 <= mouse_y <= self.y + self.height + 10:
                    self.dragging = True
                    self.update_value(mouse_y)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # 左クリック
                self.dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_x, mouse_y = event.pos
                self.update_value(mouse_y)
    
    def update_value(self, mouse_y):
        # マウス位置からスライダー値を計算
        relative_y = max(self.y, min(mouse_y, self.y + self.height))
        normalized_y = (relative_y - self.y) / self.height
        self.value = self.max_val - normalized_y * (self.max_val - self.min_val)
        self.handle_y = relative_y

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
                    # アクションがなくても押されたらTrueを返す
                    return True
        return False

# 波形生成関数
def generate_waveform(frequency, duration, volume, waveform_type, params):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 波形タイプにより異なる音色を生成
    if waveform_type == 0:  # Sine wave
        wave = np.sin(2 * np.pi * frequency * t)
    elif waveform_type == 1:  # Square wave
        wave = np.sign(np.sin(2 * np.pi * frequency * t))
    elif waveform_type == 2:  # Sawtooth wave
        wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))
    elif waveform_type == 3:  # Triangle wave
        wave = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
    elif waveform_type == 4:  # Custom wave with noise
        sine_wave = np.sin(2 * np.pi * frequency * t)
        noise = np.random.uniform(-0.5, 0.5, len(t)) * params['noise']
        wave = sine_wave + noise
    
    # 音量調整
    wave = wave * volume
    
    # LPF簡易フィルター (簡単な低域通過フィルター)
    if params['lpf'] > 0:
        from scipy.signal import butter, filtfilt
        nyquist = 0.5 * sample_rate
        cutoff = params['lpf'] * 20000  # 0-1の値から0-20kHzに変換
        normal_cutoff = cutoff / nyquist
        b, a = butter(4, normal_cutoff, btype='low', analog=False)
        wave = filtfilt(b, a, wave)
    
    # エンベロープ適用 (ADSR)
    attack = int(params['attack'] * sample_rate)
    decay = int(params['decay'] * sample_rate)
    sustain_level = params['sustain']
    release = int(params['release'] * sample_rate)
    
    # エンベロープ作成
    env = np.ones(len(wave))
    
    # アタック
    if attack > 0:
        env[:attack] = np.linspace(0, 1, attack)
    
    # ディケイ
    if decay > 0:
        decay_end = min(attack + decay, len(wave))
        env[attack:decay_end] = np.linspace(1, sustain_level, decay_end - attack)
    
    # サステイン
    if attack + decay < len(wave):
        env[attack + decay:] = sustain_level
    
    # リリース
    if release > 0:
        release_start = max(0, len(wave) - release)
        env[release_start:] = np.linspace(env[release_start], 0, len(wave) - release_start)
    
    # エンベロープ適用
    wave = wave * env
    
    # モノラル波形を作成
    wave = wave.astype(np.float32)
    
    try:
        # ステレオ化 (修正版) - 同じサイズのステレオ配列を作成
        stereo = np.zeros((len(wave), 2), dtype=np.float32)
        stereo[:, 0] = wave  # 左チャンネル
        stereo[:, 1] = wave  # 右チャンネル
        
        # 8ビットにクリップ (-1.0〜1.0の範囲に収める)
        stereo = np.clip(stereo, -1.0, 1.0)
        
        # メモリレイアウトを確実にC連続に
        stereo = np.ascontiguousarray(stereo)
        
        # PyGame用の音声データに変換
        return pygame.sndarray.make_sound(stereo)
    except Exception as e:
        print(f"音声生成エラー: {e}")
        return None

# 音を保存する関数
def save_sound(sound, filename):
    if not os.path.exists("sounds"):
        os.makedirs("sounds")
    # WAVファイルとして保存
    sound.write_wav(f"sounds/{filename}.wav")
    return True

# GUIなしで直接音声生成関数
def generate_and_save_sound(params, waveform_type, filename):
    """GUIなしで音声を生成して保存する関数"""
    sound = generate_waveform(
        params['frequency'], params['duration'], params['volume'],
        waveform_type, params
    )
    if sound:
        save_sound(sound, filename)
        return True
    return False

# 録音データを結合して保存する関数
def save_recording(sound_list, filename):
    """複数の音声データを結合して1つのWAVファイルとして保存する"""
    if not sound_list:
        return False
    
    if not os.path.exists("recordings"):
        os.makedirs("recordings")
    
    try:
        # より単純なアプローチ: 各サウンドを個別のファイルとして保存し、後で結合
        temp_files = []
        
        # 一時ファイルを作成
        for i, sound in enumerate(sound_list):
            temp_filename = f"temp_{i}.wav"
            sound.write_wav(temp_filename)
            temp_files.append(temp_filename)
        
        # 結合先のファイルを作成
        output_filename = f"recordings/{filename}.wav"
        
        # 最初のファイルを結合先にコピー
        if temp_files:
            with open(temp_files[0], 'rb') as src, open(output_filename, 'wb') as dst:
                dst.write(src.read())
            
            # 追加のファイルを結合
            for temp_file in temp_files[1:]:
                with open(temp_file, 'rb') as src:
                    # ヘッダーを読み飛ばす (44バイト)
                    src.seek(44)
                    data = src.read()
                    
                    # 結合先ファイルにデータを追加
                    with open(output_filename, 'ab') as dst:
                        dst.write(data)
        
        # 一時ファイルを削除
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except OSError as e:
                print(f"一時ファイル削除エラー: {e}")
                
        return True
    except Exception as e:
        print(f"録音保存エラー: {e}")
        # 一時ファイルをクリーンアップ
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except OSError as e:
                print(f"一時ファイル削除エラー: {e}")
        return False

# メイン関数
def main(headless=False):
    # ヘッドレスモードの設定
    if headless:
        import os
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        # 自動テスト実行
        print("ヘッドレスモードでテスト実行中...")
        test_params = {
            'frequency': 440.0,
            'duration': 1.0,
            'volume': 0.5,
            'attack': 0.1,
            'decay': 0.1,
            'sustain': 0.7,
            'release': 0.2,
            'lpf': 0.8,
            'noise': 0.0
        }
        for wf_type in range(5):  # 5種類の波形をテスト
            generate_and_save_sound(test_params, wf_type, f"test_waveform_{wf_type}")
            print(f"波形タイプ {wf_type} の音声を保存しました")
        return

    clock = pygame.time.Clock()
    running = True
    
    # サウンドパラメータ
    params = {
        'frequency': 440.0,
        'duration': 1.0,
        'volume': 0.5,
        'waveform': 0,
        'attack': 0.1,
        'decay': 0.1,
        'sustain': 0.7,
        'release': 0.2,
        'lpf': 0.8,
        'noise': 0.0
    }
    
    # 波形タイプのリスト
    waveform_types = ["正弦波", "矩形波", "のこぎり波", "三角波", "ノイズ"]
    current_waveform = 0
    
    # スライダーの作成 (位置を調整)
    sliders = [
        Slider(100, 150, 40, 200, 100, 1000, params['frequency'], "周波数 (Hz)", LIGHT_BLUE),
        Slider(200, 150, 40, 200, 0.1, 5.0, params['duration'], "長さ (秒)", LIGHT_GREEN),
        Slider(300, 150, 40, 200, 0.0, 1.0, params['volume'], "音量", LIGHT_RED),
        Slider(400, 150, 40, 200, 0.0, 1.0, params['attack'], "アタック", LIGHT_YELLOW),
        Slider(500, 150, 40, 200, 0.0, 1.0, params['decay'], "ディケイ", LIGHT_YELLOW),
        Slider(600, 150, 40, 200, 0.0, 1.0, params['sustain'], "サステイン", LIGHT_YELLOW),
        Slider(700, 150, 40, 200, 0.0, 1.0, params['release'], "リリース", LIGHT_YELLOW),
        Slider(800, 150, 40, 200, 0.0, 1.0, params['lpf'], "フィルター", LIGHT_BLUE),
        Slider(900, 150, 40, 200, 0.0, 1.0, params['noise'], "ノイズ量", LIGHT_RED),
    ]
    
    # ボタンの作成
    play_button = Button(300, 450, 150, 50, "再生", GREEN)
    save_button = Button(500, 450, 150, 50, "保存", BLUE)
    waveform_button = Button(700, 450, 150, 50, waveform_types[current_waveform], RED)
    record_button = Button(900, 450, 150, 50, "録音開始", LIGHT_RED)
    
    # 音声オブジェクト
    current_sound = None
    filename_input = ""
    show_filename_input = False
    keyboard_focus = False
    
    # 録音関連
    is_recording = False
    recording_sounds = []
    recording_start_time = 0
    
    # エラーメッセージ
    error_message = ""
    error_time = 0
    
    # 最後に再生した音のパラメータ
    last_played_params = None
    
    # キーボード設定
    keys = {
        pygame.K_z: 261.63,  # C4 (ド)
        pygame.K_s: 277.18,  # C#4
        pygame.K_x: 293.66,  # D4 (レ)
        pygame.K_d: 311.13,  # D#4
        pygame.K_c: 329.63,  # E4 (ミ)
        pygame.K_v: 349.23,  # F4 (ファ)
        pygame.K_g: 369.99,  # F#4
        pygame.K_b: 392.00,  # G4 (ソ)
        pygame.K_h: 415.30,  # G#4
        pygame.K_n: 440.00,  # A4 (ラ)
        pygame.K_j: 466.16,  # A#4
        pygame.K_m: 493.88,  # B4 (シ)
        pygame.K_COMMA: 523.25,  # C5 (高いド)
    }
    
    # デバッグ情報
    debug_info = []
    
    while running:
        current_time = pygame.time.get_ticks()
        
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # スライダーのイベント処理
            for slider in sliders:
                slider.handle_event(event)
            
            # ボタンのイベント処理 - 修正箇所
            if play_button.handle_event(event):
                debug_info.append(f"再生ボタンが押されました: {current_time}")
                
                # パラメータ更新
                params['frequency'] = sliders[0].value
                params['duration'] = sliders[1].value
                params['volume'] = sliders[2].value
                params['attack'] = sliders[3].value
                params['decay'] = sliders[4].value
                params['sustain'] = sliders[5].value
                params['release'] = sliders[6].value
                params['lpf'] = sliders[7].value
                params['noise'] = sliders[8].value
                
                # 音を生成して再生
                try:
                    current_sound = generate_waveform(
                        params['frequency'], params['duration'], params['volume'],
                        current_waveform, params
                    )
                    if current_sound:
                        current_sound.play()
                        last_played_params = params.copy()
                        last_played_params['waveform_type'] = current_waveform
                        last_played_params['waveform_name'] = waveform_types[current_waveform]
                        debug_info.append(f"音声生成成功: 波形={waveform_types[current_waveform]}, 周波数={params['frequency']:.1f}Hz")
                    else:
                        error_message = "音声生成に失敗しました"
                        error_time = current_time
                        debug_info.append("音声生成失敗")
                except Exception as e:
                    print(f"音声生成エラー: {e}")
                    error_message = f"エラー: {str(e)}"
                    error_time = current_time
                    debug_info.append(f"音声生成エラー: {str(e)}")
            
            if save_button.handle_event(event):
                debug_info.append(f"保存ボタンが押されました: {current_time}")
                if current_sound:
                    show_filename_input = True
                    keyboard_focus = True
                else:
                    error_message = "保存する音声がありません。先に「再生」を押してください。"
                    error_time = current_time
                    debug_info.append("保存音声なし")
                
            if waveform_button.handle_event(event):
                debug_info.append(f"波形ボタンが押されました: {current_time}")
                current_waveform = (current_waveform + 1) % len(waveform_types)
                waveform_button.text = waveform_types[current_waveform]
                debug_info.append(f"波形変更: {waveform_types[current_waveform]}")
            
            if record_button.handle_event(event):
                if not is_recording:
                    # 録音開始
                    is_recording = True
                    recording_sounds = []
                    recording_start_time = current_time
                    record_button.text = "録音停止"
                    record_button.color = LIGHT_GREEN
                    debug_info.append(f"録音開始: {current_time}")
                else:
                    # 録音停止
                    is_recording = False
                    record_button.text = "録音開始"
                    record_button.color = LIGHT_RED
                    debug_info.append(f"録音停止: {current_time}、{len(recording_sounds)}個の音声")
                    
                    # 録音データがあれば保存ダイアログを表示
                    if recording_sounds:
                        # 録音データが多すぎる場合は警告
                        if len(recording_sounds) > 50:
                            error_message = f"録音データが多すぎます ({len(recording_sounds)}個)。最初の50個のみ保存します。"
                            recording_sounds = recording_sounds[:50]
                            error_time = current_time
                        
                        show_filename_input = True
                        keyboard_focus = True
                        error_message = "録音したファイル名を入力してください"
                        error_time = current_time
                    else:
                        error_message = "録音データがありません"
                        error_time = current_time
            
            # ファイル名入力処理
            if show_filename_input:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if filename_input:
                            if is_recording:
                                # 録音停止
                                is_recording = False
                                record_button.text = "録音開始"
                                record_button.color = LIGHT_RED
                            
                            if recording_sounds:
                                try:
                                    # 録音データを保存
                                    if save_recording(recording_sounds, filename_input):
                                        error_message = f"録音ファイル '{filename_input}.wav' を保存しました"
                                        recording_sounds = []
                                    else:
                                        error_message = "録音の保存に失敗しました"
                                except Exception as e:
                                    error_message = f"録音保存エラー: {str(e)}"
                                    
                                error_time = current_time
                                debug_info.append(f"録音保存: {filename_input}.wav")
                                filename_input = ""
                                show_filename_input = False
                            elif current_sound:
                                try:
                                    save_sound(current_sound, filename_input)
                                    error_message = f"ファイル '{filename_input}.wav' を保存しました"
                                    error_time = current_time
                                    debug_info.append(f"ファイル保存: {filename_input}.wav")
                                except Exception as e:
                                    error_message = f"保存エラー: {str(e)}"
                                    error_time = current_time
                                    debug_info.append(f"保存エラー: {str(e)}")
                                filename_input = ""
                                show_filename_input = False
                    elif event.key == pygame.K_BACKSPACE:
                        filename_input = filename_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        filename_input = ""
                        show_filename_input = False
                    else:
                        if keyboard_focus and len(filename_input) < 20:
                            if 32 <= event.key <= 126 or event.key > 256:  # ASCII文字または日本語
                                filename_input += event.unicode
            
            # キーボード音階
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not show_filename_input:
                    # スペースキーが押された場合、再生ボタンと同じ機能を実行
                    debug_info.append(f"スペースキーで再生開始: {current_time}")
                    
                    # パラメータ更新
                    params['frequency'] = sliders[0].value
                    params['duration'] = sliders[1].value
                    params['volume'] = sliders[2].value
                    params['attack'] = sliders[3].value
                    params['decay'] = sliders[4].value
                    params['sustain'] = sliders[5].value
                    params['release'] = sliders[6].value
                    params['lpf'] = sliders[7].value
                    params['noise'] = sliders[8].value
                    
                    # 音を生成して再生
                    try:
                        current_sound = generate_waveform(
                            params['frequency'], params['duration'], params['volume'],
                            current_waveform, params
                        )
                        if current_sound:
                            current_sound.play()
                            last_played_params = params.copy()
                            last_played_params['waveform_type'] = current_waveform
                            last_played_params['waveform_name'] = waveform_types[current_waveform]
                            debug_info.append(f"音声生成成功: 波形={waveform_types[current_waveform]}, 周波数={params['frequency']:.1f}Hz")
                            
                            # 録音中なら録音リストに追加
                            if is_recording:
                                try:
                                    # 録音データが多すぎる場合は制限
                                    if len(recording_sounds) < 100:  # 最大100個まで
                                        recording_sounds.append(current_sound)
                                        debug_info.append(f"録音中: 音声追加 ({len(recording_sounds)}個目)")
                                    else:
                                        # 録音上限に達した場合は録音を停止
                                        is_recording = False
                                        record_button.text = "録音開始"
                                        record_button.color = LIGHT_RED
                                        error_message = "録音上限に達しました (100個)。録音を停止します。"
                                        error_time = current_time
                                        debug_info.append("録音上限に達しました")
                                except Exception as e:
                                    print(f"録音エラー: {e}")
                                    debug_info.append(f"録音エラー: {str(e)}")
                        else:
                            error_message = "音声生成に失敗しました"
                            error_time = current_time
                            debug_info.append("音声生成失敗")
                    except Exception as e:
                        print(f"音声生成エラー: {e}")
                        error_message = f"エラー: {str(e)}"
                        error_time = current_time
                        debug_info.append(f"音声生成エラー: {str(e)}")
                elif not show_filename_input and event.key in keys:
                    params['frequency'] = keys[event.key]
                    sliders[0].value = keys[event.key]
                    sliders[0].handle_y = sliders[0].y + (1 - (sliders[0].value - sliders[0].min_val) / (sliders[0].max_val - sliders[0].min_val)) * sliders[0].height
                    debug_info.append(f"キーボード演奏: {event.key} -> {params['frequency']:.1f}Hz")
                    
                    # 短い音を生成して再生
                    temp_params = params.copy()
                    temp_params['duration'] = 0.3  # キーボード演奏では短い音
                    try:
                        sound = generate_waveform(
                            temp_params['frequency'], temp_params['duration'], temp_params['volume'],
                            current_waveform, temp_params
                        )
                        if sound:
                            sound.play()
                            
                            # 録音中なら録音リストに追加
                            if is_recording:
                                try:
                                    # 録音データが多すぎる場合は制限
                                    if len(recording_sounds) < 100:  # 最大100個まで
                                        recording_sounds.append(sound)
                                        debug_info.append(f"録音中: 音声追加 ({len(recording_sounds)}個目)")
                                    else:
                                        # 録音上限に達した場合は録音を停止
                                        is_recording = False
                                        record_button.text = "録音開始"
                                        record_button.color = LIGHT_RED
                                        error_message = "録音上限に達しました (100個)。録音を停止します。"
                                        error_time = current_time
                                        debug_info.append("録音上限に達しました")
                                except Exception as e:
                                    print(f"録音エラー: {e}")
                                    debug_info.append(f"録音エラー: {str(e)}")
                    except Exception as e:
                        print(f"音声生成エラー: {e}")
                        debug_info.append(f"キーボード音声エラー: {str(e)}")
        
        # 画面描画
        screen.fill(BLACK)
        
        # タイトル
        title_text = large_font.render("シンプルシンセサイザー", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title_text, title_rect)
        
        subtitle_text = font.render("つまみを上下に動かして音を変化させよう", True, LIGHT_GREEN)
        subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, 90))
        screen.blit(subtitle_text, subtitle_rect)
        
        # 波形表示エリア
        pygame.draw.rect(screen, DARK_GRAY, (50, 520, WIDTH - 100, 150))
        pygame.draw.rect(screen, WHITE, (50, 520, WIDTH - 100, 150), width=1)
        wave_label = font.render("波形表示", True, WHITE)
        screen.blit(wave_label, (60, 530))
        
        # 波形の描画
        if last_played_params:
            wave_width = WIDTH - 120
            wave_height = 100
            wave_x = 60
            wave_y = 560
            
            # 波形の描画
            pygame.draw.line(screen, GRAY, (wave_x, wave_y + wave_height // 2), 
                           (wave_x + wave_width, wave_y + wave_height // 2), 1)
            
            points = []
            for i in range(wave_width):
                x = wave_x + i
                t = i / 100  # 時間パラメータ
                
                if last_played_params['waveform_type'] == 0:  # 正弦波
                    y = wave_y + wave_height // 2 - int(np.sin(2 * np.pi * t) * wave_height // 3)
                elif last_played_params['waveform_type'] == 1:  # 矩形波
                    y = wave_y + wave_height // 2 - int(np.sign(np.sin(2 * np.pi * t)) * wave_height // 3)
                elif last_played_params['waveform_type'] == 2:  # のこぎり波
                    y = wave_y + wave_height // 2 - int((2 * (t % 1) - 1) * wave_height // 3)
                elif last_played_params['waveform_type'] == 3:  # 三角波
                    y = wave_y + wave_height // 2 - int((2 * np.abs(2 * (t % 1 - 0.5)) - 1) * wave_height // 3)
                else:  # ノイズ
                    y = wave_y + wave_height // 2 - int(np.sin(2 * np.pi * t) * wave_height // 3)
                    noise = np.random.uniform(-0.3, 0.3) * wave_height // 2 * last_played_params['noise']
                    y += int(noise)
                
                points.append((x, y))
            
            # 波形の線を描画
            if points:
                pygame.draw.lines(screen, LIGHT_BLUE, False, points, 2)
        
        # スライダー描画
        for slider in sliders:
            slider.draw(screen)
        
        # ボタン描画
        play_button.draw(screen)
        save_button.draw(screen)
        waveform_button.draw(screen)
        record_button.draw(screen)
        
        # 録音中表示
        if is_recording:
            rec_time = (current_time - recording_start_time) / 1000.0  # 秒単位
            rec_text = font.render(f"録音中: {rec_time:.1f}秒 ({len(recording_sounds)}音)", True, LIGHT_RED)
            rec_rect = rec_text.get_rect(center=(WIDTH // 2, HEIGHT - 60))
            # 点滅効果
            if current_time % 1000 < 500:
                pygame.draw.circle(screen, LIGHT_RED, (WIDTH // 2 - rec_rect.width // 2 - 15, HEIGHT - 60), 8)
            screen.blit(rec_text, rec_rect)
        
        # キーボード説明
        keyboard_text = font.render("キーボード: Z=ド, X=レ, C=ミ, V=ファ, B=ソ, N=ラ, M=シ, <=高いド", True, WHITE)
        keyboard_rect = keyboard_text.get_rect(center=(WIDTH // 2, 400))
        screen.blit(keyboard_text, keyboard_rect)
        
        keyboard2_text = small_font.render("黒鍵: S=ド#, D=レ#, G=ファ#, H=ソ#, J=ラ#", True, LIGHT_YELLOW)
        keyboard2_rect = keyboard2_text.get_rect(center=(WIDTH // 2, 430))
        screen.blit(keyboard2_text, keyboard2_rect)
        
        space_text = font.render("スペースキーで再生", True, LIGHT_GREEN)
        space_rect = space_text.get_rect(center=(WIDTH // 2, 470))
        screen.blit(space_text, space_rect)
        
        # ファイル名入力表示
        if show_filename_input:
            pygame.draw.rect(screen, DARK_GRAY, (WIDTH // 2 - 300, HEIGHT // 2 - 50, 600, 100))
            pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 300, HEIGHT // 2 - 50, 600, 100), width=2)
            
            input_text = font.render("ファイル名: " + filename_input + ("_" if keyboard_focus and pygame.time.get_ticks() % 1000 < 500 else ""), True, WHITE)
            input_rect = input_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            screen.blit(input_text, input_rect)
            
            info_text = small_font.render("Enterで保存、Escでキャンセル", True, WHITE)
            info_rect = info_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
            screen.blit(info_text, info_rect)
        
        # エラーメッセージ表示
        if error_message and current_time - error_time < 3000:  # 3秒間表示
            error_surface = font.render(error_message, True, LIGHT_RED)
            error_rect = error_surface.get_rect(center=(WIDTH // 2, HEIGHT - 30))
            screen.blit(error_surface, error_rect)
        
        # 現在のパラメータ表示
        if last_played_params:
            param_title = font.render("最後に再生した音:", True, LIGHT_GREEN)
            param_rect = param_title.get_rect(topleft=(100, 370))
            screen.blit(param_title, param_rect)
            
            current_params = [
                f"周波数: {last_played_params['frequency']:.2f} Hz",
                f"長さ: {last_played_params['duration']:.2f} 秒",
                f"音量: {last_played_params['volume']:.2f}",
                f"波形: {last_played_params['waveform_name']}"
            ]
            
            for i, param_text in enumerate(current_params):
                text = small_font.render(param_text, True, WHITE)
                screen.blit(text, (120, 400 + i * 20))
        
        # デバッグ情報表示 (最新5件のみ)
        if debug_info:
            for i, info in enumerate(debug_info[-5:]):
                debug_text = small_font.render(info, True, LIGHT_GREEN)
                screen.blit(debug_text, (WIDTH - 400, 10 + i * 20))
            
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    import sys
    # コマンドライン引数で実行モードを切り替え
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        main(headless=True)
    else:
        try:
            pass
        except ImportError:
            print("Scipyライブラリが必要です。'pip install scipy'を実行してインストールしてください。")
        main(headless=False) 