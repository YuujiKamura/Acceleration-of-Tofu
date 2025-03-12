# シンプルドラムマシン

シンプルなビートを作成できるPythonベースのドラムマシンです。グリッド上でドラムパターンを作成し、ループ再生できます。

## 特徴

- 5種類のドラム音源（キック、スネア、ハイハット、トム、クラップ）
- 16ステップのビートグリッド
- テンポ調整機能 (60-200 BPM)
- 基本パターン（4拍子、ロック、ディスコ）のプリセット
- 視覚的なビート表示と再生位置インジケーター

## 使い方

1. グリッド上のセルをクリックして、ドラムパターンを作成します。
2. 「再生」ボタンをクリックしてビートを再生します。
3. 「停止」ボタンで再生を停止します。
4. 「クリア」ボタンでパターンをリセットします。
5. 下部のスライダーでテンポを調整できます。
6. プリセットパターンボタンで基本的なビートを素早く作成できます。

## 必要条件

- Python 3.x
- pygame
- numpy
- scipy

## インストール方法

```
pip install pygame numpy scipy
```

## 実行方法

```
python drum_machine.py
```

## 操作方法

- グリッドのセルをクリックして音を配置/削除
- 「再生」ボタンまたはスペースキーでループ再生
- 「停止」ボタンまたはスペースキーで停止
- 「クリア」ボタンでグリッドをリセット
- テンポスライダーでリズムの速さを調整

## 開発情報

このドラムマシンはPygameを使用して作成されました。サウンドはNumPyを使用して生成されています。 