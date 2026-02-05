import json
from flask import Flask, render_template, request
from datetime import date

app = Flask(__name__)

def wczytaj():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def procent_ukonczenia_sezonu(dane, sezon):
    # zabezpieczenie
    if not dane["zawodnicy"] or not dane["dyscypliny"]:
        return 0

    liczba_zawodnikow = len(dane["zawodnicy"])
    liczba_dyscyplin = len(dane["dyscypliny"])

    maks_startow = liczba_zawodnikow * liczba_dyscyplin

    # unikalne (zawodnik, dyscyplina) w danym sezonie
    unikalne_starty = set()

    for w in dane["wyniki"]:
        if str(w.get("sezon")) != str(sezon):
            continue

        klucz = (w["zawodnik_id"], w["dyscyplina_id"])
        unikalne_starty.add(klucz)

    liczba_startow = len(unikalne_starty)

    return round((liczba_startow / maks_startow) * 100, 1)




@app.route("/")
def index():
    dane = wczytaj()
    today = date.today().isoformat()
    wybrany_sezon = request.args.get("sezon")
    wybrany_zawodnik = request.args.get("zawodnik")
    wybrana_dyscyplina = request.args.get("dyscyplina", "1")
    aktywny_sezon = str(dane["sezony"]["aktywny"])


    wyniki = dane["wyniki"]

    if wybrany_sezon:
        wyniki = [
            w for w in wyniki
            if w.get("sezon") == wybrany_sezon
        ]

    # ========================= 
    # KLASYFIKACJA GENERALNA
    # =========================
    punkty_zawodnikow = {}

    for w in wyniki:
        punkty_zawodnikow.setdefault(w["zawodnik_id"], 0)

    # grupowanie: (sezon, dyscyplina)
    grupy = {}

    for w in wyniki:
        klucz = (w["sezon"], w["dyscyplina_id"])
        grupy.setdefault(klucz, []).append(w)

    for (sezon, dysc_id), grupa in grupy.items():
        dysc = next(d for d in dane["dyscypliny"] if d["id"] == dysc_id)

        grupa.sort(
            key=lambda w: w["wynik"],
            reverse=dysc["wiecej_lepiej"]
        )

        liczba = len(grupa)
        poprzedni = None
        osoby_przed = 0

        for i, w in enumerate(grupa):
            if poprzedni is None:
                osoby_przed = 0
            elif w["wynik"] != poprzedni:
                osoby_przed = i

            pkt = liczba - osoby_przed
            punkty_zawodnikow[w["zawodnik_id"]] += pkt
            poprzedni = w["wynik"]





    zawodnicy = []
    for z in dane["zawodnicy"]:
        zawodnicy.append({
            "id": z["id"],
            "imie": z["imie"],
            "punkty": punkty_zawodnikow.get(z["id"], 0)
        })

    zawodnicy.sort(key=lambda x: x["punkty"], reverse=True)

    poprzednie_punkty = None
    miejsce = 0
    licznik = 0

    for z in zawodnicy:
        licznik += 1
        if poprzednie_punkty != z["punkty"]:
            miejsce = licznik
        z["miejsce"] = miejsce
        poprzednie_punkty = z["punkty"]


    # =========================
    # DZISIEJSZE ZAWODY
    # =========================
    dzisiejsze_wyniki = [
        w for w in dane["wyniki"]
        if w.get("data") == today
    ]

    dzisiejsza_tabela = []

    for d in dane["dyscypliny"]:
        wyniki_dyscypliny = [
            w for w in dzisiejsze_wyniki
            if w["dyscyplina_id"] == d["id"]
        ]

        if not wyniki_dyscypliny:
            continue

        wyniki_dyscypliny.sort(
            key=lambda w: w["wynik"],
            reverse=d["wiecej_lepiej"]
        )

        liczba = len(wyniki_dyscypliny)

        poprzedni = None
        osoby_przed = 0

        for i, w in enumerate(wyniki_dyscypliny):
            if poprzedni is None:
                osoby_przed = 0
            elif w["wynik"] != poprzedni:
                osoby_przed = i

            punkty = liczba - osoby_przed

            dzisiejsza_tabela.append({
                "zawodnik_id": w["zawodnik_id"],
                "dyscyplina_id": w["dyscyplina_id"],
                "wynik": w["wynik"],
                "miejsce": osoby_przed + 1,
                "punkty": punkty
            })

            poprzedni = w["wynik"]


    zawodnicy_map = {z["id"]: z["imie"] for z in dane["zawodnicy"]}
    dyscypliny_map = {d["id"]: d["nazwa"] for d in dane["dyscypliny"]}

