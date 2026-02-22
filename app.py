"""
Seneman Sözlük — Streamlit uygulaması
Gemini ile akademik İngilizce kelime analizi ve Reading Center.
"""

import html
import json
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
import google.generativeai as genai
import markdown as md

# --- Word list persistence ---
SAVED_WORDS_FILE = Path(__file__).resolve().parent / "saved_words.json"
READING_LIBRARY_FILE = Path(__file__).resolve().parent / "reading_library.json"

# --- Theme colors (sidebar'dan seçilecek) ---
THEMES = {
    "dark": {
        "bg": "#121212",
        "card_bg": "#1E1E1E",
        "border": "#333",
        "text": "#E0E0E0",
        "text_muted": "#B0B0B0",
        "input_bg": "#1E1E1E",
        "accent": "#2DD4BF",
        "button": "#A78BFA",
        "button_hover": "#C4B5FD",
    },
    "light": {
        "bg": "#f5f5f5",
        "card_bg": "#FFFFFF",
        "border": "#ddd",
        "text": "#1a1a1a",
        "text_muted": "#555",
        "input_bg": "#FFFFFF",
        "accent": "#0d9488",
        "button": "#7c3aed",
        "button_hover": "#8b5cf6",
    },
}

def load_saved_words():
    try:
        if SAVED_WORDS_FILE.exists():
            with open(SAVED_WORDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}

