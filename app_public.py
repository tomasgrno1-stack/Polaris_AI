import streamlit as st
import google.generativeai as genai
from PIL import Image

# Nastavenie stránky
st.set_page_config(
    page_title="Alex – AI Asistent",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Načítanie API kľúča
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Chýba GOOGLE_API_KEY v Secrets!")
    st.stop()

# Definícia rolí
ROLY = {
    "Osobný asistent": "Voláš sa Alex. Si môj osobný AI asistent. Vždy odpovedáš výlučne po slovensky. Si priateľský, prirodzený a nápomocný.",
    "Programátor": "Voláš sa Alex. Si expert na programovanie, Python, web a technológie. Odpovedáš presne s prehľadným kódom a vysvetleniami po slovensky.",
    "Učiteľ angličtiny": "Voláš sa Alex. Si trpezlivý učiteľ angličtiny. Na správy odpovedáš po anglicky a pod to pridáš slovenský preklad.",
    "Stručný asistent": "Voláš sa Alex. Tvoja odpoveď musí mať maximálne 2 až 3 vety po slovensky."
}

st.title("✦ Alex")
st.caption("Tvoj osobný AI asistent • online na webe")

# Bočný panel s nastaveniami
with st.sidebar:
    st.header("⚙️ Nastavenia")
    
    vybrana_rola = st.selectbox("Rola Alexa:", list(ROLY.keys()))
    vybrany_model = st.selectbox(
        "Model AI:",
        ["gemini-2.0-flash", "gemini-1.5-pro"],
        help="2.0 Flash je rýchly, 1.5 Pro je určený na zložitejšie logické úlohy."
    )
    povolit_web = st.checkbox("🌐 Vyhľadávať na internete", value=False)
    
    st.divider()
    
    st.subheader("📎 Priložiť súbor / obrázok")
    nahraty_subor = st.file_uploader(
        "Prilož súbor pre Alexa:",
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

# Inicializácia histórie
if "messages" not in st.session_state:
    st.session_state.messages = []

# Zobrazenie histórie
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Vstup od používateľa
if prompt := st.chat_input("Napíš správu Alexovi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("*Alex premýšľa...*")

        try:
            tools = ["google_search_retrieval"] if povolit_web else None

            model = genai.GenerativeModel(
                model_name=vybrany_model,
                system_instruction=ROLY[vybrana_rola],
                tools=tools
            )

            # Príprava obsahov pre model
            obsah_spravy = [prompt]

            if nahraty_subor is not None:
                if nahraty_subor.type in ["image/png", "image/jpeg", "image/jpg"]:
                    img = Image.open(nahraty_subor)
                    obsah_spravy.append(img)
                elif nahraty_subor.type == "text/plain":
                    text_suboru = nahraty_subor.read().decode("utf-8")
                    obsah_spravy.append(f"\n\nObsah priloženého textového súboru:\n{text_suboru}")

            # Príprava histórie konverzácie
            gemini_history = []
            for m in st.session_state.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [m["content"]]})

            chat = model.start_chat(history=gemini_history)
            response = chat.send_message(obsah_spravy)
            
            odpoved = response.text
            message_placeholder.markdown(odpoved)
            st.session_state.messages.append({"role": "assistant", "content": odpoved})

        except Exception as e:
            message_placeholder.error(f"Chyba pri generovaní odpovede: {str(e)}")
