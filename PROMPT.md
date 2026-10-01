# Hackathon Opentusk 2026 – Storico della chat e passaggio di consegne

> Conversazione del 30/09/2026 tra Nicola Vacca (docente, IIS Marconi-Hack, Bari) e Claude (Cowork),
> proseguita la sera stessa in **Claude Code su VS Code** (sezione 2.7). Il progetto è nella cartella
> `unicosti/`; lo zip `unicosti_puglia.zip` contiene la versione originale di Cowork.
> Per riprendere: leggere prima le sezioni **3 (stato)** e **5 (prossimi passi)**.

---

## 1. Contesto

**Evento:** Hackathon Opentusk 2026, giovedì 1 ottobre 2026, 8:30–20:00, Fiera del Levante (Bari), Padiglione 152 Regione Puglia.
Documento di riferimento: <https://docs.google.com/document/d/1-agMNnuXe6C7F8p8AJNt3L5amLCH7U6M-OGlMfkn8M0/edit>

**Regole chiave:**
- Il progetto deve usare **almeno un dataset di dati.puglia.it**, che deve restare il **dataset principale**. Le altre fonti (ISTAT, dati.gov.it, OpenCoesione, ARPA, Eurostat, OSM) servono ad arricchirlo.
- Prodotto: app/web app, dashboard, mockup, prototipo o storytelling con i dati, in italiano.
- AI consentita. Pitch finale breve (~5 minuti).
- Criteri della giuria: impatto e utilità 30, uso degli open data 25, originalità 20, fattibilità tecnica 15, qualità del pitch 10.
- Strumenti consigliati: VS Code, Python/pandas, Streamlit, Git/GitHub, OpenRefine, Knime/Orange.
- Premiati 2024 da tenere presenti per l'originalità: EcoCluster, LidoLink, Ulivin, **iMENSA Puglia**, Apulian Cybersecurity LivingLabs, **SafeRoad Bari**.

**Note tecniche su dati.puglia.it:**
- Il catalogo usa l'API CKAN: `https://dati.puglia.it/ckan/api/3/action/package_search?q=...`
- Gruppo "Istruzione, cultura e sport": 189 dataset, per lo più comunali (Lecce, Bari, Oria…).

---

## 2. Andamento della conversazione

### 2.1 Prima domanda: idee e critica all'idea dei libri scolastici

**Richiesta di Nicola:** partire da dati.puglia.it e proporre idee su scuola e istruzione, incrociando con i siti del documento. Valutare con sincerità la sua idea: dataset dei libri adottati dalle scuole pugliesi, con queste funzioni:
- confronto con scuole simili quando si supera il tetto di spesa;
- ottimizzatore che cambia meno libri possibile per rientrare nella spesa;
- voti degli studenti sui singoli argomenti dei libri;
- clustering territoriale ("quale regione ha fatto le mie scelte").

**Risposta, in sintesi:**
- Il dataset esiste: **"Adozioni libri di testo scolastici – Regione Puglia"** del Ministero (MIM) su dati.istruzione.it, ID `DS0713ALTPUGLIA`, aggiornato il 09/09/2026. Colonne: `CodiceScuola, AnnoCorso, SezioneAnno, TipoGradoScuola, Combinazione, Disciplina, CodiceISBN, Autori, Titolo, Sottotitolo, Volume, Editore, Prezzo, NuovaAdoz, DaAcquist, Consigliato`.
- **Problema grosso:** non è su dati.puglia.it, quindi rischia di violare la regola del dataset principale.
- Critica funzione per funzione:
  - **Tetti di spesa:** non sono nel dataset; vanno inseriti a mano dal decreto 2026/27 (es. 346 € per il primo anno del tecnico tecnologico). Il formato del libro (misto −10%, digitale −30%) non è nel dataset. Vanno esclusi i libri solo consigliati e la primaria (gratuita). Per trovare "scuole simili" serve l'anagrafe delle scuole MIM.
  - **Ottimizzatore:** è la parte più originale; si risolve con programmazione lineare (PuLP). Limiti: i volumi pluriennali non si cambiano a metà ciclo, e i docenti scelgono per qualità, non per prezzo.
  - **Voti degli studenti:** la parte più debole (nessun dato, parte da zero, privacy dei minori). Al massimo un mockup.
  - **Clustering tra regioni:** mostrerebbe soprattutto le quote degli editori; più utile raggruppare le singole scuole.
