"""
UniCosti Puglia - quanto costa l'università, anno per anno.
Avvio:  streamlit run app.py
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from motore import ETICHETTA, QUALITA, Calcolatore, Dati, Studente

st.set_page_config(page_title="UniCosti Puglia", page_icon="🎓", layout="wide")

# Palette categoriale (skill dataviz, ordine fisso) per le macro-voci
CATEGORIE = {
    "Tasse": "#2a78d6",
    "Affitto": "#eb6834",
    "Trasporti": "#1baf7a",
    "Vitto": "#eda100",
    "Libri e varie": "#e87ba4",
    "Borsa ADISU": "#008300",
}
MAPPA_VOCI = {
    "Tassa regionale + bollo": "Tasse", "Contributo ateneo": "Tasse",
    "Affitto stanza": "Affitto",
    "Bus urbano": "Trasporti", "Rientri a casa": "Trasporti", "Abbonamento treno/bus": "Trasporti",
    "Mensa": "Vitto", "Spesa alimentare a casa": "Vitto",
    "Libri e materiale": "Libri e varie", "Spese varie": "Libri e varie",
    "Borsa ADISU": "Borsa ADISU",
}
BADGE = {"M": "🟢", "R": "🟢", "D": "🟡", "S_fonte": "🟠", "S": "🔴"}


COLORI_STATUS = {"pendolare": "#1baf7a", "fuorisede": "#eb6834", "in sede": "#2a78d6"}


@st.cache_resource
def carica():
    d = Dati()
    return d, Calcolatore(d)


@st.cache_data
def carica_adisu():
    """Microdati ADISU da dati.puglia.it (prodotti da strumenti/adisu_dati_puglia.py); None se mancano."""
    try:
        return pd.read_csv("data/adisu_contesto.csv"), pd.read_csv("data/adisu_isee.csv")
    except FileNotFoundError:
        return None, None


dati, calc = carica()
adisu, adisu_isee = carica_adisu()
euro = lambda x: f"{x:,.0f} €".replace(",", ".")

# ------------------------------------------------------------------ input
with st.sidebar:
    st.header("I tuoi dati")
    isee = st.number_input("ISEE universitario (€)", 0, 200000, 18000, step=500)
    ispe = st.number_input("ISPE (€)", 0, 500000, 20000, step=1000)
    comuni = sorted(r["comune"] for r in dati.comuni.values())
    comune = st.selectbox("Comune di residenza", comuni, index=comuni.index("Altamura"))
    genere = st.radio("Genere (per l'incremento borsa STEM)", ["F", "M"], horizontal=True, index=1)
    status = st.selectbox("Dove vivrai?", ["auto", "in sede", "pendolare", "fuorisede"],
                          help="'auto' lo stima dalla distanza tra il tuo comune e la sede")
    scenario = st.radio("Durata", ["medio", "in corso"],
                        format_func=lambda s: "tempo medio reale (AlmaLaurea)" if s == "medio" else "tutto in corso",
                        horizontal=False)

stud = Studente(isee, ispe, comune, genere, status, scenario)

st.title("🎓 UniCosti Puglia")
st.caption("Quanto costa davvero l'università, anno per anno, e cosa succede dopo la laurea. "
           "Ogni numero dichiara da dove viene.")

tab1, tab2, tab3 = st.tabs(["Il mio percorso", "Confronta tutti i percorsi", "Fonti e affidabilità"])

# ------------------------------------------------------------------ tab 1
with tab1:
    opzioni = {p["id"]: p["nome"] for p in dati.percorsi.values()}
    pid = st.selectbox("Percorso", list(opzioni), format_func=opzioni.get, index=8)
    r = calc.calcola(stud, pid)
    stt, km, motivo = r["status"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Costo netto totale", euro(r["costo_netto"]),
              help="Costi meno borse. Se è negativo la borsa copre più delle spese.")
    c2.metric("Anni previsti", len(r["anni"]))
    c3.metric("Borsa ADISU in totale", euro(r["borse"]) if r["idoneo_borsa"] else "non idoneo")
    c4.metric("Affidabilità del calcolo", f"{r['affidabilita']:.0%}")
    st.caption(f"Status stimato: **{stt}** ({motivo}).")

    # grafico anno per anno: barre impilate, borsa sotto lo zero
    righe = []
    for a in r["anni"]:
        for v in a.voci:
            righe.append({"anno": f"Anno {a.n}" + (" (fc)" if a.fuori_corso else ""), "cat": MAPPA_VOCI[v.nome], "euro": v.importo})
    df = pd.DataFrame(righe).groupby(["anno", "cat"], sort=False, as_index=False)["euro"].sum()
    fig = go.Figure()
    for cat, col in CATEGORIE.items():
        sub = df[df.cat == cat]
        if sub.empty or sub.euro.abs().sum() == 0:
            continue
        fig.add_bar(x=sub.anno, y=sub.euro, name=cat, marker_color=col,
                    marker_line_color="white", marker_line_width=2,
                    hovertemplate="%{x}<br>" + cat + ": %{y:,.0f} €<extra></extra>")
    netto = [a.totale for a in r["anni"]]
    fig.add_scatter(x=[f"Anno {a.n}" + (" (fc)" if a.fuori_corso else "") for a in r["anni"]], y=netto,
                    mode="markers+lines", name="Netto anno", line=dict(color="#0b0b0b", width=2),
                    marker=dict(size=9), hovertemplate="%{x}<br>Netto: %{y:,.0f} €<extra></extra>")
    fig.update_layout(barmode="relative", height=420, margin=dict(t=30, l=10, r=10, b=10),
                      legend=dict(orientation="h", y=1.1), yaxis_title="€ per anno",
                      plot_bgcolor="rgba(0,0,0,0)", yaxis=dict(gridcolor="rgba(128,128,128,0.2)", zerolinecolor="#888"))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("(fc) = anno fuori corso, previsto perché in media i laureati di questo corso impiegano di più.")

    with st.expander("Dettaglio voce per voce, con il tipo di ogni dato"):
        det = [{"Anno": a.n, "Corso": a.corso, "Voce": v.nome, "€": round(v.importo),
                "Dato": f"{BADGE[v.tipo]} {ETICHETTA[v.tipo]}", "Nota": v.nota}
               for a in r["anni"] for v in a.voci]
        st.dataframe(pd.DataFrame(det), use_container_width=True, hide_index=True)

    # studenti come te: microdati ADISU su dati.puglia.it
    st.subheader("Studenti come te")
    ateneo = r["corsi"][0]["ateneo"]
    ad = adisu[adisu.ateneo == ateneo] if adisu is not None else pd.DataFrame()
    if ad.empty:
        st.info("Dati ADISU non disponibili: esegui `python strumenti/adisu_dati_puglia.py` per scaricarli da dati.puglia.it.")
    else:
        nome_ateneo = ad.UNIVERSITA.iloc[0]
        ultimo = ad.anno_accademico.max()
        ult = ad[ad.anno_accademico == ultimo]
        tot = ult.beneficiari.sum()
        stesso = ult[ult.status == stt].beneficiari.sum()
        matr = ult[ult.tipo_stud == "primo anno"]
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Borsisti ADISU {ultimo}", f"{tot:,}".replace(",", "."), help=nome_ateneo)
        c2.metric(f"Di cui {stt}", f"{stesso / tot:.0%}", help="Quota dei borsisti dell'ateneo con il tuo stesso status")
        c3.metric("Borsisti al primo anno", f"{matr.beneficiari.sum():,}".replace(",", "."),
                  help=f"Tra loro il {matr[matr.status == stt].beneficiari.sum() / matr.beneficiari.sum():.0%} è {stt}")

        col_a, col_b = st.columns(2)
        per_anno = ad.groupby(["anno_accademico", "status"], as_index=False).beneficiari.sum()
        fig = go.Figure()
        for s, colore in COLORI_STATUS.items():
            sub = per_anno[per_anno.status == s]
            fig.add_bar(x=sub.anno_accademico, y=sub.beneficiari, name=s, marker_color=colore,
                        marker_line_color="white", marker_line_width=2,
                        hovertemplate="%{x}<br>" + s + ": %{y:,} borsisti<extra></extra>")
        fig.update_layout(barmode="stack", height=320, margin=dict(t=40, l=10, r=10, b=10),
                          title=dict(text=f"Borsisti {nome_ateneo} per status", font_size=14),
                          legend=dict(orientation="h", y=-0.15), plot_bgcolor="rgba(0,0,0,0)",
                          yaxis=dict(gridcolor="rgba(128,128,128,0.2)"))
        col_a.plotly_chart(fig, use_container_width=True)

        if adisu_isee is not None:
            anno_isee = adisu_isee.anno_accademico.max()
            fi = adisu_isee[adisu_isee.anno_accademico == anno_isee]
            fi = fi.groupby(["isee_da", "fascia_isee"], as_index=False).beneficiari.sum().sort_values("isee_da")
            fi["a"] = fi.fascia_isee.str.split("-").str[1].astype(float)
            mia = fi[(fi.isee_da <= isee) & (isee <= fi.a)]
            colori = ["#2a78d6" if f in set(mia.fascia_isee) else "#b8c4d0" for f in fi.fascia_isee]
            fig2 = go.Figure(go.Bar(x=fi.beneficiari, y=fi.fascia_isee + " €", orientation="h", marker_color=colori,
                                    hovertemplate="ISEE %{y}<br>%{x:,} borsisti<extra></extra>"))
            fig2.update_layout(height=320, margin=dict(t=40, l=10, r=10, b=10), plot_bgcolor="rgba(0,0,0,0)",
                               title=dict(text=f"Borsisti in Puglia per fascia ISEE ({anno_isee})", font_size=14),
                               xaxis=dict(gridcolor="rgba(128,128,128,0.2)"))
            col_b.plotly_chart(fig2, use_container_width=True)
            if mia.empty:
                col_b.caption(f"Con ISEE {euro(isee)} sei fuori dalle fasce dei borsisti di quell'anno.")
            else:
                sotto = fi[fi.a < isee].beneficiari.sum() / fi.beneficiari.sum()
                col_b.caption(f"La tua fascia è evidenziata: il {sotto:.0%} dei borsisti pugliesi aveva un ISEE più basso del tuo. "
                              "Dato regionale: il dataset per fascia di reddito non indica l'ateneo.")
        st.caption("Fonte: 🟢 microdati ADISU Puglia su [dati.puglia.it](https://dati.puglia.it/ckan/dataset/"
                   "borse-di-studio-2023-24-studenti-idonei-e-beneficiari-distinti-per-richiesta-status-di-fuorisede), "
                   "una riga per borsista, 2020/21–2023/24. In Puglia tutti gli idonei ricevono la borsa.")

    st.subheader("E dopo la laurea?")
    occ = r["occupazione"]
    cols = st.columns(3)
    for col, h in zip(cols, ["1 anno", "3 anni", "5 anni"]):
        e = occ.get(h)
        if e:
            col.metric(f"Occupati a {h}", f"{e['tasso_occupazione']:.0f}%")
            col.caption((f"{euro(e['retribuzione'])}/mese netti · " if e["retribuzione"] else "") +
                        f"{e['intervistati']} intervistati · campione **{e['affidabilita_campione']}**")
        else:
            col.metric(f"Occupati a {h}", "n.d.")
    if occ.get("iscritti_magistrale_1anno"):
        st.info(f"A un anno dalla triennale il {occ['iscritti_magistrale_1anno']:.0f}% è iscritto a una magistrale: "
                "il tasso di occupazione della sola triennale va letto con questo in mente.")
    st.caption(f"Fonte: [AlmaLaurea]({occ['fonte']}). Il tasso è la quota di laureati che lavorano, calcolata su chi non lavorava già al momento della laurea: "
               "non è una probabilità individuale.")

    # confronto 3 anni vs 3+2 per lo stesso corso
    coppia = [p for p in dati.percorsi.values() if p["corso_1"] == dati.percorsi[pid]["corso_1"]]
    if len(coppia) == 2:
        st.subheader("Triennale o 3+2?")
        cc = st.columns(2)
        for col, p in zip(cc, sorted(coppia, key=lambda x: bool(x["corso_2"]))):
            rr = calc.calcola(stud, p["id"])
            o = rr["occupazione"]
            best = o.get("5 anni") or o.get("1 anno")
            orizzonte = "5 anni" if o.get("5 anni") else "1 anno"
            col.markdown(f"**{p['nome']}**")
            col.write(f"{len(rr['anni'])} anni · netto **{euro(rr['costo_netto'])}**")
            if best:
                col.write(f"Occupati a {orizzonte}: **{best['tasso_occupazione']:.0f}%** · "
                          f"{euro(best['retribuzione'] or 0)}/mese")

# ------------------------------------------------------------------ tab 2
with tab2:
    tutti = []
    for p in dati.percorsi.values():
        rr = calc.calcola(stud, p["id"])
        o = rr["occupazione"]
        e = o.get("5 anni") or o.get("1 anno")
        tutti.append({
            "Percorso": p["nome"], "Anni": len(rr["anni"]), "Costo netto €": round(rr["costo_netto"]),
            "Affidabilità": round(rr["affidabilita"], 2),
            "Occupati %": e["tasso_occupazione"] if e else None,
            "Orizzonte": "5 anni" if o.get("5 anni") else "1 anno",
            "Retribuzione €/mese": e["retribuzione"] if e else None,
            "Campione": e["affidabilita_campione"] if e else "n.d.",
        })
    tdf = pd.DataFrame(tutti).sort_values("Costo netto €")
    st.dataframe(tdf, use_container_width=True, hide_index=True, height=740)
    st.caption("Per i percorsi di sola triennale l'occupazione è a 1 anno ed è bassa perché quasi tutti proseguono: "
               "non va confrontata direttamente con i 5 anni dei 3+2.")

# ------------------------------------------------------------------ tab 3
with tab3:
    st.markdown("""
