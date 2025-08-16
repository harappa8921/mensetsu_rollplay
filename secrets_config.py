"""
Streamlit Secrets設定用のプロンプト管理
本番環境ではStreamlit Cloudのsecretsから読み込み、開発環境ではprompts.pyから読み込む
"""

import streamlit as st

def get_prompts_from_secrets():
    """Streamlit secretsからプロンプトデータを取得"""
    try:
        # Streamlit Cloud環境での設定
        rules_template = st.secrets["prompts"]["RULES_TEMPLATE"]
        question_template = st.secrets["prompts"]["QUESTION_TEMPLATE"]
        judge_template = st.secrets["prompts"]["JUDGE_TEMPLATE"]
        feedback_template = st.secrets["prompts"]["FEEDBACK_TEMPLATE"]
        evaluation_format = st.secrets["prompts"]["EVALUATION_FORMAT"]
        partial_feedback_template = st.secrets["prompts"]["PARTIAL_FEEDBACK_TEMPLATE"]
        partial_evaluation_format = st.secrets["prompts"]["PARTIAL_EVALUATION_FORMAT"]
        
        # 質問リストを新しいTOML配列形式で取得
        questions_list = []
        if "questions_list" in st.secrets["prompts"]:
            for question_data in st.secrets["prompts"]["questions_list"]:
                questions_list.append({
                    "title": question_data["title"],
                    "point_keys": question_data["point_keys"],
                    "content": question_data["content"]
                })
        
        # 評価ポイントリストを新しいTOMLテーブル形式で取得
        evaluation_points_list = {}
        if "evaluation_points_list" in st.secrets["prompts"]:
            evaluation_points_list = dict(st.secrets["prompts"]["evaluation_points_list"])
        
        return {
            "RULES_TEMPLATE": rules_template,
            "QUESTION_TEMPLATE": question_template,
            "JUDGE_TEMPLATE": judge_template,
            "FEEDBACK_TEMPLATE": feedback_template,
            "EVALUATION_FORMAT": evaluation_format,
            "PARTIAL_FEEDBACK_TEMPLATE": partial_feedback_template,
            "PARTIAL_EVALUATION_FORMAT": partial_evaluation_format,
            "questions_list": questions_list,
            "evaluation_points_list": evaluation_points_list
        }
        
    except Exception as e:
        # 開発環境またはsecretsが設定されていない場合はローカルファイルから読み込み
        try:
            from prompts import (
                RULES_TEMPLATE, QUESTION_TEMPLATE, JUDGE_TEMPLATE, 
                FEEDBACK_TEMPLATE, EVALUATION_FORMAT, 
                PARTIAL_FEEDBACK_TEMPLATE, PARTIAL_EVALUATION_FORMAT,
                questions_list, evaluation_points_list
            )
            return {
                "RULES_TEMPLATE": RULES_TEMPLATE,
                "QUESTION_TEMPLATE": QUESTION_TEMPLATE,
                "JUDGE_TEMPLATE": JUDGE_TEMPLATE,
                "FEEDBACK_TEMPLATE": FEEDBACK_TEMPLATE,
                "EVALUATION_FORMAT": EVALUATION_FORMAT,
                "PARTIAL_FEEDBACK_TEMPLATE": PARTIAL_FEEDBACK_TEMPLATE,
                "PARTIAL_EVALUATION_FORMAT": PARTIAL_EVALUATION_FORMAT,
                "questions_list": questions_list,
                "evaluation_points_list": evaluation_points_list
            }
        except ImportError:
            st.error("プロンプト設定が見つかりません。Streamlit Cloudのsecretsを設定するか、ローカル環境でprompts.pyファイルを配置してください。")
            st.stop()