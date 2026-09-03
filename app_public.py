import streamlit as st
import google.generativeai as genai
from PIL import Image
import time

# 1. Nastavenie stránky
st.set_page_config(
    page_title="Polaris",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. Vlastné CSS pre čistý tmavý vzhľad
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
    h1 {
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Načítanie API kľúča
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Chýba GOOGLE_API_KEY v Secrets!")
    st.stop()

# 4. Definícia rolí v ženskom rode
ROLY = {
    "Osobná asistentka": "Voláš sa Polaris. Si moja osobná AI asistentka. Hovoríš výlučne po slovensky v ženskom rode. Odpovedaj stručne a k veci.",
    "Programátorka": "Voláš sa Polaris. Si expertka na Python a web. Odpovedaj stručne s prehľadným kódom po slovensky.",
    "Učiteľka angličtiny": "Voláš sa Polaris. Odpovedaj po anglicky a pod to pridaj stručný slovenský preklad.",
    "Stručná asistentka": "Voláš sa Polaris. Odpovedaj maximálne v 2-3 krátkych vetách po slovensky."
}

st.title("✨ Polaris")
st.caption("Tvoja osobná AI asistentka")

# 5. Bočný panel
with st.sidebar:
    st.header("⚙️ Nastavenia")
    vybrana_rola = st.selectbox("Rola Polaris:", list(ROLY.keys()))
    
    st.divider()
    
    st.subheader("📎 Súbor / Obrázok")
    nahraty_subor = st.file_uploader(
        "Prilož súbor:",
        type=["png", "jpg", "jpeg", "txt"],
        help="Nahraj obrázok alebo textový súbor."
    )

    st.divider()
    if st.button("🗑 Vymazať históriu", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 6. Inicializácia histórie
if "messages" not in st.session_state:
    st.session_state.messages = []

# 7. Zobrazenie histórie konverzácie
for msg in st.session_state.messages:
    avatar = "✨" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# 8. Spracovanie vstupu
if prompt := st.chat_input("Ako ti môžem pomôcť?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
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

        # Použitie oficiálne podporovaného rýchleho modelu bez 404 chyby
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-002",
            system_instruction=ROLY[vybrana_rola],
            generation_config=generation_config
        )

        obsah_spravy = [prompt]

        if nahraty_subor is not None:
            if nahraty_subor.type in ["image/png", "image/jpeg", "image/jpg"]:
                img = Image.open(nahraty_subor)
                obsah_spravy.append(img)
            elif nahraty_subor.type == "text/plain":
                text_suboru = nahraty_subor.read().decode("utf-8")
                obsah_spravy.append(f"\n\nText zo súboru:\n{text_suboru}")

        pouzita_historia = st.session_state.messages[:-1][-4:]
        
        gemini_history = []
        for m in pouzita_historia:
            role = "user" if m["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [m["content"]]})

        chat = model.start_chat(history=gemini_history)
        
        pauzy = [3, 8]
        for pokus, cakanie in enumerate(pauzy):
            try:
                response = chat.send_message(obsah_spravy, stream=True)
                
                plny_text = ""
                for chunk in response:
                    plny_text += chunk.text
                    message_placeholder.markdown(plny_text + "▌")
                
                message_placeholder.markdown(plny_text)
                st.session_state.messages.append({"role": "assistant", "content": plny_text})
                break
            except Exception as e:
                if "429" in str(e) and pokus < len(pauzy) - 1:
                    message_placeholder.warning(f"Siete sú vyťažené, čakám {cakanie} sekúnd...")
                    time.sleep(cakanie)
                else:
                    message_placeholder.error(f"Chyba: {str(e)}")
                    break
