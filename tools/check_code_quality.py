#!/usr/bin/env python
"""
コード品質チェックスクリプト
使用方法: python tools/check_code_quality.py
"""

import os
import subprocess
import re
import sys
from pathlib import Path
from datetime import datetime

# 作業ディレクトリをプロジェクトルートに変更
os.chdir(Path(__file__).parent.parent)

def print_header(text):
    """ヘッダーテキストを出力"""
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)

def run_command(cmd):
    """コマンドを実行し出力を返す"""
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout

def check_complexity():
    """複雑度チェック"""
    print_header("循環的複雑度チェック")
    
    # 高複雑度関数の検出
    output = run_command("radon cc --min E game/")
    if output.strip():
        print("⚠️ 複雑度が高すぎる関数が見つかりました（E以上）:")
        print(output)
    else:
        print("✅ 複雑度E以上の関数はありません")
    
    # 全体の複雑度の概要
    print("\n📊 複雑度の概要:")
    summary = run_command("radon cc game/ --average")
    print(summary)
    
    return bool(output.strip())

def check_file_size():
    """ファイルサイズチェック"""
    print_header("ファイルサイズチェック")
    
    output = run_command("radon raw game/ -s")
    
    # 大きなファイルを検出
    big_files = re.findall(r'(game[\\/][^\n]+)\n\s+LOC: (\d+)', output)
    big_files = [(f, int(loc)) for f, loc in big_files if int(loc) > 500]
    
    if big_files:
        print("⚠️ 以下のファイルは500行を超えています:")
        for file, loc in sorted(big_files, key=lambda x: x[1], reverse=True):
            print(f"  - {file}: {loc}行")
    else:
        print("✅ すべてのファイルは500行未満です")
    
    # 全体の統計
    total_match = re.search(r'\*\* Total \*\*\s+LOC: (\d+)', output)
    if total_match:
        total_loc = int(total_match.group(1))
        print(f"\n📊 プロジェクト全体の行数: {total_loc}行")
    
    return bool(big_files)

def check_maintainability():
    """保守性指標の確認"""
    print_header("保守性指標")
    
    output = run_command("radon mi game/")
    print(output)
    
    # 保守性の低いファイルをチェック
    low_mi_files = re.findall(r'(game[\\/][^\n]+) - ([ABCF])\s+\(([0-9.]+)\)', output)
    low_mi_files = [(f, grade, score) for f, grade, score in low_mi_files if grade in ['C', 'F']]
    
    return bool(low_mi_files)

def generate_report():
    """レポートの生成"""
    has_complexity_issues = check_complexity()
    has_size_issues = check_file_size()
    has_maintainability_issues = check_maintainability()
    
    print_header("レポートサマリー")
    print(f"📅 チェック日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if has_complexity_issues or has_size_issues or has_maintainability_issues:
        print("\n⚠️ リファクタリングを検討すべき問題が見つかりました")
        
        if has_complexity_issues:
            print("  - 複雑度が高すぎる関数があります")
        if has_size_issues:
            print("  - 大きすぎるファイルがあります")
        if has_maintainability_issues:
            print("  - 保守性の低いコードがあります")
        
        # 改善提案
        print("\n📝 改善提案:")
        print("  1. 大きなクラスや関数を複数の小さなものに分割する")
        print("  2. 長すぎるメソッドを機能単位で分割する")
        print("  3. 複雑な条件分岐をシンプルにする（ストラテジーパターンの使用など）")
        print("  4. 共通処理を独立した関数に抽出する")
        print("  5. 関連機能を別ファイルに移動させる")
        
        return 1
    else:
        print("\n✅ おめでとうございます！コード品質に問題は見つかりませんでした。")
        return 0

if __name__ == "__main__":
    # 必要なライブラリの確認
    try:
        import radon
    except ImportError:
        print("Error: radon がインストールされていません。")
        print("pip install radon を実行してインストールしてください。")
        sys.exit(1)
    
    # レポート生成
    exit_code = generate_report()
    sys.exit(exit_code) 