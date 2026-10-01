"""
Scarica da dati.puglia.it i microdati ADISU sulle borse di studio (2020/21-2023/24)
e produce due file:
  - data/adisu_contesto.csv: per anno, ateneo e tipo di studente (primo anno /
    anni successivi), quanti beneficiari sono fuorisede, pendolari o in sede;
  - data/adisu_isee.csv: per anno, quanti beneficiari ci sono in ogni fascia ISEE
    (dato regionale: il dataset "per fascia di reddito" non indica l'ateneo).

Serve a due cose:
  1. ancorare il progetto a dati.puglia.it (regola dell'hackathon);
  2. mostrare nell'app "studenti come te" (es. quota di fuorisede tra i borsisti di UniBa).

Uso:  python strumenti/adisu_dati_puglia.py
"""
import io
import re
import unicodedata
from pathlib import Path

import pandas as pd
import requests

API = "https://dati.puglia.it/ckan/api/3/action/package_search"
DATA = Path(__file__).resolve().parent.parent / "data"
FONTE = "ADISU Puglia su dati.puglia.it (microdati borse di studio)"
IFP = {"F": "fuorisede", "P": "pendolare", "S": "in sede"}
TIPO_STUD = {"M": "primo anno", "A": "anni successivi"}

# Sigle degli atenei, cercate nel nome normalizzato (senza accenti, apostrofi, punti)
SIGLE = [
    ("bari aldo moro", "UNIBA", "Università degli Studi di Bari Aldo Moro"),
    ("politecnico di bari", "POLIBA", "Politecnico di Bari"),
    ("salento", "UNISALENTO", "Università del Salento"),
    ("universita degli studi di foggia", "UNIFG", "Università degli Studi di Foggia"),
    ("degennaro", "LUM", "Libera Università Mediterranea Giuseppe Degennaro"),
]


def chiave(nome: str) -> str:
    """'Universita\\' del Salento', 'Università del Salento', 'Universit� del Salento' -> 'universit del salento'."""
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9() ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def sigla_e_nome(nome: str) -> tuple[str, str]:
    k = chiave(nome).replace("universit ", "universita ")
    for pezzo, sigla, canonico in SIGLE:
        if pezzo in k:
            return sigla, canonico
    return "ALTRO", re.sub(r"\s+", " ", re.sub(r"[\".]", " ", nome)).strip()


def leggi_csv(url: str) -> pd.DataFrame:
    raw = requests.get(url, timeout=120).content
    try:
        testo = raw.decode("utf-8-sig")
    except UnicodeDecodeError:  # alcuni anni sono pubblicati in Windows-1252
        testo = raw.decode("cp1252")
    return pd.read_csv(io.StringIO(testo), dtype=str, sep=None, engine="python")


def dataset(q: str, parola: str):
    """Trova i dataset ADISU il cui titolo contiene `parola` (uno per anno)."""
    r = requests.get(API, params={"q": q, "rows": 50}, timeout=60)
    r.raise_for_status()
    for ds in r.json()["result"]["results"]:
        if parola not in ds["title"].lower():
            continue
        anno = ds["title"].split("Borse di studio")[1].split("-")[0].strip()  # es. "2023/24"
        for res in ds["resources"]:
            url = res["url"]
            if url.lower().endswith(".csv") and "legenda" not in url.lower():
                yield anno, url, ds["name"]


def scarica(q: str, parola: str) -> pd.DataFrame:
    tabelle = []
    for anno, url, nome in dataset(q, parola):
        print("scarico", anno, url)
        df = leggi_csv(url)
        df["anno_accademico"] = anno
        df["dataset"] = f"https://dati.puglia.it/ckan/dataset/{nome}"
        tabelle.append(df)
    if not tabelle:
        raise SystemExit(f"Nessun dataset '{parola}' trovato: controlla la query sull'API CKAN")
    df = pd.concat(tabelle, ignore_index=True)
    df["status"] = df["IFP"].map(IFP)
    df["tipo_stud"] = df["TIPO_STUD"].map(TIPO_STUD)
    return df


def contesto():
    df = scarica("Adisu fuorisede", "fuorisede")
    df[["ateneo", "UNIVERSITA"]] = df["UNIVERSITA"].map(sigla_e_nome).tolist()
    chiavi = ["anno_accademico", "ateneo", "UNIVERSITA", "tipo_stud", "status"]
    out = df.groupby(chiavi + ["dataset"]).size().rename("beneficiari").reset_index()
    out["quota"] = out["beneficiari"] / out.groupby(chiavi[:4])["beneficiari"].transform("sum")
    out["fonte"] = FONTE
    out["tipo_dato"] = "M"
    out.to_csv(DATA / "adisu_contesto.csv", index=False)
    print(f"scritto adisu_contesto.csv ({len(out)} righe)")
    ult = out[(out.anno_accademico == out.anno_accademico.max()) & (out.ateneo != "ALTRO")]
    print(ult.pivot_table(index="ateneo", columns="status", values="beneficiari", aggfunc="sum").to_string())


def isee():
    df = scarica("Adisu fascia di reddito", "reddito")
    chiavi = ["anno_accademico", "tipo_stud", "status", "FASCIA_ISEE"]
    out = df.groupby(chiavi + ["dataset"]).size().rename("beneficiari").reset_index()
    out = out.rename(columns={"FASCIA_ISEE": "fascia_isee"})
    out["isee_da"] = out["fascia_isee"].str.split("-").str[0].astype(int)
    out["fonte"] = FONTE
    out["tipo_dato"] = "M"
    out.sort_values(["anno_accademico", "isee_da"]).to_csv(DATA / "adisu_isee.csv", index=False)
    print(f"scritto adisu_isee.csv ({len(out)} righe)")


if __name__ == "__main__":
    contesto()
    isee()