- **Altre idee con dati.puglia.it:** "Dopo il diploma" (dati ARPAL sulle assunzioni), "Posso permettermi l'università?" (borse ADISU), raggiungibilità delle scuole in bus (orari trasporti Lecce e AMTAB Bari), scuole sicure (rischio sismico ed edifici, dati di pochi comuni), mense (sconsigliata: iMENSA nel 2024), dove studiare.
- **Proposta ibrida:** "Scegli la scuola giusta": costo dei libri + tempo in bus + assunzioni in provincia.

### 2.2 Seconda domanda: "Posso permettermi l'università?", ci sono dati sufficienti?

**Dataset ADISU su dati.puglia.it:** 12 dataset (3 tipi × 4 anni, dal 2020/21 al 2023/24).
- Sono **microdati: una riga per studente**, anonima.
- Colonne: `TIPO_STUD` (M primo anno / A anni successivi), `IDONEITA` (B beneficiario / S idoneo senza borsa), `IFP` (F fuorisede / P pendolare / S in sede), `TIPO_CORSO` (L, LM, LMG, LTC, LSC, DR, SP), `UNIVERSITA`, `FACOLTA_DIPARTIMENTO`; a seconda del file anche `FASCIA_ISEE`, `FASCIA_ISPE` oppure `TIPO_ALLOGGIO`.
- File di esempio (2023/24, per status fuorisede): `https://dati.puglia.it/ckan/dataset/f70bb070-9195-4f13-b737-218248b22fe2/resource/c0061e1b-f95f-47e2-aa50-743430c53e89/download/dataset-adisupuglia-graduatorieiiiaggiornamento-bds2023_24-all_b_all-02042026.csv`

**Perché la "probabilità di avere la borsa" non funziona:**
1. I file contengono solo i beneficiari (nome file `all_b`, nessuna riga con S).
2. La Puglia copre il 100% degli idonei (anche nel 2026/27: 66 milioni, circa 28.000 idonei).
3. Al primo anno l'idoneità dipende solo dal reddito: ISEE ≤ 26.000 € e ISPE ≤ 56.000 €.

**Proposta alternativa:** un calcolatore di idoneità e importo della borsa sede per sede, più la sezione "studenti come te" dai microdati ADISU.

### 2.3 Terza domanda: calcolatore dei costi universitari

**Richiesta:** costo anno per anno e totale; borsa, trasporti o affitto; ipotesi triennale e 3+2; tempo medio di laurea per corso e sede; probabilità di essere assunti. Stimare i dati mancanti con le API Claude, distinguendo dati misurati e stimati, con un indice di affidabilità.

**Verifica delle fonti:** tabella voce per voce (vedi la sezione 4). Problemi di metodo da non sottovalutare:
- la durata media considera solo chi si laurea;
- gli anni fuori corso fanno perdere la borsa;
- il tasso di occupazione non è una probabilità individuale;
- AlmaLaurea è pubblica ma non è open data;
- la regola del dataset di dati.puglia.it.

**Proposta di indice di affidabilità:** somma sulle voci di (peso in euro della voce × qualità), con qualità M = 1, R = 1, D = 0,7, S_fonte = 0,4, S = 0,1.

### 2.4 Quarta domanda: cosa vuol dire "riempire le righe"?

Spiegato: un motore Python più tabelle CSV con colonne fisse (valore, fonte, tipo di dato), da compilare cercando i dati nelle fonti. Proposta di divisione dei ruoli tra gli studenti.

### 2.5 Quinta domanda: "questo lavoro lo devi fare tu"

