import streamlit as st
import arxiv_scraper
import techcrunch
import venture_beat
import stanford_ai
import theverge
import thn
import key_manager
from openai import OpenAI
from main import export_all_summaries
from datetime import datetime
import os

# App-Konfiguration
st.set_page_config(page_title="🧠 AI Research Summarizer", layout="wide")

# Hilfsfunktion zur Auswahl relevanter Artikel
def filter_relevant_articles(summaries, user_query):
    """Wähle die relevantesten Artikel basierend auf der Benutzerabfrage aus"""
    user_query_lower = user_query.lower()
    
    relevant_articles = {}
    
    # Für ArXiv - nur wenn vorhanden
    if "arxiv" in summaries and summaries["arxiv"]:
        relevant_arxiv = {}
        for title, data in summaries["arxiv"].items():
            # Prüfe Titel und Zusammenfassung auf Relevanz zur Abfrage
            if (user_query_lower in title.lower() or 
                user_query_lower in data['summary'].lower()):
                relevant_arxiv[title] = data
        
        # Wenn keine relevanten gefunden, nimm die ersten 5
        if not relevant_arxiv:
            for title, data in list(summaries["arxiv"].items())[:5]:
                relevant_arxiv[title] = data
                
        relevant_articles["arxiv"] = relevant_arxiv
    
    # Für andere Quellen - nur wenn vorhanden
    for source_key in ["techcrunch", "venturebeat", "stanford", "theverge", "thehackernews"]:
        if source_key in summaries and summaries[source_key]:
            relevant_source = []
            
            # Spezialbehandlung für Stanford-Format
            if source_key == "stanford":
                articles = [{"title": t, "link": l, "summary": s} for t, l, s in summaries[source_key]]
            else:
                articles = summaries[source_key]
            
            # Suche nach relevanten Artikeln
            for article in articles:
                title = article.get("title") or article.get("Titel", "")
                summary = article.get("summary") or article.get("Zusammenfassung", "")
                
                if (user_query_lower in title.lower() or 
                    (summary and user_query_lower in summary.lower())):
                    relevant_source.append(article)
            
            # Wenn keine relevanten gefunden, nimm die ersten 3
            if not relevant_source and articles:
                relevant_source = articles[:3]
                
            relevant_articles[source_key] = relevant_source
    
    return relevant_articles

# Navigation in der Sidebar
page = st.sidebar.radio("Navigation", ["📚 Artikel", "💬 Chat-Assistent"])

# Gemeinsame Sidebar-Einstellungen
st.sidebar.header("🔧 Einstellungen")

# ArXiv-Einstellungen
max_articles = st.sidebar.slider("🔢 Max. Anzahl ArXiv-Paper", 1, 30, 10)
arxiv_category = st.sidebar.selectbox(
    "📚 ArXiv Kategorie",
    options={
        "Künstliche Intelligenz (cs.AI)": "cs.AI",
        "Maschinelles Lernen (cs.LG)": "cs.LG",
        "Computer Vision (cs.CV)": "cs.CV",
        "Statistical ML (stat.ML)": "stat.ML",
        "Natural Language Processing (cs.CL)": "cs.CL"
    }.values()
)

# Citation-Einstellungen
citation_style = st.sidebar.multiselect(
    "📑 Zitationsstile",
    options=["apa", "mla", "chicago", "bibtex"],
    default=["apa"]
)

# Quellenwahl
use_arxiv = st.sidebar.checkbox("ArXiv", value=True)
use_techcrunch = st.sidebar.checkbox("TechCrunch", value=True)
use_venturebeat = st.sidebar.checkbox("VentureBeat", value=True)
use_stanford = st.sidebar.checkbox("Stanford Blog", value=True)
use_theverge = st.sidebar.checkbox("TheVerge", value=True)
use_thn = st.sidebar.checkbox("TheHackerNews", value=True)

# Chat-spezifische Einstellungen
if page == "💬 Chat-Assistent":
    st.sidebar.header("💬 Chat-Einstellungen")
    if st.sidebar.button("Chat-Verlauf löschen"):
        st.session_state.chat_history = []
        st.rerun()
    
    # GPT-Modellwahl
    gpt_model = st.sidebar.selectbox(
        "🤖 GPT-Modell",
        options=["gpt-3.5-turbo", "gpt-4"],
        index=0
    )

