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

# 2. Tmavé CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    [data-testid="stChatMessage"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    [data-testid="stChatInput"] {
        border-radius: 20px;
        border: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Načítanie API kľúča
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Chýba GOOGLE_API_KEY v Secrets!")
    st.stop()

# 4. Štrutkúra pre ukladanie viacerých chatov
if "chats" not in st.session_state:
    st.session_state.chats = {} # Ukladá konverzácie {chat_id: {"title": str, "messages": list}}

if "current_chat_id" not in st.session_state:
    # Vytvorenie prvého chatu
    prve_id = str(uuid.uuid4())
    st.session_state.chats[prve_id] = {"title": "Nový chat", "messages": []}
    st.session_state.current_chat_id = prve_id

# Helper funkcia pre vytvorenie nového chatu
def vytvor_novy_chat():
    nove_id = str(uuid.uuid4())
    st.session_state.chats[nove_id] = {"title": "Nový chat", "messages": []}
    st.session_state.current_chat_id = nove_id

# 5. Definícia rolí
ROLY = {
    "Osobná asistentka": "Voláš sa Polaris. Si moja osobná AI asistentka. Hovoríš výlučne po slovensky v ženskom rode. Odpovedaj stručne a k veci.",
    "Programátorka": "Voláš sa Polaris. Si expertka na Python a web. Odpovedaj stručne s prehľadným kódom po slovensky.",
    "Učiteľka angličtiny": "Voláš sa Polaris. Odpovedaj po anglicky a pod to pridaj stručný slovenský preklad.",
    "Stručná asistentka": "Voláš sa Polaris. Odpovedaj maximálne v 2-3 krátkych vetách po slovensky."
}

# 6. Bočný panel v štýle ChatGPT
with st.sidebar:
    st.title("✨ Polaris")
    
    # Tlačidlo pre nový chat
    if st.button("➕ Nový chat", use_container_width=True):
        vytvor_novy_chat()
        st.rerun()

    st.divider()
    st.subheader("💬 História chatov")
    
    # Zoznam uložených chatov
    for chat_id, chat_data in list(st.session_state.chats.items()):
        # Označenie aktívneho chatu
        is_active = (chat_id == st.session_state.current_chat_id)
        label = f"📍 {chat_data['title']}" if is_active else chat_data['title']
        
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(label, key=f"select_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            # Tlačidlo na zmazanie konkrétneho chatu
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
    
    nahraty_subor = st.file_uploader(
        "Prilož súbor:",
        type=["png", "jpg", "jpeg", "txt"],
        help="Nahraj obrázok alebo textový súbor."
    )

# 7. Zobrazenie správ aktuálne zvoleného chatu
aktualny_chat = st.session_state.chats[st.session_state.current_chat_id]

st.title(aktualny_chat["title"])

for msg in aktualny_chat["messages"]:
    avatar = "✨" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# 8. Odeslanie správy
if prompt := st.chat_input("Ako ti môžem pomôcť?"):
    # Ak je to prvá správa v chate, premenuj názov chatu podľa textu
    if len(aktualny_chat["messages"]) == 0:
        aktualny_chat["title"] = prompt[:20] + "..." if len(prompt) > 20 else prompt

    aktualny_chat["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="✨"):
        message_placeholder = st.empty()

        generation_config = genai.types.GenerationConfig(
            temperature=0.5,
            top_p=0.8,
            top_k=20,
            max_output_tokens=1000
        )

        obsah_spravy = [prompt]

        if nahraty_subor is not None:
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

        dostupne_modely = ["gemini-2.0-flash", "gemini-pro"]
        
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
