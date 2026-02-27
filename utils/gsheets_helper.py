import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

@st.cache_resource
def get_connection():
    """Initializes and returns a Google Sheets connection."""
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def fetch_data(sheet_name: str) -> list:
    """Fetches data from the specified sheet and returns it as a list of dictionaries."""
    try:
        conn = get_connection()
        # Read the sheet. Assumes columns: timestamp, title, content
        df = conn.read(worksheet=sheet_name, ttl=60)
        # Drop rows where all elements are NaN
        df = df.dropna(how="all")
        if df.empty:
            return []
        # Convert to list of dicts
        return df.to_dict("records")
    except Exception as e:
        st.error("Google Sheets'e ulaşılamadı. Lütfen internet bağlantınızı veya `.streamlit/secrets.toml` ayarlarınızı (ve tablo adını) kontrol edin.")
        return []

def append_data(sheet_name: str, title: str, content: str) -> bool:
    """Appends a new record to the specified sheet."""
    try:
        conn = get_connection()
        # Read existing data to concatenate
        existing_df = conn.read(worksheet=sheet_name, ttl=0)
        existing_df = existing_df.dropna(how="all")
        
        # Sütunlar: timestamp, title, content
        new_record = pd.DataFrame([{
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "content": content
        }])
        
        # Concatenate and update
        if existing_df.empty:
            updated_df = new_record
        else:
            updated_df = pd.concat([existing_df, new_record], ignore_index=True)
            
        conn.update(worksheet=sheet_name, data=updated_df)
        
        # Clear the cache for the fetch_data function
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error("Google Sheets'e veri yazılırken bir hata oluştu. İnternet bağlantınızı veya tablo izinlerinizi kontrol edin.")
        return False