**Come leggere l'affidabilità.** Ogni voce ha un tipo di dato:
🟢 *misurato* o *regola ufficiale* (qualità 1,0) · 🟡 *derivato* (0,7) · 🟠 *stimato con fonte* (0,4) · 🔴 *stimato* (0,1).
L'indice è la media della qualità, pesata su quanto ogni voce pesa in euro sul totale.
Se l'affitto vale metà del costo ed è stimato, l'indice scende: è lì che servono dati migliori.
""")
    st.subheader("Parametri")
    par = pd.DataFrame(dati.parametri.values())
    par["tipo_dato"] = par["tipo_dato"].map(lambda t: f"{BADGE[t]} {ETICHETTA[t]}")
    st.dataframe(par, use_container_width=True, hide_index=True,
                 column_config={"fonte": st.column_config.LinkColumn("fonte")})
    st.subheader("Corsi (AlmaLaurea)")
    st.dataframe(pd.DataFrame(dati.corsi.values()), use_container_width=True, hide_index=True)
    st.subheader("Tasse di ateneo")
    st.dataframe(pd.DataFrame(dati.tasse), use_container_width=True, hide_index=True)
    st.caption("Tetti di legge (L. 232/2016) applicati dopo la formula: 'entro' = fino alla durata legale + 1, 'oltre' = dopo.")
    st.dataframe(pd.DataFrame(dati.tetti), use_container_width=True, hide_index=True)
    if adisu is not None:
        st.subheader("Borsisti ADISU (dati.puglia.it)")
        st.dataframe(adisu.drop(columns=["fonte"]), use_container_width=True, hide_index=True,
                     column_config={"dataset": st.column_config.LinkColumn("dataset")})
