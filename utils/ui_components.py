# utils/ui_components.py
import streamlit as st

def render_grouped_pagination(items: list, group_size: int, label_prefix: str, content_renderer_func):
    """
    Groups items into pages and displays them as buttons in the sidebar.
    When a button is clicked, it opens a dialog with the items as expanders.
    
    :param items: List of items fetched from Google Sheets.
    :param group_size: Number of items per button/page.
    :param label_prefix: Prefix for the button label (e.g., "Kelime Listesi", "Okuma Metinleri").
    :param content_renderer_func: The function that renders the HTML content inside the dialog.
    """
    if not items:
        st.sidebar.info("Kayıt bulunamadı.")
        return

    # Invert to show newest first
    items = list(reversed(items))
    total_items = len(items)
    total_pages = (total_items + group_size - 1) // group_size

    for i in range(total_pages):
        start_idx = i * group_size
        end_idx = min(start_idx + group_size, total_items)
        page_items = items[start_idx:end_idx]
        
        button_label = f"📁 {label_prefix} {i + 1} ({len(page_items)} Kayıt)"
        
        if st.sidebar.button(button_label, key=f"page_btn_{label_prefix}_{i}", use_container_width=True):
            show_grouped_items_dialog(f"{label_prefix} {i + 1}", page_items, content_renderer_func)

@st.dialog("Kayıt Detayları", width="large")
def show_grouped_items_dialog(title: str, page_items: list, content_renderer_func):
    st.markdown(f"### {title}")
    st.markdown("<p style='opacity:0.7; margin-bottom: 20px;'>İncelemek istediğiniz kaydın üzerine tıklayın.</p>", unsafe_allow_html=True)
    
    for idx, item in enumerate(page_items):
        item_title = item.get("title", "İsimsiz")
        # Ensure it's reasonably short for the expander header
        short_title = item_title[:45] + "..." if len(item_title) > 45 else item_title
        
        with st.expander(f"✨ {short_title}"):
            content = item.get("content", "")
            content_renderer_func(content)
                  
