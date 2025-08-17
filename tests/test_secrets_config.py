"""
設定管理機能のユニットテスト

このテストファイルでは、secrets_config.py の設定読み込み機能を検証します。
Streamlit Secretsとローカルファイルのフォールバック機能をテストします。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSecretsConfig(unittest.TestCase):
    """設定管理機能のテストクラス"""

    def setUp(self):
        """各テストの前に実行される初期化処理"""
        self.sample_secrets = {
            "prompts": {
                "RULES_TEMPLATE": "テストルール",
                "QUESTION_TEMPLATE": "テスト質問",
                "JUDGE_TEMPLATE": "テスト判定",
                "FEEDBACK_TEMPLATE": "テストフィードバック",
                "EVALUATION_FORMAT": "テスト評価",
                "PARTIAL_FEEDBACK_TEMPLATE": "テスト部分フィードバック",
                "PARTIAL_EVALUATION_FORMAT": "テスト部分評価",
                "questions_list": [
                    {
                        "title": "テスト質問1",
                        "point_keys": ["テストポイント1"],
                        "content": "テスト内容1"
                    }
                ],
                "evaluation_points_list": {
                    "テストポイント1": "テスト説明1"
                }
            }
        }

    @patch('streamlit.secrets')
    def test_get_prompts_from_secrets_success(self, mock_secrets):
        """Streamlit Secretsからの正常な読み込みテスト"""
        # モックの設定
        mock_secrets.__getitem__.side_effect = lambda key: self.sample_secrets[key]
        
        # テスト対象をインポート（モック後に）
        from secrets_config import get_prompts_from_secrets
        
        # テスト実行
        result = get_prompts_from_secrets()
        
        # 結果検証
        self.assertEqual(result["RULES_TEMPLATE"], "テストルール")
        self.assertEqual(result["QUESTION_TEMPLATE"], "テスト質問")
        self.assertEqual(len(result["questions_list"]), 1)
        self.assertEqual(result["questions_list"][0]["title"], "テスト質問1")
        self.assertEqual(result["evaluation_points_list"]["テストポイント1"], "テスト説明1")

    @patch('streamlit.secrets')
    @patch('secrets_config.st.error')
    @patch('secrets_config.st.stop')
    def test_get_prompts_from_secrets_fallback_failure(self, mock_stop, mock_error, mock_secrets):
        """Secrets読み込み失敗時のフォールバック失敗テスト"""
        # Streamlit Secretsの読み込みを失敗させる
        mock_secrets.__getitem__.side_effect = KeyError("secrets not found")
        
        # prompts.pyのインポートも失敗させる
        with patch.dict('sys.modules', {'prompts': None}):
            # テスト対象をインポート
            from secrets_config import get_prompts_from_secrets
            
            # テスト実行
            get_prompts_from_secrets()
            
            # エラー表示とアプリ停止が呼ばれることを確認
            mock_error.assert_called_once()
            mock_stop.assert_called_once()

    @patch('streamlit.secrets')
    def test_get_prompts_from_secrets_fallback_success(self, mock_secrets):
        """Secrets読み込み失敗時のローカルファイルフォールバック成功テスト"""
        # Streamlit Secretsの読み込みを失敗させる
        mock_secrets.__getitem__.side_effect = KeyError("secrets not found")
        
        # ローカルのpromptsモジュールをモック
        mock_prompts = MagicMock()
        mock_prompts.RULES_TEMPLATE = "ローカルルール"
        mock_prompts.QUESTION_TEMPLATE = "ローカル質問"
        mock_prompts.JUDGE_TEMPLATE = "ローカル判定"
        mock_prompts.FEEDBACK_TEMPLATE = "ローカルフィードバック"
        mock_prompts.EVALUATION_FORMAT = "ローカル評価"
        mock_prompts.PARTIAL_FEEDBACK_TEMPLATE = "ローカル部分フィードバック"
        mock_prompts.PARTIAL_EVALUATION_FORMAT = "ローカル部分評価"
        mock_prompts.questions_list = [{"title": "ローカル質問", "point_keys": ["ローカルポイント"], "content": "ローカル内容"}]
        mock_prompts.evaluation_points_list = {"ローカルポイント": "ローカル説明"}
        
        with patch.dict('sys.modules', {'prompts': mock_prompts}):
            # テスト対象をインポート
            from secrets_config import get_prompts_from_secrets
            
            # テスト実行
            result = get_prompts_from_secrets()
            
            # ローカルファイルから読み込まれたことを確認
            self.assertEqual(result["RULES_TEMPLATE"], "ローカルルール")
            self.assertEqual(result["questions_list"][0]["title"], "ローカル質問")


class TestSecretsConfigEdgeCases(unittest.TestCase):
    """エッジケースのテスト"""

    @patch('streamlit.secrets')
    def test_empty_questions_list(self, mock_secrets):
        """空の質問リストの処理テスト"""
        empty_secrets = {
            "prompts": {
                "RULES_TEMPLATE": "テストルール",
                "QUESTION_TEMPLATE": "テスト質問",
                "JUDGE_TEMPLATE": "テスト判定",
                "FEEDBACK_TEMPLATE": "テストフィードバック",
                "EVALUATION_FORMAT": "テスト評価",
                "PARTIAL_FEEDBACK_TEMPLATE": "テスト部分フィードバック",
                "PARTIAL_EVALUATION_FORMAT": "テスト部分評価",
                "questions_list": [],  # 空のリスト
                "evaluation_points_list": {}  # 空の辞書
            }
        }
        
        mock_secrets.__getitem__.side_effect = lambda key: empty_secrets[key]
        
        from secrets_config import get_prompts_from_secrets
        
        result = get_prompts_from_secrets()
        
        # 空のリストと辞書が正しく処理されることを確認
        self.assertEqual(len(result["questions_list"]), 0)
        self.assertEqual(len(result["evaluation_points_list"]), 0)

    @patch('streamlit.secrets')
    def test_missing_questions_list_key(self, mock_secrets):
        """questions_listキーが欠けている場合のテスト"""
        incomplete_secrets = {
            "prompts": {
                "RULES_TEMPLATE": "テストルール",
                "QUESTION_TEMPLATE": "テスト質問",
                "JUDGE_TEMPLATE": "テスト判定",
                "FEEDBACK_TEMPLATE": "テストフィードバック",
                "EVALUATION_FORMAT": "テスト評価",
                "PARTIAL_FEEDBACK_TEMPLATE": "テスト部分フィードバック",
                "PARTIAL_EVALUATION_FORMAT": "テスト部分評価",
                # questions_listキーが欠けている
                "evaluation_points_list": {"テストポイント": "テスト説明"}
            }
        }
        
        mock_secrets.__getitem__.side_effect = lambda key: incomplete_secrets[key]
        
        from secrets_config import get_prompts_from_secrets
        
        result = get_prompts_from_secrets()
        
        # questions_listが空のリストとして初期化されることを確認
        self.assertEqual(len(result["questions_list"]), 0)
        self.assertEqual(len(result["evaluation_points_list"]), 1)


if __name__ == '__main__':
    # テスト実行
    unittest.main(verbosity=2)