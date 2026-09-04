import streamlit as st
import google.generativeai as genai
from PIL import Image
import uuid
import pypdf
import docx
import pandas as pd
import requests

# 1. Nastavenie stránky
st.set_page_config(
    page_title="Polaris",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. Automatická detekcia jazyka používateľa podľa IP adresy
@st.cache_data(ttl=86400)
def ziskaj_jazyk_pouzivatela():
    try:
        response = requests.get("https://ipapi.co/json/", timeout=3)
        data = response.json()
        krajina = data.get("country_code", "US")
        
        jazyky = {
            "SK": "sk",
            "CZ": "cs",
            "DE": "de",
            "AT": "de",
            "PL": "pl",
            "ES": "es",
            "FR": "fr",
            "IT": "it"
        }
        return jazyky.get(krajina, "en")
    except Exception:
        return "en"

jazyk_ui = ziskaj_jazyk_pouzivatela()

# Slovník lokalizácie užívateľského rozhrania
TEXTY = {
    "sk": {
        "title": "✨ Polaris",
        "subtitle": "Autor: Tomáš Grňo",
        "new_chat": "➕ Nový",
        "clear_all": "🧹 Všetko",
        "history": "💬 História chatov",
        "settings": "⚙️ Nastavenia",
        "placeholder": "Ako ti môžem pomôcť?",
        "hero_title": "Ahoj, ja som Polaris ✨",
        "hero_sub": "S čím chceš dnes začať?",
        "card1_title": "💡 Navrhni nápad na projekt",
        "card1_sub": "Aplikácia alebo biznis nápad",
        "card1_prompt": "Navrhni mi 3 kreatívne nápady na softvérový projekt.",
        "card2_title": "📝 Napíš e-mail / správu",
        "card2_sub": "Profesionálna komunikácia",
        "card2_prompt": "Pomôž mi napísať profesionálny e-mail s poďakovaním.",
        "role_label": "Rola Polaris:",
        "thinking": "Polaris premýšľa..."
    },
    "cs": {
        "title": "✨ Polaris",
        "subtitle": "Autor: Tomáš Grňo",
        "new_chat": "➕ Nový",
        "clear_all": "🧹 Vše",
        "history": "💬 Historie chatů",
        "settings": "⚙️ Nastavení",
        "placeholder": "Jak vám mohu pomoci?",
        "hero_title": "Ahoj, já jsem Polaris ✨",
        "hero_sub": "Čím dnes začneme?",
        "card1_title": "💡 Navrhni nápad na projekt",
        "card1_sub": "Aplikace nebo podnikatelský nápad",
        "card1_prompt": "Navrhni mi 3 kreativní nápady na softwarový projekt.",
        "card2_title": "📝 Napiš e-mail / zprávu",
        "card2_sub": "Profesionální komunikace",
        "card2_prompt": "Pomoz mi napsat profesionální e-mail s poděkováním.",
        "role_label": "Role Polaris:",
        "thinking": "Polaris přemýšlí..."
    },
    "de": {
        "title": "✨ Polaris",
        "subtitle": "Autor: Tomáš Grňo",
        "new_chat": "➕ Neu",
        "clear_all": "🧹 Alles löschen",
        "history": "💬 Chat-Verlauf",
        "settings": "⚙️ Einstellungen",
        "placeholder": "Wie kann ich dir helfen?",
        "hero_title": "Hallo, ich bin Polaris ✨",
        "hero_sub": "Womit möchtest du heute beginnen?",
        "card1_title": "💡 Schlage eine Projektidee vor",
        "card1_sub": "App- oder Geschäftsidee",
        "card1_prompt": "Schlage mir 3 kreative Ideen für ein Softwareprojekt vor.",
        "card2_title": "📝 Schreibe eine E-Mail / Nachricht",
        "card2_sub": "Professionelle Kommunikation",
        "card2_prompt": "Hilf mir, eine professionelle Dankes-E-Mail zu schreiben.",
        "role_label": "Rolle von Polaris:",
        "thinking": "Polaris denkt nach..."
    },
    "en": {
        "title": "✨ Polaris",
        "subtitle": "Created by: Tomáš Grňo",
        "new_chat": "➕ New",
        "clear_all": "🧹 Clear all",
        "history": "💬 Chat History",
        "settings": "⚙️ Settings",
        "placeholder": "How can I help you?",
        "hero_title": "Hello, I am Polaris ✨",
        "hero_sub": "What would you like to start with today?",
        "card1_title": "💡 Suggest a project idea",
        "card1_sub": "App or business idea",
        "card1_prompt": "Suggest 3 creative ideas for a software project.",
        "card2_title": "📝 Write an email / message",
        "card2_sub": "Professional communication",
        "card2_prompt": "Help me write a professional thank-you email.",
        "role_label": "Polaris Role:",
        "thinking": "Polaris is thinking..."
    }
}

t = TEXTY.get(jazyk_ui, TEXTY["en"])

# 3. CSS Štýlovanie
st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
        background-attachment: fixed;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(circle at 50% 30%, rgba(76, 29, 149, 0.25) 0%, rgba(15, 23, 42, 0) 70%),
                    radial-gradient(circle at 80% 80%, rgba(14, 165, 233, 0.15) 0%, rgba(15, 23, 42, 0) 50%);
        pointer-events: none;
        z-index: 0;
    }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.6); }
    ::-webkit-scrollbar-thumb { background: rgba(56, 189, 248, 0.2); border-radius: 10px; }

    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    [data-testid="stSidebar"] .stButton > button {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0.5rem 0;
        margin-bottom: 0.8rem;
        animation: fadeIn 0.3s ease-out forwards;
    }

    [data-testid="stChatMessageAvatarUser"] {
        background: linear-gradient(135deg, #6366f1, #a855f7) !important;
        border-radius: 50% !important;
    }

    [data-testid="stChatMessageAvatarAssistant"] {
        background: linear-gradient(135deg, #0ea5e9, #a855f7) !important;
        border-radius: 50% !important;
    }

    [data-testid="stChatInput"] {
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        background-color: rgba(15, 23, 42, 0.9) !important;
    }

    div[data-testid="stBottom"], div[data-testid="stBottom"] > div {
        background: transparent !important;
        border: none !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.stPopover) {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: calc(100% - 40px);
        max-width: 730px;
        z-index: 100;
        background-color: #0f172a;
        padding: 6px 12px;
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }

    .stPopover>button {
        border-radius: 50% !important;
        width: 42px !important;
        height: 42px !important;
        padding: 0 !important;
        font-size: 20px !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
    }

    .main .block-container { padding-bottom: 120px; }
    </style>
""", unsafe_allow_html=True)

# 4. Načítanie API kľúča
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Chýba GOOGLE_API_KEY v Secrets!")
    st.stop()

# 5. Dynamické získanie modelov s výberom Flash verzii pre rýchlosť
@st.cache_data(ttl=3600)
def ziskaj_dostupne_modely():
    try:
        modely = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modely.append(m.name)
        
        if modely:
            flash_modely = [m for m in modely if "flash" in m.lower()]
            ostatne = [m for m in modely if "flash" not in m.lower()]
            return flash_modely + ostatne
            
        return ["models/gemini-1.5-flash"]
    except Exception:
        return ["models/gemini-1.5-flash"]

# 6. Správa session state
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    prve_id = str(uuid.uuid4())
    st.session_state.chats[prve_id] = {"title": "Polaris", "messages": []}
    st.session_state.current_chat_id = prve_id

if "aktivny_rezim" not in st.session_state:
    st.session_state.aktivny_rezim = "Standard"

def vytvor_novy_chat():
    nove_id = str(uuid.uuid4())
    st.session_state.chats[nove_id] = {"title": "Polaris", "messages": []}
    st.session_state.current_chat_id = nove_id

# 7. Dynamické roly s detekciou jazyka vstupu
ROLY = {
    "Personal Assistant": "You are Polaris, a personal AI assistant. ALWAYS respond in the EXACT same language that the user uses to write to you (e.g., if the user writes in Slovak, respond in Slovak; if in English, respond in English, etc.). Maintain a helpful, concise, and direct tone.",
    "Programmer": "You are Polaris, an expert programmer. ALWAYS respond in the EXACT same language used by the user. Provide concise answers with clean code blocks.",
    "English Teacher": "You are Polaris. Respond in English and provide a brief translation in the language used by the user below.",
    "Concise Assistant": "You are Polaris. ALWAYS respond in the EXACT same language used by the user, limiting responses to a maximum of 2-3 short sentences."
}
