"""
面接ロールプレイシステムのロジック部分
"""

import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser



def get_rules(profile):
    """共通のルールプロンプトを生成"""
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

def setup_llm(api_key):
    """LLMセットアップ"""
    if not api_key:
        raise ValueError("OpenAI API key is required")
    
    os.environ["OPENAI_API_KEY"] = api_key
    
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        openai_api_key=api_key
    )

def add_newlines_by_period(text):
    """句読点で改行を挿入"""
    return re.sub(r'(?<=[。？！])', '\n', text)

def get_history_text(chat_history):
    """チャット履歴をテキスト形式で取得"""
    if not chat_history:
        return ""
    
    history_lines = []
    for message in chat_history:
        if message["role"] == "assistant":
            history_lines.append(f"面接官：{message['content']}")
        else:
            history_lines.append(f"あなた：{message['content']}")
    
    return "\n".join(history_lines)

def generate_question(llm, rules, question_content, evaluation_points, history):
    """質問を生成"""
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

def judge_need_followup(llm, history):
    """深掘り質問が必要かを判定"""
    from prompts import JUDGE_TEMPLATE
    
    judge_prompt = ChatPromptTemplate.from_template(JUDGE_TEMPLATE)
    judge_chain = judge_prompt | llm | StrOutputParser()
    
    return judge_chain.invoke({"history": history}).strip()

def generate_feedback(llm, evaluation_points_list, history):
    """フィードバックを生成"""
    from secrets_config import get_prompts_from_secrets
    prompts = get_prompts_from_secrets()
    
    feedback_prompt = ChatPromptTemplate.from_template(prompts["FEEDBACK_TEMPLATE"])
    feedback_chain = feedback_prompt | llm | StrOutputParser()
    
    return feedback_chain.invoke({
        "evaluation_points_list": evaluation_points_list,
        "evaluation_format": prompts["EVALUATION_FORMAT"],
        "history": history
    })

def generate_partial_feedback(llm, evaluation_points_list, history):
    """部分的なフィードバックを生成（面接中断時用）"""
    from secrets_config import get_prompts_from_secrets
    prompts = get_prompts_from_secrets()
    
    feedback_prompt = ChatPromptTemplate.from_template(prompts["PARTIAL_FEEDBACK_TEMPLATE"])
    feedback_chain = feedback_prompt | llm | StrOutputParser()
    
    return feedback_chain.invoke({
        "evaluation_points_list": evaluation_points_list,
        "evaluation_format": prompts["PARTIAL_EVALUATION_FORMAT"],
        "history": history
    })