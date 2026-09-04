import streamlit as st
import google.generativeai as genai
from PIL import Image
import uuid
import pypdf
import docx
import pandas as pd

# 1. Nastavenie stránky
st.set_page_config(
    page_title="Polaris",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. Moderné a kompletné CSS štýlovanie
st.markdown("""
    <style>
    /* Globálne pozadie a písmo */
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

    /* Prispôsobený (Custom) Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.6);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(56, 189, 248, 0.2);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(168, 85, 247, 0.5);
    }

    /* Bočný panel */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Glassmorphism tlačidlá v bočnom paneli */
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        transition: all 0.2s ease-in-out !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(56, 189, 248, 0.15) !important;
        border-color: rgba(56, 189, 248, 0.4) !important;
        transform: translateX(2px);
    }

    /* Plynulý dojazd správ (Fade-In) */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0.5rem 0;
        margin-bottom: 0.8rem;
        animation: fadeIn 0.3s ease-out forwards;
    }

    /* Využitie kruhových efektov pre avatary */
    [data-testid="stChatMessageAvatarUser"] {
        background: linear-gradient(135deg, #6366f1, #a855f7) !important;
        border-radius: 50% !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    [data-testid="stChatMessageAvatarAssistant"] {
        background: linear-gradient(135deg, #0ea5e9, #a855f7) !important;
        border-radius: 50% !important;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
    }

    /* Chat input štýlovanie a glow pri náhľade */
    [data-testid="stChatInput"] {
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        background-color: rgba(15, 23, 42, 0.9) !important;
        transition: all 0.3s ease;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: rgba(168, 85, 247, 0.6) !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.3) !important;
    }

    /* Skrytie pozadia spodného panela Streamlitu */
    div[data-testid="stBottom"],
    div[data-testid="stBottom"] > div {
        background: transparent !important;
        border: none !important;
    }

    /* Ukotvenie spodnej lišty */
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
        align-items: center;
        overflow: hidden;
    }

    .stPopover>button {
        border-radius: 50% !important;
        width: 42px !important;
        height: 42px !important;
        padding: 0 !important;
        font-size: 20px !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* Animovaný indikátor načítania */
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 5px rgba(168, 85, 247, 0.4); }
        50% { box-shadow: 0 0 18px rgba(56, 189, 248, 0.8); }
        100% { box-shadow: 0 0 5px rgba(168, 85, 247, 0.4); }
    }

    div[data-baseweb="spinner"] {
        border-top-color: #a855f7 !important;
        border-left-color: #38bdf8 !important;
        animation: pulseGlow 1.5s infinite ease-in-out;
    }

    div[data-testid="stPopoverBody"] {
        background-color: #161b22 !important;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
    }

    /* Štýlovanie blokov kódu */
    .stCodeBlock {
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }

    .main .block-container {
        padding-bottom: 120px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Načítanie API kľúča
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Chýba GOOGLE_API_KEY v Secrets!")
    st.stop()

# Garantované zoradenie: Gemini 2.5 Flash Lite ako primárny model
@st.cache_data(ttl=3600)
def ziskaj_dostupne_modely():
    # Primárne verzie s modelom 2.5 Flash Lite na 1. mieste
    priority_list = [
        "models/gemini-2.5-flash-lite",
        "gemini-2.5-flash-lite",
        "models/gemini-1.5-flash-lite",
        "models/gemini-1.5-flash"
    ]
    
    try:
        dostupne = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                dostupne.append(m.name)
        
        # Filtrovanie pre zaistenie poradia s fallbackom
        vysledok = [m for m in priority_list if m in dostupne]
        for m in dostupne:
            if m not in vysledok:
                vysledok.append(m)
                
        return vysledok if vysledok else priority_list
    except Exception:
        return priority_list

# 4. Štruktúra pre ukladanie chatov
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    prve_id = str(uuid.uuid4())
    st.session_state.chats[prve_id] = {"title": "Polaris", "messages": []}
    st.session_state.current_chat_id = prve_id

if "aktivny_rezim" not in st.session_state:
    st.session_state.aktivny_rezim = "Štandardný"

def vytvor_novy_chat():
    nove_id = str(uuid.uuid4())
    st.session_state.chats[nove_id] = {"title": "Polaris", "messages": []}
    st.session_state.current_chat_id = nove_id

# 5. Definícia rolí
ROLY = {
    "Osobná asistentka": "Voláš sa Polaris. Si moja osobná AI asistentka. Hovoríš výlučne po slovensky v ženskom rode. Odpovedaj stručne a k veci.",
    "Programátorka": "Voláš sa Polaris. Si expertka na Python a web. Odpovedaj stručne s prehľadným kódom po slovensky.",
    "Učiteľka angličtiny": "Voláš sa Polaris. Odpovedaj po anglicky a pod to pridaj stručný slovenský preklad.",
    "Stručná asistentka": "Voláš sa Polaris. Odpovedaj maximálne v 2-3 krátkych vetách po slovensky."
}

# 6. Bočný panel
with st.sidebar:
    st.title("✨ Polaris")
    
    col_new, col_clear = st.columns([0.7, 0.3])
    with col_new:
        if st.button("➕ Nový", use_container_width=True):
            vytvor_novy_chat()
            st.rerun()
    with col_clear:
        if st.button("🧹 Všetko", help="Vymazať celú históriu chatov", use_container_width=True):
            st.session_state.chats = {}
            vytvor_novy_chat()
            st.rerun()

    st.divider()
    st.subheader("💬 História chatov")
    
    for chat_id, chat_data in list(st.session_state.chats.items()):
        is_active = (chat_id == st.session_state.current_chat_id)
        label = f"📍 {chat_data['title']}" if is_active else chat_data['title']
        
        col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
        with col1:
            if st.button(label, key=f"select_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("✏️", key=f"edit_btn_{chat_id}"):
                st.session_state[f"editing_{chat_id}"] = not st.session_state.get(f"editing_{chat_id}", False)
                st.rerun()
        with col3:
            if st.button("🗑", key=f"del_{chat_id}"):
                del st.session_state.chats[chat_id]
                if st.session_state.current_chat_id == chat_id:
                    if st.session_state.chats:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                    else:
                        vytvor_novy_chat()
                st.rerun()

        if st.session_state.get(f"editing_{chat_id}", False):
            novy_nazov = st.text_input("Nový názov:", value=chat_data['title'], key=f"rename_input_{chat_id}")
            if st.button("Uložiť názov", key=f"save_rename_{chat_id}", use_container_width=True):
                if novy_nazov.strip():
                    st.session_state.chats[chat_id]['title'] = novy_nazov.strip()
                    st.session_state[f"editing_{chat_id}"] = False
                    st.rerun()

    st.divider()
    st.header("⚙️ Nastavenia")
    vybrana_rola = st.selectbox("Rola Polaris:", list(ROLY.keys()))

# 7. Zobrazenie správ
aktualny_chat = st.session_state.chats[st.session_state.current_chat_id]

st.title("✨ Polaris")
st.caption(f"Tvorca: Tomáš Grňo | Režim: {st.session_state.aktivny_rezim}")

# Hero úvodná sekcia s rýchlymi kartičkami pri prázdnom chate
if len(aktualny_chat["messages"]) == 0:
    st.markdown("""
        <div style="text-align: center; padding: 30px 20px 20px 20px;">
            <h2 style="background: linear-gradient(to right, #38bdf8, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.2rem; font-weight: 700;">
                Ahoj, ja som Polaris ✨
            </h2>
            <p style="color: #94a3b8; font-size: 1.05rem;">S čím chceš dnes začať?</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_card1, col_card2 = st.columns(2)
    with col_card1:
        if st.button("💡 **Navrhni nápad na projekt**\n\n_Aplikácia alebo biznis nápad_", use_container_width=True):
            st.session_state["pouzity_prompt"] = "Navrhni mi 3 kreatívne nápady na softvérový projekt."
            st.rerun()
    with col_card2:
        if st.button("📝 **Napíš e-mail / správu**\n\n_Profesionálna komunikácia_", use_container_width=True):
            st.session_state["pouzity_prompt"] = "Pomôž mi napísať profesionálny e-mail s poďakovaním."
            st.rerun()

for idx, msg in enumerate(aktualny_chat["messages"]):
    avatar = "✨" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        if "image" in msg and msg["image"] is not None:
            st.image(msg["image"], use_container_width=True)
        
        if "file_info" in msg and msg["file_info"]:
            st.caption(f"📎 Priložený súbor: **{msg['file_info']}**")
            
        st.markdown(msg["content"])
        
        if msg["role"] == "assistant":
            with st.popover("📋 Kopírovať"):
                st.code(msg["content"], language=None)

# 8. Spodná lišta
col_plus, col_input = st.columns([0.1, 0.9])

with col_plus:
    with st.popover("➕"):
        nahraty_subor = st.file_uploader(
            "Priložiť súbor (Obrázok, TXT, PDF, DOCX, XLSX, CSV):",
            type=["png", "jpg", "jpeg", "txt", "pdf", "docx", "xlsx", "xls", "csv"]
        )

        st.divider()

        if st.button("🖼 **Obrázky** — Vytvárajte a upravujte", use_container_width=True):
            st.session_state.aktivny_rezim = "Obrázky"
            st.rerun()
        if st.button("🎵 **Hudba** — Vytvárajte zvukové stopy", use_container_width=True):
            st.session_state.aktivny_rezim = "Hudba"
            st.rerun()
        if st.button("🖥 **Canvas** — Programujte, píšte alebo vytvárajte snímky", use_container_width=True):
            st.session_state.aktivny_rezim = "Canvas"
            st.rerun()

with col_input:
    prompt_input = st.chat_input("Ako ti môžem pomôcť?")

# Zachytenie vstupu z kartičky alebo z textového políčka
prompt = prompt_input or st.session_state.pop("pouzity_prompt", None)

# 9. Spracovanie vstupu
if prompt:
    if len(aktualny_chat["messages"]) == 0:
        aktualny_chat["title"] = prompt[:18] + "..." if len(prompt) > 18 else prompt

    sprava_pouzivatela = {"role": "user", "content": prompt}
    obsah_spravy = [prompt]
    
    if 'nahraty_subor' in locals() and nahraty_subor is not None:
        subor_typ = nahraty_subor.type
        nazov_suboru = nahraty_subor.name
        
        if subor_typ in ["image/png", "image/jpeg", "image/jpg"]:
            img = Image.open(nahraty_subor)
            obsah_spravy.append(img)
            sprava_pouzivatela["image"] = img
            sprava_pouzivatela["file_info"] = nazov_suboru
            
        elif subor_typ == "text/plain":
            text_suboru = nahraty_subor.read().decode("utf-8")
            obsah_spravy.append(f"\n\nText zo súboru {nazov_suboru}:\n{text_suboru}")
            sprava_pouzivatela["file_info"] = nazov_suboru
            
        elif subor_typ == "application/pdf":
            try:
                pdf_reader = pypdf.PdfReader(nahraty_subor)
                pdf_text = ""
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text() or ""
                obsah_spravy.append(f"\n\nObsah z PDF súboru {nazov_suboru}:\n{pdf_text}")
                sprava_pouzivatela["file_info"] = nazov_suboru
            except Exception as e:
                st.error(f"Chyba pri čítaní PDF: {e}")

        elif nazov_suboru.endswith(".docx"):
            try:
                doc = docx.Document(nahraty_subor)
                docx_text = "\n".join([p.text for p in doc.paragraphs if p.text])
                obsah_spravy.append(f"\n\nObsah z Word dokumentu {nazov_suboru}:\n{docx_text}")
                sprava_pouzivatela["file_info"] = nazov_suboru
            except Exception as e:
                st.error(f"Chyba pri čítaní Word súboru: {e}")

        elif nazov_suboru.endswith((".xlsx", ".xls", ".csv")):
            try:
                if nazov_suboru.endswith(".csv"):
                    df = pd.read_csv(nahraty_subor)
                else:
                    df = pd.read_excel(nahraty_subor)
                
                excel_text = df.to_markdown(index=False)
                obsah_spravy.append(f"\n\nÚdaje z tabuľky {nazov_suboru}:\n{excel_text}")
                sprava_pouzivatela["file_info"] = nazov_suboru
            except Exception as e:
                st.error(f"Chyba pri čítaní tabuľky: {e}")

    aktualny_chat["messages"].append(sprava_pouzivatela)
    
    with st.chat_message("user", avatar="👤"):
        if "image" in sprava_pouzivatela:
            st.image(sprava_pouzivatela["image"], use_container_width=True)
        if "file_info" in sprava_pouzivatela:
            st.caption(f"📎 Priložený súbor: **{sprava_pouzivatela['file_info']}**")
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="✨"):
        message_placeholder = st.empty()

        with st.spinner("Polaris premýšľa..."):
            generation_config = genai.types.GenerationConfig(
                temperature=0.5,
                top_p=0.8,
                top_k=20,
                max_output_tokens=1000
            )

            if st.session_state.aktivny_rezim == "Obrázky":
                obsah_spravy.append("\n[Používateľ zvolil režim vytvárania a úpravy obrázkov]")
            elif st.session_state.aktivny_rezim == "Hudba":
                obsah_spravy.append("\n[Používateľ zvolil režim vytvárania hudby a zvukov]")
            elif st.session_state.aktivny_rezim == "Canvas":
                obsah_spravy.append("\n[Používateľ zvolil režim Canvas na vývoj kódu a tvorbu snímok]")

            pouzita_historia = aktualny_chat["messages"][:-1][-4:]
            
            gemini_history = []
            for m in pouzita_historia:
                role = "user" if m["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [m["content"]]})

            dostupne_modely = ziskaj_dostupne_modely()
            
            posledna_chyba = ""
            uspesne = False
            
            for nazov_modelu in dostupne_modely:
                try:
                    model = genai.GenerativeModel(
                        model_name=nazov_modelu,
                        system_instruction=ROLY[vybrana_rola],
                        generation_config=generation_config
                    )
                    
                    chat = model.start_chat(history=gemini_history)
                    response = chat.send_message(obsah_spravy, stream=True)
                    
                    plny_text = ""
                    for chunk in response:
                        plny_text += chunk.text
                        message_placeholder.markdown(plny_text + "▌")
                    
                    message_placeholder.markdown(plny_text)
                    aktualny_chat["messages"].append({"role": "assistant", "content": plny_text})
                    uspesne = True
                    st.rerun()
                    break
                except Exception as e:
                    posledna_chyba = str(e)
                    continue

            if not uspesne:
                message_placeholder.error(f"Chyba: {posledna_chyba}")
