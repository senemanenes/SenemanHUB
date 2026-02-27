# utils/config.py
import re
import markdown as md
import html

# --- Modern Theme colors (Pastel/Duolingo Style) ---
THEMES = {
    "dark": {
        "bg": "#0F172A",
        "card_bg": "#1E293B",
        "border": "#334155",
        "text": "#F8FAFC",
        "text_muted": "#94A3B8",
        "input_bg": "#0F172A",
        "accent": "#38BDF8",
        "button": "linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)",
        "button_hover": "linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)",
        "shadow": "0 8px 25px rgba(0,0,0,0.3)"
    },
    "light": {
        "bg": "#F8FAFC",
        "card_bg": "#FFFFFF",
        "border": "#E2E8F0",
        "text": "#0F172A",
        "text_muted": "#64748B",
        "input_bg": "#F1F5F9",
        "accent": "#0EA5E9",
        "button": "linear-gradient(135deg, #818CF8 0%, #A78BFA 100%)",
        "button_hover": "linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)",
        "shadow": "0 8px 25px rgba(0,0,0,0.06)"
    },
}

SECTION_STYLES = {
    "header": ("header", "#059669"),
    "turkce": ("turkce", "#059669"),
    "turkce2": ("turkce", "#059669"),
    "english": ("english", "#E11D48"),
    "english2": ("english", "#E11D48"),
    "kullanim": ("kullanim", "#2563EB"),
    "collocations": ("collocations", "#D97706"),
    "kelime-formlari": ("kelime-formlari", "#7C3AED"),
    "es-zit": ("es-zit", "#16A34A"),
    "ornekler": ("ornekler", "#BE123C"),
    "default": ("default", "#64748B"),
}

MODEL_OPTIONS = [
    "Gemini 2.5 Flash",
    "Gemini 2.0 Flash",
    "Gemini 1.5 Flash"
]

MODEL_ID_MAP = {
    "Gemini 2.5 Flash": "models/gemini-2.5-flash",
    "Gemini 2.0 Flash": "models/gemini-2.0-flash",
    "Gemini 1.5 Flash": "models/gemini-1.5-flash",
}

def _build_base_css(theme: str) -> str:
    t = THEMES.get(theme, THEMES["dark"])
    css = f"""
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Merriweather:ital,wght@0,400;0,700;1,400&display=swap');
    
    .stApp, .stApp * {{ font-family: 'Nunito', sans-serif !important; }}
    .stApp {{ background-color: {t['bg']} !important; }}
    .stApp .stMarkdown, .stApp p, .stApp label, .stApp .stCaption {{ color: {t['text']} !important; }}
    
    .stTextInput input, .stTextArea textarea {{ 
        background-color: {t['input_bg']} !important; 
        color: {t['text']} !important; 
        border: 2px solid {t['border']} !important;
        border-radius: 12px;
        padding: 10px 15px;
        transition: border-color 0.2s;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: #8B5CF6 !important;
    }}
    
    .stButton > button {{ 
        background: {t['button']} !important; 
        color: #FFFFFF !important; 
        border-radius: 16px; 
        font-weight: 700; 
        border: none; 
        padding: 8px 16px;
        box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    .stButton > button:hover {{ 
        background: {t['button_hover']} !important; 
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(99, 102, 241, 0.4);
    }}
    .stButton > button:active {{
        transform: translateY(1px);
    }}
    
    h1, h2, h3 {{ color: {t['text']} !important; font-weight: 800; letter-spacing: -0.5px; }}
    """
    return css

def _build_dict_css(theme: str) -> str:
    t = THEMES.get(theme, THEMES["dark"])
    parts = [
        f"""
        .word-header-box {{ background: {t['input_bg']}; border: 2px solid {t['border']}; border-radius: 15px; padding: 18px 24px; margin-bottom: 25px; font-weight: 800; color: {t['accent']}; font-size: 1.3rem; text-align: center; box-shadow: {t['shadow']}; }}
        .result-card {{ background: {t['card_bg']}; border: 1px solid {t['border']}; border-radius: 20px; box-shadow: {t['shadow']}; padding: 35px; margin-bottom: 25px; color: {t['text']}; transition: transform 0.3s; }}
        .result-card:hover {{ transform: scale(1.005); }}
        .result-card .section {{ margin-bottom: 15px; background: {t['input_bg']}; padding: 15px 20px; border-radius: 12px; }}
        .result-card .section hr.sep {{ display: none; }}
        .result-card .section hr.example-sep {{ border: none; border-top: 1px dashed {t['border']}; margin: 15px 0; }}
        .result-card .section p, .result-card .section li {{ line-height: 1.8; font-size: 1.05rem; color: {t['text']}; margin-bottom: 12px; }}
        .result-card em {{ color: {t['text_muted']} !important; font-style: italic; font-weight: 600; font-size: 0.95rem; }}
        """
    ]
    for key, (cls, color) in SECTION_STYLES.items():
        parts.append(f".result-card .section.section-{cls} strong, .result-card .section.section-{cls} h3 {{ color: {color} !important; font-weight: 800; display: block; margin-bottom: 8px; font-size: 1.15rem; }}")
    return "\n".join(parts)

