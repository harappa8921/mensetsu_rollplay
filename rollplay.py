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
        st.session_state.current_stage = "welcome"
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

def restart_interview():
    """面接を再開（プロフィール情報は保持）"""
    # プロフィール情報を保存
    saved_profile = st.session_state.get("profile", {}).copy()
    saved_api_key = st.session_state.get("api_key", "")
    saved_llm = st.session_state.get("llm", None)
    
    # セッション状態をリセット
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # 保存した情報を復元
    st.session_state.profile = saved_profile
    st.session_state.api_key = saved_api_key
    st.session_state.llm = saved_llm
    st.session_state.current_stage = "profile"

def skip_to_feedback():
    """フィードバック段階にスキップ"""
    st.session_state.current_stage = "feedback"
    st.session_state.is_interrupted = True

def clean_question_text(question_text):
    """質問文から余計な履歴を除去して純粋な質問のみを抽出"""
    # 「面接官：」以降の部分を抽出
    if "面接官：" in question_text:
        # 最後の「面接官：」以降を取得
        parts = question_text.split("面接官：")
        if len(parts) > 1:
            return parts[-1].strip()
    
    # 「面接官：」がない場合、改行で分割して最後の質問部分を取得
    lines = question_text.strip().split('\n')
    
    # 自己紹介や履歴部分を除去して質問部分を探す
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        # 質問文の特徴を持つ行を探す
        if line and ('？' in line or 'か？' in line or 'ですか' in line or 'ください' in line):
            # その行から質問部分を抽出
            if '？' in line:
                question_parts = line.split('？')
                if len(question_parts) >= 2:
                    # 最後の「？」までを質問として扱う
                    return '？'.join(question_parts[:-1]) + '？'
            return line
    
    # 最後の手段として、最後の文を返す
    if lines:
        return lines[-1].strip()
    
    return question_text.strip()

def format_feedback_display(feedback_text):
    """フィードバックテキストを見やすく整形して表示"""
    lines = feedback_text.split('\n')
    
    # 詳細評価セクションの開始を検出
    in_evaluation_section = False
    evaluation_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 合否結果の表示
        if '合否結果：' in line:
            result = line.split('合否結果：')[1].strip()
            if '即合格' in result:
                st.success(f"**合否結果**: {result}")
            elif '合格' in result and '不合格' not in result:
                st.success(f"**合否結果**: {result}")
            elif 'ボーダー' in result:
                st.warning(f"**合否結果**: {result}")
            elif '不合格' in result:
                st.error(f"**合否結果**: {result}")
            else:
                st.info(f"**合否結果**: {result}")
            st.markdown("---")
            continue
        
        # 評価セクションの開始を検出
        if line.startswith('- ') and ('評価：' in line or 'フィードバック' in line):
            if '評価：' in line:
                st.subheader("詳細評価")
                in_evaluation_section = True
            continue
        
        # 評価セクション内の処理
        if in_evaluation_section:
            # 総評の開始で評価セクション終了
            if '総評：' in line:
                # 蓄積された評価内容を表示
                if evaluation_lines:
                    evaluation_text = '\n'.join(evaluation_lines)
                    st.markdown(evaluation_text)
                
                # 総評を表示
                comment = line.split('総評：')[1].strip()
                st.markdown("---")
                st.subheader("総評")
                st.markdown(f"{comment}")
                in_evaluation_section = False
                evaluation_lines = []
                continue
            else:
                # 評価内容を蓄積
                evaluation_lines.append(line)
                continue
        
        # 総評の表示（評価セクション外の場合）
        if '総評：' in line:
            comment = line.split('総評：')[1].strip()
            st.markdown("---")
            st.subheader("📝 総評")
            st.markdown(f"{comment}")
            continue
        
        # 通常のテキスト
        if line and not line.startswith('-'):
            st.markdown(line)
    
    # 評価セクションが最後まで続いた場合の処理
    if in_evaluation_section and evaluation_lines:
        evaluation_text = '\n'.join(evaluation_lines)
        st.markdown(evaluation_text)

# メイン関数
def main():
    init_session_state()
    
    st.title("👨‍💼 面接ロールプレイ")
    
    # ウェルカム画面
    if st.session_state.current_stage == "welcome":
        show_welcome_screen()
    
    # APIキー入力段階
    elif st.session_state.current_stage == "api_key":
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

