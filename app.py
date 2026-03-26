import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import uuid

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Self-Assessment: Chronos vs Kayrós", layout="centered")

# --- COSTANTI E DATI ---
DOMANDE = [
    {
        "testo": "1. Per definire e organizzare la mia produttività quotidiana:",
        "A": "Per essere efficiente, cerco di riempire ogni minuto disponibile, puntando alla velocità e a depennare più compiti possibili dalla mia lista.",
        "B": "Mi concentro sull'identificare e svolgere le cose 'giuste', privilegiando l'efficacia e la direzione strategica rispetto alla mera velocità."
    },
    {
        "testo": "2. Durante lo svolgimento di un compito impegnativo, il mio rapporto con l'orologio:",
        "A": "Sento parecchio il peso della scadenza: controllo spesso l'ora e vivo il tempo come un flusso inesorabile da battere.",
        "B": "Perdo la cognizione del tempo: mi immergo completamente nell'attività che sto svolgendo, e provo piacere nel processo in cui sono coinvolto."
    },
    {
        "testo": "3. Normalmente come gestisci la reperibilità e le innumerevoli fonti di distrazione (ad esempio: mail, notifiche, chiamate in arrivo)?",
        "A": "Sono sempre connesso e cerco di rispondere subito a tutto, dedicandomi innanzitutto ad attività facili e veloci da svolgere.",
        "B": "Mi isolo intenzionalmente per difendere il mio spazio mentale, dedicando lunghi blocchi di tempo ininterrotto al lavoro profondo."
    },
    {
        "testo": "4. Considerando i quadranti della Matrice di Eisenhower, dove passi la maggior parte del tuo tempo lavorativo?",
        "A": "Nei quadranti dell'urgenza: mi trovo spesso a dover risolvere emergenze dell'ultimo minuto o a reagire alle richieste degli altri.",
        "B": "Nel secondo quadrante: mi dedico ad attività importanti ma non urgenti, come quelle finalizzate a prevenire le crisi o alla pianificazione strategica."
    },
    {
        "testo": "5. Come reagisci di fronte a un compito particolarmente difficile, che ti provoca resistenza o ansia?",
        "A": "Per ottenere un rapido sollievo dall'ansia, tendo a procrastinare, rifugiandomi in compiti più facili, anche se so che questo a lungo termine peggiora la situazione.",
        "B": "Lo affronto deliberatamente, cercando un bilanciamento tra le mie abilità e le sfide che possono stimolare la mia crescita ed evoluzione personale."
    },
    {
        "testo": "6. In conclusione, qual è il tuo obiettivo globale rispetto alla gestione del tempo?",
        "A": "Avere un'agenda perfettamente ottimizzata e rispettare ogni singola scadenza pianificata.",
        "B": "Creare un impatto significativo, favorire la mia autorealizzazione e raggiungere un profondo benessere personale."
    }
]

