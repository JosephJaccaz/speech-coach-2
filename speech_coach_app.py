
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
        "transcription_label": "📝 Transcription générée :",
        "ong_label": "📌 Sélectionne l’ONG concernée :",
        "messages": {
            "speech_ready": "✅ Speech reçu et prêt à être analysé",
            "transcription_done": "✅ Transcription terminée. Analyse en cours...",
            "langue_detectee": "🗣️ Langue détectée :",
            "transcription_spinner": "⏳ Transcription en cours...",
            "generation_feedback": "💬 Génération du feedback pédagogique...",
            "feedback_envoye": "✅ Feedback envoyé automatiquement à"
        }
    },
    "de": {
        "titre": "🎤 Speech Coach IA",
        "intro": "Willkommen! Lade hier deine Sprachaufnahme hoch, um ein Feedback zu erhalten.",
        "upload_label": "📁 Hier deine Audiodatei hochladen (nur MP3 oder WAV)",
        "email_label": "✉️ E-Mail-Adresse des Fundraisers (für den Erhalt des Feedbacks)",
        "info_format": "⚠️ Aktuell werden nur MP3- und WAV-Dateien unterstützt.",
        "transcription_label": "📝 Transkription:",
        "ong_label": "📌 Wähle die betroffene NGO aus:",
        "messages": {
            "speech_ready": "✅ Speech empfangen und bereit zur Analyse",
            "transcription_done": "✅ Transkription abgeschlossen. Analyse läuft...",
            "langue_detectee": "🗣️ Erkannte Sprache:",
            "transcription_spinner": "⏳ Transkription läuft...",
            "generation_feedback": "💬 Generierung des pädagogischen Feedbacks...",
            "feedback_envoye": "✅ Feedback wurde automatisch gesendet an"
        }
    },
    "it": {
        "titre": "🎤 Speech Coach IA",
        "intro": "Benvenuto! Carica qui il tuo speech per ricevere un feedback.",
        "upload_label": "📁 Carica il tuo file audio (solo MP3 o WAV)",
        "email_label": "✉️ Indirizzo e-mail del dialogatore (per ricevere il feedback)",
        "info_format": "⚠️ Al momento sono supportati solo file MP3 e WAV.",
        "transcription_label": "📝 Trascrizione generata:",
        "ong_label": "📌 Seleziona l'ONG interessata:",
        "messages": {
            "speech_ready": "✅ Speech ricevuto e pronto per l'analisi",
            "transcription_done": "✅ Trascrizione completata. Analisi in corso...",
            "langue_detectee": "🗣️ Lingua rilevata:",
            "transcription_spinner": "⏳ Trascrizione in corso...",
            "generation_feedback": "💬 Generazione del feedback pedagogico...",
            "feedback_envoye": "✅ Feedback inviato automaticamente a"
        }
    }
}


