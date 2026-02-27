import streamlit as st
from utils.config import MODEL_OPTIONS, MODEL_ID_MAP, _build_base_css, _build_dict_css, markdown_to_card_html
from utils.gemini_helper import get_gemini_model, analyze_word
from utils.gsheets_helper import fetch_data, append_data
from utils.ui_components import render_grouped_pagination

st.set_page_config(page_title="📖 Sözlük", layout="centered", initial_sidebar_state="collapsed")

if "saved_words_current" not in st.session_state:
    st.session_state.saved_words_current = False

if "current_word_result" not in st.session_state:
    st.session_state.current_word_result = None

def save_current_item_gs():
    if st.session_state.current_word_result and not st.session_state.saved_words_current:
        title = st.session_state.current_word_result.get("title", "")
        content = st.session_state.current_word_result.get("content", "")
        if append_data("Words", title, content):
            st.session_state.saved_words_current = True
            st.toast("Google Sheets'e eklendi!")

def render_word_content(content):
    cleaned_html = '\n'.join([line.strip() for line in content.split('\n')])
    final_html = cleaned_html.replace('```html', '').replace('```', '')
    st.markdown(final_html, unsafe_allow_html=True)

def _get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        return (key or "").strip() if key else ""
    except Exception: return ""

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

with st.sidebar:
    st.header("🎨 Tema")
    theme_index = 0 if st.session_state.get("theme", "dark") == "dark" else 1
    theme_choice = st.radio("Tema", options=["🌙 Karanlık", "☀️ Aydınlık"], index=theme_index, key="theme_radio_dict", label_visibility="collapsed")
    st.session_state["theme"] = "light" if theme_choice == "☀️ Aydınlık" else "dark"

    st.header("🤖 Model")
    selected_model_label = st.selectbox("Model seçin", options=MODEL_OPTIONS, index=0, key="global_model_select_dict", label_visibility="collapsed")
    
    st.header("☁️ Google Sheets Kayıtları")
    gs_words = fetch_data("Words")
    render_grouped_pagination(gs_words, group_size=10, label_prefix="Kelime Listesi", content_renderer_func=render_word_content)

st.markdown(f"<style>{_build_base_css(st.session_state['theme'])}{_build_dict_css(st.session_state['theme'])}</style>", unsafe_allow_html=True)

_api_key = _get_api_key()
secilen_model = MODEL_ID_MAP.get(selected_model_label, "models/gemini-2.5-flash")
model = get_gemini_model(_api_key, secilen_model, "dict")

st.title("📖 Sözlük")

word = st.text_input("İngilizce kelime", placeholder="Örn: resilience, integrity")
col1, col2, col3 = st.columns([1, 2, 1])
with col2: analyze_clicked = st.button("Search", use_container_width=True)

if analyze_clicked and word.strip():
    if not _api_key: st.warning("API anahtarı gizli dosyalarda (secrets) bulunamadı!")
    else:
        st.caption(f"Kullanılan model: **{selected_model_label}**")
        with st.spinner("Kelime analiz ediliyor..."):
            result_md = analyze_word(model, word)
            if result_md:
                st.session_state["last_word"] = word.strip()
                st.session_state["last_result_md"] = result_md
                html_content = markdown_to_card_html(result_md, word.strip())
                st.session_state.current_word_result = {
                    "title": word.strip(),
                    "content": html_content
                }
                st.session_state.saved_words_current = False
                st.markdown(html_content, unsafe_allow_html=True)
            else: st.warning("Yanıt üretemedi.")
elif analyze_clicked and not word.strip(): st.warning("Kelime girin.")
    
if st.session_state.get("current_word_result"):
    is_saved = st.session_state.saved_words_current
    col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
    with col_s2:
        st.button(
            "💾 Google Sheets'e Kaydet" if not is_saved else "✅ Kaydedildi",
            key="save_session_word",
            on_click=save_current_item_gs,
            disabled=is_saved,
            use_container_width=True
        )
