
import streamlit as st
import openai
import smtplib
import io
import re
import matplotlib.pyplot as plt
import numpy as np
from langdetect import detect
from email.mime.text import MIMEText
from pathlib import Path
import json
from PIL import Image, ImageChops


st.set_page_config(page_title="Speech Coach IA", page_icon="🎤")

# Logo
st.markdown(
    "<div style='text-align: center; margin-bottom: 30px;'>"
    "<img src='https://www.thejob.ch/wp-content/themes/corris2014/images/corris_logo.svg' width='200'>"
    "</div>",
    unsafe_allow_html=True
)

# 🌍 Langue
langue_choisie = st.selectbox(
    "Choisis ta langue / Wähle deine Sprache / Scegli la tua lingua",
    options=["fr", "de", "it"],
    format_func=lambda x: {"fr": "Français 🇫🇷", "de": "Deutsch 🇩🇪", "it": "Italiano 🇮🇹"}[x]
)

# 🧾 Interface textes
textes = {
    "fr": {
        "titre": "🎤 Speech Coach IA",
        "intro": "Bienvenue ! Upload ici un speech pour savoir s’il colle aux standards vus en formation.",
        "upload_label": "📁 Dépose ici ton fichier audio (MP3 ou WAV uniquement)",
        "email_label": "✉️ Adresse e-mail du·de la Dialogueur·euse (pour recevoir le feedback)",
        "info_format": "⚠️ Pour l’instant, seuls les fichiers MP3 et WAV sont pris en charge.",
        "transcription_label": "📝 Transcription générée :"
        "ong_label": "📌 Sélectionne l’ONG concernée :"
    },
    "de": {
        "titre": "🎤 Speech Coach IA",
        "intro": "Willkommen! Lade hier deine Sprachaufnahme hoch, um ein Feedback zu erhalten.",
        "upload_label": "📁 Hier deine Audiodatei hochladen (nur MP3 oder WAV)",
        "email_label": "✉️ E-Mail-Adresse des Fundraisers (für den Erhalt des Feedbacks)",
        "info_format": "⚠️ Aktuell werden nur MP3- und WAV-Dateien unterstützt.",
        "transcription_label": "📝 Transkription:"
        "ong_label": "📌 Wähle die betroffene NGO aus:"
    },
    "it": {
        "titre": "🎤 Speech Coach IA",
        "intro": "Benvenuto! Carica qui il tuo speech per ricevere un feedback.",
        "upload_label": "📁 Carica il tuo file audio (solo MP3 o WAV)",
        "email_label": "✉️ Indirizzo e-mail del dialogatore (per ricevere il feedback)",
        "info_format": "⚠️ Al momento sono supportati solo file MP3 e WAV.",
        "transcription_label": "📝 Trascrizione generata:"
        "ong_label": "📌 Seleziona l'ONG interessata:"
    }
}

barometre_legendes = {
    "fr": "- 🟢 Excellent (9–10) ...",
    "de": "- 🟢 Exzellent (9–10) ...",
    "it": "- 🟢 Eccellente (9–10) ..."
}

t = textes[langue_choisie]

# 🎛 Interface utilisateur
st.title(t["titre"])
st.write(t["intro"])
user_email = st.text_input(t["email_label"], key="email")

# Sélection ONG
ong_dir = Path("data/organisations")
ong_files = list(ong_dir.glob("*.json"))
ong_names = [f.stem.replace("_", " ").title() for f in ong_files]
ong_map = dict(zip(ong_names, ong_files))
ong_choisie = st.selectbox(t["ong_label"], ong_names)

audio_file = st.file_uploader(t["upload_label"], type=["mp3", "wav"])
audio_bytes = audio_file.read() if audio_file else None

st.markdown(t["info_format"])

openai.api_key = st.secrets["openai_key"]

# Traitement
if user_email and audio_bytes and ong_choisie:
    st.success("✅ Speech reçu et prêt à être analysé")

    with st.spinner("⏳ Transcription en cours avec Whisper..."):
        audio_io = io.BytesIO(audio_bytes)
        audio_io.name = "speech.wav"
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_io,
            response_format="text"
        )

    st.success("✅ Transcription terminée. Analyse en cours...")
    langue_detectee = detect(transcript)
    st.info(f"🗣️ Langue détectée : {langue_detectee.upper()}")

    # Prompt
    prompt_path = Path("prompts") / f"prompt_{langue_choisie}.txt"
    if not prompt_path.exists():
        st.error(f"❌ Prompt manquant pour la langue : {langue_choisie}")
        st.stop()
    with open(prompt_path, encoding="utf-8") as f:
        prompt_intro = f.read()

    # ONG
    ong_path = ong_map[ong_choisie]
    with open(ong_path, encoding="utf-8") as f:
        ong_data = json.load(f)
    ong_lang_data = ong_data.get(langue_choisie, {})
    slogan = ong_lang_data.get("slogan", "—")
    redflags = ", ".join(ong_lang_data.get("redflags", []))
    pitch_model = ong_lang_data.get("pitch_reference", "—")
    stats = ong_data.get("stats_importantes", {})

    ong_context = f"""
🔎 Infos ONG ({ong_choisie}) :

- Slogan : {slogan}
- Redflags : {redflags}
- Pitch modèle : {pitch_model}
- Statistiques : {stats}
"""

    prompt = f"""{prompt_intro}

{ong_context}

{transcript}
"""

    with st.spinner("💬 Génération du feedback pédagogique..."):
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un coach bienveillant et structuré pour des ONG."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        feedback = response.choices[0].message.content
        st.markdown(feedback)

else:
    st.info("📥 Merci de remplir tous les champs pour lancer l’analyse.")