PROFILI = {
    "A": {
        "titolo": "Dittatura della linea retta (Maggioranza A)",
        "descrizione": "Sei un eccellente esecutore e un professionista impeccabile nell'ottimizzazione del calendario, ma vivi nella 'dittatura della linea retta'. Il tuo focus principale è sull'efficienza: cerchi di fare le cose nel modo corretto e velocemente. Tuttavia, questo approccio puramente quantitativo rischia di portarti al sovraccarico cognitivo e di farti vivere costantemente in uno stato reattivo e di urgenza. Il rischio maggiore è l'inefficacia: potresti essere bravissimo ad affrontare con il metodo giusto il problema sbagliato.",
        "consiglio": "Devi iniziare a sottrarre tempo alle attività operative per ampliare la tua visione strategica. Abbraccia il limite di tempo su poche attività ad alto impatto (unendo la Legge di Parkinson al Principio di Pareto) per sbloccare il tuo potenziale."
    },
    "B": {
        "titolo": "Tempo Rotondo e Nutriente (Maggioranza B)",
        "descrizione": "Sei orientato verso il tempo 'rotondo e nutriente'. Non ti limiti a misurare il ticchettio dell'orologio, ma sai riconoscere e cogliere le opportunità. Hai compreso l'importanza del Deep Work e sai isolarti per proteggere la tua concentrazione rara dai sabotatori digitali. Puntando allo stato di Flow, permetti al tuo cervello di disattivare l'autocritica e di massimizzare sia la produttività che la creatività. La tua gestione del tempo è proattiva e mira al benessere eudaimonico, investendo nel tuo 'Sé futuro'.",
        "consiglio": "Continua a coltivare questa sensibilità, ma ricorda che 'tiranneggiare il kayrós' richiede sempre una base organizzativa per non cadere nel caos."
    },
    "Equilibrio": {
        "titolo": "La Danza Perfetta (Profilo Bilanciato)",
        "descrizione": "Sei vicino a padroneggiare quella che il testo definisce 'la danza perfetta' tra Chronos e Kayrós. Hai capito il paradosso della gestione del tempo: utilizzi una rigorosa struttura basata su Chronos (regole, pianificazione, sistemi di gestione) non come una gabbia, ma come uno strumento essenziale per liberare spazio mentale. Questa disciplina organizzativa ti permette di avere la lucidità e la libertà di deviare strategicamente quando si presenta un'intuizione o un'opportunità ad alto valore (Kayrós).",
        "consiglio": "Continua a bilanciare struttura e flessibilità. Usa i tuoi sistemi per gestire l'ordinario, così da avere le energie mentali per cogliere lo straordinario."
    }
}

# --- FUNZIONI ---
def crea_donut_chart(count_a, count_b):
    labels = ['Chronos (Efficienza/Urgenza)', 'Kayrós (Efficacia/Flusso)']
    sizes = [count_a, count_b]
    colors = ['#FF9999', '#66B2FF'] # Rosso tenue per Chronos, Blu tenue per Kayros
    
    # Se l'utente non ha risposto a nulla (caso limite non possibile nel form, ma per sicurezza)
    if count_a == 0 and count_b == 0:
        sizes = [50, 50]
        colors = ['#DDDDDD', '#DDDDDD']

    fig, ax = plt.subplots(figsize=(5, 5))
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%', 
                                      startangle=90, pctdistance=0.85, 
                                      wedgeprops=dict(width=0.4, edgecolor='w'))
    
    plt.setp(autotexts, size=10, weight="bold", color="white")
    plt.setp(texts, size=10)
    
    # Rimuove il bordo per farlo sembrare più pulito
    ax.axis('equal')  
    return fig

def salva_su_drive(dati_riga):
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # ATTENZIONE: Crea questo foglio su Drive prima di fare il deploy!
        sheet = client.open("Risultati_Chronos_Kayros").sheet1
        sheet.append_row(dati_riga)
        return True
    except Exception as e:
        print(f"Errore di salvataggio: {e}")
        return False