# =========================
# REKORDY DYSCYPLIN (Z REMISAMI)
# =========================
    rekordy = []

    for d in dane["dyscypliny"]:
        wyniki_d = [
            w for w in dane["wyniki"]
            if w["dyscyplina_id"] == d["id"]
        ]

        if not wyniki_d:
            continue

        # najlepszy wynik
        if d["wiecej_lepiej"]:
            najlepszy = max(w["wynik"] for w in wyniki_d)
        else:
            najlepszy = min(w["wynik"] for w in wyniki_d)

        # WSZYSCY rekordziści
        rekordzisci = [
            w for w in wyniki_d
            if w["wynik"] == najlepszy
        ]

        for r in rekordzisci:
            zawodnik = next(
                z for z in dane["zawodnicy"]
                if z["id"] == r["zawodnik_id"]
            )

            rekordy.append({
                "dyscyplina": d["nazwa"],
                "wynik": r["wynik"],
                "zawodnik": zawodnik["imie"],
                "zawodnik_id": zawodnik["id"],
                "data": r.get("data", "-"),
                "sezon": r.get("sezon", "-")
            })


    # 🔥 filtr: tylko dyscypliny, w których zawodnik MA rekord
    if wybrany_zawodnik and wybrany_zawodnik.strip() != "":
        rekordy = [
            r for r in rekordy
            if str(r["zawodnik_id"]) == wybrany_zawodnik
        ]

    # ✅ sezony LICZONE ZAWSZE
    sezony = sorted(
        {w.get("sezon") for w in dane["wyniki"] if w.get("sezon")}
    )
    # =========================
    # TABELA DYSCYPLINY (SEZON)
    # =========================

    wybrana_dyscyplina = request.args.get("dyscyplina", "1")

    aktywny_sezon = wybrany_sezon or max(
        {w["sezon"] for w in dane["wyniki"]},
        default="1"
    )

    wyniki_dyscypliny = [
        w for w in dane["wyniki"]
        if w["sezon"] == aktywny_sezon
        and str(w["dyscyplina_id"]) == wybrana_dyscyplina
    ]

    dyscyplina = next(
        d for d in dane["dyscypliny"]
        if str(d["id"]) == wybrana_dyscyplina
    )

    wyniki_dyscypliny.sort(
        key=lambda w: w["wynik"],
        reverse=dyscyplina["wiecej_lepiej"]
    )

    tabela_dyscypliny = []

    liczba = len(wyniki_dyscypliny)
    poprzedni = None
    osoby_przed = 0

    for i, w in enumerate(wyniki_dyscypliny):
        if poprzedni is None:
            osoby_przed = 0
        elif w["wynik"] != poprzedni:
            osoby_przed = i

        tabela_dyscypliny.append({
            "miejsce": osoby_przed + 1,
            "zawodnik": next(
                z["imie"] for z in dane["zawodnicy"]
                if z["id"] == w["zawodnik_id"]
            ),
            "punkty": liczba - osoby_przed,
            "wynik": w["wynik"],
            "data": w.get("data", "-")
        })

        poprzedni = w["wynik"]

    aktywny_sezon = wybrany_sezon or dane["sezony"]["aktywny"]

    procent_sezonu = procent_ukonczenia_sezonu(
        dane,
        aktywny_sezon
    )


    return render_template(
        "index.html",
        zawodnicy=zawodnicy,
        rekordy=rekordy,
        sezony=sezony,
        wybrany_sezon=wybrany_sezon,
        wybrany_zawodnik=wybrany_zawodnik,  # 🔥 TO BYŁO BRAKUJĄCE
        wszyscy_zawodnicy=dane["zawodnicy"],
        tabela_dyscypliny=tabela_dyscypliny,
        dyscypliny=dane["dyscypliny"],
        wybrana_dyscyplina=wybrana_dyscyplina,
        procent_sezonu=procent_sezonu 
    )







