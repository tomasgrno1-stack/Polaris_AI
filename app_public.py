import streamlit as st
import google.generativeai as genai

# Nastavenie stránky
st.set_page_config(page_title="Alex – AI Asistent", page_icon="✦", layout="centered")

# Nacítanie API kľúča zo Streamlit Secrets
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Chýba GOOGLE_API_KEY v nastaveniach Streamlit Cloud!")
    st.stop()

# Definícia rolí
ROLY = {
    "Osobný asistent": "Voláš sa Alex. Si môj osobný AI asistent. Vždy odpovedáš výlučne po slovensky. Si priateľský, nápomocný a vysvetľuješ veci jednoducho.",
    "Programátor": "Voláš sa Alex. Si expert na programovanie, Python, web a technológie. Odpovedáš presne, poskytuješ čistý kód s vysvetleniami po slovensky.",
    "Učiteľ angličtiny": "Voláš sa Alex. Si trpezlivý učiteľ angličtiny. Na správy odpovedáš po anglicky a pod to vždy pridáš slovenský preklad.",
    "Stručný asistent": "Voláš sa Alex. Tvoja odpoveď musí mať maximálne 2 až 3 vety. Žiadna omáčka, iba priame fakty po slovensky."
}

st.title("✦ Alex")
st.caption("Tvoj osobný AI asistent • online na webe")

# Bočný panel
with st.sidebar:
    st.header("Nastavenia")
    vybrana_rola = st.selectbox("Rola Alexa:", list(ROLY.keys()))
    if st.button("🗑 Vymazať históriu"):
        st.session_state.messages = []
        st.rerun()

# Inicializácia histórie
if "messages" not in st.session_state:
    st.session_state.messages = []

# Zobrazenie histórie
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Vstup používateľa
if prompt := st.chat_input("Napíš správu Alexovi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("*Alex premýšľa...*")

        try:
            # Inicializácia modelu Gemini
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash-latest",
                system_instruction=ROLY[vybrana_rola]
            )

            # Príprava histórie správ pre Google Gemini API
            gemini_history = []
            for m in st.session_state.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [m["content"]]})

            chat = model.start_chat(history=gemini_history)
            response = chat.send_message(prompt)
            
            odpoved = response.text
            message_placeholder.markdown(odpoved)
            st.session_state.messages.append({"role": "assistant", "content": odpoved})

        except Exception as e:
            message_placeholder.error(f"Chyba pri generovaní odpovede: {str(e)}")
