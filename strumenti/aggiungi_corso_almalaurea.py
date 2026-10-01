"""
Aggiunge un corso a data/corsi.csv leggendo le pagine pubbliche di AlmaLaurea.

Ogni corso AlmaLaurea ha un "codicione" di 16 cifre, ad esempio
0720206200800001 = Politecnico di Bari, Ingegneria informatica e dell'automazione (L-8).
Si trova cercando su Google:  statistiche.almalaurea.it trasparenza "<nome corso>" <ateneo>

Il programma scarica due pagine:
  - scheda trasparenza  -> occupazione a 1/3/5 anni, retribuzione, soddisfazione
  - profilo laureati    -> durata media degli studi, regolarità, età alla laurea
ne estrae il testo e chiede a Claude di trasformarlo in JSON (le tabelle AlmaLaurea
sono irregolari; è lo stesso metodo usato per compilare i dati iniziali).

Uso:
    export ANTHROPIC_API_KEY=...
    python strumenti/aggiungi_corso_almalaurea.py --codicione 0720206200800001 \
        --id PB-INF-L --ateneo POLIBA --tipo L --durata 3 --citta Bari --stem 1 --model <id modello>
NOTA: scritto senza poterlo eseguire (sito non raggiungibile dall'ambiente di sviluppo):
va provato domani. Se AlmaLaurea blocca le richieste, copiate a mano i numeri dalle due pagine.
"""
import argparse
import csv
import json
import re
from pathlib import Path

import anthropic
import requests
from bs4 import BeautifulSoup

DATA = Path(__file__).resolve().parent.parent / "data"
URL_T = "https://statistiche.almalaurea.it/universita/statistiche/trasparenza?codicione={c}"
URL_P = ("https://statistiche.almalaurea.it/cgi-php/universita/statistiche/visualizza.php?anno=2025"
         "&corstipo={t}&ateneo=tutti&facolta=tutti&gruppo=tutti&classe=tutti&postcorso={c}&LANG=it&CONFIG=profilo")
CORSTIPO = {"L": "L", "LM": "LS", "LMCU": "LSE"}  # codici usati da AlmaLaurea

CAMPI = ["nome", "classe", "laureati_2025", "eta_media_laurea", "durata_media_anni", "perc_in_corso", "perc_fc1",
         "perc_fc2", "perc_fc3", "perc_fc4", "perc_fc5plus", "indice_ritardo", "occ_1anno", "retr_1anno",
         "intervistati_1anno", "iscritti_lm_1anno", "occ_3anni", "retr_3anni", "intervistati_3anni",
         "occ_5anni", "retr_5anni", "intervistati_5anni", "soddisfazione"]


def testo(url):
    h = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0 (progetto scolastico)"})
    h.raise_for_status()
    return BeautifulSoup(h.text, "html.parser").get_text(" ", strip=True)[:60000]


def main():
    ap = argparse.ArgumentParser()
    for k in ("codicione", "id", "ateneo", "tipo", "citta", "model"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--durata", type=int, required=True)
    ap.add_argument("--stem", default="0")
    a = ap.parse_args()

    ut, up = URL_T.format(c=a.codicione), URL_P.format(t=CORSTIPO[a.tipo], c=a.codicione)
    prompt = (
        "Estrai dai due testi (pagine AlmaLaurea) i valori del CORSO (non del confronto con ateneo o classe). "
        f"Rispondi solo con JSON con queste chiavi: {CAMPI}. Numeri col punto decimale, null se assente. "
        "occ_* = tasso di occupazione %, retr_* = retribuzione mensile netta in euro, "
        "intervistati_* = numero di intervistati per quell'orizzonte; perc_* = regolarità negli studi.\n\n"
        f"=== SCHEDA TRASPARENZA ===\n{testo(ut)}\n\n=== PROFILO LAUREATI ===\n{testo(up)}"
    )
    msg = anthropic.Anthropic().messages.create(model=a.model, max_tokens=1500,
                                                messages=[{"role": "user", "content": prompt}])
    j = json.loads(re.search(r"\{.*\}", msg.content[0].text, re.S).group(0))
    print(json.dumps(j, indent=1, ensure_ascii=False))

    righe = list(csv.DictReader(open(DATA / "corsi.csv", encoding="utf-8")))
    cols = list(righe[0].keys())
    nuova = {c: "" for c in cols}
    nuova.update({k: ("" if v is None else v) for k, v in j.items() if k in cols})
    nuova.update(id=a.id, ateneo=a.ateneo, tipo=a.tipo, durata_legale=a.durata, citta_sede=a.citta,
                 stem=a.stem, codicione=a.codicione, fonte_profilo=up, fonte_occupazione=ut,
                 anno_dati="Profilo 2025; Occupazione 2025", tipo_dato="M",
                 nota="estratto automaticamente: verificare a campione sulle pagine AlmaLaurea")
    righe = [r for r in righe if r["id"] != a.id] + [nuova]
    with open(DATA / "corsi.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(righe)
    print("corso aggiunto. Ricordate di aggiungere il percorso in data/percorsi.csv")


if __name__ == "__main__":
    main()