@app.route("/zawodnik/<int:zawodnik_id>")
def zawodnik(zawodnik_id):
    wybrana_dyscyplina = request.args.get("dyscyplina")

    dane = wczytaj()

    zawodnik = next(
        z for z in dane["zawodnicy"]
        if z["id"] == zawodnik_id
    )

    historia = []

    for w in dane["wyniki"]:
        if w["zawodnik_id"] != zawodnik_id:
            continue

        if wybrana_dyscyplina and str(w["dyscyplina_id"]) != wybrana_dyscyplina:
            continue


        dyscyplina = next(
            d for d in dane["dyscypliny"]
            if d["id"] == w["dyscyplina_id"]
        )

        # wszystkie wyniki w tej samej dyscyplinie i dacie
        wyniki_konkurencji = [
            x for x in dane["wyniki"]
            if x["dyscyplina_id"] == w["dyscyplina_id"]
            and x.get("sezon") == w.get("sezon")
        ]

        wyniki_konkurencji.sort(
            key=lambda x: x["wynik"],
            reverse=dyscyplina["wiecej_lepiej"]
        )

        miejsce = next(
            i for i, x in enumerate(wyniki_konkurencji)
            if x["zawodnik_id"] == zawodnik_id
        )

        poprzedni = None
        osoby_przed = 0

        for i, x in enumerate(wyniki_konkurencji):
            if poprzedni is None:
                osoby_przed = 0
            elif x["wynik"] != poprzedni:
                osoby_przed = i

            if x["zawodnik_id"] == zawodnik_id:
                punkty = len(wyniki_konkurencji) - osoby_przed
                miejsce = osoby_przed + 1
                break

            poprzedni = x["wynik"]



        historia.append({
            "dyscyplina": dyscyplina["nazwa"],
            "miejsce": miejsce,   # +1 bo 
            "wynik": w["wynik"],
            "punkty": punkty,
            "data": w.get("data", "brak daty"),
            "sezon": w.get("sezon", "-")
        })
    rekordy_osobiste = []

    for d in dane["dyscypliny"]:
        wyniki = [
            w for w in dane["wyniki"]
            if w["zawodnik_id"] == zawodnik_id
            and w["dyscyplina_id"] == d["id"]
        ]

        if not wyniki:
            continue

        wyniki.sort(
            key=lambda w: w["wynik"],
            reverse=d["wiecej_lepiej"]
        )

        rekord = wyniki[0]

        rekordy_osobiste.append({
            "dyscyplina": d["nazwa"],
            "wynik": rekord["wynik"],
            "data": rekord.get("data", "-"),
            "sezon": rekord.get("sezon", "-")
        })

    return render_template(
        "zawodnik.html",
        zawodnik=zawodnik,
        historia=historia,
        rekordy=rekordy_osobiste,
        dyscypliny=dane["dyscypliny"],
        wybrana_dyscyplina=wybrana_dyscyplina
    )

@app.route("/zawody")
def zawody():
    dane = wczytaj()

    daty = sorted(
        {w.get("data", "brak daty") for w in dane["wyniki"]},
        reverse=True
    )

    return render_template(
        "zawody.html",
        daty=daty
    )


@app.route("/zawody/<data>")
def zawody_dnia(data):
    dane = wczytaj()

    wyniki_dnia = [
        w for w in dane["wyniki"]
        if w.get("data", "brak daty") == data
    ]

    dyscypliny = []
    for d in dane["dyscypliny"]:
        wyniki = [
            w for w in wyniki_dnia
            if w["dyscyplina_id"] == d["id"]
        ]

        if not wyniki:
            continue

        wyniki.sort(
            key=lambda w: w["wynik"],
            reverse=d["wiecej_lepiej"]
        )

        tabela = []
        poprzedni_wynik = None
        osoby_przed = 0

        for i, w in enumerate(wyniki):
            if poprzedni_wynik is None:
                osoby_przed = 0
            elif w["wynik"] != poprzedni_wynik:
                osoby_przed = i

            miejsce = osoby_przed + 1

            zawodnik = next(
                z for z in dane["zawodnicy"]
                if z["id"] == w["zawodnik_id"]
            )

            tabela.append({
                "miejsce": miejsce,
                "zawodnik": zawodnik["imie"],
                "wynik": w["wynik"]
            })

            poprzedni_wynik = w["wynik"]


        dyscypliny.append({
            "nazwa": d["nazwa"],
            "tabela": tabela
        })

    return render_template(
        "zawody_dnia.html",
        data=data,
        dyscypliny=dyscypliny
    )