Claude ha raccolto i dati da solo, documentando le fonti, e ha scritto il motore, l'app e gli script. È il progetto nello zip. Dettagli nelle sezioni 3 e 4.

**Note tecniche emerse durante la raccolta:**
- Dall'ambiente di sviluppo, `curl` verso dati.puglia.it, dati.istruzione.it, dati-ustat.mur.gov.it, AlmaLaurea e i siti degli atenei era **bloccato**. Raggiungibile solo GitHub. I dati sono stati letti con uno strumento di lettura web.
- **URL AlmaLaurea utili** (il codicione è di 16 cifre, es. `0720206200800001`):
  - scheda trasparenza (occupazione a 1/3/5 anni, stipendio): `https://statistiche.almalaurea.it/universita/statistiche/trasparenza?codicione=<codicione>`
  - profilo laureati (durata e regolarità): `https://statistiche.almalaurea.it/cgi-php/universita/statistiche/visualizza.php?anno=2025&corstipo=<L|LS|LSE>&ateneo=tutti&facolta=tutti&gruppo=tutti&classe=tutti&postcorso=<codicione>&LANG=it&CONFIG=profilo`
  - `corstipo`: L = triennale, **LS** = magistrale, **LSE** = ciclo unico.
  - Struttura del codicione: provincia (072 Bari, 075 Lecce) + indice ateneo (01 UniBa o UniSalento, 02 Poliba) + tipo (06 L, 07 LM/LMCU) + classe (L-n → 20nn; LM-n → 30(n+1), es. LM-32 → 3033; LMG/01 → 0514) + progressivo di 5 cifre.
  - Il tasso di occupazione AlmaLaurea è calcolato sui laureati che **non lavoravano** già alla laurea.
- **Correzione importante:** il +20% STEM della borsa ADISU vale **solo per le studentesse**.
- **UniSalento:** il sito blocca la lettura automatica, quindi le tasse sono stimate.

### 2.6 Domande successive

- **Configurazione di `stima_con_claude.py`:** l'API **non è inclusa** nei piani Pro, Max, Team o Enterprise; si paga a parte, a credito prepagato, dalla Console (platform.claude.com).
  - Prezzi: ricerca web 10 $ ogni 1.000 ricerche; Sonnet 5.5 (`claude-sonnet-5-5`) 2 $/10 $ per milione di token in ingresso/uscita; Haiku 4.5 (`claude-haiku-4-5-20251001`) 1 $/5 $.
  - Un giro dello script costa circa 1–2 $.
  - Passi: creare la chiave API, esportare `ANTHROPIC_API_KEY`, lanciare `python strumenti/stima_con_claude.py --model claude-sonnet-5-5` (opzione `--solo <chiave>` per un parametro solo).
  - Non dare la chiave agli studenti e impostare un limite di spesa.
- **`aggiungi_corso_almalaurea.py`:** facoltativo, se bastano i 20 corsi già presenti.
- **Perché l'app gira senza `adisu_dati_puglia.py`:** in quel momento l'app **non leggeva** `data/adisu_contesto.csv`. Il collegamento è stato fatto il 30/09 sera in Claude Code (vedi la sezione 2.7).

### 2.7 Sessione in Claude Code (30/09/2026 sera)

- **Dati ADISU (passo 1):** da VS Code dati.puglia.it è raggiungibile. Lo script scarica i 4 anni (2020/21–2023/24). Correzioni fatte:
  - alcuni CSV sono in cp1252: ora legge UTF-8 e, se non riesce, cp1252;
  - i nomi degli atenei cambiano da un anno all'altro: ora sono normalizzati con una sigla (UNIBA, POLIBA, UNISALENTO, UNIFG, LUM, ALTRO);
  - aggiunta la distinzione primo anno / anni successivi (`TIPO_STUD`);
  - aggiunto il file `data/adisu_isee.csv` dal dataset "per fascia di reddito". È solo regionale: quel dataset non ha la colonna ateneo.