# Hauptbereich - Artikelseite
if page == "📚 Artikel":
    st.title("🧠 AI Research & News Summarizer")
    
    # Abruf-Button
    if st.button("🔍 Artikel abrufen & zusammenfassen"):
        with st.spinner("Lade Inhalte..."):
            arxiv_data = arxiv_scraper.main_arxiv(
                categories=[arxiv_category],
                max_results=max_articles,
                citation_styles=citation_style if citation_style else ["apa"]
            ) if use_arxiv else None

            techcrunch_data = techcrunch.main_techcrunch() if use_techcrunch else None
            venturebeat_data = venture_beat.main_venturebeat() if use_venturebeat else None
            stanford_data = stanford_ai.main_stanford() if use_stanford else None
            theverge_data = theverge.main_verge() if use_theverge else None
            thn_data = thn.main_thn() if use_thn else None

            st.session_state["summaries"] = {
                "arxiv": arxiv_data,
                "techcrunch": techcrunch_data,
                "venturebeat": venturebeat_data,
                "stanford": stanford_data,
                "theverge": theverge_data,
                "thehackernews": thn_data
            }

            st.success("✅ Zusammenfassungen erfolgreich erstellt!")

    # Tabs für Artikel
    if "summaries" in st.session_state:
        summaries = st.session_state["summaries"]
        tabs = st.tabs(["ArXiv", "TechCrunch", "VentureBeat", "Stanford", "TheVerge", "TheHackerNews"])

        def show_articles(articles):
            for item in articles:
                title = item.get("Titel") or item.get("title")
                link = item.get("Link") or item.get("link")
                summary = item.get("Zusammenfassung") or item.get("summary")
                st.markdown(f"### {title}")
                st.markdown(f"[🔗 Link zum Artikel]({link})")
                if summary:
                    st.write(summary)
                else:
                    st.info("Keine Zusammenfassung verfügbar")
                st.markdown("---")

        # Tab 1: ArXiv
        with tabs[0]:
            if summaries["arxiv"]:
                for title, data in summaries["arxiv"].items():
                    st.markdown(f"### {title}")
                    st.markdown(f"**Autoren:** {data['authors']}")
                    st.markdown(f"**Veröffentlicht:** {data['published']}")
                    st.markdown(f"[PDF Link]({data['link']})")
                    
                    # Display citations if available
                    if 'citations' in data and data['citations']:
                        with st.expander("📑 Zitationen anzeigen"):
                            for style, citation_text in data['citations'].items():
                                st.markdown(f"**{style.upper()}:**")
                                st.code(citation_text, language="text")
                                if st.button(f"Kopieren ({style})", key=f"copy_{style}_{title}"):
                                    st.write("✅ In Zwischenablage kopiert!")
                    
                    st.write(data["summary"])
                    st.markdown("---")

        # Tabs 2–6: Andere Quellen
        for i, key in enumerate(["techcrunch", "venturebeat", "stanford", "theverge", "thehackernews"], start=1):
            with tabs[i]:
                data = summaries[key]
                if data:
                    if key == "stanford":
                        data = [{"title": t, "link": l, "summary": s} for t, l, s in data]
                    show_articles(data)

        # Exportbereich
        st.markdown("## 📥 Zusammenfassungen exportieren")

        if st.button("📄 Word-Datei erzeugen"):
            os.makedirs("summary", exist_ok=True)
            export_all_summaries(
                arxiv_data=summaries["arxiv"],
                techcrunch_data=summaries["techcrunch"],
                venturebeat_data=summaries["venturebeat"],
                stanford_data=summaries["stanford"],
                theverge_data=summaries["theverge"],
                thn_data=summaries["thehackernews"]
            )
            date_str = datetime.today().strftime('%Y-%m-%d')
            filepath = f"summary/AI_Zusammenfassungen_{date_str}.docx"

            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    st.download_button("📥 Download .docx", data=f, file_name=os.path.basename(filepath))
            else:
                st.error("❌ Datei nicht gefunden.")

