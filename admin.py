import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


# ================== DANE ==================

def wczytaj_dane():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def zapisz_dane(dane):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=2, ensure_ascii=False)

dane = wczytaj_dane()


# ================== OKNO ==================

root = tk.Tk()
root.title("Panel zawodów")
root.geometry("600x500")


# ================== AUTOCOMPLETE ZAWODNIK ==================

tk.Label(root, text="Dodaj wynik", font=("Arial", 11, "bold")).pack(pady=10)

ramka_zawodnik = tk.Frame(root)
ramka_zawodnik.pack(fill="x", padx=10)

tk.Label(ramka_zawodnik, text="Imię zawodnika").pack(anchor="w")

ramka_input = tk.Frame(ramka_zawodnik)
ramka_input.pack(fill="x")

zawodnik_var = tk.StringVar()
imiona = [z["imie"] for z in dane["zawodnicy"]]

entry_zawodnik = tk.Entry(ramka_input, textvariable=zawodnik_var)
entry_zawodnik.grid(row=0, column=0, sticky="ew")

btn_dodaj_zawodnika = tk.Button(
    ramka_input,
    text="➕",
    width=4,
    state="disabled"
)
btn_dodaj_zawodnika.grid(row=0, column=1, padx=5)

ramka_input.columnconfigure(0, weight=1)

lista = tk.Listbox(ramka_zawodnik, height=5)
lista.pack(fill="x")
lista.pack_forget()


def aktualizuj_liste(*args):
    tekst = zawodnik_var.get().lower()
    lista.delete(0, tk.END)

    if not tekst:
        lista.pack_forget()
        return

    pasujace = [i for i in imiona if i.lower().startswith(tekst)]

    if not pasujace:
        lista.pack_forget()
        return

    for imie in pasujace:
        lista.insert(tk.END, imie)

    lista.pack(fill="x")


def wybierz_z_listy(event=None):
    if not lista.curselection():
        return
    imie = lista.get(lista.curselection())
    zawodnik_var.set(imie)
    lista.pack_forget()
    entry_zawodnik.focus_set()


def sprawdz_zawodnika(*args):
    imie = zawodnik_var.get().strip().lower()
    istnieje = any(z["imie"].lower() == imie for z in dane["zawodnicy"])
    btn_dodaj_zawodnika.config(
        state="normal" if imie and not istnieje else "disabled"
    )


def dodaj_nowego_zawodnika():
    imie = zawodnik_var.get().strip()
    if not imie:
        return

    dane["zawodnicy"].append({
        "id": len(dane["zawodnicy"]) + 1,
        "imie": imie,
        "punkty": 0
    })

    zapisz_dane(dane)
    imiona.append(imie)
    btn_dodaj_zawodnika.config(state="disabled")
    messagebox.showinfo("OK", f"Dodano zawodnika: {imie}")


btn_dodaj_zawodnika.config(command=dodaj_nowego_zawodnika)

lista.bind("<Return>", wybierz_z_listy)
lista.bind("<Double-Button-1>", wybierz_z_listy)

zawodnik_var.trace_add("write", aktualizuj_liste)
zawodnik_var.trace_add("write", sprawdz_zawodnika)

# ================== WYNIK ==================
tk.Label(root, text="Wynik").pack(anchor="w", padx=10)
entry_wynik = tk.Entry(root)
entry_wynik.pack(fill="x", padx=10)

# tk.Label(root, text="Sezon").pack(anchor="w", padx=10)
# entry_sezon = tk.Entry(root)
# entry_sezon.insert(0, "1")
# entry_sezon.pack(fill="x", padx=10)


