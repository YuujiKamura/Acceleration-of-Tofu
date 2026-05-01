# PLAN — Acceleration of Tofu

> **Status: DRAFT**. このプランは外部 collaborator / AI agent (Claude Code, Codex 等) が独立判断するための reference。owner (YuujiKamura) が最終確定。`[?]` マークは推測 / 未確認、owner 確認待ち。

## はじめに

`web/` 配下に TypeScript + Phaser 3 で書かれた 2D 対戦 shooter。`legacy/pygbag/` の Python + pygame 版が源流 (ClaudeCode で生成された開発中デモ、現在は web 移植が主開発)。本プランは web 版を対象とする。

## 1. プレイヤーの目標

- 相手プレイヤーの HP を 0 にする (versus 1v1 local)
- 副次目標: 豆ゲージ管理 (overheat 回避)、水分ゲージ管理 (中央 regen)、ハイパーモード活用 (高火力 trade)

## 2. メインループ

1. 移動 (4 方向) + ダッシュ (i-frame 付き)
2. 武器 A (beam) で削る、武器 B (ballistic burst) で範囲圧
3. 当てる / 当てられる → 豆ゲージ ↑ → 上限で overheat lock
4. 中央エリアに戻ると水分 regen、overheat も回復
5. ハイパーゲージ充填 → スペシャル (spread burst, A+X) で打開
6. HP 0 でラウンド決着

## 3. 入力と操作方法

| | 移動 | A (beam) | B (ballistic) | Dash | Shield | Hyper | Special |
|--|--|--|--|--|--|--|--|
| P1 (ネギ) | ↑↓←→ | Z | X | LShift | S | Space | A+X |
| P2 (紅生姜) | WASD | F | G | `[?]` | `[?]` | `[?]` | `[?]` |

`[?]` 部分は README に記載なし、`web/src/systems/Input.ts` で確認必要 (DRAFT につき未追跡)。

## 4. 勝利と失敗の状態

- **勝利**: 相手の HP を 0 にした側
- **失敗**: 自分の HP が 0 になる
- **引き分け**: `[?]` (タイマー or 相討ち時の挙動、確認必要)
- ラウンド制 / 一発決着 / best-of-N: `[?]`

## 5. 進行度または難易度

- 対戦ゲーのため階層的進行はなし
- AI 強度: `web/src/systems/SimpleAI.ts` に存在。難易度カーブ・レベル切替は **未確認**
- トレーニングモード / 自動テストモードあり (`AutoTestScene.ts`)

## 6. ビジュアルの方向性

- 豆腐モチーフ: 白 (`TOFU_WHITE = 0xf5f5f0`)、ネギ緑 (`NEGI_GREEN = 0x00b446`)、紅生姜赤 (`BENI_RED = 0xc83232`)
- ファミコン風レトロ (BGM / 効果音)
- 弾は「豆腐粒 / 豆乳的物体」イメージ — 灰色 (gray) は theme から外れる (issue #18 該当)
- HUD: 豆ゲージ + 水分ゲージ + ハイパーゲージ (P1 上、P2 下 想定 / 確認要)

## 7. スタックとホスティングに関する前提条件

- ターゲット: モダンブラウザ (Chromium / Firefox / Safari) + モバイル portrait / landscape
- WASM 配信なし (TypeScript 直で配信、Phaser 3)
- ローカル 2P のみ (オンライン対戦は scope 外)
- Node 20+ for build
- GitHub Pages 配信 (`https://yuujikamura.github.io/Acceleration-of-Tofu/`)
- `legacy/pygbag/` 系の Python 版は archive 扱い、新機能は web 側のみ

## 8. マイルストーンの順序

`[?]` owner 未明示。issue tracker 上の cosmetic 系 (#16/#17/#18) が最近の focus に見えるが、より大きなロードマップ (新キャラ / online / レベルデザイン等) があるなら別途記載。

現時点で観測される **暗黙のマイルストーン**:

1. **Cosmetic 整備** (進行中) — #16 PAUSE icon overlap, #17 mobile portrait 非対称, #18 burst 灰色 → 豆腐白 (本 PR で部分対応)
2. **Python → TypeScript 移植の完成度** — `Player.ts` / `Projectile.ts` 内の `py:NNN` cross-reference を見ると Python 版機能が source of truth。差分検出 / 完全移植が暗黙の継続課題
3. **AI / バランス調整** — `SimpleAI.ts` の難易度 / 自動テストでの balance verification (これが本記事 npaka note の "難しいゲームロジックの改善" use case と直接対応)

## まとめ

本プランは記事 (https://note.com/npaka/n/n8fb9f73d2ce3) の OpenAI Codex game-dev guide の PLAN.md 8 項目仕様に従って書いた **DRAFT**。`[?]` 箇所は code 読みでは確定できず owner 確認が必要なギャップ。

書く過程で **発見されたギャップ**:

1. P2 操作系の README 未記載 (`Input.ts` に存在するはずだが README が古い)
2. 引き分け / ラウンド制の仕様が code / doc どちらにも明示なし
3. ロードマップ / マイルストーンが不在 — issue tracker と README に散在、集約 doc がない
4. Python → TypeScript 移植の完了基準が未定義 (どこまで移植して legacy/ を archive 化するか)

これら 4 点が PLAN.md を書くまで顕在化してなかった。**プランを書く行為自体が repo の隠れた undocumented decisions を炙り出す**、というのが記事 advice "プランを立てろ" のメカニズム。