barometre_legendes = {
    "fr": """
- 🟢 **Excellent (9–10)** : Alignement parfait avec la méthode d’adhésion – discours inspirant, clair et éthique.
- 🟢 **Bon (7–8)** : Tu es sur la bonne voie – encore perfectible sur quelques points.
- 🟠 **Moyen (5–6)** : Équilibre émotionnel fragile – attention à certaines maladresses.
- 🔴 **Faible (3–4)** : Ton discours perd en impact – problème de ton ou de structure.
- ⛔ **Problématique (1–2)** : Le discours doit être entièrement revu – manque d’adhésion sincère.
    """,
    "de": """
- 🟢 **Exzellent (9–10)** : Perfekte Übereinstimmung mit dem Dialogkonzept – inspirierend, klar und ethisch.
- 🟢 **Gut (7–8)** : Du bist auf dem richtigen Weg – kleine Verbesserungen sind noch möglich.
- 🟠 **Mittel (5–6)** : Emotionale Balance instabil – einzelne Schwächen im Aufbau oder Ton.
- 🔴 **Schwach (3–4)** : Der Pitch verliert an Wirkung – problematische Tonalität oder Struktur.
- ⛔ **Problematisch (1–2)** : Muss vollständig überarbeitet werden – fehlende ehrliche Zustimmung.
    """,
    "it": """
- 🟢 **Eccellente (9–10)** : Allineamento perfetto con il metodo di adesione – discorso chiaro, etico e coinvolgente.
- 🟢 **Buono (7–8)** : Sei sulla buona strada – margine di miglioramento su alcuni punti.
- 🟠 **Medio (5–6)** : Equilibrio emotivo fragile – attenzione a tono e costruzione.
- 🔴 **Debole (3–4)** : Il discorso perde impatto – problemi di tono o struttura.
- ⛔ **Problema (1–2)** : Va completamente rivisto – manca l’adesione sincera.
    """
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

def format_feedback_as_html(feedback_text, langue):
    html = feedback_text
    html = html.replace("✓", "<span style='color:green; font-weight:bold;'>✓</span>")
    html = html.replace("⚠️", "<span style='color:red; font-weight:bold;'>⚠️</span>")
    html = html.replace("Suggestion d'amélioration", "<span style='color:#007BFF; font-weight:bold;'>Suggestion d'amélioration</span>")
    html = html.replace("Verbesserungsvorschlag", "<span style='color:#007BFF; font-weight:bold;'>Verbesserungsvorschlag</span>")
    html = html.replace("Suggerimento di miglioramento", "<span style='color:#007BFF; font-weight:bold;'>Suggerimento di miglioramento</span>")
    html = html.replace("**", "")
    paragraphs = html.split("\n")
    html_body = ""
    for line in paragraphs:
        line = line.strip()
        if not line:
            continue
        if line.startswith(("🟢", "📊", "🔍", "🎯", "🤝", "💢", "🌱", "🚀", "➡️", "📝")):
            html_body += f"<p style='margin:20px 0 6px 0; font-weight:bold;'>{line}</p>"
        elif line.startswith("🎯 **Conclusions et perspectives**"):
            html_body += "<hr style='margin:24px 0; border:none; border-top:2px solid #eee;'>"
            html_body += f"<p style='margin:20px 0 6px 0; font-weight:bold;'>{line}</p>"
        else:
            html_body += f"<p style='margin:4px 0;'>{line}</p>"

    if langue == "de":
        intro = "<p>Hallo 👋<br>Hier ist dein persönliches Feedback zur Analyse deines Sprach-Pitchs :</p><br>"
        signature = "<p style='color:gray;'>--<br>Speech Coach IA 🧠<br>Ein Werkzeug mit Herz – für Fundraiser und Trainer:innen.</p>"
    elif langue == "it":
        intro = "<p>Ciao 👋<br>Ecco il tuo feedback personalizzato sull’analisi del tuo pitch vocale :</p><br>"
        signature = "<p style='color:gray;'>--<br>Speech Coach IA 🧠<br>Uno strumento creato con cura per dialogatori e formatori.</p>"
    else:
        intro = "<p>Bonjour 👋<br>Voici ton feedback personnalisé suite à l’analyse de ton pitch vocal :</p><br>"
        signature = "<p style='color:gray;'>--<br>Speech Coach IA 🧠<br>Un outil conçu avec soin pour les dialogueurs et leurs formateurs.</p>"

    if langue == "fr":
        signature += "<p style='font-size:12px; color:#aaa;'>PS : Ce feedback a été généré avec amour, café ☕ et un soupçon de GPT par Joseph 💻</p>"

    return f"""
    <div style='font-family: Verdana, sans-serif; font-size: 15px; color:#000;'>
        {intro}
        {html_body}
        {signature}
    </div>
    """

# Fonctions utilitaires 

def draw_gauge(score):
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(5, 1.8), dpi=160, subplot_kw={'projection': 'polar'})

    # Mettre 0 à gauche (horizontal) et rotation antihoraire
    ax.set_theta_zero_location('W')  # 0° : Bas
    ax.set_theta_direction(-1)

    # Définition des zones
    zones = [
        (0, 2, '#8B0000'),     # Rouge foncé
        (2, 4, '#FF4500'),     # Orange vif
        (4, 6, '#FFA500'),     # Orange clair
        (6, 8, '#ADFF2F'),     # Vert clair
        (8, 10, '#228B22')     # Vert foncé
    ]

    for start, end, color in zones:
        theta1 = np.interp(start, [0, 10], [0, np.pi])
        theta2 = np.interp(end, [0, 10], [0, np.pi])
        ax.barh(
            y=1,
            width=theta2 - theta1,
            left=theta1,
            height=0.35,
            color=color,
            edgecolor='white',
            linewidth=1.5
        )

    # Aiguille
    angle = np.interp(score, [0, 10], [0, np.pi])
    ax.plot([angle, angle], [0, 1], color='black', lw=3)
    ax.plot(angle, 1, 'o', color='black', markersize=6)

    # Nettoyage du style
    ax.set_ylim(0, 1.1)
    ax.axis('off')
    plt.subplots_adjust(left=0.05, right=0.95, top=1.05, bottom=-10)
    fig.patch.set_alpha(0)  # Fond transparent (utile si tu veux l'intégrer avec d'autres éléments visuels)


    from PIL import Image, ImageChops

    # 1. Sauvegarde le graphique dans un buffer mémoire
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0, transparent=True)
    plt.close(fig)  # nettoyage mémoire
    buf.seek(0)
    img = Image.open(buf)

    # 2. Crop automatique du fond blanc transparent
    bg = Image.new(img.mode, img.size, (255, 255, 255, 0))  # fond transparent
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()

    if bbox:
        img_cropped = img.crop(bbox)
    else:
        img_cropped = img  # fallback : pas de différence détectée

    # 3. Affichage sans le moindre bord inutile
    st.image(img_cropped)



