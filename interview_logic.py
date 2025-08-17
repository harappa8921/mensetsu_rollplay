"""
面接ロールプレイシステムのロジック部分
"""

import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser



# ユーザープロフィールを基にルールプロンプトを生成する関数
def get_rules(profile):
    from secrets_config import get_prompts_from_secrets
    prompts = get_prompts_from_secrets()
    return prompts["RULES_TEMPLATE"].format(
        age=profile["age"],
        current_gyokai=profile["current_gyokai"],
        current_job=profile["current_job"],
        role=profile["role"],
        experience_years=profile["experience_years"],
        target_gyokai=profile["target_gyokai"],
        target_job=profile["target_job"]
    )

# OpenAI APIキーの有効性を検証する関数
def validate_api_key(api_key):
    """
    Args:
        api_key (str): 検証するOpenAI APIキー
        
    Returns:
        tuple: (bool, str) - (検証成功フラグ, メッセージ)
               True, "成功メッセージ" または False, "エラーメッセージ"
    """
    if not api_key or not api_key.startswith("sk-"):
        return False, "有効なOpenAI APIキーを入力してください（sk-で始まる必要があります）"
    
    try:
        # 簡単なテスト用のLLMインスタンスを作成
        test_llm = ChatOpenAI(
            model="gpt-4o-mini",  # より安価なモデルでテスト
            temperature=0,
            openai_api_key=api_key,
            max_tokens=10
        )
        
        # 最小限のテスト呼び出し
        test_prompt = ChatPromptTemplate.from_template("こんにちは")
        test_chain = test_prompt | test_llm | StrOutputParser()
        
        # APIキーテスト実行
        test_chain.invoke({})
        
        return True, "APIキーが正常に検証されました"
        
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return False, "APIキーが無効です。正しいOpenAI APIキーを入力してください"
        elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
            return False, "APIキーのクォータまたは請求設定に問題があります"
        elif "rate_limit" in error_msg.lower():
            return False, "レート制限に達しています。しばらく待ってから再試行してください"
        else:
            return False, f"APIキーの検証中にエラーが発生しました: {error_msg}"

# LLM（言語モデル）をセットアップする関数
def setup_llm(api_key):
    if not api_key:
        raise ValueError("OpenAI API key is required")
    
    os.environ["OPENAI_API_KEY"] = api_key
    
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        openai_api_key=api_key
    )

# 文章の句読点で改行を挿入する関数（読みやすさ向上）
def add_newlines_by_period(text):
    return re.sub(r'(?<=[。？！])', '\n', text)

# チャット履歴をテキスト形式で取得する関数（LLMへの入力用）
def get_history_text(chat_history):
    if not chat_history:
        return ""
    
    history_lines = []
    for message in chat_history:
        if message["role"] == "assistant":
            history_lines.append(f"面接官：{message['content']}")
        else:
            history_lines.append(f"あなた：{message['content']}")
    
    return "\n".join(history_lines)

# AIを使って面接質問を生成する関数（メイン機能）
def generate_question(llm, rules, question_content, evaluation_points, history):
    """
    Args:
        llm: 設定済みのLangChain LLMインスタンス
        rules (str): 面接ルールとユーザープロフィールの組み合わせ
        question_content (str): 質問カテゴリの内容（例：転職理由、現職の取り組みなど）
        evaluation_points (str): 評価ポイントの説明文
        history (str): これまでの会話履歴
        
    Returns:
        str: 生成された面接質問文（LLMが出力したテキスト）
    """
    from secrets_config import get_prompts_from_secrets
    prompts = get_prompts_from_secrets()
    
    question_prompt = ChatPromptTemplate.from_template(prompts["QUESTION_TEMPLATE"])
    create_question_chain = question_prompt | llm | StrOutputParser()
    
    return create_question_chain.invoke({
        "rules": rules,
        "question": question_content,
        "evaluation_points": evaluation_points,
        "history": history
    })

# 深掘り質問が必要かどうかをAIで判定する関数
def judge_need_followup(llm, history):
    """
    Args:
        llm: 設定済みLangChain LLMインスタンス
        history (str): これまでの会話履歴
        
    Returns:
        str: "Yes" または "No" のみを返す（深掘り必要か判定）
    """
    from secrets_config import get_prompts_from_secrets
    prompts = get_prompts_from_secrets()
    
    judge_prompt = ChatPromptTemplate.from_template(prompts["JUDGE_TEMPLATE"])
    judge_chain = judge_prompt | llm | StrOutputParser()
    
    return judge_chain.invoke({"history": history}).strip()

# 面接全体のフィードバックをAIで生成する関数
def generate_feedback(llm, evaluation_points_list, history):
    """
    Args:
        llm: 設定済みLangChain LLMインスタンス
        evaluation_points_list (dict): 評価ポイントの辞書（キー: 評価軸名、値: 説明）
        history (str): 面接全体の会話履歴
        
    Returns:
        str: 構造化されたフィードバックテキスト（合否結果、評価、総評を含む）
    """
    from secrets_config import get_prompts_from_secrets
    prompts = get_prompts_from_secrets()
    
    feedback_prompt = ChatPromptTemplate.from_template(prompts["FEEDBACK_TEMPLATE"])
    feedback_chain = feedback_prompt | llm | StrOutputParser()
    
    return feedback_chain.invoke({
        "evaluation_points_list": evaluation_points_list,
        "evaluation_format": prompts["EVALUATION_FORMAT"],
        "history": history
    })

# 面接中断時の部分フィードバックをAIで生成する関数
def generate_partial_feedback(llm, evaluation_points_list, history):
    """
    Args:
        llm: 設定済みLangChain LLMインスタンス
        evaluation_points_list (dict): 評価ポイントの辞書
        history (str): 面接中断までの会話履歴
        
    Returns:
        str: 部分的なフィードバックテキスト（未回答項目は"評価なし"として表示）
    """
    from secrets_config import get_prompts_from_secrets
    prompts = get_prompts_from_secrets()
    
    feedback_prompt = ChatPromptTemplate.from_template(prompts["PARTIAL_FEEDBACK_TEMPLATE"])
    feedback_chain = feedback_prompt | llm | StrOutputParser()
    
    return feedback_chain.invoke({
        "evaluation_points_list": evaluation_points_list,
        "evaluation_format": prompts["PARTIAL_EVALUATION_FORMAT"],
        "history": history
    })
