"""
Motore di calcolo: quanto costa l'università, anno per anno.

Legge i CSV nella cartella data/ e, dati i dati dello studente e un percorso
(triennale, 3+2 o ciclo unico), restituisce:
  - il dettaglio dei costi anno per anno, voce per voce
  - il tipo di ogni dato (M misurato, R regola ufficiale, D derivato,
    S_fonte stimato con fonte, S stimato senza fonte)
  - l'indice di affidabilità del costo totale
  - gli esiti occupazionali del corso finale (AlmaLaurea)

Uso da riga di comando (esempio):
    python motore.py --isee 18000 --comune Altamura --percorso P09 --genere F
"""
from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

DATA = Path(__file__).parent / "data"

# Qualità di ciascun tipo di dato, usata per l'indice di affidabilità
QUALITA = {"M": 1.0, "R": 1.0, "D": 0.7, "S_fonte": 0.4, "S": 0.1}
ETICHETTA = {
    "M": "misurato",
    "R": "regola ufficiale",
    "D": "derivato",
    "S_fonte": "stimato (con fonte)",
    "S": "stimato",
}


# ---------------------------------------------------------------- caricamento
def _leggi(nome: str) -> list[dict]:
    with open(DATA / nome, encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Dati:
    def __init__(self) -> None:
        self.parametri = {r["chiave"]: r for r in _leggi("parametri.csv")}
        self.corsi = {r["id"]: r for r in _leggi("corsi.csv")}
        self.percorsi = {r["id"]: r for r in _leggi("percorsi.csv")}
        self.atenei = {r["id"]: r for r in _leggi("atenei.csv")}
        self.tasse = _leggi("tasse.csv")
        self.tetti = _leggi("tetti_contributo.csv")
        self.tariffe = _leggi("tariffe_trasporto.csv")
        self.comuni = {r["comune"].lower(): r for r in _leggi("comuni_puglia.csv")}

    def p(self, chiave: str) -> float:
        return float(self.parametri[chiave]["valore"])

    def t(self, chiave: str) -> str:
        return self.parametri[chiave]["tipo_dato"]


def peggiore(*tipi: str) -> str:
    """Il tipo di una voce calcolata da più dati è quello meno affidabile."""
    return min(tipi, key=lambda t: QUALITA[t])


def fascia(righe: list[dict], ateneo: str, isee: float) -> dict | None:
    """Prima riga dell'ateneo (in ordine crescente di ISEE) che contiene l'ISEE."""
    for r in righe:
        if r["ateneo"] == ateneo and float(r["isee_da"]) <= isee <= float(r["isee_a"]):
            return r
    return None


# ---------------------------------------------------------------- geografia
def distanza_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ---------------------------------------------------------------- input
@dataclass
class Studente:
    isee: float
    ispe: float
    comune: str
    genere: str = "M"             # "F" per l'incremento STEM studentesse
    status: str = "auto"          # auto | in sede | pendolare | fuorisede
    scenario: str = "medio"       # in corso | medio


@dataclass
class Voce:
    nome: str
    importo: float                # positivo = costo, negativo = entrata (borsa)
    tipo: str
    nota: str = ""


@dataclass
class Anno:
    n: int
    corso: str
    fuori_corso: bool
    voci: list[Voce] = field(default_factory=list)

    @property
    def totale(self) -> float:
        return sum(v.importo for v in self.voci)


# ---------------------------------------------------------------- calcolo
class Calcolatore:
    def __init__(self, dati: Dati | None = None) -> None:
        self.d = dati or Dati()

    # --- status abitativo
    def status(self, s: Studente, citta_sede: str) -> tuple[str, float, str]:
        d = self.d
        c = d.comuni.get(s.comune.lower())
        sede = d.comuni[citta_sede.lower()]
        if c is None:
            raise ValueError(f"Comune '{s.comune}' non trovato tra i comuni pugliesi")
        km = distanza_km(float(c["lat"]), float(c["lon"]), float(sede["lat"]), float(sede["lon"]))
        km_strada = km * d.p("fattore_strada")
        if s.status != "auto":
            return s.status, km_strada, "scelto dall'utente"
        if c["comune"].lower() == citta_sede.lower():
            return "in sede", 0.0, "stesso comune della sede"
        if km_strada <= d.p("soglia_km_pendolare"):
            return "pendolare", km_strada, f"{km_strada:.0f} km stimati (soglia {d.p('soglia_km_pendolare'):.0f} km, ipotesi)"
        return "fuorisede", km_strada, f"{km_strada:.0f} km stimati (oltre soglia, ipotesi)"

    def idoneo(self, s: Studente) -> bool:
        return s.isee <= self.d.p("borsa_isee_max") and s.ispe <= self.d.p("borsa_ispe_max")

    # --- singole voci
    def borsa(self, s, st, corso, anno_nel_corso, legale) -> Voce | None:
        d = self.d
        if not self.idoneo(s):
            return None
        chiave = {"fuorisede": "borsa_fuorisede", "pendolare": "borsa_pendolare", "in sede": "borsa_insede"}[st]
        base = d.p(chiave)
        incr, note = 0.0, []
        if s.isee < d.p("borsa_isee_max") * 0.5:
            incr += d.p("borsa_incr_isee_basso"); note.append("+15% ISEE basso")
        tipo = d.t(chiave)
        if s.genere == "F" and corso["stem"] == "1":
            incr += d.p("borsa_incr_stem_studentesse"); note.append("+20% studentessa STEM")
            tipo = peggiore(tipo, "S_fonte")  # la classificazione STEM dei corsi è nostra
        importo = base * (1 + incr)
        if anno_nel_corso <= legale:
            q = 1.0
        elif anno_nel_corso == legale + 1:
            q = d.p("borsa_semestre_extra_quota"); note.append("semestre aggiuntivo al 50%")
            tipo = peggiore(tipo, d.t("borsa_semestre_extra_quota"))
        else:
            return Voce("Borsa ADISU", 0.0, "R", "oltre la durata coperta dalla borsa")
        return Voce("Borsa ADISU", -importo * q, tipo, "; ".join(note) + " (ipotesi: requisiti di merito rispettati)")

    def tasse(self, s, corso, anno_nel_corso, legale, ha_borsa) -> list[Voce]:
        d = self.d
        at = corso["ateneo"]
        voci = []
        # tassa regionale + bollo
        if s.isee <= 26000:
            tr = d.p("tassa_regionale_isee_1")
        elif s.isee <= 52000:
            tr = d.p("tassa_regionale_isee_2")
        else:
            tr = d.p("tassa_regionale_isee_3")
        voci.append(Voce("Tassa regionale + bollo", tr + d.p("bollo"), "R"))
        # contributo di ateneo
        if ha_borsa:
            voci.append(Voce("Contributo ateneo", 0.0, "R", "esonero totale per borsisti/idonei ADISU"))
            return voci
        # 1. no tax area: ISEE sotto soglia ed entro la durata legale + N anni
        if s.isee <= d.p(f"notax_{at}_isee") and anno_nel_corso <= legale + d.p(f"notax_{at}_anni_extra"):
            tipo = peggiore(d.t(f"notax_{at}_isee"), d.t(f"notax_{at}_anni_extra"))
            voci.append(Voce("Contributo ateneo", 0.0, tipo, "no tax area"))
            return voci
        # 2. formula ISEE (fasce di tasse.csv in ordine crescente: vince la prima che contiene l'ISEE)
        f = fascia(d.tasse, at, s.isee)
        imp = float(f["alpha"]) * s.isee + float(f["beta"])
        tipo, note = f["tipo_dato"], [f["formula_originale"]]
        # 3. tetti di legge (L. 232/2016), diversi entro e oltre la durata legale + 1
        fase = "entro" if anno_nel_corso <= legale + 1 else "oltre"
        t = fascia([r for r in d.tetti if r["fase"] == fase], at, s.isee)
        if t and float(t["alpha"]) * s.isee + float(t["beta"]) < imp:
            imp = float(t["alpha"]) * s.isee + float(t["beta"])
            tipo, note = peggiore(tipo, t["tipo_dato"]), note + ["tetto " + t["formula_originale"]]
        # 4. penalità per gli anni fuori corso: imp x (1 + perc) + fisso, con un eventuale massimo
        if anno_nel_corso > legale + d.p(f"fc_anni_senza_penalita_{at}"):
            imp = imp * (1 + d.p(f"fc_perc_{at}")) + d.p(f"fc_fisso_{at}")
            if f"fc_max_{at}" in d.parametri:
                imp = min(imp, d.p(f"fc_max_{at}"))
            tipo = peggiore(tipo, d.t(f"fc_fisso_{at}"), d.t(f"fc_perc_{at}"))
            note.append("maggiorazione fuori corso")
        voci.append(Voce("Contributo ateneo", round(imp, 2), tipo, "; ".join(note)))
        return voci

    def abitare_e_muoversi(self, s, st, km, citta) -> list[Voce]:
        d = self.d
        voci = []
        if st == "fuorisede":
            k = f"stanza_singola_{citta}"
            voci.append(Voce("Affitto stanza", d.p(k) * d.p("mesi_affitto"), peggiore(d.t(k), d.t("mesi_affitto")),
                             f"{d.p(k):.0f} EUR/mese x {d.p('mesi_affitto'):.0f} mesi"))
            voci.append(Voce("Bus urbano", d.p(f"abb_urbano_studenti_{citta}") * d.p("mesi_abbonamento"),
                             peggiore(d.t(f"abb_urbano_studenti_{citta}"), d.t("mesi_abbonamento"))))
            voci.append(Voce("Rientri a casa", d.p("viaggi_casa_fuorisede") * d.p("mesi_abbonamento"), "S"))
        elif st == "pendolare":
            mensile = next(float(t["abbonamento_mensile"]) for t in d.tariffe
                           if float(t["km_da"]) <= max(1, round(km)) <= float(t["km_a"]))
            costo = mensile * d.p("mesi_abbonamento")
            nota = f"abbonamento {mensile:.0f} EUR/mese (fascia {round(km)} km)"
            if s.isee <= d.p("bonus_trasporti_isee_max"):
                costo -= mensile * d.p("bonus_trasporti_quota") * d.p("bonus_trasporti_mesi")
                nota += "; bonus regionale -50% ott-mag (se i fondi non finiscono)"
            voci.append(Voce("Abbonamento treno/bus", costo, peggiore("R", "D", d.t("mesi_abbonamento")), nota))
        else:
            voci.append(Voce("Bus urbano", d.p(f"abb_urbano_studenti_{citta}") * d.p("mesi_abbonamento"),
                             peggiore(d.t(f"abb_urbano_studenti_{citta}"), d.t("mesi_abbonamento"))))
        return voci

    def vivere(self, st, citta, fuori_corso=False) -> list[Voce]:
        d = self.d
        pasti = {"fuorisede": "pasti_anno_fuorisede", "pendolare": "pasti_anno_pendolare", "in sede": "pasti_anno_insede"}[st]
        k = f"pasto_mensa_{citta}"
        voci = [Voce("Mensa", d.p(pasti) * d.p(k), peggiore(d.t(pasti), d.t(k)),
                     f"{d.p(pasti):.0f} pasti x {d.p(k):.2f} EUR")]
        if st == "fuorisede":
            voci.append(Voce("Spesa alimentare a casa", d.p("spesa_alimentare_extra_fuorisede") * d.p("mesi_extra_spesa"), "S"))
        if fuori_corso:  # i libri si comprano negli anni regolari: restano pochi esami e la tesi
            q = d.p("libri_quota_fuori_corso")
            voci.append(Voce("Libri e materiale", d.p("libri_materiale") * q,
                             peggiore(d.t("libri_materiale"), d.t("libri_quota_fuori_corso")), f"{q:.0%} negli anni fuori corso"))
        else:
            voci.append(Voce("Libri e materiale", d.p("libri_materiale"), d.t("libri_materiale")))
        voci.append(Voce("Spese varie", d.p("spese_varie") * d.p("mesi_extra_spesa"), d.t("spese_varie")))
        return voci

    # --- durata di un corso nello scenario scelto
    def anni_corso(self, corso, scenario) -> tuple[int, str]:
        legale = int(corso["durata_legale"])
        if scenario == "in corso":
            return legale, "R"
        media = float(corso["durata_media_anni"])
        return max(legale, int(media + 0.5)), "D"  # durata media arrotondata (dato misurato, arrotondamento = derivato)

    # --- calcolo completo
    def calcola(self, s: Studente, id_percorso: str) -> dict:
        d = self.d
        perc = d.percorsi[id_percorso]
        ids = [perc["corso_1"]] + ([perc["corso_2"]] if perc["corso_2"] else [])
        anni: list[Anno] = []
        n = 0
        info_status = None
        for cid in ids:
            corso = d.corsi[cid]
            citta = corso["citta_sede"]
            st, km, motivo = self.status(s, citta)
            info_status = info_status or (st, km, motivo)
            legale = int(corso["durata_legale"])
            durata, tipo_durata = self.anni_corso(corso, s.scenario)
            for a in range(1, durata + 1):
                n += 1
                anno = Anno(n, corso["nome"] + f" ({corso['classe']})", a > legale)
                b = self.borsa(s, st, corso, a, legale)
                ha_borsa = b is not None and b.importo != 0
                anno.voci += self.tasse(s, corso, a, legale, ha_borsa)
                anno.voci += self.abitare_e_muoversi(s, st, km, citta)
                anno.voci += self.vivere(st, citta, a > legale)
                if b is not None:
                    anno.voci.append(b)
                if a > legale:  # gli anni fuori corso esistono perché la durata è un dato medio
                    for v in anno.voci:
                        v.tipo = peggiore(v.tipo, tipo_durata)
                anni.append(anno)

        costi = sum(v.importo for a in anni for v in a.voci if v.importo > 0)
        borse = -sum(v.importo for a in anni for v in a.voci if v.importo < 0)
        peso_tot = sum(abs(v.importo) for a in anni for v in a.voci) or 1
        affid = sum(abs(v.importo) / peso_tot * QUALITA[v.tipo] for a in anni for v in a.voci)
        quota_tipo = {}
        for a in anni:
            for v in a.voci:
                quota_tipo[v.tipo] = quota_tipo.get(v.tipo, 0) + abs(v.importo) / peso_tot

        finale = d.corsi[ids[-1]]
        return {
            "percorso": perc["nome"],
            "status": info_status,
            "idoneo_borsa": self.idoneo(s),
            "anni": anni,
            "costo_lordo": costi,
            "borse": borse,
            "costo_netto": costi - borse,
            "affidabilita": affid,
            "quota_per_tipo": quota_tipo,
            "occupazione": esiti(finale),
            "corsi": [d.corsi[c] for c in ids],
        }


def esiti(corso: dict) -> dict:
    """Esiti occupazionali AlmaLaurea del corso finale, con giudizio sul campione."""
    def giudizio(n):
        if not n:
            return "n.d."
        n = int(float(n))
        return "alta" if n >= 50 else "media" if n >= 20 else "bassa"
    out = {}
    for h, k in (("1 anno", "1anno"), ("3 anni", "3anni"), ("5 anni", "5anni")):
        if corso.get(f"occ_{k}"):
            out[h] = {
                "tasso_occupazione": float(corso[f"occ_{k}"]),
                "retribuzione": float(corso[f"retr_{k}"]) if corso.get(f"retr_{k}") else None,
                "intervistati": corso.get(f"intervistati_{k}") or None,
                "affidabilita_campione": giudizio(corso.get(f"intervistati_{k}")),
            }
    out["iscritti_magistrale_1anno"] = float(corso["iscritti_lm_1anno"]) if corso.get("iscritti_lm_1anno") else None
    out["fonte"] = corso["fonte_occupazione"]
    return out


# ---------------------------------------------------------------- CLI
def stampa(r: dict) -> None:
    st, km, motivo = r["status"]
    print(f"\n=== {r['percorso']} ===")
    print(f"Status: {st} ({motivo}) | idoneo alla borsa: {'sì' if r['idoneo_borsa'] else 'no'}")
    for a in r["anni"]:
        fc = " [fuori corso]" if a.fuori_corso else ""
        print(f"\nAnno {a.n} - {a.corso}{fc}: netto {a.totale:,.0f} EUR")
        for v in a.voci:
            print(f"   {v.nome:<26}{v.importo:>10,.0f}  [{ETICHETTA[v.tipo]}] {v.nota}")
    print(f"\nCosto lordo {r['costo_lordo']:,.0f} | borse {r['borse']:,.0f} | NETTO {r['costo_netto']:,.0f} EUR")
    print(f"Indice di affidabilità: {r['affidabilita']:.2f}  " +
          ", ".join(f"{ETICHETTA[k]} {v:.0%}" for k, v in sorted(r["quota_per_tipo"].items(), key=lambda x: -x[1])))
    print("Esiti occupazionali (AlmaLaurea):")
    for h, e in r["occupazione"].items():
        if isinstance(e, dict):
            print(f"   a {h}: occupati {e['tasso_occupazione']}% | {e['retribuzione']} EUR/mese | "
                  f"intervistati {e['intervistati']} (campione {e['affidabilita_campione']})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--isee", type=float, required=True)
    ap.add_argument("--ispe", type=float, default=20000)
    ap.add_argument("--comune", required=True)
    ap.add_argument("--genere", default="M")
    ap.add_argument("--status", default="auto")
    ap.add_argument("--scenario", default="medio", choices=["in corso", "medio"])
    ap.add_argument("--percorso", required=True)
    a = ap.parse_args()
    s = Studente(a.isee, a.ispe, a.comune, a.genere, a.status, a.scenario)
    stampa(Calcolatore().calcola(s, a.percorso))