@app.route("/sezony")
def sezony():
    dane = wczytaj()

    sezony = sorted(
        {w.get("sezon", "brak") for w in dane["wyniki"]}
    )

    return render_template(
        "sezony.html",
        sezony=sezony
    )
@app.route("/sezony/<sezon>")
def sezon(sezon):
    dane = wczytaj()

    wyniki = [
        w for w in dane["wyniki"]
        if w.get("sezon") == sezon
    ]

    # inicjalizacja punktów
    zawodnicy_pkt = {}
    for w in wyniki:
        zawodnicy_pkt.setdefault(w["zawodnik_id"], 0)

    # grupowanie: (sezon, dyscyplina)
    grupy = {}

    for w in wyniki:
        klucz = (w["sezon"], w["dyscyplina_id"])
        grupy.setdefault(klucz, []).append(w)

    # liczenie punktów
    for (sezon_id, dysc_id), grupa in grupy.items():
        dysc = next(d for d in dane["dyscypliny"] if d["id"] == dysc_id)

        grupa.sort(
            key=lambda w: w["wynik"],
            reverse=dysc["wiecej_lepiej"]
        )

        liczba = len(grupa)
        poprzedni = None
        osoby_przed = 0

        for i, w in enumerate(grupa):
            if poprzedni is None:
                osoby_przed = 0
            elif w["wynik"] != poprzedni:
                osoby_przed = i

            pkt = liczba - osoby_przed
            zawodnicy_pkt[w["zawodnik_id"]] += pkt
            poprzedni = w["wynik"]



    ranking = []
    for z in dane["zawodnicy"]:
        if z["id"] in zawodnicy_pkt:
            ranking.append({
                "imie": z["imie"],
                "punkty": zawodnicy_pkt[z["id"]]
            })

    ranking.sort(key=lambda x: x["punkty"], reverse=True)

    return render_template(
        "sezon.html",
        sezon=sezon,
        ranking=ranking
    )
@app.route("/ranking")
def ranking():
    dane = wczytaj()
    wybrana_dyscyplina = request.args.get("dyscyplina")

    ranking = []

    for d in dane["dyscypliny"]:
        # filtr dyscypliny
        if wybrana_dyscyplina and str(d["id"]) != wybrana_dyscyplina:
            continue

        # wszystkie wyniki tej dyscypliny
        wyniki = [
            w for w in dane["wyniki"]
            if w["dyscyplina_id"] == d["id"]
        ]

        if not wyniki:
            continue

        # najlepszy wynik KAŻDEGO zawodnika
        najlepsze = {}

        for w in wyniki:
            zid = w["zawodnik_id"]

            if zid not in najlepsze:
                najlepsze[zid] = w
            else:
                lepszy = w["wynik"] > najlepsze[zid]["wynik"] if d["wiecej_lepiej"] else w["wynik"] < najlepsze[zid]["wynik"]
                if lepszy:
                    najlepsze[zid] = w

        # sortowanie najlepszych startów
        lista = list(najlepsze.values())
        lista.sort(
            key=lambda w: w["wynik"],
            reverse=d["wiecej_lepiej"]
        )

        # budowa tabeli
        poprzedni_wynik = None
        osoby_przed = 0

        for i, w in enumerate(lista):
            if poprzedni_wynik is None:
                osoby_przed = 0
            elif w["wynik"] != poprzedni_wynik:
                osoby_przed = i

            miejsce = osoby_przed + 1

            zawodnik = next(
                z for z in dane["zawodnicy"]
                if z["id"] == w["zawodnik_id"]
            )

            ranking.append({
                "miejsce": miejsce,
                "zawodnik": zawodnik["imie"],
                "zawodnik_id": zawodnik["id"],
                "wynik": w["wynik"],
                "data": w.get("data", "-"),
                "sezon": w.get("sezon", "-"),
                "dyscyplina": d["nazwa"]
            })

            poprzedni_wynik = w["wynik"]


    return render_template(
        "ranking.html",
        ranking=ranking,
        dyscypliny=dane["dyscypliny"],
        wybrana_dyscyplina=wybrana_dyscyplina
    )
@app.route("/regulamin")
def regulamin():
    return render_template("regulamin.html")

if __name__ == "__main__":
    app.run(debug=True)

