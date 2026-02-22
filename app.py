"""
Seneman Sözlük — Streamlit uygulaması
Gemini ile akademik İngilizce kelime analizi.
"""

import html
import json
import re
from pathlib import Path

import streamlit as st
import google.generativeai as genai
import markdown as md

# --- Word list persistence ---
SAVED_WORDS_FILE = Path(__file__).resolve().parent / "saved_words.json"


def load_saved_words():
    """Load list names and entries from JSON; return empty dict if missing."""
    try:
        if SAVED_WORDS_FILE.exists():
            with open(SAVED_WORDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def save_saved_words(data: dict):
    """Save list names and entries to JSON."""
    with open(SAVED_WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
    [Türkçe Çevirisi - Mutlaka Alt Satırda ve İtalik]
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

# Section key -> (CSS class, hex color) for headers
SECTION_STYLES = {
    "header": ("header", "#00796B"),
    "turkce": ("turkce", "#00796B"),       # TR Anlamı / İkinci Anlamı
    "turkce2": ("turkce", "#00796B"),
    "english": ("english", "#D32F2F"),     # English Meaning (primary/secondary)
    "english2": ("english", "#D32F2F"),
    "kullanim": ("kullanim", "#1976D2"),  # Kullanım Alanları
    "collocations": ("collocations", "#E65100"),
    "kelime-formlari": ("kelime-formlari", "#7B1FA2"),
    "es-zit": ("es-zit", "#388E3C"),      # Eş ve Zıt Anlamlar
    "ornekler": ("ornekler", "#C62828"),  # Örnek Cümleler
    "default": ("default", "#9CA3AF"),
}

# Sidebar model seçenekleri -> API model ID
MODEL_OPTIONS = [
    "Gemini 1.5 Flash (Hızlı Test)",
    "Gemini 3.1 Pro (Akademik Analiz)",
    "Gemini 2.5 Flash",
]
MODEL_ID_MAP = {
    "Gemini 1.5 Flash (Hızlı Test)": "gemini-1.5-flash",
    "Gemini 3.1 Pro (Akademik Analiz)": "gemini-3.1-pro-preview",
    "Gemini 2.5 Flash": "gemini-2.5-flash",
}


def _detect_section(block: str) -> str:
    """Block içeriğine göre section anahtarını döner."""
    block_lower = block.strip().lower()
    if block_lower.startswith("# ") or "**word type:**" in block_lower[:200]:
        return "header"
    if "**türkçe anlamı:**" in block_lower and "ikinci" not in block_lower:
        return "turkce"
    if "**ikinci anlamı (türkçe):**" in block_lower:
        return "turkce2"
    if "**english meaning (secondary):**" in block_lower or "**english meaning (secondary)**" in block_lower:
        return "english2"
    if "**english meaning:**" in block_lower:
        return "english"
    if "kullanım alanları" in block_lower or "**kullanım alanları**" in block_lower:
        return "kullanim"
    if "collocations" in block_lower or "birlikte kullanımlar" in block_lower:
        return "collocations"
    if "kelime formları" in block_lower or "**kelime formları**" in block_lower:
        return "kelime-formlari"
    if "eş ve zıt" in block_lower or "eş ve zıt anlamlar" in block_lower:
        return "es-zit"
    if "örnek cümleler" in block_lower or "örnek cümleler (" in block_lower:
        return "ornekler"
    return "default"


# --- Custom CSS: Dark mode, Spotify-style typography, word box, thin separators ---
def _build_css() -> str:
    parts = [
        """
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp,
    .stApp * {
        font-family: 'Montserrat', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .stApp {
        background-color: #121212 !important;
    }
    
    .stApp .stMarkdown,
    .stApp p,
    .stApp label,
    .stApp .stCaption {
        color: #E0E0E0 !important;
    }
    
    .word-header-box {
        background: #1E1E1E;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 16px;
        font-family: 'Montserrat', 'Inter', sans-serif !important;
        font-weight: 600;
        color: #2DD4BF;
        font-size: 1.1rem;
        box-sizing: border-box;
    }
    
    .result-card {
        background: #1E1E1E;
        border: 1px solid #333;
        border-radius: 20px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
        padding: 30px;
        margin-bottom: 20px;
        font-family: 'Montserrat', 'Inter', sans-serif !important;
        color: #E0E0E0;
    }
    
    .result-card .section {
        margin-bottom: 12px;
    }
    
    .result-card .section hr.sep {
        border: none;
        border-top: 0.5px solid #333;
        margin: 14px 0;
    }
    
    .result-card .section hr.example-sep {
        border: none;
        border-top: 0.2px solid #333;
        margin: 10px 0;
    }
    
    .result-card .section h1,
    .result-card .section h2,
    .result-card .section h3 {
        font-family: 'Montserrat', 'Inter', sans-serif !important;
        font-weight: 600;
    }
    
    .result-card .section p,
    .result-card .section li {
        line-height: 1.75;
        font-size: 1rem;
        color: #E0E0E0;
        margin-bottom: 10px;
        font-family: 'Montserrat', 'Inter', sans-serif !important;
    }
    
    .result-card em {
        color: #B0B0B0 !important;
        font-style: italic;
        font-size: 0.95rem;
    }
    
    .stTextInput label,
    .stButton > button {
        font-family: 'Montserrat', 'Inter', sans-serif !important;
    }
    
    .stTextInput input {
        background-color: #1E1E1E !important;
        color: #E0E0E0 !important;
        border: 1px solid #333 !important;
    }
    
    .stButton > button {
        background-color: #A78BFA !important;
        color: #FFFFFF !important;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: #C4B5FD !important;
        color: #FFFFFF !important;
        border: none;
    }
    
    h1 {
        color: #E0E0E0 !important;
    }
""",
    ]
    for key, (cls, color) in SECTION_STYLES.items():
        parts.append(f"""
    .result-card .section.section-{cls} h1,
    .result-card .section.section-{cls} h2,
    .result-card .section.section-{cls} h3,
    .result-card .section.section-{cls} strong {{
        color: {color} !important;
        font-weight: 600;
    }}
""")
    return "\n".join(parts)


st.markdown(f"<style>{_build_css()}</style>", unsafe_allow_html=True)


def get_gemini_model(api_key: str, model_id: str):
    """Seçilen model ID ile GenerativeModel oluşturur."""
    if not api_key or not api_key.strip():
        return None
    genai.configure(api_key=api_key.strip())
    return genai.GenerativeModel(
        model_name=model_id,
        system_instruction=SYSTEM_INSTRUCTIONS,
    )


def analyze_word(model, word: str) -> str:
    """Verilen kelimeyi Gemini ile analiz eder; markdown metin döner."""
    if not word or not word.strip():
        return ""
    prompt = f"Şu İngilizce kelimeyi yukarıdaki şablona göre analiz et. Doğrudan şablonla başla, giriş veya kapanış cümlesi yazma.\n\nKelime: {word.strip()}"
    response = model.generate_content(prompt)
    return response.text if response.text else ""


def markdown_to_card_html(markdown_text: str, searched_word: str = "") -> str:
    """Markdown'u bölümlere ayırır, her bölüme renkli başlık/hr atar ve kart HTML'i üretir."""
    if not markdown_text.strip():
        return ""
    blocks = re.split(r"\n---\n", markdown_text)
    html_parts = []
    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue
        section_key = _detect_section(block)
        cls, _ = SECTION_STYLES.get(section_key, ("default", "#9CA3AF"))
        if section_key == "ornekler":
            sub_blocks = re.split(r"\n---\n", block)
            section_html_parts = []
            for j, sub in enumerate(sub_blocks):
                sub = sub.strip()
                if not sub:
                    continue
                sub_html = md.markdown(
                    sub,
                    extensions=["extra", "nl2br"],
                    output_format="html",
                )
                if j > 0:
                    section_html_parts.append('<hr class="example-sep" style="border: none; border-top: 0.2px solid #333; margin: 10px 0;" />')
                section_html_parts.append(sub_html)
            block_html = "\n".join(section_html_parts)
        else:
            block_html = md.markdown(
                block,
                extensions=["extra", "nl2br"],
                output_format="html",
            )
        if i > 0:
            html_parts.append('<hr class="sep" style="border: none; border-top: 0.5px solid #333; margin: 14px 0;" />')
        html_parts.append(f'<div class="section section-{cls}">{block_html}</div>')
    inner = "\n".join(html_parts)
    card = f'<div class="result-card">{inner}</div>'
    if searched_word:
        word_box = f'<div class="word-header-box">Word: {html.escape(searched_word.strip())}</div>'
        return word_box + card
    return card


# --- Sidebar: Model + List management (API key only from st.secrets, never shown) ---
saved_words_data = load_saved_words()


def _get_api_key():
    """Read API key only from st.secrets; never displayed on screen."""
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        return (key or "").strip() if key else ""
    except Exception:
        return ""


with st.sidebar:
    st.sidebar.header("📌 Mod")
    main_mode = st.sidebar.radio(
        "Sayfa",
        options=["🔍 Search Mode", "📚 My Library"],
        index=0,
        key="main_mode",
        label_visibility="collapsed",
    )
    st.sidebar.header("⚙️ Model Ayarları")
    selected_model_label = st.sidebar.selectbox(
        "Model",
        options=MODEL_OPTIONS,
        index=0,
        help="Hızlı test için 1.5 Flash, detaylı analiz için 3.1 Pro önerilir.",
    )
    st.sidebar.header("📂 Liste Yönetimi")
    list_options = list(saved_words_data.keys()) if saved_words_data else []
    if not list_options:
        list_options = ["— Liste seçiniz veya oluşturun —"]
    selected_list = st.sidebar.selectbox(
        "Liste seçin",
        options=list_options,
        key="word_list_select",
        label_visibility="visible",
    )
    has_list_selected = selected_list and selected_list in saved_words_data
    new_list_name = st.sidebar.text_input(
        "Yeni liste adı",
        placeholder="Liste adı yazın",
        key="new_list_name",
        label_visibility="visible",
    )
    create_list_clicked = st.sidebar.button("Yeni Liste Oluştur", key="create_list_btn")
    if create_list_clicked and (new_list_name or "").strip():
        name = (new_list_name or "").strip()
        if name not in saved_words_data:
            saved_words_data[name] = []
            save_saved_words(saved_words_data)
            st.sidebar.success(f"'{name}' listesi oluşturuldu!")
            st.rerun()
        else:
            st.sidebar.warning("Bu isimde bir liste zaten var.")

# --- Main UI (Search vs Library) ---
st.title("🏛️ Seneman Sözlük")

if main_mode == "🔍 Search Mode":
    word = st.text_input(
        "İngilizce kelime",
        placeholder="Örn: resilience, integrity, mitigate",
        label_visibility="visible",
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_clicked = st.button("search", use_container_width=True)

    if analyze_clicked and word.strip():
        api_key = _get_api_key()
        if not api_key:
            st.warning("API anahtarı sistemde tanımlı değil, lütfen yöneticiyle iletişime geçin.")
        else:
            model_id = MODEL_ID_MAP.get(selected_model_label, "gemini-1.5-flash")
            st.caption(f"Kullanılan model: **{selected_model_label}**")
            with st.spinner("Kelime analiz ediliyor..."):
                model = get_gemini_model(api_key, model_id)
                if model:
                    result_md = analyze_word(model, word)
                    if result_md:
                        st.session_state["last_word"] = word.strip()
                        st.session_state["last_result_md"] = result_md
                        result_html = markdown_to_card_html(result_md, searched_word=word.strip())
                        st.markdown(result_html, unsafe_allow_html=True)
                        st.download_button(
                            label="Kopyala (.md)",
                            data=result_md,
                            file_name=f"senemanbaba_{word.strip().lower().replace(' ', '_')}.md",
                            mime="text/markdown",
                            use_container_width=True,
                        )
                    else:
                        st.warning(
                            "Model yanıt üretemedi. Kelimeyi tekrar deneyin veya API anahtarını kontrol edin."
                        )
    elif analyze_clicked and not word.strip():
        st.warning("Lütfen bir kelime girin.")

    # --- Kaydet button and list feedback ---
    has_result_to_save = (
        "last_word" in st.session_state
        and "last_result_md" in st.session_state
        and st.session_state.get("last_result_md")
    )
    if not has_list_selected:
        st.warning("Lütfen önce bir liste seçin veya oluşturun.")
    save_disabled = not has_list_selected or not has_result_to_save
    col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
    with col_s2:
        save_clicked = st.button("💾 Kaydet", use_container_width=True, disabled=save_disabled, key="save_word_btn")
    if save_clicked and has_list_selected and has_result_to_save:
        entry = {
            "word": st.session_state["last_word"],
            "markdown": st.session_state["last_result_md"],
        }
        saved_words_data[selected_list].append(entry)
        save_saved_words(saved_words_data)
        st.toast(f"Kelime '{selected_list}' listesine başarıyla eklendi!")

else:
    # --- 📚 My Library (list-to-detail flow, no API calls) ---
    library_data = load_saved_words()
    lists_with_words = {k: v for k, v in library_data.items() if isinstance(v, list) and len(v) > 0}
    total_words = sum(len(v) for v in lists_with_words.values())

    if not library_data or total_words == 0:
        st.info("Henüz kayıtlı bir kelimeniz yok. Search kısmından kelime eklemeye başlayın!")
    else:
        # Session state: which word index is selected (None = list view only)
        if "library_selected_word_index" not in st.session_state:
            st.session_state["library_selected_word_index"] = None
        if "library_selected_list_prev" not in st.session_state:
            st.session_state["library_selected_list_prev"] = None

        library_list_names = list(lists_with_words.keys())
        library_selected_list = st.selectbox(
            "Liste seçin",
            options=library_list_names,
            key="library_list_select",
            label_visibility="visible",
        )
        # Reset word selection when user switches list
        if st.session_state.get("library_selected_list_prev") != library_selected_list:
            st.session_state["library_selected_list_prev"] = library_selected_list
            st.session_state["library_selected_word_index"] = None

        entries = lists_with_words.get(library_selected_list, [])
        if not entries:
            st.info("Bu listede henüz kelime yok.")
        else:
            selected_idx = st.session_state.get("library_selected_word_index")

            # ----- List view: vertical list of word buttons -----
            if selected_idx is None:
                st.subheader("Kelimeler")
                for i, entry in enumerate(entries):
                    word_label = entry.get("word", "?")
                    if st.button(
                        word_label,
                        key=f"lib_word_{library_selected_list}_{i}",
                        use_container_width=True,
                        type="primary" if selected_idx == i else "secondary",
                    ):
                        st.session_state["library_selected_word_index"] = i
                        st.rerun()
            else:
                # ----- Detail view: one selected word -----
                selected_entry = entries[selected_idx]
                word_for_display = selected_entry.get("word", "")
                markdown_for_display = selected_entry.get("markdown", "")

                # Top control: back to list
                if st.button("⬅️ Listeye Dön", key="library_back_btn"):
                    st.session_state["library_selected_word_index"] = None
                    st.rerun()

                if markdown_for_display:
                    result_html = markdown_to_card_html(markdown_for_display, searched_word=word_for_display)
                    st.markdown(result_html, unsafe_allow_html=True)
                else:
                    st.warning("Bu kayıt için analiz metni bulunamadı.")

                # Delete at bottom of detail card
                st.markdown("---")
                if st.button("❌ Listeden Sil", key="library_delete_btn"):
                    library_data[library_selected_list].pop(selected_idx)
                    save_saved_words(library_data)
                    st.session_state["library_selected_word_index"] = None
                    st.toast(f"'{word_for_display}' listeden silindi.")
                    st.rerun()
