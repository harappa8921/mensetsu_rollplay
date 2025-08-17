"""
面接ロジックのユニットテスト

このテストファイルでは、interview_logic.py の各関数の動作を検証します。
AI関連の機能はモックを使用して、プロンプトに依存しない部分をテストします。
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interview_logic import (
    add_newlines_by_period,
    get_history_text,
    get_rules
)


class TestInterviewLogic(unittest.TestCase):
    """面接ロジック関数のテストクラス"""

    def setUp(self):
        """各テストの前に実行される初期化処理"""
        self.sample_profile = {
            "age": "30",
            "current_gyokai": "IT",
            "current_job": "エンジニア",
            "role": "リーダー",
            "experience_years": "5年",
            "target_gyokai": "コンサルティング",
            "target_job": "データサイエンティスト"
        }

    def test_add_newlines_by_period(self):
        """句読点での改行挿入機能のテスト"""
        # 基本的なケース
        input_text = "こんにちは。元気ですか？はい、元気です！"
        expected = "こんにちは。\n元気ですか？\nはい、元気です！\n"
        result = add_newlines_by_period(input_text)
        self.assertEqual(result, expected)
        
        # 句読点がない場合
        input_text = "改行なし"
        expected = "改行なし"
        result = add_newlines_by_period(input_text)
        self.assertEqual(result, expected)
        
        # 空文字列の場合
        input_text = ""
        expected = ""
        result = add_newlines_by_period(input_text)
        self.assertEqual(result, expected)

    def test_get_history_text(self):
        """チャット履歴テキスト変換機能のテスト"""
        # 空の履歴
        empty_history = []
        result = get_history_text(empty_history)
        self.assertEqual(result, "")
        
        # 通常の履歴
        chat_history = [
            {"role": "assistant", "content": "質問です"},
            {"role": "user", "content": "回答です"},
            {"role": "assistant", "content": "次の質問です"}
        ]
        
        expected = "面接官：質問です\nあなた：回答です\n面接官：次の質問です"
        result = get_history_text(chat_history)
        self.assertEqual(result, expected)

    @patch('interview_logic.get_prompts_from_secrets')
    def test_get_rules(self, mock_get_prompts):
        """ルールプロンプト生成機能のテスト"""
        # モックの設定
        mock_prompts = {
            "RULES_TEMPLATE": """年齢：{age}、現在：{current_gyokai}業界{current_job}、
役割：{role}、経験：{experience_years}、
転職先：{target_gyokai}業界{target_job}"""
        }
        mock_get_prompts.return_value = mock_prompts
        
        # テスト実行
        result = get_rules(self.sample_profile)
        
        # 結果検証
        expected = """年齢：30、現在：IT業界エンジニア、
役割：リーダー、経験：5年、
転職先：コンサルティング業界データサイエンティスト"""
        self.assertEqual(result, expected)
        
        # モックが正しく呼ばれたか確認
        mock_get_prompts.assert_called_once()


class TestInterviewLogicIntegration(unittest.TestCase):
    """統合テスト - 複数の関数の組み合わせテスト"""

    def test_history_and_formatting_integration(self):
        """履歴取得と文字列整形の統合テスト"""
        # サンプル履歴作成
        chat_history = [
            {"role": "assistant", "content": "志望動機を教えてください。"},
            {"role": "user", "content": "転職したいです。成長したいです！"}
        ]
        
        # 履歴をテキストに変換
        history_text = get_history_text(chat_history)
        
        # 改行を追加
        formatted_text = add_newlines_by_period(history_text)
        
        # 期待値
        expected = "面接官：志望動機を教えてください。\nあなた：転職したいです。\n成長したいです！\n"
        
        self.assertEqual(formatted_text, expected)


class TestErrorHandling(unittest.TestCase):
    """エラーハンドリングのテスト"""

    def test_get_history_text_with_invalid_data(self):
        """不正なデータでの履歴取得テスト"""
        # roleキーが欠けている場合
        invalid_history = [
            {"content": "テストメッセージ"}
        ]
        
        # エラーが発生することを確認
        with self.assertRaises(KeyError):
            get_history_text(invalid_history)

    def test_add_newlines_with_none(self):
        """None値での改行追加テスト"""
        # None値の場合はエラーが発生することを確認
        with self.assertRaises(TypeError):
            add_newlines_by_period(None)


if __name__ == '__main__':
    # テスト実行
    unittest.main(verbosity=2)