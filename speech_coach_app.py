import streamlit as st
import openai
import smtplib
import io
import re
import matplotlib.pyplot as plt
import numpy as np
from langdetect import detect
from email.mime.text import MIMEText



st.experimental_audio_recorder = getattr(st, "audio_recorder", None)


st.set_page_config(page_title="Speech Coach IA", page_icon="🎤")

# Logo
st.markdown(
    '''
    <div style='text-align: center; margin-bottom: 30px;'>
        <img src='https://www.thejob.ch/wp-content/themes/corris2014/images/corris_logo.svg' width='200'>
    </div>
    ''',
    unsafe_allow_html=True
)

# 🌍 Sélecteur de langue
langue_choisie = st.selectbox(
    "Choisis ta langue / Wähle deine Sprache / Scegli la tua lingua",
    options=["fr", "de", "it"],
    format_func=lambda x: {"fr": "Français 🇫🇷", "de": "Deutsch 🇩🇪", "it": "Italiano 🇮🇹"}[x]
)

# Textes localisés
textes = {
    "fr": {
        "titre": "🎤 Speech Coach IA",
        "intro": "Bienvenue ! Upload ici un speech pour savoir s’il colle aux standards vus en formation.",
        "upload_label": "📁 Dépose ici ton fichier audio (MP3 ou WAV uniquement)",
        "email_label": "✉️ Adresse e-mail du·de la Dialogueur·euse (pour recevoir le feedback)",
        "info_format": "⚠️ Pour l’instant, seuls les fichiers MP3 et WAV sont pris en charge.",
        "transcription_label": "📝 Transcription générée :"
    },
    "de": {
        "titre": "🎤 Speech Coach IA",
        "intro": "Willkommen! Lade hier deine Sprachaufnahme hoch, um ein Feedback zu erhalten.",
        "upload_label": "📁 Hier deine Audiodatei hochladen (nur MP3 oder WAV)",
        "email_label": "✉️ E-Mail-Adresse des Fundraisers (für den Erhalt des Feedbacks)",
        "info_format": "⚠️ Aktuell werden nur MP3- und WAV-Dateien unterstützt.",
        "transcription_label": "📝 Transkription:"
    },
    "it": {
        "titre": "🎤 Speech Coach IA",
        "intro": "Benvenuto! Carica qui il tuo speech per ricevere un feedback.",
        "upload_label": "📁 Carica il tuo file audio (solo MP3 o WAV)",
        "email_label": "✉️ Indirizzo e-mail del dialogatore (per ricevere il feedback)",
        "info_format": "⚠️ Al momento sono supportati solo file MP3 e WAV.",
        "transcription_label": "📝 Trascrizione generata:"
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

# Interface
st.title(t["titre"])
st.write(t["intro"])
user_email = st.text_input(t["email_label"], key="email")

audio_file = st.file_uploader(t["upload_label"], type=["mp3", "wav"], key="audio")
audio_bytes = None
if audio_file:
    audio_bytes = audio_file.read()



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


note = None


if user_email and audio_bytes is not None:
    st.success("✅ Speech reçu et prêt à être analysé")

    with st.spinner("⏳ Transcription en cours avec Whisper..."):
        
        audio_io = io.BytesIO(audio_bytes)
        audio_io.name = "speech.wav"  # nom générique, utile pour Whisper
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_io,
            response_format="text"
        )

    st.success("✅ Transcription terminée. Analyse en cours...")

    langue_detectee = detect(transcript)
    st.info(f"🗣️ Langue détectée : {langue_detectee.upper()}")

    # Définir le prompt selon la langue choisie
    if langue_choisie == "fr":
        prompt_intro = """Tu es un coach expert en rhétorique, spécialisé dans la formation de dialogueurs pour des ONG.

Tu t'adresses ici directement à un·e dialogueur·euse qui vient d'enregistrer un **speech** d'entraînement. Ton rôle est de lui faire un retour complet, clair et motivant.
Tu dois évaluer à la fois la qualité du contenu, la structure du discours et l’émotion transmise dans la voix.

Avant de conclure ton retour, veille à ce que l’analyse respecte ces points :

- Si le pitch contient des **chiffres, données chiffrées ou résultats quantitatifs**, vérifie qu’ils sont **présentés de manière crédible et précise**.
- Si un chiffre semble **exagéré, invérifiable ou manipulatoire**, signale-le comme étant à **risque de “bullshit”**.
- Tu ne dois **jamais inventer de chiffres ou d'exemples chiffrés** dans ton propre feedback.
- Encourage à utiliser une **formulation plus qualitative ou nuancée** à la place de tout chiffre douteux.

Sois rigoureux dans ce point. Le but est d’éviter tout usage maladroit ou imprécis de données dans un discours d’adhésion.

Tu dois être exigeant, pour que la personne qui t'envoie un speech ait un jugement honnête. Si c'est pourri ou qu'une partie du speech est absente, tu dois le dire et ce n'est pas okay
Ta réponse doit être structurée **exactement** selon ce plan :

---

🟢 **Résumé global**

Commence par un petit résumé général de ton speech (2 à 3 phrases maximum). L’idée est de donner une première impression générale sur le speech.

---

📊 **Note sur 10**

Donne une note sur 10 pour ta performance globale (clarté, structure, émotion, impact). Soit exigeant.
Ex : “7/10 – Tu poses une intention très claire dès le départ, mais la partie ‘problème’ est un peu rapide.”

---

🔍 **Analyse détaillée (par étapes)**

Dans cette partie, analyse objectivement le speech selon les 7 étapes du discours classique d’un·e dialogueur·euse. Tu peux ici revenir à un ton plus neutre (sans tutoiement).

🎯 1. Accroche (qui doit transmettre de la curiosité et ou de la sympathie, il faut éviter les questions fermées avec une durée de temps comme "salut, tu as deux minutes" ou "je m'excuse de te déranger") 
🤝 2. Introduction  (qui doit inspirer de la confiance, il faut qu'on ait l'impression d'un dialogue, avec des questions pour savoir que fait la personne (fictive) dans la vie)
💢 3. Problème  (qui doit transmettre de l'empathie et de l'indignation, il faut expliquer le problème, et que cela n'est pas normal qu'il existe)
🌱 4. Solution  (qui doit transmettre de l'espoir, montrer que ce problème n'est pas insoluble, il faut se remettre à sourire et avoir un ton enjoué)
🚀 5. Succès  (qui doit transmettre de l'envie : montrer que cela est concret et que dans le passé, l'association a eu des succès)
➡️ 6. Transition  (qui doit être une phrase affirmative très simple, qui guide la personne et fait le lien entre le speech rempli d'émotions et le formulaire)
📝 7. Explication du formulaire (simple, structurée et claire, la terminologie doit être centrée sur un formulaire en deux parties : une partie identité, une partie générosité, que le tout semble simple)

Voici la structure à suivre pour chaque étape :

🎯 **[Nom de la partie]**
- **Présence** : ✓ ou ⚠️
- **Émotion perçue**
- **Résumé**
- **Suggestion d'amélioration**

---

🎯 **Conclusions et perspectives**

Reprends ici le tutoiement.

Ton objectif est d’évaluer si le discours repose sur une méthode d’adhésion sincère ou s’il dévie vers des techniques de manipulation émotionnelle, culpabilisation ou pression implicite.
Identifie et signale précisément les éléments suivants :
Tonalité manipulatrice : emploi excessif de peur, de chantage émotionnel, d’exagérations ou de termes anxiogènes.
Culpabilisation du passant : tournures de phrases qui font sentir au passant qu’il serait "mauvais", "indifférent", ou "complice" s’il ne donne pas.
Langage trop insistant ou directif : absence d’espace pour le choix du passant, formules qui imposent plutôt qu’elles n’invitent.
Respect du libre arbitre : absence de validation du droit du passant à dire non.
Équilibre émotionnel : discours basé sur une énergie positive, sincère et informative, sans mise en scène excessive ni pathos appuyé.
Pour chaque élément problématique, cite le passage exact, explique pourquoi c’est problématique et propose une alternative formulée de manière plus éthique.
Termine par un message chaleureux, encourageant mais motivant et honnête. Félicite l’effort fourni, encourage à continuer, et donne quelques conseils utiles pour améliorer tes prochains speechs.
Tu peux conclure de manière simple, pro et humaine.
"""
    elif langue_choisie == "de":
        prompt_intro = """Du bist ein Coach mit rhetorischer Expertise, spezialisiert auf die Schulung von Fundraiser:innen für NGOs im Direktkontakt.

Du sprichst hier direkt mit einem:einer Dialoger:in, der:die gerade ein **Trainings-Speech** aufgenommen hat. Deine Aufgabe ist es, ein vollständiges, klares und motivierendes Feedback zu geben.
Du sollst sowohl die Qualität des Inhalts, den Aufbau des Gesprächs als auch die emotionale Wirkung der Stimme beurteilen.

Bevor du dein Feedback abschließt, achte auf Folgendes:

- Wenn der Speech **Zahlen, Statistiken oder Ergebnisse** enthält, überprüfe, ob sie **glaubwürdig und nachvollziehbar** präsentiert sind.
- Wenn eine Zahl **übertrieben, spekulativ oder manipulativ** wirkt, markiere sie als **potenziell problematisch ("Bullshit"-Risiko)**.
- Gib **niemals selbst erfundene Zahlen** im Feedback an.
- Ermutige dazu, **qualitative oder vorsichtigere Formulierungen** zu verwenden, wenn Daten unsicher oder übertrieben erscheinen.

Sei in diesem Punkt besonders aufmerksam. Ziel ist es, jede ungenaue oder irreführende Datennutzung im Adhäsionsgespräch zu vermeiden.

Sei dabei anspruchsvoll – die Person, die dir den Speech schickt, hat ein ehrliches Urteil verdient. Wenn der Speech schwach ist oder einzelne Teile fehlen, musst du es auch so benennen – das ist nicht in Ordnung.
Deine Antwort muss **genau** nach folgendem Schema aufgebaut sein:

---

🟢 **Gesamteindruck**

Beginne mit einem kurzen allgemeinen Eindruck von deinem Speech (max. 2–3 Sätze). Ziel ist es, einen ersten Gesamteindruck zu vermitteln.

---

📊 **Note von 1 bis 10**

Gib eine Bewertung auf einer Skala von 1 bis 10 (Klarheit, Struktur, Emotion, Wirkung). Sei dabei ehrlich und fordernd.
Beispiel: „7/10 – Du zeigst von Anfang an eine klare Absicht, aber die Problemphase wirkt zu kurz.“

---

🔍 **Detaillierte Analyse (in Schritten)**

In diesem Abschnitt analysierst du den Speech objektiv anhand der 7 klassischen Etappen eines Fundraising-Gesprächs. Du kannst hier zu einem neutraleren Ton übergehen (kein „Du“).

🎯 1. Einstieg (soll Neugier und Sympathie wecken – vermeide geschlossene Zeitfragen wie „Hast du zwei Minuten?“ oder „Entschuldige die Störung.“)
🤝 2. Vorstellung (soll Vertrauen aufbauen – es soll wie ein echter Dialog wirken, z. B. mit Fragen zum (fiktiven) Alltag des Gegenübers)
💢 3. Problem (soll Empathie und Empörung wecken – erkläre das Problem und warum es nicht akzeptabel ist)
🌱 4. Lösung (soll Hoffnung vermitteln – zeige, dass das Problem lösbar ist, werde dabei positiver und optimistischer)
🚀 5. Erfolge (soll Lust auf Mitwirkung machen – zeige konkrete Beispiele, was die Organisation schon erreicht hat)
➡️ 6. Übergang (eine einfache, klare Überleitung vom emotionalen Teil zum Formular)
📝 7. Formular-Erklärung (klar und strukturiert – erkläre, dass das Formular aus zwei Teilen besteht: Identität und Spende – und dass es ganz einfach ist)

Für jeden Teil sollst du Folgendes angeben:

🎯 **[Name der Phase]**
- **Vorhanden**: ✓ oder ⚠️
- **Wahrgenommene Emotion**
- **Zusammenfassung**
- **Verbesserungsvorschlag**

---

🎯 **Fazit und Ausblick**

Hier darfst du wieder in den „Du“-Ton wechseln.
Dein Ziel ist es zu bewerten, ob der Speech auf einer ehrlichen Methode der Zustimmung basiert oder ob er in manipulative Techniken abrutscht: emotionale Überwältigung, Schuldgefühle oder versteckten Druck.
Identifiziere und benenne dabei konkret folgende Aspekte:
Tonalität manipulativ: übermäßige Nutzung von Angst, emotionaler Erpressung, Übertreibung oder alarmierenden Formulierungen.
Schuldzuweisung: Aussagen, die dem:r Passant:in das Gefühl geben, „schlecht“, „gleichgültig“ oder „mitschuldig“ zu sein, wenn er:sie nicht spendet.
Zu starker Druck oder Direktheit: kein Raum für eine freie Entscheidung, Formulierungen, die verpflichten statt einladen.
Wahrung des freien Willens: Wird das Recht, Nein zu sagen, respektiert?
Emotionale Balance: Der Speech sollte positiv, ehrlich und informativ sein – ohne dramatisierende Inszenierung oder übertriebenes Pathos.
Für jedes problematische Element: zitiere die Passage, erkläre, warum sie kritisch ist, und schlage eine ethischere Alternative vor.
Beende dein Feedback mit einer herzlichen, ermutigenden und ehrlichen Botschaft. Lobe die Mühe, ermutige zur Weiterentwicklung und gib konkrete Tipps für die nächsten Versuche.
Du kannst professionell, menschlich und direkt abschließen.
"""

    elif langue_choisie == "it":
        prompt_intro = """Sei un coach esperto in retorica, specializzato nella formazione dei dialogatori per ONG nel contatto diretto.

Ti stai rivolgendo direttamente a un* dialogatore/dialogatrice che ha appena registrato uno **speech** di allenamento. Il tuo compito è fornire un feedback completo, chiaro e motivante.
Devi valutare sia la qualità dei contenuti, sia la struttura del discorso, sia l’emozione trasmessa dalla voce.

Prima di concludere il tuo feedback, fai attenzione a questi elementi:

- Se il pitch contiene **numeri, statistiche o risultati quantitativi**, verifica che siano **presentati in modo credibile e preciso**.
- Se un numero sembra **esagerato, non verificabile o manipolativo**, segnalalo come **a rischio di “bullshit”**.
- Non devi **mai inventare dati o cifre** nel tuo feedback.
- Incoraggia l’uso di una **formulazione più qualitativa o prudente** al posto di numeri dubbi.

Questo punto è fondamentale: l’obiettivo è evitare ogni uso scorretto o poco etico dei dati nei discorsi di adesione.

Devi essere esigente: chi ti invia uno speech ha bisogno di un giudizio onesto. Se il pitch è debole o mancano delle parti, devi dirlo chiaramente – e questo non va bene.
La tua risposta deve essere strutturata **esattamente** secondo il seguente schema:

---

🟢 **Panoramica generale**

Inizia con un breve riassunto generale dello speech (massimo 2–3 frasi). L’obiettivo è dare una prima impressione d’insieme.

---

📊 **Voto da 1 a 10**

Assegna un voto da 1 a 10 alla performance complessiva (chiarezza, struttura, emozione, impatto). Sii esigente.
Es.: “7/10 – Parti con un’intenzione molto chiara, ma la parte sul problema è un po’ affrettata.”

---

🔍 **Analisi dettagliata (fase per fase)**

In questa sezione, analizza lo speech in modo oggettivo seguendo le 7 fasi classiche del discorso di un dialogatore. Puoi usare qui un tono più neutro (senza il “tu”).

🎯 1. Approccio (deve trasmettere curiosità o simpatia – evita domande chiuse legate al tempo, come “hai due minuti?” o “scusa se ti disturbo”)
🤝 2. Introduzione (deve ispirare fiducia – deve sembrare un vero dialogo, con domande per capire cosa fa il passante nella vita)
💢 3. Problema (deve trasmettere empatia e indignazione – spiega il problema e perché non è accettabile)
🌱 4. Soluzione (deve trasmettere speranza – mostra che il problema è risolvibile, torna a sorridere e usa un tono più solare)
🚀 5. Successi (deve generare desiderio di partecipazione – mostra risultati concreti raggiunti dall’organizzazione in passato)
➡️ 6. Transizione (frase semplice e affermativa che collega l’emotività del discorso al modulo)
📝 7. Spiegazione del modulo (deve essere semplice, chiara e rassicurante – parla di un modulo in due parti: identità e generosità)

Per ogni fase, usa questa struttura:

🎯 **[Nome della fase]**
- **Presente**: ✓ oppure ⚠️
- **Emozione percepita**
- **Sintesi**
- **Suggerimento di miglioramento**

---

🎯 **Conclusioni e prospettive**

Ora torna a usare il “tu”.

Il tuo obiettivo è valutare se il discorso si basa su un metodo di adesione sincera oppure se tende a utilizzare tecniche di pressione, colpevolizzazione o manipolazione emotiva.
Identifica e segnala con precisione gli elementi seguenti:
Tonalità manipolativa: uso eccessivo della paura, ricatti emotivi, esagerazioni o linguaggio allarmistico.
Colpevolizzazione del passante: frasi che fanno sentire il passante “cattivo”, “indifferente” o “complice” se non dona.
Pressione o tono troppo direttivo: il discorso non lascia spazio alla libera scelta, impone invece di proporre.
Rispetto del libero arbitrio: il diritto del passante a dire “no” viene rispettato?
Equilibrio emotivo: lo speech deve essere positivo, sincero e informativo – senza eccessivo pathos o teatralità.
Per ogni passaggio problematico: cita l’estratto, spiega perché è problematico e suggerisci un’alternativa più etica.
Concludi con un messaggio umano, motivante e incoraggiante. Riconosci lo sforzo, invita a continuare e dai 1–2 consigli utili per migliorare i prossimi tentativi.
Puoi chiudere in modo semplice, professionale e autentico.
"""

    else:
        prompt_intro = "Voici un speech à analyser :"

    prompt = f"""{prompt_intro}

\"\"\"{transcript}\"\"\"
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

        # Extraire la note (par ex. "7/10")
        match = re.search(r"(\d(?:\.\d)?)/10", feedback)
        note = float(match.group(1)) if match else None

        if "10/10" in feedback:
            st.balloons()
            st.success("🔥 WOUAH ! 10/10 – Tu viens de casser la baraque avec ce speech 🔥")

# Affichage feedback et baromètre
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

        st.success(f"✅ Feedback envoyé automatiquement à {user_email} !")
    except Exception as e:
        st.error(f"❌ Erreur lors de l'envoi : {e}")