- **Sezione "Studenti come te" in `app.py` (passo 2):**
  - numero di borsisti dell'ateneo, quota con lo stesso status dell'utente, borsisti al primo anno;
  - grafico dei borsisti per status nei 4 anni;
  - grafico dei borsisti pugliesi per fascia ISEE, con la fascia dell'utente evidenziata;
  - se i file mancano compare un messaggio e l'app continua a funzionare;
  - la tabella ADISU compare anche nella scheda "Fonti e affidabilità".
- **Decisione di Nicola:** **non si usano le API key di Claude**. Il passo 3 (`stima_con_claude.py`) è abbandonato e `aggiungi_corso_almalaurea.py` non si usa.
- **Tasse UniSalento (passo 4):** il sito ora risponde. Trovato l'**Allegato A – Modello di contribuzione 2026/27** (<https://www.unisalento.it/documents/20143/132441/Allegato-A_26-27.pdf/4ad07be3-c288-f2b9-aa2d-4bac262b2bce>); copia in `raw/unisalento/`.
  - Quota reddito (QRED): 0 fino a ISEE 13.000 €. Tra 13.000 e 40.000 € vale (ISEE−13.000)/27.000 × 1.700. Tra 40.000 e 60.000 € vale 1.700 + 40 € ogni 5.000 €. Oltre, (ISEE−14.000) × 0,00003 × 1.400 (o × 1.500 da 80.000 €), fino a un massimo di 3.000 €.
  - Riduzioni di ateneo sulla QRED: 100% fino a 25.000 €, poi 50% fino a 26.000 €, 25% fino a 28.000 €, 10% fino a 30.000 € e 5% fino a 40.000 €. **La no tax area piena arriva a 25.000 €, non a 26.000 €.**
  - Quota non meritevole: 140 €. Quota fuori corso: 0 fino a 2 anni fuori corso per gli studenti meritevoli, poi 200 €.
  - Riduzioni per merito fino al 40%, **non modellate**: il calcolo è prudente.
  - Esonero totale per borsisti e idonei ADISU: confermato dalla pagina degli esoneri.
  - Tassa regionale 2026/27 (146/170/195 €): confermata sul sito UniSalento.
- **Revisione delle regole sul fuori corso** (nata dalla domanda di Nicola: "le tasse non cambiano nell'anno fuori corso?"). Nel caso predefinito il primo anno fuori corso resta davvero nella no tax area. Rileggendo i regolamenti, però, sono emersi degli errori, ora corretti:
  - **UniBa, art. 4.5 (tetti della L. 232/2016):**
    - con ISEE tra 26.000 e 30.000 €, entro la durata legale + 1, il contributo non supera (ISEE−13.000) × 0,07 × 0,65 (o × 0,85 tra 28.000 e 30.000 €). Con ISEE 27.000 € sono 637 € invece di 1.386 € all'anno;
    - oltre la durata legale + 1 i tetti sono 200 € (fino a ISEE 22.000 €), 400 € (fino a 25.000 €), poi (ISEE−13.000) × 0,105 × 0,50/0,75/0,90;
    - il vecchio `fc_minimo_UNIBA` di 706,71 € sovrastimava.
  - **UniBa, art. 4.4.3:** +50 € dal 2° anno fuori corso.
  - **Poliba:**
    - la formula ufficiale è moltiplicata per 1,01 (massimo 2.121 €, non 2.100 €);
    - oltre la durata legale + 1 si paga la formula +6% +200 €, fino a 3.000 €. Prima c'era solo un minimo di 200 € stimato;
    - il regolamento 2026/27 non è ancora pubblicato: si usa il 2025/26.
  - **UniSalento:** la quota fuori corso di 200 € dal 3° anno fuori corso ora vale per qualunque ISEE.
