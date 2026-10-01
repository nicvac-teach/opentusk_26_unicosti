# UniCosti Puglia

Calcolatore dei costi universitari per le università pugliesi: costo anno per anno e totale,
borsa ADISU, tasse, affitto o trasporti, durata reale degli studi, esiti occupazionali.
Ogni numero dichiara **da dove viene** e **che tipo di dato è**; da questo nasce un **indice di affidabilità**.

Prototipo per l'Hackathon Opentusk 2026. Dati raccolti il 30/09/2026.

## Avvio

```bash
pip install -r requirements.txt
streamlit run app.py
# oppure da riga di comando:
python motore.py --isee 18000 --comune Altamura --percorso P09 --genere F
```

## Struttura

| File | Cosa contiene |
|---|---|
| `motore.py` | calcolo dei costi anno per anno, indice di affidabilità, esiti occupazionali |
| `app.py` | interfaccia Streamlit (3 schede: il mio percorso, confronto, fonti) |
| `data/corsi.csv` | 20 corsi di UniBa, Poliba e UniSalento: durata, regolarità, occupazione (AlmaLaurea) |
| `data/percorsi.csv` | 20 percorsi: triennale, 3+2, ciclo unico |
| `data/parametri.csv` | bando ADISU, tasse regionali, trasporti, affitti, mensa, stime: con fonte e tipo |
| `data/tasse.csv` | fasce ISEE del contributo di ateneo (importo = alpha × ISEE + beta), senza la no tax area |
| `data/tetti_contributo.csv` | tetti di legge al contributo (L. 232/2016, UniBa art. 4.5), entro e oltre la durata legale + 1 |
| `data/tariffe_trasporto.csv` | abbonamenti mensili regionali per fascia di km (Trenitalia, Tariffa 40/14/Puglia) |
| `data/comuni_puglia.csv` | 255 comuni pugliesi con coordinate (per la distanza dalla sede) |
| `data/atenei.csv` | sedi degli atenei |
| `data/adisu_contesto.csv` | borsisti ADISU per anno, ateneo, primo anno/successivi e status (da **dati.puglia.it**) |
| `data/adisu_isee.csv` | borsisti ADISU in Puglia per fascia ISEE (da **dati.puglia.it**, dato regionale) |
| `strumenti/adisu_dati_puglia.py` | scarica i microdati ADISU da **dati.puglia.it** e produce i due file sopra |
| `strumenti/stima_con_claude.py` | stima i parametri mancanti con Claude + ricerca web (da eseguire) |
| `strumenti/aggiungi_corso_almalaurea.py` | aggiunge un corso leggendo AlmaLaurea (da eseguire) |

## Tipi di dato e indice di affidabilità

| Tipo | Significato | Qualità |
|---|---|---|
| M | misurato (statistica o rilevazione) | 1,0 |
| R | regola ufficiale (bando, regolamento, tariffa) applicata ai dati dello studente | 1,0 |
| D | derivato da dati misurati con un'ipotesi dichiarata | 0,7 |
| S_fonte | stimato, con una fonte | 0,4 |
| S | stimato senza fonte | 0,1 |

Una voce calcolata da più dati prende il tipo **peggiore** tra quelli usati.
Indice = somma su tutte le voci di (peso in euro della voce sul totale × qualità).

## Fonti

**Corsi: durata, regolarità, occupazione** — AlmaLaurea, Profilo dei laureati 2025 e Condizione
occupazionale 2025 (laureati 2024 a 1 anno, 2022 a 3 anni, 2020 a 5 anni). Per ogni corso i due link
esatti sono nelle colonne `fonte_profilo` e `fonte_occupazione` di `data/corsi.csv`.
Il tasso di occupazione è calcolato da AlmaLaurea sui laureati che *non lavoravano* al momento della laurea.

