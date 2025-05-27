# Speech Coach IA

**Speech Coach IA** est une application pédagogique développée pour accompagner les dialogueur·euse·s d’ONG dans l’amélioration de leur pitch vocal, à travers un feedback structuré basé sur l’intelligence artificielle.

---

## 🎯 Objectif
Permettre à chaque dialogueur·euse de :
- s'entraîner de façon autonome,
- recevoir une analyse structurée de son pitch,
- progresser grâce à un retour bienveillant, exigeant et personnalisé.

---

## 🔍 Fonctionnement
1. L’utilisateur envoie un fichier audio (MP3 ou WAV).
2. L’outil transcrit l’audio à l’aide de **Whisper (OpenAI)**.
3. Il détecte la langue (français, allemand, italien).
4. Il utilise un prompt GPT-4 adapté à la langue pour analyser le pitch.
5. Il renvoie un feedback structuré (en 7 étapes) + un baromètre de performance.
6. Le feedback est envoyé par mail au dialogueur.

---

## 🌐 Langues supportées
- 🇫🇷 Français
- 🇩🇪 Allemand
- 🇮🇹 Italien

---

## 📁 Architecture actuelle (monofichier)
```
speech-coach-2/
├── speech_coach_app.py       ← toute l'application est ici (Streamlit)
├── prompts/
│   ├── prompt_fr.txt
│   ├── prompt_de.txt
│   └── prompt_it.txt
├── data/
│   └── organisations/*.json  ← contexte des ONG
├── requirements.txt
└── README.md
```

---

## 📦 Dépendances principales
- `streamlit`
- `openai`
- `langdetect`
- `matplotlib`
- `fpdf`
- `Pillow`

---

## 🚀 Lancer l’application en local
```bash
pip install -r requirements.txt
streamlit run speech_coach_app.py
```

---

## ☁️ Déploiement avec Streamlit Cloud

1. Crée un dépôt GitHub avec ce code.
2. Va sur [streamlit.io/cloud](https://streamlit.io/cloud) et connecte ton dépôt.
3. Indique `speech_coach_app.py` comme fichier principal ("main file").
4. Dans les secrets, ajoute ta clé OpenAI et email dans `.streamlit/secrets.toml` :
```toml
openai_key = "sk-..."
email_user = "ton.email@corris.com"
email_password = "motdepasse"
```
5. Clique sur "Deploy" — ton app est en ligne !

---

## 📌 Remarques
- Aucun fichier audio n’est conservé.
- L’analyse GPT-4 est purement formative.
- Ce dépôt va évoluer vers une **architecture modulaire** dans un futur dépôt `speech-coach-v2`.