# --- MAIN APP ---
def main():
    try:
        st.image("GENERA Logo Colore.png", use_container_width=True)
    except:
        st.warning("Immagine logo non trovata. Assicurati che 'GENERA Logo Colore.png' sia nella repository.")
    
    st.markdown("<h1 style='text-align: center;'>Autovalutazione: Chronos vs Kayrós</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #555;'>Chi guida il tuo tempo?</h3>", unsafe_allow_html=True)

    # Introduzione
    st.markdown("""
    Benvenuto in questo strumento di autovalutazione. L'obiettivo è esplorare il tuo approccio alla gestione del tempo, 
    bilanciando **Chronos** (il tempo misurabile, l'efficienza, l'orologio) e **Kayrós** (il momento opportuno, l'efficacia, il flusso).
    
    Rispondi alle seguenti 6 domande scegliendo l'opzione che descrive **meglio il tuo comportamento abituale**.
    """)
    st.markdown("<p style='font-size: 0.8em; background-color: #FFFF99; padding: 5px; border-radius: 5px;'>Proseguendo nella compilazione acconsento a che i dati raccolti potranno essere utilizzati in forma aggregata esclusivamente per finalità statistiche.</p>", unsafe_allow_html=True)

    if 'submitted_ck' not in st.session_state:
        st.session_state.submitted_ck = False

    if not st.session_state.submitted_ck:
        with st.form("questionario_ck_form"):
            
            st.header("Informazioni socio-anagrafiche")
            nome = st.text_input("Nome o Nickname")
            
            col1, col2 = st.columns(2)
            with col1:
                genere = st.selectbox("Genere", ["Maschile", "Femminile", "Non binario", "Non risponde"])
            with col2:
                eta = st.selectbox("Età", ["Fino a 20 anni", "21-30 anni", "31-40 anni", "41-50 anni", "51-60 anni", "61-70 anni", "Più di 70 anni"])
                
            col3, col4 = st.columns(2)
            with col3:
                studio = st.selectbox("Titolo di studio", ["Licenza media", "Qualifica professionale", "Diploma di maturità", "Laurea triennale", "Laurea magistrale (o ciclo unico)", "Titolo post lauream"])
            with col4:
                job = st.selectbox("Job", ["Imprenditore", "Top manager", "Middle manager", "Impiegato", "Operaio", "Tirocinante", "Libero professionista"])

            st.header("Il Test")
            risposte = {}
            for i, q in enumerate(DOMANDE):
                st.markdown(f"**{q['testo']}**")
                
                # Creiamo una lista di opzioni per il radio button
                opzioni_testo = [q['A'], q['B']]
                
                # La scelta dell'utente
                scelta = st.radio(
                    f"nascosto_{i}", 
                    options=opzioni_testo, 
                    key=f"q_{i}",
                    label_visibility="collapsed"
                )
                
                # Salviamo 'A' o 'B' nel dizionario a seconda della scelta
                risposte[i] = "A" if scelta == q['A'] else "B"
                st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            submit_button = st.form_submit_button("Invia e Scopri il tuo Profilo")

        if submit_button:
            if not nome:
                st.error("Per favore, inserisci un nome o nickname per procedere.")
            else:
                st.session_state.submitted_ck = True
                st.session_state.dati_utente_ck = [str(uuid.uuid4()), genere, eta, studio, job]
                st.session_state.risposte_ck = risposte
                st.rerun()

    # SEZIONE FEEDBACK
    if st.session_state.submitted_ck:
        st.header("I tuoi Risultati")
        
        risp = st.session_state.risposte_ck
        
        # Conteggio delle A e delle B
        count_a = list(risp.values()).count("A")
        count_b = list(risp.values()).count("B")
        
        # Determinazione del profilo
        if count_a > count_b:
            profilo_risultante = PROFILI["A"]
        elif count_b > count_a:
            profilo_risultante = PROFILI["B"]
        else:
            profilo_risultante = PROFILI["Equilibrio"]

        # Salvataggio su Drive
        riga_db = st.session_state.dati_utente_ck + [risp[i] for i in range(len(DOMANDE))] + [profilo_risultante["titolo"]]
        salvato = salva_su_drive(riga_db)
        if not salvato:
            st.warning("I risultati sono stati generati, ma si è verificato un problema nel salvataggio sul server. Puoi comunque consultare il tuo profilo qui sotto.")

        # Layout a colonne per affiancare grafico e testo introduttivo
        col_grafico, col_testo = st.columns([1, 1])
        
        with col_grafico:
            fig = crea_donut_chart(count_a, count_b)
            st.pyplot(fig)
            
        with col_testo:
            st.markdown(f"### Il tuo Profilo:\n## {profilo_risultante['titolo']}")
            st.write(f"**Risposte A (Chronos):** {count_a} su 6")
            st.write(f"**Risposte B (Kayrós):** {count_b} su 6")

        st.markdown("---")
        st.markdown("### Analisi del Profilo")
        st.write(profilo_risultante["descrizione"])
        
        st.info(f"💡 **Il Consiglio per te:** {profilo_risultante['consiglio']}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Compila un nuovo test"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.9em;'>Powered by GÉNERA</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