- **Nuova struttura del calcolo del contributo in `motore.py`**, in 4 passi:
  1. no tax area (parametri `notax_{ateneo}_isee` e `notax_{ateneo}_anni_extra`);
  2. formula ISEE di `tasse.csv`, che ora contiene la formula piena senza la no tax area;
  3. tetti del nuovo `data/tetti_contributo.csv` (colonna `fase`: entro/oltre la durata legale + 1);
  4. penalità fuori corso (parametri `fc_anni_senza_penalita_*`, `fc_perc_*`, `fc_fisso_*`, `fc_max_*`, che sostituiscono `fc_minimo_*`).

  L'app mostra i tetti nella scheda "Fonti".
- **Libri negli anni fuori corso** (proposta di Nicola): nuovo parametro `libri_quota_fuori_corso` = 0,25, di tipo S. I libri si comprano negli anni regolari; negli anni fuori corso restano pochi esami e la tesi.
- **Prove:** motore su 9.600 e 6.400 combinazioni, 0 errori; app con AppTest, 0 errori.

---

## 3. Stato del progetto (cartella `unicosti/`)

| File | Contenuto | Stato |
|---|---|---|
| `motore.py` | classi `Dati`, `Studente`, `Calcolatore`; `calcola(studente, id_percorso)` restituisce anni e voci, costo lordo e netto, borse, indice di affidabilità, esiti occupazionali. Si usa anche da riga di comando | ✅ provato su 8.320 combinazioni, 0 errori |
| `app.py` | Streamlit, 3 schede: il mio percorso (grafico anno per anno con la borsa sotto lo zero, dettaglio con bollini del tipo di dato, **"Studenti come te" con i dati ADISU**, esiti a 1/3/5 anni, triennale vs 3+2), confronto di tutti i percorsi, fonti e affidabilità | ✅ provato con AppTest: 20 percorsi × 4 ISEE, e senza i file ADISU |
| `data/corsi.csv` | 20 corsi: durata, regolarità, occupazione a 1/3/5 anni, stipendio, intervistati, soddisfazione, link alle fonti | ✅ dati AlmaLaurea 2025 |
| `data/percorsi.csv` | P01–P20: triennale, 3+2, ciclo unico | ✅ (abbinamenti 3+2 scelti a mano, tipo S) |
| `data/parametri.csv` | borsa, tasse regionali, trasporti, affitti, mensa, stime, con fonte e tipo | ✅ |
| `data/tasse.csv` | fasce ISEE per ateneo (importo = alpha × ISEE + beta), formula piena senza no tax area | ✅ tutti da regolamento (UniSalento: Allegato A 2026/27) |
| `data/tetti_contributo.csv` | tetti di legge (L. 232/2016, UniBa art. 4.5), entro/oltre la durata legale + 1 | ✅ da regolamento |
| `data/tariffe_trasporto.csv` | Trenitalia Tariffa 40/14/Puglia, abbonamento mensile per fascia di km (1–250) | ✅ |
| `data/comuni_puglia.csv` | 255 comuni con coordinate (mancano Castro e Presicce-Acquarica) | ✅ |
| `data/adisu_contesto.csv` | borsisti ADISU per anno, ateneo (sigla), primo anno/successivi e status, con link al dataset (304 righe) | ✅ da dati.puglia.it |
| `data/adisu_isee.csv` | borsisti ADISU in Puglia per fascia ISEE, anno, status (120 righe, dato regionale) | ✅ da dati.puglia.it |
| `strumenti/adisu_dati_puglia.py` | scarica i microdati ADISU via CKAN e produce i due file sopra | ✅ eseguito il 30/09 |
| `strumenti/stima_con_claude.py` | stima i parametri di tipo S con Claude + ricerca web | ⛔ non si usa (niente API key) |
| `strumenti/aggiungi_corso_almalaurea.py` | scarica le pagine AlmaLaurea ed estrae i dati con Claude | ⛔ non si usa (niente API key) |
| `raw/` | dati grezzi raccolti (profilo, occupazione, comuni; `raw/unisalento/` con i PDF delle tasse) | – |

