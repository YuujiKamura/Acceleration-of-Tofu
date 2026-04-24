# アクセラレーションオブ豆腐 / Acceleration of Tofu

**ブラウザで即プレイ
👉 https://yuujikamura.github.io/Acceleration-of-Tofu/

**Languages**: [日本語](#日本語) · [English](#english) · [中文](#中文简体) · [한국어](#한국어)

---

## 日本語

豆腐をモチーフにした2Dシューティングゲーム。ネギと紅生姜の対決をテーマにした、ユニークな対戦アクションゲームです。
なぜか人を笑顔にする、AIがつくった変なBGM。

### 特徴

- 豆腐をモチーフにしたキャラクターデザイン
- ダッシュ、シールド、ハイパーモードなどの多彩なアクション
- ファミコン風のレトロサウンド
- 2人対戦モード、トレーニングモード、自動テストモード搭載
- カスタマイズ可能なキーコンフィグ
- **ブラウザでプレイ可能**（pygbag による WASM 対応、GitHub Pages 配信）

### 必要条件（ローカル実行）

- Python 3.8以上
- Pygame 2.0.0以上

### インストール

1. リポジトリをクローン：
```bash
git clone https://github.com/YuujiKamura/Acceleration-of-Tofu.git
cd Acceleration-of-Tofu
```

2. 依存パッケージをインストール：
```bash
pip install -r requirements.txt
```

### 実行方法

ローカルで起動：
```bash
python main.py
```

ブラウザ版（ローカルでpygbagサーバ）：
```bash
pip install pygbag
pygbag main.py
# http://localhost:8000 にアクセス
```

### 操作方法

#### プレイヤー1（ネギ）
- 移動: 矢印キー
- 攻撃A（ビームライフル）: Z
- 攻撃B（バリスティック）: X
- ダッシュ: 左シフト
- シールド: S
- ハイパーモード: スペース
- スペシャル（スプレッド）: A + X

#### プレイヤー2（紅生姜）
- 移動: WASD
- 攻撃A: F
- 攻撃B: G
- ダッシュ: 右シフト
- シールド: H
- ハイパーモード: Tab
- スペシャル: R + G

※ キーコンフィグでカスタマイズ可能

### ゲームモード

1. 対戦モード — 2人のプレイヤーで対戦、HPが0になったプレイヤーの負け
2. トレーニングモード — 1人で練習可能、HPが0になっても自動回復
3. 自動テストモード — AIどうしの対戦を観戦、テスト時間を選択可能

### ディレクトリ構造

```
.
├── assets/          # 画像、音声 (ogg)
├── game/            # ゲームのメインロジック
├── synth/           # オフラインBGM/効果音生成ツール（実行時には不要）
├── tests/           # テストコード
├── bgm/             # 事前レンダリング済みBGM (ogg)
├── main.py          # エントリーポイント（async main、pygbag対応）
├── requirements.txt # 依存パッケージ
└── .github/workflows/pygbag-deploy.yml # GitHub Pages 自動ビルド&デプロイ
```

### 開発者向け情報

**テスト実行:**
```bash
python -m pytest tests/
```

**効果音/BGM 生成（オフラインツール）:**
```bash
python synth/rockman_title.py   # タイトルBGM生成
python synth/generate_sounds.py # 効果音生成
```

**GitHub Pages 再デプロイ:**
master ブランチに push すれば `.github/workflows/pygbag-deploy.yml` が自動で pygbag build → Pages に deploy。

---

## English

A 2D fighting shooter game themed around tofu. A unique versus-action game centered on the battle between negi (green onion) and beni-shoga (red pickled ginger). Features strangely charming AI-generated BGM.

### Play in browser
👉 https://yuujikamura.github.io/Acceleration-of-Tofu/

(Powered by [pygbag](https://pygame-web.github.io/) — Pygame running in WebAssembly via Pyodide.)

### Features

- Tofu-inspired character design
- Dash, shield, hyper mode and more varied actions
- Famicom-style retro sound
- 2-player versus, training, and auto-test (AI vs AI) modes
- Customizable key config
- **Browser-playable** via pygbag WASM, hosted on GitHub Pages

### Local requirements

- Python 3.8+
- Pygame 2.0.0+

### Install & Run (local)

```bash
git clone https://github.com/YuujiKamura/Acceleration-of-Tofu.git
cd Acceleration-of-Tofu
pip install -r requirements.txt
python main.py
```

### Controls

| Action | Player 1 (Negi) | Player 2 (Beni-shoga) |
|---|---|---|
| Move | Arrow keys | WASD |
| Attack A (beam rifle) | Z | F |
| Attack B (ballistic) | X | G |
| Dash | Left Shift | Right Shift |
| Shield | S | H |
| Hyper mode | Space | Tab |
| Special (spread) | A + X | R + G |

Key config is customizable.

### Game modes

1. **Versus** — 2-player PvP, HP-to-zero loss
2. **Training** — solo practice, HP auto-recovers
3. **Auto-test** — AI vs AI spectator mode, selectable duration

### For developers

```bash
# Run tests
python -m pytest tests/

# Generate sounds/BGM (offline tools)
python synth/rockman_title.py
python synth/generate_sounds.py

# Local browser build (pygbag dev server at :8000)
pip install pygbag
pygbag main.py
```

Pushing to `master` auto-rebuilds and redeploys to GitHub Pages via the workflow at `.github/workflows/pygbag-deploy.yml`.

---

## 中文（简体）

以豆腐为主题的2D对战射击游戏。围绕葱和红姜对决的独特动作对战游戏。由AI生成的、不知为何令人微笑的奇妙BGM。

### 浏览器即玩
👉 https://yuujikamura.github.io/Acceleration-of-Tofu/

（基于 [pygbag](https://pygame-web.github.io/) — 通过 Pyodide 在 WebAssembly 中运行 Pygame。）

### 特点

- 豆腐主题角色设计
- 冲刺、护盾、超速模式等多样化动作
- Famicom 风格复古音效
- 双人对战、训练、自动测试（AI对战）三种模式
- 可自定义按键配置
- 通过 pygbag WASM 技术**在浏览器中游玩**，托管于 GitHub Pages

### 本地运行

```bash
git clone https://github.com/YuujiKamura/Acceleration-of-Tofu.git
cd Acceleration-of-Tofu
pip install -r requirements.txt
python main.py
```

需要 Python 3.8+ 和 Pygame 2.0.0+。

### 操作

| 动作 | 玩家1（葱） | 玩家2（红姜） |
|---|---|---|
| 移动 | 方向键 | WASD |
| 攻击A（光束步枪） | Z | F |
| 攻击B（弹道） | X | G |
| 冲刺 | 左Shift | 右Shift |
| 护盾 | S | H |
| 超速模式 | 空格 | Tab |
| 特殊（散射） | A + X | R + G |

按键配置可自定义。

---

## 한국어

두부를 모티브로 한 2D 대전 슈팅 게임. 파와 붉은 생강의 대결을 주제로 한 독특한 대전 액션 게임. 왠지 사람을 미소짓게 만드는, AI가 만든 이상한 BGM.

### 브라우저에서 플레이
👉 https://yuujikamura.github.io/Acceleration-of-Tofu/

([pygbag](https://pygame-web.github.io/) 기반 — Pyodide를 통해 WebAssembly에서 Pygame 실행.)

### 특징

- 두부 모티브의 캐릭터 디자인
- 대시, 실드, 하이퍼 모드 등 다양한 액션
- 패미컴 스타일 레트로 사운드
- 2인 대전, 트레이닝, 자동 테스트(AI 대전) 모드 탑재
- 커스터마이징 가능한 키 설정
- pygbag WASM으로 **브라우저 플레이 가능**, GitHub Pages 배포

### 로컬 실행

```bash
git clone https://github.com/YuujiKamura/Acceleration-of-Tofu.git
cd Acceleration-of-Tofu
pip install -r requirements.txt
python main.py
```

Python 3.8+ 및 Pygame 2.0.0+ 필요.

### 조작

| 동작 | 플레이어1 (파) | 플레이어2 (붉은 생강) |
|---|---|---|
| 이동 | 화살표 키 | WASD |
| 공격A (빔 라이플) | Z | F |
| 공격B (탄도) | X | G |
| 대시 | 왼쪽 Shift | 오른쪽 Shift |
| 실드 | S | H |
| 하이퍼 모드 | Space | Tab |
| 스페셜 (확산) | A + X | R + G |

키 설정은 커스터마이징 가능.

---

## ライセンス / License / 许可 / 라이선스

MIT License.
