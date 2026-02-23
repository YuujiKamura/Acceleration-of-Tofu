import pygame

# ゲームウィンドウの設定
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "アクセラレーションオブ豆腐"

# ゲームの定数
ARENA_RADIUS = 300  # 円形アリーナの半径
ARENA_CENTER_X = SCREEN_WIDTH // 2
ARENA_CENTER_Y = SCREEN_HEIGHT // 2
ARENA_WARNING_RADIUS = ARENA_RADIUS - 20  # 警告リングの半径

# フォント設定
JAPANESE_FONT_NAMES = ['Yu Gothic', 'Yu Gothic UI', 'MS Gothic', 'Meiryo', 'IPAGothic', 'Noto Sans CJK JP', 'MS UI Gothic', 'MS Mincho', 'BIZ UDゴシック', 'BIZ UDPゴシック']
DEFAULT_FONT = 'Arial'

# プレイヤー設定
PLAYER_SPEED = 5
PLAYER_DASH_SPEED = 9  # 12から9へ変更（ダッシュ速度を遅く）
DASH_RING_DURATION = 30  # フレーム数
DASH_COOLDOWN = 5  # ダッシュクールダウン（フレーム数）
SHIELD_DURATION = 50  # シールドの持続時間（フレーム数）（1秒から3秒に変更）
SHIELD_COOLDOWN = 120  # シールドのクールダウン（フレーム数）
HYPER_DURATION = 180  # ハイパーモードの持続時間（フレーム数）
MAX_HEALTH = 1000
MAX_HEAT = 300  # 最大ヒート（％）
MAX_HYPER = 300  # 最大ハイパーゲージ（％）
HEAT_DECREASE_RATE = 1.0  # ヒート減少率（0.5から1.0に変更、2倍の減少速度）
HYPER_DECREASE_RATE_AT_BORDER = 2  # 境界線でのハイパーゲージ減少率
HYPER_CONSUMPTION_RATE = 1.0  # ハイパーモード中の消費率（フレームごと）
HYPER_ACTIVATION_COST = 50  # ハイパーモード発動時の初期コスト

