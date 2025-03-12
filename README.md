# アクセラレーションオブ豆腐

豆腐をモチーフにした2Dシューティングゲーム。ネギと紅生姜の対決をテーマにした、ユニークな対戦アクションゲームです。

## 特徴

- 豆腐をモチーフにしたキャラクターデザイン
- ダッシュ、シールド、ハイパーモードなどの多彩なアクション
- ファミコン風のレトロサウンド
- 2人対戦モード、トレーニングモード、自動テストモード搭載
- カスタマイズ可能なキーコンフィグ

## 必要条件

- Python 3.8以上
- Pygame 2.0.0以上

## インストール

1. リポジトリをクローン：
```bash
git clone https://github.com/yourusername/acceleration-of-tofu.git
cd acceleration-of-tofu
```

2. 依存パッケージをインストール：
```bash
pip install -r requirements.txt
```

## 実行方法

ゲームを起動：
```bash
python main.py
```

## ディレクトリ構造

```
.
├── assets/          # 画像、音声などのアセット
├── game/           # ゲームのメインロジック
│   ├── arena.py    # アリーナ（ステージ）の管理
│   ├── constants.py # 定数定義
│   ├── game.py     # ゲームのメインクラス
│   ├── hud.py      # HUD（スコア表示など）
│   ├── player.py   # プレイヤー関連の処理
│   └── projectile.py # 弾の処理
├── synth/          # サウンドエンジン
│   ├── rockman_title.py  # タイトルBGM生成
│   ├── famicom_sound.py  # ファミコン風音源
│   └── ...
├── tests/          # テストコード
├── main.py         # エントリーポイント
└── requirements.txt # 依存パッケージ

## 操作方法

### プレイヤー1（ネギ）
- 移動: 矢印キー
- 攻撃A（ビームライフル）: Z
- 攻撃B（バリスティック）: X
- ダッシュ: 左シフト
- シールド: S
- ハイパーモード: スペース
- スペシャル（スプレッド）: A + X

### プレイヤー2（紅生姜）
- 移動: WASD
- 攻撃A: F
- 攻撃B: G
- ダッシュ: 右シフト
- シールド: H
- ハイパーモード: Tab
- スペシャル: R + G

※ キーコンフィグでカスタマイズ可能

## ゲームモード

1. 対戦モード
   - 2人のプレイヤーで対戦
   - HPが0になったプレイヤーの負け

2. トレーニングモード
   - 1人で練習可能
   - HPが0になっても自動回復

3. 自動テストモード
   - AIどうしの対戦を観戦
   - テスト時間を選択可能

## 開発者向け情報

### テストの実行

```bash
python -m pytest tests/
```

### サウンドの生成

新しいBGMや効果音を生成：
```bash
python synth/rockman_title.py  # タイトルBGM生成
python synth/generate_sounds.py  # 効果音生成
```

## ライセンス

MITライセンス 