from google import genai
from google.genai import types
import streamlit as st

SYSTEM_INSTRUCTIONS_DICT = """Sen 'Seneman Sözlük' için çalışan, akademik bir dil asistanısın. Çıktılarını şu KATI formatta ver:
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

SYSTEM_INSTRUCTIONS_TRANS = """Sen 'Seneman Sözlük' için çalışan, profesyonel bir çevirmen ve dilbilimci asistanısın. 
Görevin, kullanıcının verdiği Türkçe cümleyi en doğal, akademik veya profesyonel İngilizce karşılığıyla çevirmek ve yapısını analiz etmektir.
Çıktı formatı KESİNLİKLE şu JSON yapısında olmalıdır. (Düz metin verme, sadece JSON ver):
{
  "translation": "İngilizce çeviri",
  "logic": "Cümlenin İngilizceye çevrilirken kullanılan gramer yapısı veya mantığının kısa bir Türkçe açıklaması (Hangi tense kullanıldı, neden o bağlaç tercih edildi vs.)",
  "vocabulary": [
    {"en": "word1", "tr": "kelime1_anlami"},
    {"en": "word2", "tr": "kelime2_anlami"}
  ]
}
"""

# Fallback chain
FALLBACK_CHAIN = ["models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-flash"]

def get_gemini_model(api_key: str, model_id: str, module_type: str = "dict"):
    if not api_key or not api_key.strip(): 
        st.error("API Anahtarı eksik veya boş.")
        return None
    try:
        client = genai.Client(api_key=api_key.strip())
        system_instruction = SYSTEM_INSTRUCTIONS_DICT if module_type == "dict" else (SYSTEM_INSTRUCTIONS_TRANS if module_type == "trans" else None)
        return {"client": client, "model_id": model_id, "system_instruction": system_instruction}
    except Exception as e:
        st.error(f"Gemini API Bağlantı Hatası: {str(e)}")
        return None

def _execute_with_fallback(model_data, prompt, config=None):
    client = model_data["client"]
    initial_model = model_data["model_id"]
    
    # Identify the starting index in the fallback chain
    try:
        start_idx = FALLBACK_CHAIN.index(initial_model)
    except ValueError:
        start_idx = 0
    
    # Try the initial model and then the remaining fallback models in order
    current_chain = [initial_model] + [m for m in FALLBACK_CHAIN if m != initial_model]
    
    last_error = ""
    for model_name in current_chain:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt, config=config)
            if model_name != initial_model:
                st.info(f"💡 Kotanız dolduğu için otomatik olarak bir alt modele ({model_name}) geçiş yapıldı.")
            return response.text or ""
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "resource_exhausted" in err_msg or "quota" in err_msg:
                last_error = str(e)
                continue # Try next model
            else:
                st.error(f"Gemini API Hatası: {str(e)}")
                return ""
    
    st.error(f"Tüm modellerin kotası doldu. Lütfen biraz sonra tekrar deneyin. Detay: {last_error}")
    return ""

def analyze_word(model_data, word: str) -> str:
    if not model_data or not word or not word.strip(): return ""
    sys_inst = model_data["system_instruction"]
    prompt = f"Şu İngilizce kelimeyi yukarıdaki şablona göre analiz et. Doğrudan şablonla başla, giriş veya kapanış cümlesi yazma.\n\nKelime: {word.strip()}"
    config = types.GenerateContentConfig(system_instruction=sys_inst) if sys_inst else None
    return _execute_with_fallback(model_data, prompt, config)

def generate_reading_text(model_data, topic: str) -> str:
    if not model_data: return ""
    sys_inst = model_data["system_instruction"]
    prompt = f"""
    You are a professional content creator for channels like PolyMatter, Wendover Productions, or Knowledgia.
    TASK: Write a unique, specific, and academic-level article in English about a RANDOM and INTERESTING sub-topic within the field of '{topic}'.
    Generate an English reading text that is STRICTLY between 300 and 400 words long. Do not exceed 400 words under any circumstances.
    The text MUST be written strictly at a B2 or C1 English proficiency level (CEFR). Use clear, engaging, and modern language suitable for upper-intermediate to advanced learners. Strictly avoid overly academic, archaic, or unnecessarily obscure vocabulary.
    """
    config = types.GenerateContentConfig(system_instruction=sys_inst) if sys_inst else None
    return _execute_with_fallback(model_data, prompt, config)

def analyze_reading_sentences(model_data, text: str) -> str:
    if not model_data: return ""
    sys_inst = model_data["system_instruction"]
    prompt = f"Analyze the following English text sentence by sentence. For each sentence use EXACTLY this format (no extra text):\n\n---\nSentence: [English sentence]\nÇeviri: [Turkish translation]\nMantık: [Brief Turkish explanation of grammar/structure/logic]\n---\n\nText:\n{text}"
    config = types.GenerateContentConfig(system_instruction=sys_inst) if sys_inst else None
    return _execute_with_fallback(model_data, prompt, config)

def translate_sentence(model_data, tr_text: str) -> str:
    if not model_data: return ""
    sys_inst = model_data["system_instruction"]
    prompt = f"Şu cümleyi çevir ve JSON olarak döndür:\n{tr_text.strip()}"
    config = types.GenerateContentConfig(system_instruction=sys_inst) if sys_inst else None
    return _execute_with_fallback(model_data, prompt, config)
