import json
import textwrap
import streamlit as st

from utils.config import MODEL_OPTIONS, MODEL_ID_MAP, _build_base_css, _build_trans_css
from utils.gemini_helper import get_gemini_model, translate_sentence
from utils.gsheets_helper import fetch_data, append_data
from utils.ui_components import render_grouped_pagination

st.set_page_config(page_title="📝 Cümle Çeviri", layout="centered", initial_sidebar_state="collapsed")

def _get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        return (key or "").strip() if key else ""
    except Exception: return ""

if "saved_translations_current" not in st.session_state:
    st.session_state.saved_translations_current = False

if "current_trans_result" not in st.session_state:
    st.session_state.current_trans_result = None

def save_current_item_gs():
    if st.session_state.current_trans_result and not st.session_state.saved_translations_current:
        title = st.session_state.current_trans_result.get("title", "")
        content = st.session_state.current_trans_result.get("content", "")
        if append_data("Translations", title, content):
            st.session_state.saved_translations_current = True
            st.toast("Google Sheets'e eklendi!")

def render_trans_content(content):
    cleaned_html = '\n'.join([line.strip() for line in content.split('\n')])
    final_html = cleaned_html.replace('```html', '').replace('```', '')
    try:
        st.html(final_html)
    except AttributeError:
        st.markdown(final_html, unsafe_allow_html=True)

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

with st.sidebar:
    st.header("🎨 Tema")
    theme_index = 0 if st.session_state.get("theme", "dark") == "dark" else 1
    theme_choice = st.radio("Tema", options=["🌙 Karanlık", "☀️ Aydınlık"], index=theme_index, key="theme_radio_trans", label_visibility="collapsed")
    st.session_state["theme"] = "light" if theme_choice == "☀️ Aydınlık" else "dark"

    st.header("🤖 Model")
    selected_model_label = st.selectbox("Model seçin", options=MODEL_OPTIONS, index=0, key="global_model_select_trans", label_visibility="collapsed")

    st.header("☁️ Google Sheets Kayıtları")
    gs_trans = fetch_data("Translations")
    render_grouped_pagination(gs_trans, group_size=5, label_prefix="Çeviri Listesi", content_renderer_func=render_trans_content)

st.markdown(f"<style>{_build_base_css(st.session_state['theme'])}{_build_trans_css(st.session_state['theme'])}</style>", unsafe_allow_html=True)

_api_key = _get_api_key()
secilen_model = MODEL_ID_MAP.get(selected_model_label, "models/gemini-2.5-flash")
model = get_gemini_model(_api_key, secilen_model, "trans")

st.title("📝 Cümle Çeviri")
st.markdown("Türkçe bir cümle yazın; profesyonel İngilizce karşılığını, yapısını (Gramer mantığını) ve önemli kelimeleri görün.")

tr_text = st.text_area("Cümle (Türkçe)", placeholder="Çevirmek istediğiniz cümleyi buraya yazın...", height=120)
if st.button("Çevir 🚀", use_container_width=True):
    if not tr_text.strip():
        st.warning("Lütfen bir cümle girin.")
    elif not _api_key:
        st.warning("API anahtarı eksik!")
    else:
        with st.spinner("Analiz ediliyor ve çevriliyor..."):
            response_text = translate_sentence(model, tr_text)
            
            # Remove Markdown JSON formatting if output contains it
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            try:
                data = json.loads(cleaned_text)
                
                en_trans = data.get("translation", "")
                logic = data.get("logic", "")
                vocab = data.get("vocabulary", [])
                
                # HTML Card Render
                vocab_html = ""
                for v in vocab:
                    en_w = v.get("en", "")
                    tr_w = v.get("tr", "")
                    vocab_html += f'<span class="trans-vocab-item"><strong>{en_w}</strong>: <i>{tr_w}</i></span>'

                html_render = f'''
                <div class="trans-card">
                    <div class="trans-header">✨ Orijinal Cümle</div>
                    <div class="trans-original">{tr_text}</div>
                    
                    <div class="trans-header" style="color:#1DB954;">🇬🇧 İngilizce Çeviri</div>
                    <div class="trans-translation">{en_trans}</div>
                    
                    <div class="trans-header" style="color:#A78BFA;">🧠 Yapı Analizi & Mantık</div>
                    <div class="trans-logic">{logic}</div>
                    
                    <div class="trans-vocab">
                        <div class="trans-vocab-title">📚 Önemli Kelimeler</div>
                        {vocab_html if vocab_html else "Yok."}
                    </div>
                </div>
                '''
                
                cleaned_html = '\n'.join([line.strip() for line in html_render.split('\n')])
                final_html = cleaned_html.replace('```html', '').replace('```', '')
                
                try:
                    st.html(final_html)
                except AttributeError:
                    st.markdown(final_html, unsafe_allow_html=True)
                    
                st.session_state.current_trans_result = {
                    "title": tr_text[:30] + "..." if len(tr_text) > 30 else tr_text,
                    "content": final_html
                }
                st.session_state.saved_translations_current = False
                
            except json.JSONDecodeError as e:
                st.error("JSON parse hatası oluştu. Model uygun formatta cevap vermedi.")
                st.code(response_text)

if st.session_state.get("current_trans_result"):
    is_saved = st.session_state.saved_translations_current
    col_t1, col_t2, col_t3 = st.columns([1, 2, 1])
    with col_t2:
        st.button(
            "💾 Google Sheets'e Kaydet" if not is_saved else "✅ Kaydedildi",
            key="save_session_trans",
            on_click=save_current_item_gs,
            disabled=is_saved,
            use_container_width=True
        )