def zapisz_wynik():
    
    try:
        wynik = float(entry_wynik.get())
    except ValueError:
        return

    zawodnik = next(z for z in dane["zawodnicy"] if z["imie"] == zawodnik_var.get())
    dysc = next(d for d in dane["dyscypliny"] if d["nazwa"] == dyscyplina_var.get())

    dane["wyniki"].append({
        "zawodnik_id": zawodnik["id"],
        "dyscyplina_id": dysc["id"],
        "wynik": wynik,
        "data": date.today().isoformat(),
        "sezon": str(dane["sezony"]["aktywny"])

    })

    zapisz_dane(dane)
    entry_wynik.delete(0, tk.END)
    zawodnik_var.set("")
    entry_zawodnik.focus_set()
    

# ================== DYSCYPLINA ==================
tk.Label(root, text="Dyscyplina").pack(anchor="w", padx=10, pady=(15, 0))

ramka_dyscyplina = tk.Frame(root)
ramka_dyscyplina.pack(fill="x", padx=10)

dyscyplina_var = tk.StringVar()

combo_dyscyplina = ttk.Combobox(
    ramka_dyscyplina,
    textvariable=dyscyplina_var,
    values=[d["nazwa"] for d in dane["dyscypliny"]]
)
combo_dyscyplina.grid(row=0, column=0, sticky="ew")
combo_dyscyplina.current(0)

btn_dodaj_dyscypline = tk.Button(
    ramka_dyscyplina,
    text="➕",
    width=4,
    state="disabled"
)
btn_dodaj_dyscypline.grid(row=0, column=1, padx=5)

ramka_dyscyplina.columnconfigure(0, weight=1)

wiecej_lepiej_var = tk.BooleanVar(value=True)
tk.Checkbutton(
    root,
    text="Więcej = lepiej",
    variable=wiecej_lepiej_var
).pack(anchor="w", padx=10)


def sprawdz_dyscypline(*args):
    nazwa = dyscyplina_var.get().strip().lower()
    istnieje = any(d["nazwa"].lower() == nazwa for d in dane["dyscypliny"])
    btn_dodaj_dyscypline.config(
        state="normal" if nazwa and not istnieje else "disabled"
    )


def dodaj_nowa_dyscypline():
    nazwa = dyscyplina_var.get().strip()
    if not nazwa:
        return

    dane["dyscypliny"].append({
        "id": len(dane["dyscypliny"]) + 1,
        "nazwa": nazwa,
        "wiecej_lepiej": wiecej_lepiej_var.get()
    })

    zapisz_dane(dane)
    combo_dyscyplina["values"] = [d["nazwa"] for d in dane["dyscypliny"]]
    btn_dodaj_dyscypline.config(state="disabled")
    messagebox.showinfo("OK", f"Dodano dyscyplinę: {nazwa}")


dyscyplina_var.trace_add("write", sprawdz_dyscypline)
btn_dodaj_dyscypline.config(command=dodaj_nowa_dyscypline)





btn_zapisz = tk.Button(root, text="Zapisz wynik", command=zapisz_wynik)
btn_zapisz.pack(pady=15)

def focus_lista(event=None):
    if lista.size() == 0:
        return
    lista.focus_set()
    lista.selection_clear(0, tk.END)
    lista.selection_set(0)
    return "break"
entry_zawodnik.bind("<Down>", focus_lista)
lista.bind("<Up>", lambda e: "break")
lista.bind("<Down>", lambda e: None)



root.bind("<Return>", lambda event: zapisz_wynik())

def zamknij_sezon():
    aktualny = dane["sezony"]["aktywny"]

    if not messagebox.askyesno(
        "Zamknąć sezon?",
        f"Czy na pewno zamknąć sezon {aktualny}?\nTej operacji nie można cofnąć."
    ):
        return

    dane["sezony"]["zamkniete"].append(aktualny)
    dane["sezony"]["aktywny"] += 1

    zapisz_dane(dane)

    messagebox.showinfo(
        "Sezon zamknięty",
        f"Rozpoczęto sezon {dane['sezony']['aktywny']}"
    )
tk.Button(
    root,
    text="🔒 Zamknij sezon",
    bg="#cc4444",
    fg="white",
    font=("Arial", 10, "bold"),
    command=zamknij_sezon
).pack(pady=10)


root.mainloop()