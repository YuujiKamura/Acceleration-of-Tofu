# Acceleration of Tofu クラス関係図

## 主要クラス構造

### GameState（列挙型）
- TITLE: タイトル画面
- GAME: ゲームプレイ中
- MENU: メニュー画面
- CONTROLS: 操作説明画面
- TRAINING: トレーニングモード
- PAUSE: 一時停止
- RESULT: 結果表示
- KEY_CONFIG: キー設定画面
- AUTO_TEST: 自動テスト
- OPTIONS: オプション画面

### Game
ゲーム全体を制御するメインクラス。
- **属性**:
  - screen: 描画先の画面
  - state: GameState（ゲームの状態）
  - arena: Arena（ゲームの舞台）
  - player1, player2: Player（プレイヤーキャラクター）
  - hud: HUD（情報表示）
  - projectiles: リスト（発射物の管理）
  - effects: リスト（エフェクトの管理）
  - sounds: 辞書（効果音の管理）
- **主要メソッド**:
  - init_sounds(): 効果音初期化
  - handle_keydown/keyup(): キー入力処理
  - update(): ゲーム状態更新
  - auto_test_ai_control(): AI制御
  - simple_ai_control(): 単純なAI
  - handle_collisions(): 衝突判定
  - draw(): 描画処理
  - add_projectile/add_effect(): オブジェクト追加
  - save/load_key_config(): キー設定管理

### Player
プレイヤーキャラクターを表現するクラス。
- **属性**:
  - x, y: 位置座標
  - radius: 当たり判定の半径
  - is_player1: プレイヤー1かどうか
  - health: 体力
  - heat: ヒートゲージ
  - hyper_gauge: ハイパーゲージ
  - weapons: 武器リスト
  - game: ゲームインスタンスへの参照
- **主要メソッド**:
  - update(): 状態更新
  - move(): 移動処理
  - handle_weapons(): 武器処理
  - create_projectile(): 発射物作成
  - activate_hyper(): ハイパーモード
  - take_damage(): ダメージ処理
  - draw(): 描画

### Weapon
武器を表現するクラス。
- **属性**:
  - name: 武器名
  - type: 武器タイプ
  - damage: 与えるダメージ
  - heat_cost: 消費ヒート量

### Projectile
発射物の基底クラス。
- **属性**:
  - x, y: 位置
  - speed_x, speed_y: 速度
  - damage: ダメージ
  - owner: 発射主
  - lifespan: 寿命
- **主要メソッド**:
  - update(): 状態更新
  - draw(): 描画
  - collides_with(): 衝突判定

#### 派生クラス
- **BeamProjectile**: ビーム型発射物
- **BallisticProjectile**: 弾道弾
- **MeleeProjectile**: 近接攻撃

### エフェクト関連クラス
- **DashRing**: ダッシュ時のエフェクト
- **ShieldEffect**: シールド効果の視覚表現
- **HyperEffect**: ハイパーモード時のエフェクト

### Arena
ゲームの舞台を表現するクラス。
- **属性**:
  - width, height: サイズ
  - center_x, center_y: 中心座標
- **主要メソッド**:
  - draw(): 描画
  - is_inside(): 領域内判定
  - is_near_border(): 端部判定

### HUD
プレイヤー情報を表示するクラス。
- **属性**:
  - player1, player2: 表示対象
  - font_name: フォント
- **主要メソッド**:
  - draw(): 描画
  - draw_health_bar(): 体力ゲージ描画
  - draw_heat_bar(): ヒートゲージ描画
  - draw_hyper_gauge(): ハイパーゲージ描画

## クラス間の関係
- **Game** は **GameState** を使用
- **Game** は **Arena**, **Player**, **HUD** を所有
- **Game** は **Projectile**, **DashRing**, **ShieldEffect**, **HyperEffect** を管理
- **Player** は **Weapon** を所有
- **Player** は **DashRing**, **ShieldEffect**, **HyperEffect** を生成
- **Player** は **Game** を参照
- **Projectile** の派生クラスとして **BeamProjectile**, **BallisticProjectile**, **MeleeProjectile** がある
- **Projectile** は **Player** を参照
- **HUD** は **Player** を参照 