**Corsi inclusi:**
- **UniBa:** Informatica L-31, Computer science LM-18, Economia e commercio L-33, Economia finanza e impresa LM-56, Scienze biologiche L-13, Biologia cellulare e molecolare LM-6, Giurisprudenza LMG/01.
- **Poliba:** Ing. informatica e automazione L-8, Ing. informatica LM-32, Ing. civile e ambientale L-7, Ing. civile LM-23, Ing. gestionale L-9, Ing. gestionale LM-31.
- **UniSalento:** Economia aziendale L-18, Management controllo e finanza con IA LM-77, Scienze biologiche L-13, Biologia sperimentale ed applicata LM-6, Ing. meccanica L-9, Ing. meccanica LM-33, Giurisprudenza LMG/01.

**Logica del motore:**
- **Status:** distanza in linea d'aria × 1,25; stesso comune = in sede; fino a 60 km = pendolare; oltre = fuorisede. L'utente può forzarlo.
- **Borsa:** ISEE ≤ 26.000 e ISPE ≤ 56.000 → importo per status; +15% se ISEE < 13.000; +20% per le studentesse di corsi STEM. Anni legali al 100%, un semestre extra al 50%, poi zero. Si ipotizza che lo studente rispetti i requisiti di merito.
- **Tasse:** tassa regionale (146/170/195 €) + bollo 16 €. I borsisti hanno l'esonero dal contributo di ateneo. Per gli altri il contributo si calcola in 4 passi:
  1. **no tax area:** UniBa fino a 26.000 € e durata legale + 2; Poliba fino a 26.000 € e + 1; UniSalento fino a 25.000 € e + 2;
  2. **formula ISEE** di `tasse.csv`;
  3. **tetti** di `tetti_contributo.csv`;
  4. **penalità fuori corso:** UniBa +50 € dal 2° anno fuori corso; Poliba +6% +200 € oltre la durata legale + 1 (massimo 3.000 €); UniSalento +200 € dal 3° anno fuori corso.
- **Libri:** negli anni fuori corso se ne spende il 25%.
- **Scenario "medio":** durata = durata media AlmaLaurea arrotondata. Gli anni fuori corso prendono il tipo di dato "derivato".
- **Tipo di una voce:** il peggiore tra i dati usati per calcolarla.

**Avvio:** `pip install -r requirements.txt` → `streamlit run app.py`
oppure `python motore.py --isee 18000 --comune Altamura --percorso P09 --genere F`

---

## 4. Fonti principali (tutte in `data/*.csv` e nel README)

