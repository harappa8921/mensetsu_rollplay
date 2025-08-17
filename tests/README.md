# テストコード

このディレクトリには、面接ロールプレイシステムのテストコードが含まれています。

## テストファイル構成

### test_interview_logic.py
- **対象**: interview_logic.py の関数
- **内容**: ビジネスロジック関数のユニットテスト
- **テスト内容**:
  - `add_newlines_by_period()`: 句読点での改行挿入
  - `get_history_text()`: チャット履歴のテキスト変換
  - `get_rules()`: ルールプロンプトの生成
  - エラーハンドリング

### test_secrets_config.py
- **対象**: secrets_config.py の設定管理機能
- **内容**: 設定読み込み機能のテスト
- **テスト内容**:
  - Streamlit Secrets からの正常読み込み
  - ローカルファイルへのフォールバック
  - エラーケースの処理
  - 空データの処理

### test_integration.py
- **対象**: システム全体の統合テスト
- **内容**: 複数コンポーネントの連携テスト
- **テスト内容**:
  - 面接ワークフローの統合
  - エラーハンドリングの統合
  - パフォーマンステスト

## テスト実行方法

### 全テスト実行
```bash
python -m pytest tests/ -v
```

### 個別テスト実行
```bash
# ユニットテストのみ
python -m pytest tests/test_interview_logic.py -v

# 設定テストのみ
python -m pytest tests/test_secrets_config.py -v

# 統合テストのみ
python -m pytest tests/test_integration.py -v
```

### unittest での実行
```bash
# 個別ファイル実行
python tests/test_interview_logic.py

# 全テスト実行
python -m unittest discover tests -v
```

## テストカバレッジ

### カバー対象
- ✅ 文字列処理関数（改行挿入、履歴変換）
- ✅ 設定管理機能（Secrets読み込み、フォールバック）
- ✅ エラーハンドリング
- ✅ 統合ワークフロー

### カバー対象外（制限事項）
- ❌ AI関連機能（LangChain、OpenAI API）
- ❌ Streamlit UI コンポーネント
- ❌ 外部API呼び出し

AI関連機能は、プロンプトが非公開であること、および外部APIの依存性があることから、モックを使用した最小限のテストのみ実装しています。

## モック使用箇所

- **LangChain機能**: 完全にモック化
- **OpenAI API**: validate_api_key のみモック化
- **Streamlit Secrets**: 完全にモック化
- **プロンプト読み込み**: モックデータを使用

## テスト設計方針

1. **ユニットテスト**: 個別関数の動作検証
2. **統合テスト**: 複数機能の連携検証
3. **エラーテスト**: 異常系の動作検証
4. **パフォーマンステスト**: 大量データでの動作検証

## 注意事項

- テスト実行時は実際のAPIキーは不要です
- prompts.py ファイルが存在しなくてもテストは実行可能です
- モックを使用しているため、実際のAI機能は検証されません