def interpret_note(score, langue):
    if langue == "de":
        # traductions en allemand ici
        if score >= 9:
            return "🟢 Exzellent – vollständig im Einklang mit dem Dialogkonzept"
        elif score >= 7:
            return "🟢 Gut – kleinere Verbesserungen möglich"
        elif score >= 5:
            return "🟠 Mittel – emotionale Balance fragil"
        elif score >= 3:
            return "🔴 Schwach – auf Ton und Inhalt achten"
        else:
            return "⛔ Problematisch – muss grundlegend überarbeitet werden"
    elif langue == "it":
        # traductions en italien ici
        if score >= 9:
            return "🟢 Eccellente – perfettamente in linea con il metodo di adesione"
        elif score >= 7:
            return "🟢 Buono – migliorabile in alcuni punti"
        elif score >= 5:
            return "🟠 Medio – equilibrio emotivo fragile"
        elif score >= 3:
            return "🔴 Debole – attenzione al tono e al messaggio"
        else:
            return "⛔ Problema – discorso da rivedere profondamente"
    else:
        # français par défaut
        if score >= 9:
            return "🟢 Excellent – alignement parfait avec la méthode d’adhésion"
        elif score >= 7:
            return "🟢 Bon – encore perfectible sur quelques points"
        elif score >= 5:
            return "🟠 Moyen – équilibre émotionnel fragile"
        elif score >= 3:
            return "🔴 Faible – attention à la tonalité et au discours"
        else:
            return "⛔ Problématique – discours à retravailler profondément"

note = None  # 

# Traitement
if user_email and audio_bytes and ong_choisie:
    st.success(t["messages"]["speech_ready"])

    with st.spinner(t["messages"]["transcription_spinner"]):
        audio_io = io.BytesIO(audio_bytes)
        audio_io.name = "speech.wav"
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_io,
            response_format="text"
        )

    st.success(t["messages"]["transcription_done"])
    langue_detectee = detect(transcript)
    st.info(f"{t['messages']['langue_detectee']} {langue_detectee.upper()}")


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

    with st.spinner(t["messages"]["generation_feedback"]):

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

        # Extraire la note
        match = re.search(r"(\d(?:\.\d)?)/10", feedback)
        note = float(match.group(1)) if match else None

    if note:
        st.markdown({
            "fr": "### 🎯 Baromètre de performance",
            "de": "### 🎯 Leistungsbarometer",
            "it": "### 🎯 Barometro di performance"
        }[langue_choisie])

        draw_gauge(note)
        st.markdown(f"**{interpret_note(note, langue_choisie)}**")

        with st.expander({
            "fr": "ℹ️ Que signifie le baromètre ?",
            "de": "ℹ️ Was bedeutet das Barometer?",
            "it": "ℹ️ Cosa indica il barometro?"
        }[langue_choisie]):
            st.markdown(barometre_legendes[langue_choisie])

        st.markdown(feedback, unsafe_allow_html=True)

        # Envoi par email
        try:
            html_feedback = format_feedback_as_html(feedback, langue_detectee)
            msg = MIMEText(html_feedback, "html", "utf-8")
            msg["Subject"] = "💬 Speech Coach IA : Feedback de ton speech"
            msg["From"] = st.secrets["email_user"]
            msg["To"] = user_email

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(st.secrets["email_user"], st.secrets["email_password"])
                server.send_message(msg)

            st.success(f"{t['messages']['feedback_envoye']} {user_email} !")
        except Exception as e:
            st.error(f"❌ Erreur lors de l'envoi : {e}")