def _build_reading_css(theme: str) -> str:
    t = THEMES.get(theme, THEMES["dark"])
    return f"""
    .reading-book-style {{
        background-color: {t['card_bg']};
        padding: 45px 55px;
        border-radius: 20px;
        border: 1px solid {t['border']};
        box-shadow: {t['shadow']};
        line-height: 2 !important;
        font-size: 1.15rem;
        color: {t['text']} !important;
        margin-bottom: 35px;
        text-align: justify;
        font-family: 'Merriweather', serif !important;
        transition: transform 0.3s;
    }}
    .reading-book-style:hover {{ transform: translateY(-3px); box-shadow: 0 12px 30px rgba(0,0,0,0.1); }}
    .reading-book-style p, .reading-book-style h1, .reading-book-style h2, .reading-book-style h3 {{
        color: {t['text']} !important;
        font-family: 'Merriweather', serif !important;
    }}
    
    .analysis-card {{
        background: {t['card_bg']};
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 25px;
        border: 2px solid {t['border']};
        box-shadow: {t['shadow']};
        border-left: 6px solid #10B981;
        font-family: 'Nunito', sans-serif !important;
        color: {t['text']} !important;
        transition: transform 0.2s;
    }}
    .analysis-card:hover {{ transform: translateX(5px); }}
    .analysis-card p {{ color: {t['text']} !important; font-family: 'Nunito', sans-serif !important; font-size: 1.05rem; }}
    .header-sentence {{ color: #10B981; font-weight: 800; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px; }}
    .header-translation {{ color: #3B82F6; font-weight: 800; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px; margin-top: 15px; }}
    .header-logic {{ color: #8B5CF6; font-weight: 800; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px; margin-top: 15px; }}
    .thick-sep {{ border: none; border-top: 4px dotted {t['border']}; margin: 50px 0; opacity: 0.6; }}
    """

def _build_trans_css(theme: str) -> str:
    t = THEMES.get(theme, THEMES["dark"])
    return f"""
    .trans-card {{ background: {t['card_bg']}; border: 1px solid {t['border']}; border-radius: 20px; box-shadow: {t['shadow']}; padding: 35px; margin-bottom: 25px; color: {t['text']}; transition: transform 0.3s; }}
    .trans-card:hover {{ transform: scale(1.01); }}
    .trans-header {{ color: {t['accent']}; font-weight: 800; font-size: 1.1rem; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; }}
    .trans-original {{ font-style: italic; color: {t['text_muted']}; margin-bottom: 25px; font-size: 1.1rem; border-left: 4px solid {t['border']}; padding-left: 15px; }}
    .trans-translation {{ font-size: 1.3rem; font-weight: 700; margin-bottom: 25px; color: {t['text']}; background: {t['input_bg']}; padding: 20px; border-radius: 12px; }}
    .trans-logic {{ padding: 20px; background-color: {t['input_bg']}; border-left: 5px solid #8B5CF6; border-radius: 12px; margin-bottom: 25px; font-size: 1.05rem; line-height: 1.6; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); }}
    .trans-vocab {{ padding-top: 15px; border-top: 2px dashed {t['border']}; }}
    .trans-vocab-title {{ color: {t['text']}; font-weight: 800; margin-bottom: 15px; font-size: 1.1rem; text-transform: uppercase; }}
    .trans-vocab-item {{ background-color: {t['input_bg']}; padding: 8px 14px; border-radius: 20px; border: 1px solid {t['border']}; margin-right: 10px; margin-bottom: 10px; display: inline-block; font-size: 0.95rem; font-weight: 600; box-shadow: 0 2px 5px rgba(0,0,0,0.03); }}
    """

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
        html_parts.append(f'<div class="section section-{cls}">{block_html}</div>')
    inner = "\n".join(html_parts)
    card = f'<div class="result-card">{inner}</div>'
    if searched_word:
        return f'<div class="word-header-box">{html.escape(searched_word.strip()).upper()}</div>' + card
    return card

def parse_analysis_to_html(raw_md: str) -> str:
    blocks = re.split(r"---", raw_md)
    html_output = ""
    for block in blocks:
        if "Sentence:" in block:
            try:
                s = re.search(r"Sentence:(.*?)(?=Çeviri:|$)", block, re.S).group(1).strip()
                t = re.search(r"Çeviri:(.*?)(?=Mantık:|$)", block, re.S).group(1).strip()
                l = re.search(r"Mantık:(.*)", block, re.S).group(1).strip()
                html_output += f'''
                <div class="analysis-card">
                    <div class="header-sentence">🇬🇧 SENTENCE</div>
                    <p>{s}</p>
                    <div class="header-translation">🇹🇷 ÇEVİRİ</div>
                    <p><i>{t}</i></p>
                    <div class="header-logic">🧠 MANTIK</div>
                    <p>{l}</p>
                </div>'''
            except AttributeError:
                pass
    return html_output