# 武器設定
WEAPON_TYPES = {
    "BEAM": "beam",         # レーザービーム
    "BALLISTIC": "ballistic", # 弾丸
    "MELEE": "melee"          # 近接攻撃
}

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
SKY = (0, 150, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
# 追加の色
NEGI_GREEN = (0, 180, 70)  # ネギの緑色
BENI_RED = (200, 50, 50)   # 紅生姜の赤色
TOFU_WHITE = (245, 245, 240)  # 豆腐の白色

# デフォルトのキーマッピング（Player 1）
# P1=矢印キー+ZXCVなど、P2=WASD+FGERTY で分離
DEFAULT_KEY_MAPPING_P1 = {
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
    pygame.K_z: "weapon_a",
    pygame.K_j: "weapon_a",
    pygame.K_x: "weapon_b",
    pygame.K_k: "weapon_b",
    pygame.K_SPACE: "hyper",
    pygame.K_l: "hyper",
    pygame.K_LSHIFT: "dash",
    pygame.K_h: "dash",
    pygame.K_c: "special",
    pygame.K_v: "shield",
}

# デフォルトのキーマッピング（Player 2）
DEFAULT_KEY_MAPPING_P2 = {
    pygame.K_w: "up",
    pygame.K_s: "down",
    pygame.K_a: "left",
    pygame.K_d: "right",
    pygame.K_f: "weapon_a",
    pygame.K_g: "weapon_b",
    pygame.K_r: "hyper",
    pygame.K_e: "dash",
    pygame.K_t: "special",
    pygame.K_y: "shield",
}

# 注: 実際のキーマッピングはGameクラスのインスタンス変数として管理する
# KEY_MAPPING_P1, KEY_MAPPING_P2, KEY_MAPPINGグローバル変数は削除

# 操作名の表示用日本語名
ACTION_NAMES = {
    "up": "上移動",
    "down": "下移動",
    "left": "左移動",
    "right": "右移動",
    "weapon_a": "武器A (ビームライフル)",
    "weapon_b": "武器B (バリスティック)",
    "hyper": "ハイパーモード",
    "dash": "ダッシュ",
    "special": "スペシャル攻撃",
    "shield": "シールド"
}

# キー名の表示用日本語名
KEY_NAMES = {
    pygame.K_UP: "↑",
    pygame.K_DOWN: "↓",
    pygame.K_LEFT: "←",
    pygame.K_RIGHT: "→",
    pygame.K_a: "A",
    pygame.K_b: "B",
    pygame.K_c: "C",
    pygame.K_d: "D",
    pygame.K_e: "E",
    pygame.K_f: "F",
    pygame.K_g: "G",
    pygame.K_h: "H",
    pygame.K_i: "I",
    pygame.K_j: "J",
    pygame.K_k: "K",
    pygame.K_l: "L",
    pygame.K_m: "M",
    pygame.K_n: "N",
    pygame.K_o: "O",
    pygame.K_p: "P",
    pygame.K_q: "Q",
    pygame.K_r: "R",
    pygame.K_s: "S",
    pygame.K_t: "T",
    pygame.K_u: "U",
    pygame.K_v: "V",
    pygame.K_w: "W",
    pygame.K_x: "X",
    pygame.K_y: "Y",
    pygame.K_z: "Z",
    pygame.K_0: "0",
    pygame.K_1: "1",
    pygame.K_2: "2",
    pygame.K_3: "3",
    pygame.K_4: "4",
    pygame.K_5: "5",
    pygame.K_6: "6",
    pygame.K_7: "7",
    pygame.K_8: "8",
    pygame.K_9: "9",
    pygame.K_SPACE: "スペース",
    pygame.K_RETURN: "Enter",
    pygame.K_ESCAPE: "Esc",
    pygame.K_TAB: "Tab",
    pygame.K_BACKSPACE: "Backspace",
    pygame.K_LSHIFT: "左Shift",
    pygame.K_RSHIFT: "右Shift",
    pygame.K_LCTRL: "左Ctrl",
    pygame.K_RCTRL: "右Ctrl",
    pygame.K_LALT: "左Alt",
    pygame.K_RALT: "右Alt"
}

# ゲームモード
GAME_MODES = {
    "TITLE": 0,
    "GAME": 1,
    "TRAINING": 2,
    "AUTO_TEST": 3  # 自動テストモード
}

# サウンド設定
SOUND_EFFECTS = {
    # BGM
    "BGM": {
        "TITLE": "assets/sounds/rockman_title.wav",
    },
    
    # UI/メニュー
    "UI": {
        "CURSOR": "assets/sounds/menu.wav",      # カーソル移動
        "SELECT": "assets/sounds/stage_clear.wav",  # 決定
        "CANCEL": "assets/sounds/damage.wav",     # キャンセル
        "HIGHSCORE": "assets/sounds/1up.wav",    # ハイスコア表示
    },
    
    # プレイヤーアクション
    "PLAYER": {
        "JUMP": "assets/sounds/jump.wav",        # ジャンプ
        "LAND": "assets/sounds/land.wav",        # 着地
        "DASH": "assets/sounds/special.wav",     # ダッシュ
        "SHIELD": "assets/sounds/shield.wav",    # シールド発動
        "HYPER": "assets/sounds/hyper.wav",      # ハイパーモード発動
    },
    
    # 攻撃
    "WEAPON": {
        "SHOT": "assets/sounds/shot.wav",        # 通常ショット
        "CHARGE": "assets/sounds/charge.wav",    # チャージショット
        "HIT": "assets/sounds/hit.wav",          # ヒット
        "SPECIAL": "assets/sounds/special.wav",  # スペシャル攻撃
    },
    
    # システム/その他
    "SYSTEM": {
        "BOSS": "assets/sounds/boss_appear.wav", # ボス出現
        "DAMAGE": "assets/sounds/damage.wav",    # ダメージ
        "ITEM": "assets/sounds/item.wav",        # アイテム取得
    }
}

# 音量設定
VOLUME_SETTINGS = {
    "BGM": 0.7,
    "UI": 0.6,
    "PLAYER": 0.7,
    "WEAPON": 0.5,
    "SYSTEM": 0.7
} 