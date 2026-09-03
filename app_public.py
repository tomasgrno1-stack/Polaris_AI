import streamlit as st
import google.generativeai as genai
from PIL import Image
import uuid

# 1. Nastavenie stránky
st.set_page_config(
    page_title="Polaris",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. CSS pozadie a zarovnanie spodnej lišty
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

    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    [data-testid="stChatMessage"] {
        background-color: rgba(22, 27, 34, 0.75) !important;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }

    [data-testid="stChatInput"] {
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        background-color: rgba(15, 23, 42, 0.9) !important;
    }

    /* Ukotvenie spodného panela úplne dole */
    div[data-testid="stHorizontalBlock"]:has(.stPopover) {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 730px;
        z-index: 100;
        background-color: rgba(15, 23, 42, 0.95);
        padding: 8px 12px;
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        align-items: center;
    }

    /* Okrúhle tlačidlo pluska v lište */
    .stPopover>button {
        border-radius: 50% !important;
        width: 42px !important;
        height: 42px !important;
        padding: 0 !important;
        font-size: 20px !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    .stButton>button {
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        background-color: rgba(30, 41, 59, 0.7);
        color: #f8fafc;
        transition: all 0.2s ease;
    }

    /* Štýlovanie načítavacej animácie */
    div[data-baseweb="spinner"] {
        border-top-color: #a855f7 !important;
        border-left-color: #38bdf8 !important;
    }

    /* Popover menu dizajn */
    div[data-testid="stPopoverBody"] {
        background-color: #161b22 !important;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
    }

    /* Odsadenie pre správy, aby ich nezakrývala spodná lišta */
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

@st.cache_data(ttl=3600)
def ziskaj_dostupne_modely():
    try:
        modely = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modely.append(m.name)
        flash_modely = [m for m in modely if "flash" in m]
        ostatne_modely = [m for m in modely if "flash" not in m]
        return flash_modely + ostatne_modely
    except Exception:
        return ["models/gemini-1.5-flash", "models/gemini-1.5-pro"]

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
    
    if st.button("➕ Nový chat", use_container_width=True):
        vytvor_novy_chat()
        st.rerun()

    st.divider()
    st.subheader("💬 História chatov")
    
    for chat_id, chat_data in list(st.session_state.chats.items()):
        is_active = (chat_id == st.session_state.current_chat_id)
        label = f"📍 {chat_data['title']}" if is_active else chat_data['title']
        
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(label, key=f"select_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("🗑", key=f"del_{chat_id}"):
                del st.session_state.chats[chat_id]
                if st.session_state.current_chat_id == chat_id:
                    if st.session_state.chats:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                    else:
                        vytvor_novy_chat()
                st.rerun()

    st.divider()
    st.header("⚙️ Nastavenia")
    vybrana_rola = st.selectbox("Rola Polaris:", list(ROLY.keys()))

# 7. Zobrazenie správ na ploche
aktualny_chat = st.session_state.chats[st.session_state.current_chat_id]

st.title("✨ Polaris")
st.caption(f"Tvoja osobná AI asistentka | Režim: {st.session_state.aktivny_rezim}")

for msg in aktualny_chat["messages"]:
    avatar = "✨" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# 8. Spodná ukotvená lišta (Plusko + Chat input v jednej línii)
col_plus, col_input = st.columns([0.1, 0.9])

with col_plus:
    with st.popover("➕"):
        # Iba čisto ikony bez textových popiskov
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.write("📎")
        with c2:
            st.write("▲")
        with c3:
            st.write("🌸")
        with c4:
            st.write("📓")

        nahraty_subor = st.file_uploader(
            "Nahrať zo zariadenia:",
            type=["png", "jpg", "jpeg", "txt"],
            label_visibility="collapsed"
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
    prompt = st.chat_input("Ako ti môžem pomôcť?")

# 9. Spracovanie vstupu
if prompt:
    if len(aktualny_chat["messages"]) == 0:
        aktualny_chat["title"] = prompt[:18] + "..." if len(prompt) > 18 else prompt

    aktualny_chat["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
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

            obsah_spravy = [prompt]

            if st.session_state.aktivny_rezim == "Obrázky":
                obsah_spravy.append("\n[Používateľ zvolil režim vytvárania a úpravy obrázkov]")
            elif st.session_state.aktivny_rezim == "Hudba":
                obsah_spravy.append("\n[Používateľ zvolil režim vytvárania hudby a zvukov]")
            elif st.session_state.aktivny_rezim == "Canvas":
                obsah_spravy.append("\n[Používateľ zvolil režim Canvas na vývoj kódu a tvorbu snímok]")

            if 'nahraty_subor' in locals() and nahraty_subor is not None:
                if nahraty_subor.type in ["image/png", "image/jpeg", "image/jpg"]:
                    img = Image.open(nahraty_subor)
                    obsah_spravy.append(img)
                elif nahraty_subor.type == "text/plain":
                    text_suboru = nahraty_subor.read().decode("utf-8")
                    obsah_spravy.append(f"\n\nText zo súboru:\n{text_suboru}")

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
                    break
                except Exception as e:
                    posledna_chyba = str(e)
                    continue

            if not uspesne:
                message_placeholder.error(f"Chyba: {posledna_chyba}")
