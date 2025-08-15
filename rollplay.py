"""
面接ロールプレイシステム - Streamlit アプリケーション
"""

import streamlit as st
from secrets_config import get_prompts_from_secrets
from interview_logic import (
    setup_llm, 
    validate_api_key,
    add_newlines_by_period, 
    get_history_text,
    generate_question,
    judge_need_followup,
    generate_feedback,
    generate_partial_feedback,
    get_rules
)

# ページ設定
st.set_page_config(
    page_title="面接ロールプレイ",
    page_icon="👨‍💼",
    layout="wide"
)

# セッション状態の初期化
def init_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "current_stage" not in st.session_state:
        st.session_state.current_stage = "api_key"
    if "profile" not in st.session_state:
        st.session_state.profile = {}
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "depth_count" not in st.session_state:
        st.session_state.depth_count = 0
    if "intro_given" not in st.session_state:
        st.session_state.intro_given = False
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "llm" not in st.session_state:
        st.session_state.llm = None

def add_message(role, content):
    """チャット履歴にメッセージを追加"""
    st.session_state.chat_history.append({
        "role": role,
        "content": content
    })

def reset_interview_session():
    """面接セッションを完全にリセット"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def skip_to_feedback():
    """フィードバック段階にスキップ"""
    st.session_state.current_stage = "feedback"
    st.session_state.is_interrupted = True

# メイン関数
def main():
    init_session_state()
    
    st.title("👨‍💼 面接ロールプレイ")
    
    # APIキー入力段階
    if st.session_state.current_stage == "api_key":
        show_api_key_form()
    
    # プロフィール入力段階
    elif st.session_state.current_stage == "profile":
        show_profile_form()
    
    # 自己紹介段階
    elif st.session_state.current_stage == "intro":
        show_intro_stage()
    
    # 質問段階
    elif st.session_state.current_stage == "questions":
        show_question_stage()
    
    # フィードバック段階
    elif st.session_state.current_stage == "feedback":
        show_feedback_stage()

def show_api_key_form():
    st.header("🔑 OpenAI APIキー設定")
    
    st.info("面接ロールプレイを開始するには、OpenAI APIキーが必要です。")
    
    st.markdown("""
    **APIキーの取得方法:**
    1. [OpenAI Platform](https://platform.openai.com/api-keys) にアクセス
    2. アカウントにログインまたは新規登録
    3. 「Create new secret key」をクリック
    4. 生成されたAPIキーをコピー
    
    💡 **ヒント:** APIキーは「sk-」で始まる文字列です
    """)
    
    with st.form("api_key_form"):
        api_key = st.text_input(
            "OpenAI APIキーを入力してください",
            type="password",
            placeholder="sk-...",
            help="APIキーは安全に暗号化されて処理されます"
        )
        
        submit_button = st.form_submit_button("APIキーを設定")
        
        if submit_button:
            if api_key and api_key.startswith("sk-"):
                try:
                    # APIキーの妥当性をテスト
                    st.session_state.llm = setup_llm(api_key)
                    st.session_state.api_key = api_key
                    st.session_state.current_stage = "profile"
                    st.success("APIキーが正常に設定されました！")
                    st.rerun()
                except Exception as e:
                    st.error(f"APIキーの設定に失敗しました: {str(e)}")
            else:
                st.error("有効なOpenAI APIキーを入力してください（sk-で始まる必要があります）")

def show_profile_form():
    st.header("📝 プロフィール入力")
    
    with st.form("profile_form"):
        age = st.text_input("年齢", placeholder="例：28")
        current_gyokai = st.text_input("現在の業界", placeholder="例：IT")
        current_job = st.text_input("現在の職種", placeholder="例：エンジニア")
        target_job = st.text_input("志望している職種", placeholder="例：データサイエンティスト")
        role = st.text_input("現在の業務の役割", placeholder="例：メンバー、リーダー、マネージャー")
        experience_years = st.text_input("現在の業務の経験年数", placeholder="例：3年")
        target_gyokai = st.text_input("転職を希望している業界", placeholder="例：コンサルティング")
        
        submit_button = st.form_submit_button("面接開始")
        
        if submit_button:
            if all([age, current_gyokai, current_job, target_job, role, experience_years, target_gyokai]):
                st.session_state.profile = {
                    "age": age,
                    "current_gyokai": current_gyokai,
                    "current_job": current_job,
                    "role": role,
                    "experience_years": experience_years,
                    "target_gyokai": target_gyokai,
                    "target_job": target_job
                }
                st.session_state.current_stage = "intro"
                st.rerun()
            else:
                st.error("すべての項目を入力してください。")

def show_intro_stage():
    st.header("🎤 自己紹介")
    
    # 中断ボタンを表示
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 最初からやり直し", help="APIキー入力から最初からやり直します"):
            reset_interview_session()
            st.rerun()
    with col2:
        if st.button("⏭️ フィードバックへスキップ", help="面接を中断してフィードバックを確認します"):
            skip_to_feedback()
            st.rerun()
    
    intro_message = """それでは、最初にあなたの自己紹介を1分（400字程度）でお願いします。
これまでのご経歴やスキルについても触れていただければと思います。"""
    
    st.info("👨‍💼 面接官からの質問")
    st.write(intro_message)
    
    with st.form("intro_form"):
        user_intro = st.text_area("自己紹介をしてください", height=150, placeholder="ここに自己紹介を入力してください...")
        submit_intro = st.form_submit_button("回答を送信")
        
        if submit_intro and user_intro:
            # チャット履歴に保存
            add_message("assistant", intro_message)
            add_message("user", user_intro)
            st.session_state.intro_given = True
            st.session_state.current_stage = "questions"
            st.rerun()

def show_question_stage():
    st.header("❓ 面接質問")
    
    # 中断ボタンを表示
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 最初からやり直し", help="APIキー入力から最初からやり直します", key="restart_questions"):
            reset_interview_session()
            st.rerun()
    with col2:
        if st.button("⏭️ フィードバックへスキップ", help="面接を中断してフィードバックを確認します", key="skip_questions"):
            skip_to_feedback()
            st.rerun()
    
    # プロンプトデータを取得
    prompts = get_prompts_from_secrets()
    questions_list = prompts["questions_list"]
    evaluation_points_list = prompts["evaluation_points_list"]
    
    # 進捗表示
    progress = (st.session_state.current_question + 1) / len(questions_list)
    st.progress(progress, f"質問 {st.session_state.current_question + 1} / {len(questions_list)}")
    
    if st.session_state.current_question < len(questions_list):
        selected_q = questions_list[st.session_state.current_question]
        
        st.subheader(f"🟦 {selected_q['title']}")
        
        evaluation_points = "\n".join(
            [f"- {k}：{evaluation_points_list[k]}" for k in selected_q["point_keys"]]
        )
        
        # 質問生成
        if f"question_{st.session_state.current_question}" not in st.session_state:
            with st.spinner("質問を生成中..."):
                output = generate_question(
                    st.session_state.llm,
                    get_rules(st.session_state.profile),
                    selected_q["content"],
                    evaluation_points,
                    get_history_text(st.session_state.chat_history)
                )
                st.session_state[f"question_{st.session_state.current_question}"] = output
        
        current_question = st.session_state[f"question_{st.session_state.current_question}"]
        
        st.info("👨‍💼 面接官からの質問")
        st.write(add_newlines_by_period(current_question))
        
        # 回答フォーム
        with st.form(f"answer_form_{st.session_state.current_question}_{st.session_state.depth_count}"):
            user_answer = st.text_area("回答してください", height=120, key=f"answer_{st.session_state.current_question}_{st.session_state.depth_count}")
            submit_answer = st.form_submit_button("回答を送信")
            
            if submit_answer and user_answer:
                # チャット履歴に保存
                add_message("assistant", current_question)
                add_message("user", user_answer)
                
                # 深掘り判定
                with st.spinner("回答を評価中..."):
                    judge_result = judge_need_followup(st.session_state.llm, get_history_text(st.session_state.chat_history))
                
                # 深掘り質問の判定（最大3回まで）
                if judge_result == "Yes" and st.session_state.depth_count < 3:
                    st.session_state.depth_count += 1
                    
                    # 深掘り質問生成
                    with st.spinner("深掘り質問を生成中..."):
                        followup_output = generate_question(
                            st.session_state.llm,
                            get_rules(st.session_state.profile),
                            "上記に対する深掘り質問を1つ出力してください。",
                            evaluation_points,
                            get_history_text(st.session_state.chat_history)
                        )
                        st.session_state[f"question_{st.session_state.current_question}"] = followup_output
                    
                    st.rerun()
                else:
                    # 次の質問へ
                    st.session_state.current_question += 1
                    st.session_state.depth_count = 0
                    
                    if st.session_state.current_question >= len(questions_list):
                        st.session_state.current_stage = "feedback"
                    
                    st.rerun()
    
    else:
        st.session_state.current_stage = "feedback"
        st.rerun()

def show_feedback_stage():
    st.header("📝 面接フィードバック")
    
    # プロンプトデータを取得
    prompts = get_prompts_from_secrets()
    evaluation_points_list = prompts["evaluation_points_list"]
    
    # 中断フラグをチェック
    is_interrupted = st.session_state.get("is_interrupted", False)
    
    # フィードバック生成
    if "feedback_result" not in st.session_state:
        with st.spinner("フィードバックを生成中..."):
            if is_interrupted:
                # 中断された場合は部分的フィードバックを生成
                feedback_output = generate_partial_feedback(
                    st.session_state.llm, 
                    evaluation_points_list, 
                    get_history_text(st.session_state.chat_history)
                )
                st.info("💡 面接が途中で中断されたため、部分的なフィードバックを表示しています。")
            else:
                # 通常のフィードバックを生成
                feedback_output = generate_feedback(
                    st.session_state.llm, 
                    evaluation_points_list, 
                    get_history_text(st.session_state.chat_history)
                )
            st.session_state.feedback_result = add_newlines_by_period(feedback_output)
    
    st.success("面接お疲れさまでした！")
    st.write(st.session_state.feedback_result)
    
    # 新しい面接を開始するボタン
    if st.button("新しい面接を開始"):
        # セッション状態をリセット
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()