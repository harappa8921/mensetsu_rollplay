# 面接ロールプレイシステム 👨‍💼

LangChainとStreamlitを使った転職面接のロールプレイシステムです。AIが面接官役となり、リアルな面接体験とフィードバックを提供します。

## 🌟 主な機能

- **パーソナライズされた面接体験**: プロフィールに基づいた質問生成
- **リアルタイム深掘り質問**: 回答に応じた追加質問
- **詳細なフィードバック**: 5つの評価軸でのスキル分析
- **セキュアなAPIキー管理**: ユーザー自身のOpenAI APIキーを使用

## 🏗️ アーキテクチャ

### ファイル構成
```
├── rollplay.py          # Streamlit UI部分
├── interview_logic.py   # ビジネスロジック
├── secrets_config.py    # プロンプト管理（Secrets対応）
├── prompts.py          # 実際のプロンプト（非公開、.gitignoreで除外）
├── requirements.txt     # 依存関係
└── .gitignore          # Git除外設定
```

### 設計思想
- **プロンプト非公開化**: 機密性の高いプロンプトはGitHubに公開されません
- **モジュール分離**: UI、ロジック、プロンプトを適切に分離
- **Streamlit Cloud対応**: Secretsを使用したセキュアな運用

## 🚀 デプロイ方法

### Streamlit Cloud でのデプロイ

1. **リポジトリをGitHubにプッシュ**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Streamlit Cloud設定**
   - [Streamlit Cloud](https://share.streamlit.io/) にアクセス
   - GitHubリポジトリを接続
   - アプリをデプロイ

3. **Secrets設定**
   - Streamlit Cloud管理画面で「Settings > Secrets」を選択
   - プロンプトを設定

## 💻 ローカル開発

### 必要な環境
- Python 3.8+
- OpenAI API Key

### セットアップ
1. **リポジトリをクローン**
   ```bash
   git clone <repository-url>
   cd mensetsu_rollplay
   ```

2. **依存関係インストール**
   ```bash
   pip install -r requirements.txt
   ```

3. **プロンプトファイル作成**
   - `prompts.py` を作成し、独自のプロンプトを定義

4. **アプリ起動**
   ```bash
   streamlit run rollplay.py
   ```

## 🔒 セキュリティ

### プロンプト保護
- `prompts.py` は `.gitignore` で除外されGitHubに公開されません
- Streamlit Cloud では Secrets 機能を使用してプロンプトを管理
- APIキーはユーザーが直接入力し、セッションでのみ保持

## 📋 技術スタック

- **フロントエンド**: Streamlit
- **LLM**: OpenAI GPT-4o
- **フレームワーク**: LangChain
- **デプロイ**: Streamlit Cloud
- **言語**: Python 3.8+

## 🎯 評価軸

システムは以下の5つの軸で面接パフォーマンスを評価します:

1. **コミュニケーション力**: 質疑応答の適切性、結論ベースの会話能力
2. **定着性**: 転職理由・志望動機から判断される継続勤務意欲
3. **課題解決力**: 仮説思考に基づく問題解決アプローチ
4. **自走力**: 業務を自分ごととして取り組む姿勢
5. **スキル**: 対象業界・職種で必要な最低限のスキル・知識

## 🤝 コントリビューション

このプロジェクトは面接スキル向上を目的としています。改善提案やバグレポートは Issues からお願いします。

## 📄 ライセンス

MIT License

## 📞 サポート

質問やサポートが必要な場合は、GitHubのIssuesをご利用ください。
