from utils import *
import streamlit as st




def save_and_display_content(content, role="user"):
    """ 儲存和顯示streamlit對話紀錄 """
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.markdown(content)


def submit_input(url_dict):
    """
    處理從 URL 字典提取的主要和參考文章內容，使用 GPT 模型進行內容摘要和查證分析。
    函數首先確認主要文章URL是否存在，然後提取並顯示這些文章的內容。如果參考文章URL也提供，
    它會進一步提取和處理這些文章。最後，函數將使用 GPT 模型對提取的內容進行摘要和查證分析。

    Args:
        url_dict (dict): 包含兩個鍵的字典：
            - "main_articles" (list of str): 主要文章的URL列表。
            - "supporting_articles" (list of str): 查證用的參考文章URL列表。

    Effects:
        - 在 Streamlit 應用中顯示錯誤、警告或其他重要信息。
        - 更新應用界面以顯示提取和分析的結果。
    """
    sum_total_promptTokens = 0
    sum_total_completionTokens = 0
    final_results = ""

    # 主要文章
    main_articles = [url.strip()
                     for url in url_dict["main_articles"] if url.strip()]
    if not main_articles:
        st.error("請輸入主要文章URL")
        return

    main_content = get_and_handle_articles(main_articles)
    save_and_display_content(main_content)

    # 參考文章
    supporting_articles = [
        url.strip() for url in url_dict["supporting_articles"] if url.strip()]
    supporting_content = ""
    if not supporting_articles:
        st.warning("沒有提供查證文章URL，將僅摘要文章")
    else:
        supporting_content = get_and_handle_articles(supporting_articles)

    # 合併主要、參考文章
    all_articles = f"main news：\n{main_content}\n other relevant news：\n{supporting_content}"

    try:
        # 主要文章送GPT分析獲取摘要
        if main_content:
            results, total_promptTokens, total_completionTokens = analytics_result(
                str(main_content), main_assistant_id)
            sum_total_promptTokens += total_promptTokens
            sum_total_completionTokens += total_completionTokens
            final_results = f"{unit}\n\n{results}\n\n"

        # 如果有參考文章則進行查證分析
        if supporting_content:
            results, total_promptTokens, total_completionTokens = analytics_result(
                str(all_articles), supporting_assistant_id)
            sum_total_promptTokens += total_promptTokens
            sum_total_completionTokens += total_completionTokens
            final_results += "二、查證情形：\n\n" + results
        else:
            final_results += "二、查證情形：\n因為沒有提供參考文章，未進行查證分析。"

        save_and_display_content(final_results, "assistant")
        save_and_display_content(f"使用 {sum_total_promptTokens} 個prompt tokens\n\n使用 {sum_total_completionTokens} 個completion tokens", "assistant")

    except Exception as e:
        st.error(f"在分析過程中發生錯誤: {str(e)}")


def login():
    """登入畫面"""
    st.header("登入")

    username = st.text_input("使用者名稱")
    password = st.text_input("密碼", type="password")

    if st.button("登入"):
        if username ==  username and password == password:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("帳號或密碼錯誤")

# 頁面設置
st.set_page_config(
    page_title='新聞摘要機器人',
    page_icon='📋',
    layout='wide',
    initial_sidebar_state='auto'
)

# 設定 Streamlit 頁面的標題
st.title("新聞摘要機器人")

# 自訂CSS格式 - 調整圖片大小
st.markdown(
    """
        <style>
        img {
            max-width: 100%;
            height: auto;
        }
        </style>
        """,
    unsafe_allow_html=True
)

# 初始化聊天室session
if "messages" not in st.session_state:
    st.session_state.messages = []

# 登入邏輯
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

with st.sidebar:
    if not st.session_state.logged_in:
        login()
    else:
        st.header("輸入主要文章URL")
        url1 = st.text_input(label="主要文章URL1", value="")
        url2 = st.text_input(label="主要文章URL2", value="")

        st.header("輸入參考文章URL")
        url3 = st.text_input(label="參考文章URL1", value="")
        url4 = st.text_input(label="參考文章URL2", value="")
        url5 = st.text_input(label="參考文章URL3", value="")
        url6 = st.text_input(label="參考文章URL4", value="")

        submit_button = st.button("執行")

        if st.button("刪除紀錄"):
            # 將一個確認標誌設置到 session 狀態中
            st.session_state.confirmation_flag = True

        if 'confirmation_flag' in st.session_state and st.session_state.confirmation_flag:
            st.write("確定要刪除紀錄？")
            if st.button("確認"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.experimental_rerun()

            if st.button("取消"):
                del st.session_state.confirmation_flag
                st.experimental_rerun()

if st.session_state.logged_in:
    # 顯示歷史訊息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 按下執行按鈕
    if submit_button:
        url_dict = {
            "main_articles": [url1, url2],
            "supporting_articles": [url3, url4, url5, url6]
        }
        submit_input(url_dict)

    # 使用者輸入
    if user_input := st.chat_input("請輸入文章獲取摘要..."):
        save_and_display_content(user_input, "user")
        try:
            final_results, total_promptTokens, total_completionTokens = analytics_result(
                str(user_input), main_assistant_id)
            save_and_display_content(final_results, "assistant")
            save_and_display_content(f"使用 {total_promptTokens} 個prompt tokens\n使用 {total_completionTokens} 個completion tokens", "assistant")
        except Exception as e:
            st.write(f"Error during analytics: {str(e)}")