def save_saved_words(data: dict):
    with open(SAVED_WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_reading_library() -> list:
    try:
        if READING_LIBRARY_FILE.exists():
            with open(READING_LIBRARY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("texts", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    except (json.JSONDecodeError, OSError):
        pass
    return []

def save_reading_library(texts: list):
    with open(READING_LIBRARY_FILE, "w", encoding="utf-8") as f:
        json.dump({"texts": texts}, f, ensure_ascii=False, indent=2)

# --- Page config ---
st.set_page_config(
    page_title="Seneman Sözlük",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --- System instructions (academic assistant + strict template) ---
SYSTEM_INSTRUCTIONS = """Sen 'Seneman Sözlük' için çalışan, akademik bir dil asistanısın. Çıktılarını şu KATI formatta ver:
- Türkçe ve İngilizce anlamlar tek kelime değil, tam ve açıklayıcı cümleler olmalı.
- 'Collocations (Birlikte Kullanımlar)' kısmını 'Kullanım Alanları'ndan hemen sonra ekle.
- Collocations Formatı:
  1. [Kalıp] ([TR Karşılığı])
  • Kullanım: [Not]
  • [EN Örnek Cümle 1]
    [TR Çevirisi - Alt Satırda]
  ---
  • [EN Örnek Cümle 2]
    [TR Çevirisi - Alt Satırda]
  ---
  Collocations kısmındaki her kalıbı (örneğin "Anticipate a problem", "Meet expectations") mutlaka şu HTML etiketi içine al: <span style='color: #C4B5FD; font-weight: bold;'>[Kalıp]</span>
- Kelime Formları kısmında "Verb", "Noun", "Adjective", "Adverb" etiketlerini mutlaka şu HTML etiketi içine al: <span style='color: #FBBF24; font-weight: bold;'>[Etiket]</span>
- 'Edatlarla Kullanımı' bölümünü Collocations'tan hemen sonra ekle. Formatı:
  ### Edatlarla Kullanımı
  • [Edatlı Yapı/Kalıp]: [Türkçe Açıklama]
  • [İngilizce Örnek Cümle]
    *[Türkçe Çevirisi - Mutlaka Alt Satırda ve İtalik]*
- Türkçe çevirilerini her zaman italik (*...*) olarak yaz. İngilizce cümle veya yapıların altındaki her Türkçe çevirinin başına mutlaka bir mermi işareti (•) koy.
- Örnek Cümleler (7 Adet) bölümü: Cümlelerin başındaki numaraları (1-, 2-, 3- vb.) tamamen kullanma. Her İngilizce cümlenin başına içi dolu yuvarlak (●) koy. Her Türkçe çevirinin (alt satırda) başına içi boş yuvarlak (○) koy. Örnekler arasındaki ince ayırım çizgilerini korumak için her (İngilizce cümle + Türkçe çevirisi) çiftinden sonra '---' yaz (son çift hariç).
- HİÇBİR giriş/çıkış cümlesi kurma; DOĞRUDAN şablonla başla.

Şablon sırası (her ana bölüm arasında --- koy):

# [kelime]
**Word Type:** [Tür]
---
**Türkçe Anlamı:** (Açıklayıcı cümle)
---
**İkinci Anlamı (Türkçe):** (Varsa)
---
**English Meaning:** (Explanatory sentence)
---
**English Meaning (Secondary):** (Varsa)
---
**Kullanım Alanları**
[Net paragraf]
---
**Collocations (Birlikte Kullanımlar)**
(Her kalıbı <span style='color: #C4B5FD; font-weight: bold;'>...</span> içine al)
[Yukarıdaki formatta]
---
### Edatlarla Kullanımı
• [Edatlı Yapı/Kalıp]: [Türkçe Açıklama]
• [İngilizce Örnek Cümle]
  *[Türkçe Çevirisi - Mutlaka Alt Satırda ve İtalik]*
---
**Kelime Formları**
(Verb, Noun, Adjective, Adverb etiketlerini <span style='color: #FBBF24; font-weight: bold;'>...</span> içine al; TR ve EN kısa tanımlarıyla)
---
**Eş ve Zıt Anlamlar**
---
**Örnek Cümleler (7 Adet)**
● [İngilizce Cümle]
○ *[Türkçe Çevirisi - Alt Satırda]*
---
(her çiftten sonra ---; numara kullanma, ● EN ve ○ TR ile yaz)"""

SECTION_STYLES = {
    "header": ("header", "#00796B"),
    "turkce": ("turkce", "#00796B"),
    "turkce2": ("turkce", "#00796B"),
    "english": ("english", "#D32F2F"),
    "english2": ("english", "#D32F2F"),
    "kullanim": ("kullanim", "#1976D2"),
    "collocations": ("collocations", "#E65100"),
    "kelime-formlari": ("kelime-formlari", "#7B1FA2"),
    "es-zit": ("es-zit", "#388E3C"),
    "ornekler": ("ornekler", "#C62828"),
    "default": ("default", "#9CA3AF"),
}

# --- 2026 MODEL SEÇENEKLERİ ---
# --- MODEL SEÇENEKLERİ (Tabelada Görünecek İsimler) ---
# --- 2026 GÜNCEL MODEL SEÇENEKLERİ ---
MODEL_OPTIONS = [
    "Gemini 2.5 Flash",
    "Gemini 3 Flash",
    "Gemini 3.1 Pro"
]

MODEL_ID_MAP = {
    "Gemini 2.5 Flash": "gemini-2.5-flash",
    "Gemini 3 Flash": "gemini-3-flash-preview",
    "Gemini 3.1 Pro": "gemini-3.1-pro-preview",
}


def _detect_section(block: str) -> str:
    block_lower = block.strip().lower()
    if block_lower.startswith("# ") or "**word type:**" in block_lower[:200]: return "header"
    if "**türkçe anlamı:**" in block_lower and "ikinci" not in block_lower: return "turkce"
    if "**ikinci anlamı (türkçe):**" in block_lower: return "turkce2"
    if "**english meaning (secondary):**" in block_lower or "**english meaning (secondary)**" in block_lower: return "english2"
    if "**english meaning:**" in block_lower: return "english"
    if "kullanım alanları" in block_lower or "**kullanım alanları**" in block_lower: return "kullanim"
    if "collocations" in block_lower or "birlikte kullanımlar" in block_lower: return "collocations"
    if "kelime formları" in block_lower or "**kelime formları**" in block_lower: return "kelime-formlari"
    if "eş ve zıt" in block_lower or "eş ve zıt anlamlar" in block_lower: return "es-zit"
    if "örnek cümleler" in block_lower or "örnek cümleler (" in block_lower: return "ornekler"
    return "default"

# --- YENİ PROFESYONEL CSS ---
def _build_css(theme: str) -> str:
    t = THEMES.get(theme, THEMES["dark"])
    bg, card_bg, border, text, text_muted = t["bg"], t["card_bg"], t["border"], t["text"], t["text_muted"]
    input_bg, accent, button, button_hover = t["input_bg"], t["accent"], t["button"], t["button_hover"]
    parts = [
        f"""
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&family=Inter:wght@400;500;600;700&family=Merriweather:ital,wght@0,300;0,400;0,700;1,400&family=Roboto:wght@300;400;500;700&display=swap');
    
    .stApp, .stApp * {{ font-family: 'Montserrat', 'Inter', -apple-system, sans-serif !important; }}
    .stApp {{ background-color: {bg} !important; }}
    .stApp .stMarkdown, .stApp p, .stApp label, .stApp .stCaption {{ color: {text} !important; }}
    
    .word-header-box {{ background: {card_bg}; border: 1px solid {border}; border-radius: 12px; padding: 14px 20px; margin-bottom: 16px; font-weight: 600; color: {accent}; font-size: 1.1rem; }}
    .result-card {{ background: {card_bg}; border: 1px solid {border}; border-radius: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.15); padding: 30px; margin-bottom: 20px; color: {text}; }}
    .result-card .section {{ margin-bottom: 12px; }}
    .result-card .section hr.sep {{ border: none; border-top: 0.5px solid {border}; margin: 14px 0; }}
    .result-card .section hr.example-sep {{ border: none; border-top: 0.2px solid {border}; margin: 10px 0; }}
    .result-card .section p, .result-card .section li {{ line-height: 1.75; font-size: 1rem; color: {text}; margin-bottom: 10px; }}
    .result-card em {{ color: {text_muted} !important; font-style: italic; font-size: 0.95rem; }}
    
    .stTextInput input {{ background-color: {input_bg} !important; color: {text} !important; border: 1px solid {border} !important; }}
    .stButton > button {{ background-color: {button} !important; color: #FFFFFF !important; border-radius: 8px; font-weight: 600; border: none; }}
    .stButton > button:hover {{ background-color: {button_hover} !important; color: #FFFFFF !important; }}
    h1 {{ color: {text} !important; }}
    
    /* ========================================= */
    /* YENİ READING CENTER TASARIMI (GECE MAVİSİ)*/
    /* ========================================= */
    .reading-book-style {{
        background-color: #0A192F;
        padding: 40px 50px;
        border-radius: 12px;
        border: 1px solid #233554;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        line-height: 1.9 !important;
        font-size: 1.1rem;
        color: #CCD6F6 !important;
        margin-bottom: 30px;
        text-align: justify;
        font-family: 'Montserrat', sans-serif !important;
    }}
    .reading-book-style p, .reading-book-style h1, .reading-book-style h2, .reading-book-style h3 {{
        color: #CCD6F6 !important;
        font-family: 'Montserrat', sans-serif !important;
    }}
    
    /* ANALİZ KARTLARI (SPOTIFY YEŞİLİ & MAVİ) */
    .analysis-card {{
        background: #112240;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 25px;
        border: 1px solid #233554;
        box-shadow: 0 6px 15px rgba(0,0,0,0.2);
        border-left: 5px solid #1DB954;
        font-family: 'Montserrat', sans-serif !important;
        color: #CCD6F6 !important;
    }}
    .analysis-card p {{ color: #CCD6F6 !important; font-family: 'Montserrat', sans-serif !important; }}
    .header-sentence {{ color: #1DB954; font-weight: 700; font-size: 1rem; text-transform: uppercase; letter-spacing: 1px; font-family: 'Montserrat', sans-serif !important; }}
    .header-translation {{ color: #BDD2FF; font-weight: 700; font-size: 1rem; text-transform: uppercase; letter-spacing: 1px; font-family: 'Montserrat', sans-serif !important; }}
    .header-logic {{ color: #F8D5FF; font-weight: 700; font-size: 1rem; text-transform: uppercase; letter-spacing: 1px; font-family: 'Montserrat', sans-serif !important; }}
    .card-divider {{ border: none; border-top: 1px solid #233554; margin: 8px 0 15px 0; }}
    .thick-sep {{ border: none; border-top: 3px double #233554; margin: 40px 0; opacity: 0.5; }}
"""
    ]
    for key, (cls, color) in SECTION_STYLES.items():
        parts.append(f".result-card .section.section-{cls} h1, .result-card .section.section-{cls} h2, .result-card .section.section-{cls} h3, .result-card .section.section-{cls} strong {{ color: {color} !important; font-weight: 600; }}")
    return "\n".join(parts)

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
st.markdown(f"<style>{_build_css(st.session_state['theme'])}</style>", unsafe_allow_html=True)

def get_gemini_model(api_key: str, model_id: str):
    if not api_key or not api_key.strip(): return None
    genai.configure(api_key=api_key.strip())
    return genai.GenerativeModel(model_name=model_id, system_instruction=SYSTEM_INSTRUCTIONS)

def analyze_word(model, word: str) -> str:
    if not word or not word.strip(): return ""
    prompt = f"Şu İngilizce kelimeyi yukarıdaki şablona göre analiz et. Doğrudan şablonla başla, giriş veya kapanış cümlesi yazma.\n\nKelime: {word.strip()}"
    return model.generate_content(prompt).text or ""

# --- Reading Center Functions ---
READING_TOPICS = ["Tarih", "Bilim", "Genel Kültür", "Mühendislik", "Siyaset", "Yapay Zeka"]

def generate_reading_text(gemini_model, topic: str) -> str:
    prompt = f"""
    You are a professional content creator for channels like PolyMatter, Wendover Productions, or Knowledgia.
    
    TASK: Write a unique, specific, and academic-level article in English about a RANDOM and INTERESTING sub-topic within the field of '{topic}'.
    
    STRICT RULES:
    1. DO NOT explain the definition or etymology of the word '{topic}'. 
    2. Instead, pick a SPECIFIC event, person, discovery, or phenomenon. (e.g., if the topic is History, don't write about 'what is history', write about 'The Great Emu War' or 'The Logistics of the 17th Century Ottoman Army').
    3. If the topic is 'Tarih', focus on interesting world history or 17-18th-century details (uniforms, tactics, military order) as I have a YouTube channel about this.
    4. TONE: Analytical, engaging, well-structured, and academic.
    5. LENGTH: 500-600 words.
    6. STRUCTURE: Start directly with a catchy title, then the article. No intro like 'Here is your article'.
    """
    response = gemini_model.generate_content(prompt)
    return (response.text or "").strip()

def analyze_reading_sentences(gemini_model, text: str) -> str:
    prompt = f"Analyze the following English text sentence by sentence. For each sentence use EXACTLY this format (no extra text):\n\n---\nSentence: [English sentence]\nÇeviri: [Turkish translation]\nMantık: [Brief Turkish explanation of grammar/structure/logic]\n---\n\nText:\n{text}"
    return (gemini_model.generate_content(prompt).text or "").strip()

# --- YENİ HTML PARSER (Kart Tasarımı İçin) ---
def parse_analysis_to_html(raw_md: str) -> str:
    # Metni ayırıp her birini kart içine alan sağlam motor
    blocks = re.split(r"---", raw_md)
    html_output = ""
    for block in blocks:
        if "Sentence:" in block:
            s = re.search(r"Sentence:(.*?)(?=Çeviri:|$)", block, re.S).group(1).strip()
            t = re.search(r"Çeviri:(.*?)(?=Mantık:|$)", block, re.S).group(1).strip()
            l = re.search(r"Mantık:(.*)", block, re.S).group(1).strip()
            html_output += f'''
            <div class="analysis-card">
                <div class="header-sentence">🇬🇧 SENTENCE</div><hr style="opacity:0.1">
                <p>{s}</p>
                <div class="header-translation">🇹🇷 ÇEVİRİ</div><hr style="opacity:0.1">
                <p><i>{t}</i></p>
                <div class="header-logic">🧠 MANTIK</div><hr style="opacity:0.1">
                <p>{l}</p>
            </div>'''
    return html_output

def markdown_to_card_html(markdown_text: str, searched_word: str = "") -> str:
    if not markdown_text.strip(): return ""
    blocks = re.split(r"\n---\n", markdown_text)
    html_parts = []
    for i, block in enumerate(blocks):
        block = block.strip()
        if not block: continue
        section_key = _detect_section(block)
        cls, _ = SECTION_STYLES.get(section_key, ("default", "#9CA3AF"))
        if section_key == "ornekler":
            sub_blocks = re.split(r"\n---\n", block)
            section_html_parts = []
            for j, sub in enumerate(sub_blocks):
                sub = sub.strip()
                if not sub: continue
                sub_html = md.markdown(sub, extensions=["extra", "nl2br"], output_format="html")
                if j > 0: section_html_parts.append('<hr class="example-sep" />')
                section_html_parts.append(sub_html)
            block_html = "\n".join(section_html_parts)
        else:
            block_html = md.markdown(block, extensions=["extra", "nl2br"], output_format="html")
        if i > 0: html_parts.append('<hr class="sep" />')
        html_parts.append(f'<div class="section section-{cls}">{block_html}</div>')
    inner = "\n".join(html_parts)
    card = f'<div class="result-card">{inner}</div>'
    if searched_word:
        return f'<div class="word-header-box">Word: {html.escape(searched_word.strip())}</div>' + card
    return card

# --- Sidebar ve State Yönetimi ---
saved_words_data = load_saved_words()
reading_library = load_reading_library()

def _get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        return (key or "").strip() if key else ""
    except Exception: return ""

with st.sidebar:
    st.sidebar.header("📌 Modül")
    app_module = st.sidebar.radio("Modül", options=["📖 Sözlük", "📚 Reading Center"], index=0, key="app_module", label_visibility="collapsed")
    st.sidebar.header("🎨 Tema")
    theme_index = 0 if st.session_state.get("theme", "dark") == "dark" else 1
    theme_choice = st.sidebar.radio("Tema", options=["🌙 Karanlık", "☀️ Aydınlık"], index=theme_index, key="theme_radio", label_visibility="collapsed")
    st.session_state["theme"] = "light" if theme_choice == "☀️ Aydınlık" else "dark"

    st.sidebar.header("🤖 Model")
    selected_model_label = st.sidebar.selectbox("Model seçin", options=MODEL_OPTIONS, index=0, key="global_model_select", label_visibility="collapsed")

    if app_module == "📖 Sözlük":
        st.sidebar.header("📌 Mod")
        main_mode = st.sidebar.radio("Sayfa", options=["🔍 Search Mode", "📚 My Library"], index=0, key="main_mode", label_visibility="collapsed")
        st.sidebar.header("📂 Liste Yönetimi")
        list_options = list(saved_words_data.keys()) if saved_words_data else []
        if not list_options: list_options = ["— Liste seçiniz veya oluşturun —"]
        selected_list = st.sidebar.selectbox("Liste seçin", options=list_options, key="word_list_select")
        has_list_selected = selected_list and selected_list in saved_words_data
        new_list_name = st.sidebar.text_input("Yeni liste adı", placeholder="Liste adı yazın", key="new_list_name")
        if st.sidebar.button("Yeni Liste Oluştur", key="create_list_btn") and (new_list_name or "").strip():
            name = (new_list_name or "").strip()
            if name not in saved_words_data:
                saved_words_data[name] = []
                save_saved_words(saved_words_data)
                st.sidebar.success(f"'{name}' listesi oluşturuldu!")
                st.rerun()
            else: st.sidebar.warning("Bu isimde bir liste zaten var.")
    else:
        st.sidebar.header("📂 Liste Oluştur")
        reading_title_to_save = st.sidebar.text_input("Makale adı", placeholder="Kayıt adı yazın", key="reading_save_title")
        save_title = (reading_title_to_save or "").strip() or (st.session_state.get("reading_current_title") or "").strip()
        save_disabled_reading = not st.session_state.get("reading_current_text") or not save_title
        if st.sidebar.button("💾 Makaleyi Kaydet", key="save_reading_btn", disabled=save_disabled_reading) and save_title and st.session_state.get("reading_current_text"):
            library = load_reading_library()
            library.append({
                "id": f"text_{len(library) + 1}",
                "title": save_title,
                "body": st.session_state["reading_current_text"],
                "topic": st.session_state.get("reading_current_topic", ""),
                "created_at": datetime.now().isoformat(),
            })
            save_reading_library(library)
            st.sidebar.success(f"'{save_title}' kaydedildi.")
            st.rerun()
        st.sidebar.header("📚 Kayıtlı Metinler")
        reading_library = load_reading_library()
        for i, item in enumerate(reading_library):
            if st.sidebar.button(f"Text {i + 1} - {item.get('title', 'Başlıksız')}", key=f"reading_load_{item.get('id', i)}", use_container_width=True):
                st.session_state["reading_selected_id"] = item.get("id")
                st.session_state["reading_current_text"] = item.get("body", "")
                st.session_state["reading_current_title"] = item.get("title", "")
                st.session_state["reading_current_topic"] = item.get("topic", "")
                st.session_state["reading_analysis_result"] = ""
                st.rerun()

# --- Global Model Setup ---
_api_key = _get_api_key()
secilen_model = MODEL_ID_MAP.get(selected_model_label, "gemini-2.0-flash")
if _api_key:
    genai.configure(api_key=_api_key)
    model = genai.GenerativeModel(secilen_model, system_instruction=SYSTEM_INSTRUCTIONS if app_module == "📖 Sözlük" else None)
else: model = None

# --- Main UI ---
if app_module == "📖 Sözlük":
    st.title("🏛️ Seneman Sözlük")
    if main_mode == "🔍 Search Mode":
        word = st.text_input("İngilizce kelime", placeholder="Örn: resilience, integrity")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2: analyze_clicked = st.button("search", use_container_width=True)

        if analyze_clicked and word.strip():
            if not _api_key: st.warning("API anahtarı eksik!")
            else:
                st.caption(f"Kullanılan model: **{selected_model_label}**")
                with st.spinner("Kelime analiz ediliyor..."):
                    result_md = analyze_word(model, word)
                    if result_md:
                        st.session_state["last_word"] = word.strip()
                        st.session_state["last_result_md"] = result_md
                        st.markdown(markdown_to_card_html(result_md, word.strip()), unsafe_allow_html=True)
                    else: st.warning("Yanıt üretemedi.")
        elif analyze_clicked and not word.strip(): st.warning("Kelime girin.")

        has_result_to_save = "last_result_md" in st.session_state and st.session_state.get("last_result_md")
        col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
        with col_s2:
            if st.button("💾 Kaydet", use_container_width=True, disabled=not (has_list_selected and has_result_to_save), key="save_word_btn"):
                saved_words_data[selected_list].append({"word": st.session_state["last_word"], "markdown": st.session_state["last_result_md"]})
                save_saved_words(saved_words_data)
                st.toast(f"'{selected_list}' listesine eklendi!")

    else:
        library_data = load_saved_words()
        lists_with_words = {k: v for k, v in library_data.items() if isinstance(v, list) and len(v) > 0}
        if not library_data or sum(len(v) for v in lists_with_words.values()) == 0:
            st.info("Kayıtlı kelimeniz yok.")
        else:
            library_selected_list = st.selectbox("Liste seçin", options=list(lists_with_words.keys()), key="library_list_select")
            entries = lists_with_words.get(library_selected_list, [])
            selected_idx = st.session_state.get("library_selected_word_index")
            if selected_idx is None:
                st.subheader("Kelimeler")
                for i, entry in enumerate(entries):
                    if st.button(entry.get("word", "?"), key=f"lib_word_{library_selected_list}_{i}", use_container_width=True):
                        st.session_state["library_selected_word_index"] = i
                        st.rerun()
            else:
                if st.button("⬅️ Listeye Dön", key="library_back_btn"):
                    st.session_state["library_selected_word_index"] = None
                    st.rerun()
                selected_entry = entries[selected_idx]
                st.markdown(markdown_to_card_html(selected_entry.get("markdown", ""), selected_entry.get("word", "")), unsafe_allow_html=True)
                st.markdown("---")
                if st.button("❌ Listeden Sil", key="library_delete_btn"):
                    library_data[library_selected_list].pop(selected_idx)
                    save_saved_words(library_data)
                    st.session_state["library_selected_word_index"] = None
                    st.rerun()

else:
    # --- 📚 Reading Center ---
    st.title("📚 Reading Center")
    if "reading_current_text" not in st.session_state: st.session_state["reading_current_text"] = ""
    if "reading_show_topic_step" not in st.session_state: st.session_state["reading_show_topic_step"] = False

    if not st.session_state["reading_show_topic_step"]:
        if st.button("✏️ Metin Yaz", key="btn_metin_yaz"):
            st.session_state["reading_show_topic_step"] = True
            st.rerun()
    else:
        topic = st.selectbox("Konu seçin", options=READING_TOPICS, key="reading_topic_select")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Metni Oluştur", key="btn_generate_reading"):
                if not model: st.warning("API anahtarı tanımlı değil.")
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
        st.markdown(f'<div class="reading-book-style">{body_html}</div>', unsafe_allow_html=True)
        if st.button("🔍 Cümle Cümle Analiz Et", key="btn_analiz_et"):
            if not model: st.warning("API anahtarı tanımlı değil.")
            else:
                with st.spinner("Cümle analiz ediliyor..."):
                    st.session_state["reading_analysis_result"] = analyze_reading_sentences(model, current_text)
                    st.rerun()
        
        if st.session_state.get("reading_analysis_result"):
            st.markdown("<div class='thick-sep'></div>", unsafe_allow_html=True)
            st.subheader("📝 Cümle Analizi")
            anal_md = st.session_state["reading_analysis_result"]
            st.markdown(parse_analysis_to_html(anal_md), unsafe_allow_html=True)