# Hauptbereich - Chat-Seite
elif page == "💬 Chat-Assistent":
    st.title("💬 KI-Forschungs-Assistent")
    
    # Prüfen ob bereits Daten geladen wurden
    if "summaries" not in st.session_state:
        st.warning("⚠️ Es wurden noch keine Artikel geladen. Bitte wechsle zur 'Artikel'-Seite und lade zuerst Inhalte.")
    else:
        st.write("""
        Stelle Fragen zu den geladenen Artikeln und Forschungspapern. Der Assistent kann:
        - Inhalte aus verschiedenen Quellen vergleichen
        - Spezifische Informationen finden
        - Konzepte erklären
        - Trends in der KI-Forschung analysieren
        - Personalisierte Zusammenfassungen erstellen
        """)
        
        # Initialisiere Chat-History falls nötig
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Zeige Chat-Verlauf
        for message in st.session_state.chat_history:
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                st.chat_message("user").write(content)
            else:
                st.chat_message("assistant").write(content)
        
        # Chat-Eingabefeld
user_query = st.chat_input("Frage etwas zu den geladenen Artikeln...")
if user_query:
    # Füge Benutzeranfrage zum Chat-Verlauf hinzu
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    # Zeige Benutzeranfrage
    st.chat_message("user").write(user_query)
    
    # Bereite Artikeldaten als Kontext vor
    summaries = st.session_state["summaries"]
    
    # Finde relevante Artikel basierend auf der Benutzerabfrage
    filtered_summaries = filter_relevant_articles(summaries, user_query)
    
    # Konvertiere Zusammenfassungen in Format für Prompt
    context = "Verfügbare Informationen:\n\n"
    
    # ArXiv-Papers einbeziehen, falls vorhanden
    if "arxiv" in filtered_summaries and filtered_summaries["arxiv"]:
        context += "ArXiv Papers:\n"
        for title, data in filtered_summaries["arxiv"].items():
            context += f"- {title}\n  Zusammenfassung: {data['summary'][:300]}...\n\n"
    
    # Andere Quellen einbeziehen, falls vorhanden
    for source_key, source_name in [
        ("techcrunch", "TechCrunch"), 
        ("venturebeat", "VentureBeat"),
        ("theverge", "The Verge"),
        ("stanford", "Stanford"),
        ("thehackernews", "TheHackerNews")
    ]:
        if source_key in filtered_summaries and filtered_summaries[source_key]:
            articles = filtered_summaries[source_key]
            if articles:
                context += f"{source_name} Artikel:\n"
                if source_key == "stanford":
                    for article in articles:
                        context += f"- {article['title']}\n  Zusammenfassung: {article['summary'][:300]}...\n\n"
                else:
                    for article in articles:
                        title = article.get("Titel") or article.get("title", "Ohne Titel")
                        summary = article.get("Zusammenfassung") or article.get("summary", "")
                        if summary:  # Nur hinzufügen, wenn summary nicht leer ist
                            context += f"- {title}\n  Zusammenfassung: {summary[:300]}...\n\n"
            
            # Bereite Prompt für OpenAI vor
            system_prompt = (
                "Du bist ein KI-Forschungsassistent, der bei der Analyse und Erklärung von wissenschaftlichen Artikeln und Tech-News hilft. "
                "Beantworte Fragen zu den bereitgestellten Artikelzusammenfassungen. "
                "Sei präzise und verständlich. Wenn die erforderlichen Informationen nicht im Kontext vorhanden sind, sage das klar. "
                "Beziehe dich auf konkrete Artikel und Forschungspapiere in deinen Antworten und vergleiche auch verschiedene Quellen."
            )
            
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                try:
                    # OpenAI API-Aufruf - verwendet ausgewähltes Modell
                    model_choice = gpt_model if 'gpt_model' in locals() else "gpt-3.5-turbo"
                    client = OpenAI(api_key=key_manager.get_openai_key())
                    response = client.chat.completions.create(
                        model=model_choice,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Hier sind Informationen aus verschiedenen KI-Forschungs- und Nachrichtenquellen:\n\n{context}\n\nBenutzerfrage: {user_query}"}
                        ],
                        stream=True,
                        max_tokens=200
                    )
                    
                    # Stream der Antwort
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                    
                    # Füge Assistentenantwort zum Chat-Verlauf hinzu
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                    
                except Exception as e:
                    response_placeholder.error(f"Fehler: {str(e)}")