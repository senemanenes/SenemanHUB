from datetime import datetime
import markdown as md
import streamlit as st

from utils.config import MODEL_OPTIONS, MODEL_ID_MAP, _build_base_css, _build_reading_css, parse_analysis_to_html
from utils.gemini_helper import get_gemini_model, generate_reading_text, analyze_reading_sentences
from utils.gsheets_helper import fetch_data, append_data
from utils.ui_components import render_grouped_pagination

st.set_page_config(page_title="📚 Reading Center", layout="centered", initial_sidebar_state="collapsed")

READING_TOPICS = ["Tarih", "Bilim", "Genel Kültür", "Mühendislik", "Siyaset", "Yapay Zeka"]

if "saved_texts_current" not in st.session_state:
    st.session_state.saved_texts_current = False

if "current_text_result" not in st.session_state:
    st.session_state.current_text_result = None

def save_current_item_gs():
    if st.session_state.current_text_result and not st.session_state.saved_texts_current:
        title = st.session_state.current_text_result.get("title", "")
        content = st.session_state.current_text_result.get("content", "")
        # Add topic into content to not lose it, or keep title informative
        topic = st.session_state.get("reading_current_topic", "")
        if topic:
            title = f"[{topic}] {title}"
        if append_data("Readings", title, content):
            st.session_state.saved_texts_current = True
            st.toast("Google Sheets'e eklendi!", icon="✅")

def render_reading_content(content):
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
    theme_choice = st.radio("Tema", options=["🌙 Karanlık", "☀️ Aydınlık"], index=theme_index, key="theme_radio_reading", label_visibility="collapsed")
    st.session_state["theme"] = "light" if theme_choice == "☀️ Aydınlık" else "dark"

    st.header("🤖 Model")
    selected_model_label = st.selectbox("Model seçin", options=MODEL_OPTIONS, index=0, key="global_model_select_reading", label_visibility="collapsed")

    st.header("☁️ Google Sheets Kayıtları")
    gs_texts = fetch_data("Readings")
    render_grouped_pagination(gs_texts, group_size=3, label_prefix="Okuma Listesi", content_renderer_func=render_reading_content)

st.markdown(f"<style>{_build_base_css(st.session_state['theme'])}{_build_reading_css(st.session_state['theme'])}</style>", unsafe_allow_html=True)

_api_key = _get_api_key()
secilen_model = MODEL_ID_MAP.get(selected_model_label, "models/gemini-2.5-flash")
model = get_gemini_model(_api_key, secilen_model, "reading")

st.title("📚 Reading Center")

if "reading_current_text" not in st.session_state: st.session_state["reading_current_text"] = ""
if "reading_show_topic_step" not in st.session_state: st.session_state["reading_show_topic_step"] = False

if not st.session_state["reading_show_topic_step"]:
    if st.button("✏️ Yeni Metin Yaz", key="btn_metin_yaz"):
        st.session_state["reading_show_topic_step"] = True
        st.session_state["reading_current_text"] = ""
        st.session_state["reading_analysis_result"] = ""
        st.rerun()
else:
    topic = st.selectbox("Konu seçin", options=READING_TOPICS, key="reading_topic_select")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Metni Oluştur", key="btn_generate_reading"):
            if not _api_key: st.warning("API anahtarı eksik!")
            else:
                with st.spinner("Makale yazılıyor..."):
                    text = generate_reading_text(model, topic)
                    if text:
                        st.session_state["reading_current_text"] = text
                        st.session_state["reading_current_topic"] = topic
                        st.session_state["reading_analysis_result"] = ""
                        st.session_state["reading_show_topic_step"] = False
                        st.rerun()
    with col_b:
        if st.button("İptal", key="btn_reading_cancel"):
            st.session_state["reading_show_topic_step"] = False
            st.rerun()

current_text = st.session_state.get("reading_current_text", "")
if current_text:
    body_html = md.markdown(current_text, extensions=["extra", "nl2br"], output_format="html")
    custom_css = f"""
<div style="
    background-color: rgba(255, 255, 255, 0.05); 
    padding: 30px; 
    border-radius: 15px; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.2); 
    line-height: 1.8; 
    font-size: 1.1em; 
    font-family: 'Helvetica Neue', sans-serif;
    border: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 20px;
">
{body_html}
</div>
"""
    st.markdown(custom_css, unsafe_allow_html=True)
    if st.button("🔍 Cümle Cümle Analiz Et", key="btn_analiz_et"):
        if not _api_key: st.warning("API anahtarı eksik!")
        else:
            with st.spinner("Cümleler analiz ediliyor..."):
                st.session_state["reading_analysis_result"] = analyze_reading_sentences(model, current_text)
                st.rerun()
    
    if st.session_state.get("reading_analysis_result"):
        st.markdown("<div class='thick-sep'></div>", unsafe_allow_html=True)
        st.subheader("📝 Cümle Analizi")
        anal_md = st.session_state["reading_analysis_result"]
        html_content = parse_analysis_to_html(anal_md)
        st.markdown(html_content, unsafe_allow_html=True)
        
        save_title_analysis = st.session_state.get("reading_current_title", "Başlıksız Metin Analizi")
        if not save_title_analysis.strip():
            save_title_analysis = "Makale Analizi"
            
        st.session_state.current_text_result = {
            "title": save_title_analysis,
            "content": html_content
        }
        st.session_state.saved_texts_current = False
    
    if st.session_state.get("current_text_result"):
        is_saved = st.session_state.saved_texts_current
        col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
        with col_r2:
            st.button(
                "💾 Google Sheets'e Kaydet" if not is_saved else "✅ Kaydedildi",
                key="save_session_analysis",
                on_click=save_current_item_gs,
                disabled=is_saved,
                use_container_width=True
            )
