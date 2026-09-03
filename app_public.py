import streamlit as st
import google.generativeai as genai
from PIL import Image

# Nastavenie stránky
st.set_page_config(
    page_title="Polaris – AI Asistentka",
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

# Definícia rolí v ženskom rode
ROLY = {
    "Osobná asistentka": "Voláš sa Polaris. Si moja osobná AI asistentka. Hovoríš výlučne po slovensky a vyjadruješ sa striktne v ženskom rode (napr. 'som pripravená', 'myslela som', 'skontrolovala som'). Si priateľská, inteligentná a nápomocná.",
    "Programátorka": "Voláš sa Polaris. Si expertka na programovanie, Python, web a technológie. Vyjadruješ sa v ženskom rode a odpovedáš presne s prehľadným kódom a vysvetleniami po slovensky.",
    "Učiteľka angličtiny": "Voláš sa Polaris. Si trpezlivá učiteľka angličtiny. Vyjadruješ sa v ženskom rode. Na správy odpovedáš po anglicky a pod to pridáš slovenský preklad.",
    "Stručná asistentka": "Voláš sa Polaris. Vyjadruješ sa v ženskom rode. Tvoja odpoveď musí mať maximálne 2 až 3 vety po slovensky."
}

st.title("✦ Polaris")
st.caption("Tvoja osobná AI asistentka • online na webe")

# Bočný panel s nastaveniami
with st.sidebar:
    st.header("⚙️ Nastavenia")
    
    vybrana_rola = st.selectbox("Rola Polaris:", list(ROLY.keys()))
    vybrany_model = st.selectbox(
        "Model AI:",
        ["gemini-3.6-flash", "gemini-1.5-pro"],
        help="gemini-3.6-flash je najrýchlejší dostupný model."
    )
    povolit_web = st.checkbox("🌐 Vyhľadávať na internete", value=False)
    
    st.divider()
    
    st.subheader("📎 Priložiť súbor / obrázok")
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

# Inicializácia histórie
if "messages" not in st.session_state:
    st.session_state.messages = []

# Zobrazenie histórie
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Vstup od používateľa
if prompt := st.chat_input("Napíš správu Polaris..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

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
            
            # Zapnutie streamovania (stream=True)
            response = chat.send_message(obsah_spravy, stream=True)
            
            plny_text = ""
            for chunk in response:
                plny_text += chunk.text
                message_placeholder.markdown(plny_text + "▌")
            
            message_placeholder.markdown(plny_text)
            st.session_state.messages.append({"role": "assistant", "content": plny_text})

        except Exception as e:
            message_placeholder.error(f"Chyba pri generovaní odpovede: {str(e)}")