def show_welcome_screen():
    st.header("面接ロールプレイシステムへようこそ")
    
    st.markdown("""
    このアプリケーションは、**転職面接の練習**を本格的にサポートするシステムです。
    AIが面接官となり、あなたの背景に合わせたリアルな面接体験を提供します。
    """)
    
    # 機能説明
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("主な機能")
        st.markdown("""
        **パーソナライズされた面接体験**
        - あなたの**年齢、現在の職種、転職希望先**を考慮
        - **業界や職種に特化**した質問を生成
        - 経験レベルに応じた適切な難易度設定
        
        **リアルな面接フロー**
        - 自己紹介から始まる本格的な面接進行
        - 深掘り質問による詳細な評価
        - 実際の面接と同様の緊張感を体験
        """)
    
    with col2:
        st.subheader("充実したフィードバック")
        st.markdown("""
        **5段階評価システム**
        - コミュニケーション力
        - 定着性
        - 課題解決力
        - 自走力（主体性）
        - 専門スキル
        
        **具体的な改善提案**
        - 良かった点と改善点を明確に指摘
        - 総合的な合否判定
        - 次回面接への具体的アドバイス
        """)
    
    # 流れの説明
    st.subheader("面接の流れ")
    
    flow_steps = [
        "**APIキー設定** - OpenAI APIキーを入力（安全に暗号化処理）",
        "**プロフィール入力** - 年齢、現職、転職希望などの基本情報",
        "**自己紹介** - 1分程度での自己PR",
        "**面接質問** - 4つのカテゴリから厳選された質問（深掘りあり）",
        "**フィードバック** - 詳細な評価と改善アドバイス"
    ]
    
    for i, step in enumerate(flow_steps, 1):
        st.markdown(f"{i}. {step}")
    
    # 注意事項
    st.info("""
    **ご利用にあたって**
    - OpenAI APIキーが必要です（従量課金制）
    - 面接は途中で中断して再開することも可能です
    - すべてのデータは安全に処理され、外部に保存されません
    """)
    
    # 開始ボタン
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("面接を開始する", type="primary", use_container_width=True):
            st.session_state.current_stage = "api_key"
            st.rerun()

def show_api_key_form():
    st.header("OpenAI APIキー設定")
    
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
            if api_key:
                with st.spinner("APIキーを検証中..."):
                    is_valid, message = validate_api_key(api_key)
                    
                if is_valid:
                    try:
                        # 検証済みのAPIキーでLLMを設定
                        st.session_state.llm = setup_llm(api_key)
                        st.session_state.api_key = api_key
                        st.session_state.current_stage = "profile"
                        st.success(message + " プロフィール入力に進みます。")
                        st.rerun()
                    except Exception as e:
                        st.error(f"LLMの設定に失敗しました: {str(e)}")
                else:
                    st.error(message)
            else:
                st.error("APIキーを入力してください")

def show_profile_form():
    st.header("プロフィール入力")
    
    # 既存のプロフィール情報を取得
    existing_profile = st.session_state.get("profile", {})
    
    with st.form("profile_form"):
        age = st.text_input("年齢", value=existing_profile.get("age", ""), placeholder="例：28")
        current_gyokai = st.text_input("現在の業界", value=existing_profile.get("current_gyokai", ""), placeholder="例：IT")
        current_job = st.text_input("現在の職種", value=existing_profile.get("current_job", ""), placeholder="例：エンジニア")
        target_job = st.text_input("志望している職種", value=existing_profile.get("target_job", ""), placeholder="例：データサイエンティスト")
        role = st.text_input("現在の業務の役割", value=existing_profile.get("role", ""), placeholder="例：メンバー、リーダー、マネージャー")
        experience_years = st.text_input("現在の業務の経験年数", value=existing_profile.get("experience_years", ""), placeholder="例：3年")
        target_gyokai = st.text_input("転職を希望している業界", value=existing_profile.get("target_gyokai", ""), placeholder="例：コンサルティング")
        
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
    st.header("自己紹介")
        
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

    # 中断ボタンを右下に表示
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("最初からやり直し", help="APIキー入力から最初からやり直します"):
            st.session_state.show_restart_confirm = True
            st.rerun()
    with col3:
        if st.button("フィードバックへスキップ", help="面接を中断してフィードバックを確認します"):
            st.session_state.show_skip_confirm = True
            st.rerun()
    
    # 確認ダイアログの表示
    if st.session_state.get("show_restart_confirm", False):
        st.warning("⚠️ 最初からやり直しますか？")
        col_confirm1, col_confirm2, col_confirm3 = st.columns([2, 1, 1])
        with col_confirm2:
            if st.button("はい", key="confirm_restart"):
                st.session_state.show_restart_confirm = False
                reset_interview_session()
                st.rerun()
        with col_confirm3:
            if st.button("いいえ", key="cancel_restart"):
                st.session_state.show_restart_confirm = False
                st.rerun()
    
    if st.session_state.get("show_skip_confirm", False):
        st.warning("⚠️ フィードバックへスキップしますか？")
        col_confirm1, col_confirm2, col_confirm3 = st.columns([2, 1, 1])
        with col_confirm2:
            if st.button("はい", key="confirm_skip"):
                st.session_state.show_skip_confirm = False
                skip_to_feedback()
                st.rerun()
        with col_confirm3:
            if st.button("いいえ", key="cancel_skip"):
                st.session_state.show_skip_confirm = False
                st.rerun()

