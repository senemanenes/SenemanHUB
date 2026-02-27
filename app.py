import streamlit as st

st.set_page_config(
    page_title='SenemanHUB',
    page_icon='https://raw.githubusercontent.com/senemanenes/DjangoAbiApp/main/logo.png',
    layout='wide'
)

LOGO_URL = "https://raw.githubusercontent.com/senemanenes/DjangoAbiApp/main/logo.png"

st.markdown(f'''
<!-- Apple / iOS iin ikonlar -->
<link rel="apple-touch-icon" sizes="180x180" href="{LOGO_URL}">
<link rel="apple-touch-startup-image" href="{LOGO_URL}">

<!-- Android ve Genel Tarayıcılar (Chrome vs.) İçin Zorunlu PWA İkonları -->
<link rel="icon" type="image/png" sizes="192x192" href="{LOGO_URL}">
<link rel="icon" type="image/png" sizes="512x512" href="{LOGO_URL}">
<link rel="shortcut icon" href="{LOGO_URL}">

<!-- Web App Meta Verileri -->
<meta name="theme-color" content="#121826">
<meta name="apple-mobile-web-app-title" content="SenemanHUB">
<meta name="application-name" content="SenemanHUB">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
''', unsafe_allow_html=True)

# Hide Streamlit UI elements (Header, Footer, Menu)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

def home_page():
    # Shared Base CSS For The App Homepage
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"

    bg_color = "#F0F4F8" if st.session_state["theme"] == "light" else "#121826"
    text_color = "#1E293B" if st.session_state["theme"] == "light" else "#F1F5F9"
    card_bg = "#FFFFFF" if st.session_state["theme"] == "light" else "#1E293B"
    border_color = "#E2E8F0" if st.session_state["theme"] == "light" else "#334155"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
        
        .stApp {{ background-color: {bg_color} !important; font-family: 'Nunito', sans-serif !important; color: {text_color} !important; }}
        h1 {{ color: {text_color} !important; font-weight: 800; letter-spacing: -0.5px; }}
        p {{ font-size: 1.1rem; line-height: 1.6; }}
        
        .welcome-card {{
            background: {card_bg};
            border: 1px solid {border_color};
            border-radius: 20px;
            padding: 35px;
            margin-top: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .welcome-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        }}
        
        .module-item {{ margin-bottom: 25px; padding: 15px; border-radius: 12px; background: rgba(0,0,0,0.02); transition: background 0.2s; }}
        .module-item:hover {{ background: rgba(0,0,0,0.04); }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("🏠 SenemanHub'a Hoş Geldiniz")

    st.markdown(f"""
    <div class="welcome-card">
        <p style="font-size:1.2rem; font-weight:600; text-align:center; color:#6366F1;">Akademik ve profesyonel İngilizce çalışmalarınızı daha verimli hale getirin.</p>
        <br>
        <p style="text-align:center; color:{text_color}; opacity:0.8;">Sol üstteki <strong style="font-size:1.2rem;">≡</strong> ikonuna tıklayarak menüyü açabilir ve modüllere erişebilirsiniz:</p>
        <hr style="border-color: {border_color}; margin: 30px 0;">
        <ul style="list-style-type: none; padding-left: 0;">
            <li class="module-item">
                <strong style="color: #10B981; font-size: 1.3rem;">📖 Sözlük</strong><br>
                <span style="opacity:0.8;">Kelime analizi yapın, kullanım alanlarını, eşanlamlıları ve edatlı yapıları örnekleriyle öğrenin.</span>
            </li>
            <li class="module-item">
                <strong style="color: #8B5CF6; font-size: 1.3rem;">📚 Reading Center</strong><br>
                <span style="opacity:0.8;">İlginizi çeken konularda yapay zeka tarafından oluşturulmuş İngilizce makaleler okuyun ve her bir cümleyi mantığıyla analiz edin.</span>
            </li>
            <li class="module-item">
                <strong style="color: #F59E0B; font-size: 1.3rem;">📝 Cümle Çeviri</strong><br>
                <span style="opacity:0.8;">Türkçe cümlelerinizin profesyonel İngilizce karşılıklarını ve bu çevirilerin gramer yapılarını keşfedin.</span>
            </li>
        </ul>
        <p style="margin-top: 30px; font-style: italic; font-size: 0.95rem; text-align: center; opacity:0.5;">
            SenemanHub — 2026
        </p>
    </div>
    """, unsafe_allow_html=True)

try:
    with st.sidebar:
        # Sadece logo yerleşimi (genişlik 180)
        st.sidebar.image(LOGO_URL, width=180)

    pg = st.navigation({
        "🏠 SenemanHUB": [
            st.Page(home_page, title="🏠 Ana Sayfa", default=True),
            st.Page("pages/1_📖_Sozluk.py", title="📖 Sözlük"),
            st.Page("pages/2_📚_Reading_Center.py", title="📚 Reading Center"),
            st.Page("pages/3_📝_Cumle_Ceviri.py", title="📝 Cümle Çeviri")
        ]
    })
    pg.run()
except AttributeError:
    home_page()