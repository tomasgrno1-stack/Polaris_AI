import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Nastavenie stránky
st.set_page_config(
    page_title="Polaris",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. Vlastné CSS pre galaktický motív
st.markdown("""
    <style>
    /* Hlavné pozadie s tématikou galaxie */
    .stApp {
        background: radial-gradient(circle at 50% 20%, #1e1b4b 0%, #0f172a 50%, #020617 100%) !important;
        background-attachment: fixed !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Úprava bočného panela */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Úprava správ chatu (Glassmorphism) */
    [data-testid="stChatMessage"] {
        background-color: rgba(30, 27, 75, 0.4) !important;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    /* Vstupné pole (Chat Input) */
    [data-testid="stChatInput"] {
        border-radius: 24px;
        border: 1px solid rgba(139, 92, 246, 0.3);
        background-color: rgba(15, 23, 42, 0.8) !important;
    }
    
    /* Nadpis a texty */
    h1 {
        font-weight: 600;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #a78bfa 0%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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
    "Osobná asistentka": "Voláš sa Polaris. Si moja osobná AI asistentka. Hovoríš výlučne po slovensky a vyjadruješ sa striktne v ženskom rode (napr. 'som pripravená', 'myslela som', 'skontrolovala som'). Si priateľská, inteligentná a nápomocná.",
    "Programátorka": "Voláš sa Polaris. Si expertka na programovanie, Python, web a technológie. Vyjadruješ sa v ženskom rode a odpovedáš presne s prehľadným kódom a vysvetleniami po slovensky.",
    "Učiteľka angličtiny": "Voláš sa Polaris. Si trpezlivá učiteľka angličtiny. Vyjadruješ sa v ženskom rode. Na správy odpovedáš po anglicky a pod to pridáš slovenský preklad.",
    "Stručná asistentka": "Voláš sa Polaris. Vyjadruješ sa v ženskom rode. Tvoja odpoveď musí mať maximálne 2 až 3 vety po slovensky."
}

st.title("✨ Polaris")
st.caption("Tvoja osobná AI asistentka")

# 5. Bočný panel
with st.sidebar:
    st.header("⚙️ Nastavenia")
    
    vybrana_rola = st.selectbox("Rola Polaris:", list(ROLY.keys()))
    vybrany_model = st.selectbox(
        "Model AI:",
        ["gemini-3.6-flash", "gemini-1.5-pro"],
        help="gemini-3.6-flash je rýchly a najnovší model."
    )
    povolit_web = st.checkbox("🌐 Vyhľadávať na internete", value=False)
    
    st.divider()
    
    st.subheader("📎 Súbor / Obrázok")
    nahraty_subor = st.file_uploader(
        "Prilož súbor pre Polaris:",
        type=["png", "jpg", "jpeg", "pdf", "txt"],
        help="Nahraj obrázok na analýzu alebo textový súbor/PDF na zhrnutie."
    )
    
    if nahraty_subor:
        if nahraty_subor.type in ["image/png", "image/jpeg", "image/jpg"]:
            st.image(nahraty_subor, caption="Náhľad obrázka", use_container_width=True)
        else:
            st.success(f"Priložený súbor: {nahraty_subor.name}")

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

# 8. Spracovanie vstupu od používateľa
if prompt := st.chat_input("Ako ti môžem dnes pomôcť?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="✨"):
        message_placeholder = st.empty()

        try:
            tools = ["google_search_retrieval"] if povolit_web else None

            # Optimalizácia konfigurácie pre maximálnu rýchlosť
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40
            )

            model = genai.GenerativeModel(
                model_name=vybrany_model,
                system_instruction=ROLY[vybrana_rola],
                tools=tools,
                generation_config=generation_config
            )

            obsah_spravy = [prompt]

            if nahraty_subor is not None:
                if nahraty_subor.type in ["image/png", "image/jpeg", "image/jpg"]:
                    img = Image.open(nahraty_subor)
                    obsah_spravy.append(img)
                elif nahraty_subor.type == "text/plain":
                    text_suboru = nahraty_subor.read().decode("utf-8")
                    obsah_spravy.append(f"\n\nObsah priloženého textového súboru:\n{text_suboru}")

            gemini_history = []
            for m in st.session_state.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [m["content"]]})

            chat = model.start_chat(history=gemini_history)
            
            # Priame streamovanie s okamžitým renderingom
            response = chat.send_message(obsah_spravy, stream=True)
            
            plny_text = ""
            for chunk in response:
                plny_text += chunk.text
                message_placeholder.markdown(plny_text + "▌")
            
            message_placeholder.markdown(plny_text)
            st.session_state.messages.append({"role": "assistant", "content": plny_text})

        except Exception as e:
            message_placeholder.error(f"Chyba pri generovaní odpovede: {str(e)}")
