# UML図 - Acceleration of Tofuプロジェクト構造

このディレクトリには、Pyreverseツールによって自動生成されたUML図が含まれています。
これらの図はプロジェクトのクラス構造とパッケージ間の依存関係を表しています。

## ファイル一覧

- `classes_AOT.puml` - gameモジュールのクラス図
- `packages_AOT.puml` - gameモジュールのパッケージ図
- `classes_AOT_ALL.puml` - プロジェクト全体のクラス図
- `packages_AOT_ALL.puml` - プロジェクト全体のパッケージ図

## 図の確認方法

これらのPlantUMLファイルを表示するには、以下の方法があります：

### オンラインでの確認

1. [PlantUML Web Server](http://www.plantuml.com/plantuml/uml/）にアクセス
2. .pumlファイルの内容をコピー＆ペースト
3. 「Submit」ボタンをクリック

### Visual Studio Codeでの確認

1. VSCodeに「PlantUML」拡張機能をインストール
2. .pumlファイルを開く
3. Alt+Dでプレビューを表示（またはコマンドパレットから「PlantUML: Preview」を選択）

### グラフィカルな図生成（Graphvizが必要）

```bash
# Graphvizをインストール（Windowsの場合）
# https://graphviz.org/download/ からインストーラをダウンロード

# PUMLファイルからPNG画像を生成
java -jar plantuml.jar classes_AOT.puml  # plantuml.jarは別途ダウンロードが必要
```

## UML図の見方

### クラス図の関係性

- `--|>` : 継承関係（矢印の先がスーパークラス）
- `--*` : コンポジション（強い集約関係）
- `--o` : 集約関係（弱い集約関係）
- `-->` : 関連関係

### パッケージ図の関係性

- `-->` : パッケージ間の依存関係（矢印の先が依存先）

## 元の図の再生成方法

以下のコマンドでUML図を再生成できます：

```bash
# Pylintをインストール（Pyreverseを含む）
pip install pylint

# gameモジュールのUML図生成
python -m pylint.pyreverse.main -o puml -p AOT game

# プロジェクト全体のUML図生成
python -m pylint.pyreverse.main -o puml -p AOT_ALL .
``` 