**Borsa ADISU 2026/27** — soglie ISEE 26.000 € e ISPE 56.000 €, importi 7.172 / 4.191 / 2.891 €, +15% ISEE basso:
[Regione Puglia, indirizzi bando 2026/27](https://press.regione.puglia.it/-/diritto-allo-studio-regione-puglia-approva-gli-indirizzi-per-il-bando-adisu-2026-2027).
+20% solo per le **studentesse** dei corsi STEM: [ADISU, bando 2024/25](https://adisupuglia.it/area_letturaNotizia/391787/pagsistema.html).
Copertura 100% degli idonei: [Il Dirigente](https://ildirigente.com/la-regione-puglia-garantisce-la-copertura-completa-delle-borse-di-studio-adisu-per-il-2026-2027/).

**Tasse** — [UniBa, regolamento 2026/27](https://www.uniba.it/it/ateneo/statuto-regolamenti/regolamenti-generali/regolamento-contribuzione-studentesca-2026-2027);
[Poliba, regolamento 2025/26](https://web.poliba.it/sites/default/files/didattica/regolamento_contribuzione_studentesca_politecnico_di_bari_25_26.pdf)
(il 2026/27 non è stato trovato);
[UniSalento, Allegato A 2026/27 – Modello di contribuzione](https://www.unisalento.it/documents/20143/132441/Allegato-A_26-27.pdf/4ad07be3-c288-f2b9-aa2d-4bac262b2bce)
(quota reddito azzerata fino a ISEE 25.000 €, poi riduzioni del 50/25/10/5% fino a 40.000 €; massimo 3.000 €; copia in `raw/unisalento/`).
Per UniSalento non si applicano le riduzioni per merito (voto di diploma, CFU): il contributo calcolato è quello pieno, quindi prudente.

Il contributo di ateneo si calcola in 4 passi: (1) no tax area (ISEE sotto soglia ed entro la durata legale + N anni: UniBa 26.000 € e +2,
Poliba 26.000 € e +1, UniSalento 25.000 € e +2); (2) formula ISEE di `tasse.csv` (Poliba con il fattore 1,01 del regolamento);
(3) tetti di `tetti_contributo.csv`; (4) penalità fuori corso: UniBa +50 € dal 2° anno fuori corso (art. 4.4.3),
Poliba formula +6% +200 € oltre la durata legale + 1 (massimo 3.000 €), UniSalento quota fuori corso di 200 € dal 3° anno fuori corso.

**Trasporti** — [Trenitalia Tariffa 40/14/Puglia](https://www.trenitalia.com/content/dam/trenitalia/allegati/info/condizioni-generali-di-trasporto/parte-iii-trasporto-regionale/tariffa-40/Tariffa_40_14_Puglia.pdf);
[Bonus trasporti Regione Puglia 2026/27](https://www.regione.puglia.it/web/lavoro-e-formazione/-/bonus-trasporti-studenti-2026-2027) (−50%, ISEE ≤ 13.000 €);
[ADISU, abbonamenti urbani agevolati](https://adisupuglia.it/pagina116420_servizio-trasporti.html/).

**Affitti** — stanza singola Bari 426 €/mese e Foggia 259 €/mese (Skuola.net su dati Immobiliare.it Insights,
[articolo del 31/08/2026](https://www.corrieredelleconomia.it/2026/08/31/bari-affitti-per-gli-studenti-in-aumento-stanze-singole-a-426-euro-al-mese/));
€/m² Bari 12,88 e Lecce 9,25 ([Immobiliare.it](https://www.immobiliare.it/mercato-immobiliare/puglia/lecce/), agosto 2026).
Lecce: stanza **derivata** = 426 × 9,25 / 12,88 ≈ 306 €/mese.

**Mensa** — [ADISU, ristorazione](https://adisupuglia.it/pagina116402_ristorazione.html/): pasto intero 6,50 € a Bari.

**Comuni e coordinate** — [matteocontrini/comuni-json](https://github.com/matteocontrini/comuni-json) e
[Comuni-Italiani-2018](https://github.com/MatteoHenryChinaski/Comuni-Italiani-2018-Sql-Json-excel).

## Ipotesi e limiti da dichiarare nel pitch

- **Status (in sede, pendolare, fuorisede)**: stimato dalla distanza (linea d'aria × 1,25, soglia 60 km).
  Il bando usa tabelle ufficiali di comuni e tempi: l'utente può scegliere lo status a mano.
- **Borsa**: si ipotizza che lo studente rispetti i requisiti di merito; semestre extra al 50% (regola nazionale, da verificare nel bando).
- **Durata media**: AlmaLaurea la calcola **solo su chi si laurea**; chi abbandona non entra nel dato, quindi è ottimistica.
- **Occupazione dopo la sola triennale**: bassa perché l'80–90% prosegue con la magistrale; non va confrontata con i 5 anni dei 3+2.
- **Campioni piccoli**: alcune magistrali hanno meno di 20 intervistati (es. Biologia cellulare UniBa, Ing. meccanica LM UniSalento): l'app lo segnala.
- **Stime senza fonte** (qualità 0,1): libri, spese varie, spesa alimentare, rientri a casa, numero di pasti.
  Negli anni fuori corso la spesa per libri è il 25% (ipotesi: i libri sono già stati comprati).
  Sono le prime da migliorare cercando fonti a mano.
- **Tasse**: si assume che lo studente abbia i CFU richiesti (no tax area, tetti di legge, studente "meritevole" UniSalento);
  non sono calcolate le riduzioni per merito, quindi il contributo è prudente. Poliba usa il regolamento 2025/26 (il 2026/27 non è pubblicato).
- **Dataset principale (dati.puglia.it)**: i microdati ADISU sulle borse 2020/21–2023/24 alimentano la sezione
  "Studenti come te" (borsisti dell'ateneo per status e andamento, posizione del proprio ISEE tra i borsisti pugliesi).
  Per aggiornarli: `python strumenti/adisu_dati_puglia.py`.

## Come sono stati raccolti i dati

I numeri AlmaLaurea sono stati letti dalle pagine pubbliche (scheda trasparenza e profilo laureati) e
ricontrollati a campione con una seconda lettura. Le altre fonti sono state lette dai documenti ufficiali
citati. Nessun numero è stato inventato: dove mancava una fonte, il dato è marcato come stima.
