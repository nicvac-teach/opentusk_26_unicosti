"""
Stima i parametri mancanti con l'API di Claude + ricerca web.

Legge data/parametri.csv, prende le righe con tipo_dato = S (stimato senza fonte)
e chiede a Claude di cercare sul web un valore con fonte. Il risultato NON
sovrascrive i dati: finisce in data/proposte_claude.csv, da controllare a mano.
Dopo il controllo, copiate valore e fonte in parametri.csv e mettete
tipo_dato = S_fonte (stimato con fonte) oppure M se la fonte è un dato misurato.

Uso:
    export ANTHROPIC_API_KEY=...
    python strumenti/stima_con_claude.py --model <id del modello>
(l'elenco dei modelli è su https://docs.claude.com/en/docs/about-claude/models)
"""
import argparse
import csv
import json
import re
from pathlib import Path

import anthropic

DATA = Path(__file__).resolve().parent.parent / "data"

PROMPT = """Sei un assistente di ricerca per un calcolatore dei costi universitari in Puglia.
Parametro da stimare: {chiave}
Descrizione: {nota}  (unità: {unita}; ambito: {ambito}; valore attuale ipotizzato: {valore})

Cerca sul web una fonte recente (preferibilmente 2025-2026, preferibilmente pubblica o statistica)
e rispondi SOLO con un oggetto JSON:
{{"valore": <numero>, "unita": "<unità>", "fonte_url": "<url>", "citazione": "<frase della fonte che contiene il numero>",
  "anno_dato": "<anno>", "tipo": "misurato" | "stima", "confidenza": "alta" | "media" | "bassa"}}
Se non trovi nulla di affidabile, usa "valore": null. Non inventare fonti."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--solo", nargs="*", help="chiavi specifiche da stimare")
    a = ap.parse_args()

    client = anthropic.Anthropic()
    righe = list(csv.DictReader(open(DATA / "parametri.csv", encoding="utf-8")))
    da_stimare = [r for r in righe if r["tipo_dato"] == "S" and (not a.solo or r["chiave"] in a.solo)]
    out = []
    for r in da_stimare:
        print("stimo", r["chiave"], "...")
        msg = client.messages.create(
            model=a.model,
            max_tokens=2000,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            messages=[{"role": "user", "content": PROMPT.format(**r)}],
        )
        testo = "".join(b.text for b in msg.content if b.type == "text")
        m = re.search(r"\{.*\}", testo, re.S)
        try:
            j = json.loads(m.group(0)) if m else {}
        except json.JSONDecodeError:
            j = {}
        out.append({"chiave": r["chiave"], "valore_attuale": r["valore"], **j, "risposta_grezza": testo[:500]})

    campi = sorted({k for o in out for k in o}, key=lambda k: (k != "chiave", k))
    with open(DATA / "proposte_claude.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        w.writerows(out)
    print("scritto data/proposte_claude.csv: CONTROLLATE ogni fonte prima di usarla")


if __name__ == "__main__":
    main()
