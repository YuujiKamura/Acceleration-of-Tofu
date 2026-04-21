from enum import Enum, auto

class GameState(Enum):
    """ゲームの状態を表す列挙型"""
    TITLE = auto()        # タイトル画面
    CHARACTER_SELECT = auto()  # キャラクター選択画面
    GAME = auto()         # ゲームプレイ中
    TRAINING = auto()     # トレーニングモード
    AUTO_TEST = auto()    # 自動テストモード
    PAUSE = auto()        # ポーズ中
    OPTIONS = auto()      # オプション画面
    KEY_CONFIG = auto()   # キーコンフィグ画面
    CONTROLS = auto()     # 操作説明画面
    GAME_OVER = auto()    # ゲームオーバー
    RESULT = auto()       # リザルト画面 