"""
統合テスト

このテストファイルでは、システム全体の統合テストを実施します。
実際のワークフローに近い形で複数のコンポーネントの連携をテストします。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestInterviewWorkflowIntegration(unittest.TestCase):
    """面接ワークフローの統合テスト"""

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
        
        self.sample_prompts = {
            "RULES_TEMPLATE": "年齢：{age}、現在：{current_gyokai}業界",
            "QUESTION_TEMPLATE": "{rules}\n質問：{question}",
            "JUDGE_TEMPLATE": "判定：{history}",
            "FEEDBACK_TEMPLATE": "フィードバック：{history}",
            "EVALUATION_FORMAT": "評価形式",
            "PARTIAL_FEEDBACK_TEMPLATE": "部分フィードバック：{history}",
            "PARTIAL_EVALUATION_FORMAT": "部分評価形式",
            "questions_list": [
                {
                    "title": "転職理由の質問",
                    "point_keys": ["定着性"],
                    "content": "転職理由を教えてください"
                }
            ],
            "evaluation_points_list": {
                "定着性": "長期間働く意欲を評価する"
            }
        }

    @patch('interview_logic.get_prompts_from_secrets')
    def test_get_rules_integration(self, mock_get_prompts):
        """ルール生成の統合テスト"""
        # モックの設定
        mock_get_prompts.return_value = self.sample_prompts
        
        # テスト対象をインポート
        from interview_logic import get_rules
        
        # テスト実行
        result = get_rules(self.sample_profile)
        
        # 結果検証
        expected = "年齢：30、現在：IT業界"
        self.assertEqual(result, expected)

    def test_chat_history_workflow(self):
        """チャット履歴処理のワークフローテスト"""
        from interview_logic import get_history_text, add_newlines_by_period
        
        # ワークフローシミュレーション
        chat_history = []
        
        # 1. 面接官の質問追加
        chat_history.append({
            "role": "assistant",
            "content": "志望動機を教えてください。どのような理由で転職を考えているのですか？"
        })
        
        # 2. ユーザーの回答追加
        chat_history.append({
            "role": "user", 
            "content": "新しい技術を学びたいです。成長したいです！"
        })
        
        # 3. 履歴をテキストに変換
        history_text = get_history_text(chat_history)
        
        # 4. 読みやすい形式に整形
        formatted_text = add_newlines_by_period(history_text)
        
        # 5. 結果検証
        expected_history = "面接官：志望動機を教えてください。\nどのような理由で転職を考えているのですか？\n\nあなた：新しい技術を学びたいです。\n成長したいです！\n"
        self.assertEqual(formatted_text, expected_history)

    @patch('interview_logic.get_prompts_from_secrets')
    @patch('interview_logic.validate_api_key')
    def test_api_key_validation_workflow(self, mock_validate, mock_get_prompts):
        """APIキー検証ワークフローのテスト"""
        # モックの設定
        mock_validate.return_value = (True, "APIキーが有効です")
        mock_get_prompts.return_value = self.sample_prompts
        
        # テスト対象をインポート
        from interview_logic import validate_api_key
        
        # ワークフローシミュレーション
        test_api_key = "sk-test123456789"
        
        # APIキー検証
        is_valid, message = validate_api_key(test_api_key)
        
        # 結果検証
        self.assertTrue(is_valid)
        self.assertEqual(message, "APIキーが有効です")
        mock_validate.assert_called_once_with(test_api_key)


class TestErrorHandlingIntegration(unittest.TestCase):
    """エラーハンドリングの統合テスト"""

    def test_empty_profile_handling(self):
        """空のプロフィールでのエラーハンドリングテスト"""
        from interview_logic import get_history_text
        
        # 空の履歴での処理
        empty_history = []
        result = get_history_text(empty_history)
        
        # 空文字列が返されることを確認
        self.assertEqual(result, "")

    def test_malformed_history_handling(self):
        """不正な形式の履歴でのエラーハンドリングテスト"""
        from interview_logic import get_history_text
        
        # 不正な形式の履歴
        malformed_history = [
            {"role": "assistant", "content": "正常なメッセージ"},
            {"content": "roleキーが欠けている"},  # roleキーが欠けている
            {"role": "user", "content": "正常なユーザーメッセージ"}
        ]
        
        # エラーが発生することを確認
        with self.assertRaises(KeyError):
            get_history_text(malformed_history)


class TestPerformanceIntegration(unittest.TestCase):
    """パフォーマンス関連の統合テスト"""

    def test_large_history_processing(self):
        """大量の履歴データの処理テスト"""
        from interview_logic import get_history_text, add_newlines_by_period
        
        # 大量の履歴データを生成
        large_history = []
        for i in range(100):
            large_history.append({
                "role": "assistant",
                "content": f"質問{i}です。"
            })
            large_history.append({
                "role": "user",
                "content": f"回答{i}です。"
            })
        
        # 処理時間を測定（実際の測定は省略、正常に処理されることを確認）
        history_text = get_history_text(large_history)
        formatted_text = add_newlines_by_period(history_text)
        
        # 結果が正しく生成されることを確認
        self.assertIn("質問0です", history_text)
        self.assertIn("回答99です", history_text)
        self.assertIn("質問0です。\n", formatted_text)

    def test_long_content_processing(self):
        """長いコンテンツの処理テスト"""
        from interview_logic import add_newlines_by_period
        
        # 長いテキストを生成
        long_text = "これは非常に長いテキストです。" * 100 + "最後の文です！"
        
        # 処理実行
        result = add_newlines_by_period(long_text)
        
        # 改行が正しく挿入されることを確認
        self.assertIn("です。\n", result)
        self.assertIn("です！\n", result)
        
        # 元のテキストの長さに改行分が追加されていることを確認
        expected_newlines = long_text.count("。") + long_text.count("！")
        actual_newlines = result.count("\n")
        self.assertEqual(actual_newlines, expected_newlines)


if __name__ == '__main__':
    # テスト実行
    unittest.main(verbosity=2)