def show_question_stage():
    st.header("面接質問")
    
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
        # 質問文をクリーニング
        cleaned_question = clean_question_text(current_question)
        
        st.info("👨‍💼 面接官からの質問")
        st.write(add_newlines_by_period(cleaned_question))
        
        # 回答フォーム
        with st.form(f"answer_form_{st.session_state.current_question}_{st.session_state.depth_count}"):
            user_answer = st.text_area("回答してください", height=120, key=f"answer_{st.session_state.current_question}_{st.session_state.depth_count}")
            submit_answer = st.form_submit_button("回答を送信")
            
            if submit_answer and user_answer:
                # チャット履歴に保存（クリーニングした質問を使用）
                add_message("assistant", cleaned_question)
                add_message("user", user_answer)
                
                # 深掘り質問の判定（最低1回は必須、最大3回まで）
                if st.session_state.depth_count < 3:
                    # 最初の1回は必ず深掘り、2回目以降はAIが判定
                    if st.session_state.depth_count == 0:
                        should_followup = True
                    else:
                        with st.spinner("回答を評価中..."):
                            judge_result = judge_need_followup(st.session_state.llm, get_history_text(st.session_state.chat_history))
                            should_followup = (judge_result == "Yes")
                    
                    if should_followup:
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
                    # 最大回数に達したので次の質問へ
                    st.session_state.current_question += 1
                    st.session_state.depth_count = 0
                    
                    if st.session_state.current_question >= len(questions_list):
                        st.session_state.current_stage = "feedback"
                    
                    st.rerun()
    
    else:
        st.session_state.current_stage = "feedback"
        st.rerun()

    # 中断ボタンを右下に表示
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("最初からやり直し", help="APIキー入力から最初からやり直します", key="restart_questions"):
            st.session_state.show_restart_confirm_q = True
            st.rerun()
    with col3:
        if st.button("フィードバックへスキップ", help="面接を中断してフィードバックを確認します", key="skip_questions"):
            st.session_state.show_skip_confirm_q = True
            st.rerun()
    
    # 確認ダイアログの表示
    if st.session_state.get("show_restart_confirm_q", False):
        st.warning("⚠️ 最初からやり直しますか？")
        col_confirm1, col_confirm2, col_confirm3 = st.columns([2, 1, 1])
        with col_confirm2:
            if st.button("はい", key="confirm_restart_q"):
                st.session_state.show_restart_confirm_q = False
                reset_interview_session()
                st.rerun()
        with col_confirm3:
            if st.button("いいえ", key="cancel_restart_q"):
                st.session_state.show_restart_confirm_q = False
                st.rerun()
    
    if st.session_state.get("show_skip_confirm_q", False):
        st.warning("⚠️ フィードバックへスキップしますか？")
        col_confirm1, col_confirm2, col_confirm3 = st.columns([2, 1, 1])
        with col_confirm2:
            if st.button("はい", key="confirm_skip_q"):
                st.session_state.show_skip_confirm_q = False
                skip_to_feedback()
                st.rerun()
        with col_confirm3:
            if st.button("いいえ", key="cancel_skip_q"):
                st.session_state.show_skip_confirm_q = False
                st.rerun()

def show_feedback_stage():
    st.header("面接フィードバック")
    
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
                st.info("面接が途中で中断されたため、部分的なフィードバックを表示しています。")
            else:
                # 通常のフィードバックを生成
                feedback_output = generate_feedback(
                    st.session_state.llm, 
                    evaluation_points_list, 
                    get_history_text(st.session_state.chat_history)
                )
            st.session_state.feedback_result = add_newlines_by_period(feedback_output)
    
    st.success("面接お疲れさまでした！")
    
    # フィードバックを整形して表示
    format_feedback_display(st.session_state.feedback_result)
    
    # 新しい面接を開始するボタン
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("新しい面接を開始", type="primary", use_container_width=True):
            # プロフィール情報を保持して面接を再開
            restart_interview()
            st.rerun()

if __name__ == "__main__":
    main()