- **AlmaLaurea**, Profilo 2025 e Occupazione 2025: link per corso in `corsi.csv`.
- **Bando ADISU 2026/27:** <https://press.regione.puglia.it/-/diritto-allo-studio-regione-puglia-approva-gli-indirizzi-per-il-bando-adisu-2026-2027>
- **+20% STEM solo studentesse:** <https://adisupuglia.it/area_letturaNotizia/391787/pagsistema.html>
- **Copertura 100%:** <https://ildirigente.com/la-regione-puglia-garantisce-la-copertura-completa-delle-borse-di-studio-adisu-per-il-2026-2027/>
- **Tasse UniBa 2026/27:** <https://www.uniba.it/it/ateneo/statuto-regolamenti/regolamenti-generali/regolamento-contribuzione-studentesca-2026-2027>
- **Tasse Poliba 2025/26:** <https://web.poliba.it/sites/default/files/didattica/regolamento_contribuzione_studentesca_politecnico_di_bari_25_26.pdf>
- **Tasse UniSalento 2026/27 (Allegato A):** <https://www.unisalento.it/documents/20143/132441/Allegato-A_26-27.pdf/4ad07be3-c288-f2b9-aa2d-4bac262b2bce>
- **Tariffa 40/14/Puglia:** <https://www.trenitalia.com/content/dam/trenitalia/allegati/info/condizioni-generali-di-trasporto/parte-iii-trasporto-regionale/tariffa-40/Tariffa_40_14_Puglia.pdf>
- **Bonus trasporti 2026/27** (−50%, ISEE ≤ 13.000): <https://www.regione.puglia.it/web/lavoro-e-formazione/-/bonus-trasporti-studenti-2026-2027>
- **ADISU trasporti** (12 €/mese urbano): <https://adisupuglia.it/pagina116420_servizio-trasporti.html/>
- **ADISU mensa** (6,50 € a Bari): <https://adisupuglia.it/pagina116402_ristorazione.html/>
- **Affitti:** stanza Bari 426 €, Foggia 259 € (<https://www.corrieredelleconomia.it/2026/08/31/bari-affitti-per-gli-studenti-in-aumento-stanze-singole-a-426-euro-al-mese/>); €/m² Bari 12,88 e Lecce 9,25 (Immobiliare.it, agosto 2026). Stanza a Lecce derivata: circa 306 €.
- **Dataset libri MIM:** <https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Adozioni+libri+di+testo>
- **Microdati ADISU:** <https://dati.puglia.it/ckan/dataset/borse-di-studio-2023-24-studenti-idonei-e-beneficiari-distinti-per-richiesta-status-di-fuorisede>
- **Microdati ADISU per fascia di reddito:** <https://dati.puglia.it/ckan/dataset/borse-di-studio-2023-24-studenti-idonei-e-beneficiari-distinti-per-tipologia-e-fascia-di-reddito>
- **ARPAL, Comunicazioni obbligatorie:** <https://dati.puglia.it/ckan/dataset/anno-2024-comunicazioni-obbligatorie>

---

## 5. Prossimi passi (per Claude Code)

**Fatti il 30/09 sera:** passo 1 (script ADISU eseguito e corretto), passo 2 ("Studenti come te" nell'app), passo 4 (tasse UniSalento dal regolamento). Il passo 3 (stime con le API di Claude) è **abbandonato**: si è deciso di non usare le API key.

Da fare:
1. **Prova finale in locale:** `streamlit run app.py` e giro completo delle 3 schede, soprattutto la nuova sezione "Studenti come te" (grafici su tema chiaro e scuro).
2. (Facoltativo) Parametri ancora di tipo S o S_fonte (`soglia_km_pendolare`, `fc_minimo_POLIBA`, `borsa_semestre_extra_quota`, affitti e altre stime in `parametri.csv`): cercarli a mano nelle fonti, senza API.
3. (Facoltativo) Tasse Poliba 2026/27: quando sarà pubblicato il regolamento, aggiornare `tasse.csv` e i parametri `fc_*_POLIBA` (ora si usa il 2025/26).
4. (Facoltativo) Pulizia: Streamlit segnala che `use_container_width` è deprecato (va sostituito con `width="stretch"`). Non blocca nulla.
5. **Pitch:** punti forti da mostrare:
   - **dataset principale da dati.puglia.it:** microdati ADISU, una riga per borsista, 4 anni;
   - "Studenti come te": per esempio, tra i borsisti Poliba la quota di fuorisede è salita dal 22% (2020/21) al 33% (2023/24); i borsisti UniSalento sono passati da 4.144 a 5.362;
   - la fascia ISEE più alta dei borsisti segue la soglia di idoneità di ogni anno: 23.000 → 23.626 → 25.000 €;
   - indice di affidabilità con i bollini colorati (le tasse UniSalento ufficiali lo hanno alzato, per esempio da circa 19% a 54%);
   - "in Puglia se sei idoneo la borsa è garantita";
   - per un borsista pendolare il costo netto può essere negativo;
   - confronto triennale vs 3+2;
   - effetto degli anni fuori corso: la borsa scende al 50% e poi si azzera, il contributo aumenta secondo le regole di ogni ateneo, la spesa per i libri cala.

   Limiti da dichiarare:
   - la durata media è ottimistica, perché considera solo chi si laurea;
   - alcune magistrali hanno campioni piccoli;
   - la soglia dei 60 km per lo status è una stima;
   - il dato ISEE ADISU è solo regionale;
   - le riduzioni per merito non sono calcolate (costo prudente);
   - la quota di libri negli anni fuori corso (25%) è una stima;
   - si assume che lo studente rispetti i requisiti di merito.
