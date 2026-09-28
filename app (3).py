 import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Walter Meier – Zeiterfassung", page_icon=None, layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .wm-header {
        background: #1a1a1a;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .wm-logo {
        font-size: 1.4rem;
        font-weight: 800;
        color: #C4D600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .wm-subtitle {
        color: #999;
        font-size: 0.85rem;
        font-weight: 400;
    }

    h1 { color: #1a1a1a !important; font-weight: 800 !important; }
    h2, h3 { color: #1a1a1a !important; font-weight: 700 !important; }

    div[data-testid="stButton"] button,
    div[data-testid="stFormSubmitButton"] button {
        background-color: #C4D600 !important;
        color: #1a1a1a !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 4px !important;
    }
    div[data-testid="stButton"] button:hover,
    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #a8b800 !important;
        color: #1a1a1a !important;
    }

    div.stDownloadButton > button {
        background-color: #1a1a1a !important;
        color: #C4D600 !important;
        border: 2px solid #C4D600 !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
    }
    div.stDownloadButton > button:hover {
        background-color: #333 !important;
    }

    div[data-testid="stTabs"] button[role="tab"],
    div[data-testid="stTabs"] button[role="tab"] span,
    div[data-testid="stTabs"] button[role="tab"] p {
        color: #C4D600 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] span,
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {
        color: #C4D600 !important;
        border-bottom-color: #C4D600 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetric"] {
        background: #f9fbe7;
        border-left: 4px solid #C4D600;
        border-radius: 4px;
        padding: 0.75rem 1rem;
    }
    div[data-testid="stMetricLabel"] { color: #555 !important; font-weight: 600 !important; }
    div[data-testid="stMetricValue"] { color: #1a1a1a !important; font-weight: 800 !important; }

    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0 !important;
        border-radius: 4px !important;
        border-left: 3px solid #C4D600 !important;
    }

    div[data-testid="stAlert"] { border-radius: 4px !important; }
    div[data-testid="stForm"] { border: none; padding: 0; }

    input[type="text"], input[type="email"], input[type="number"],
    input[type="password"], textarea {
        border: 1.5px solid #d0d0d0 !important;
        border-radius: 4px !important;
        font-family: 'Inter', sans-serif !important;
        transition: border-color 0.15s !important;
    }
    input:focus, textarea:focus {
        border-color: #C4D600 !important;
        box-shadow: 0 0 0 2px rgba(196,214,0,0.18) !important;
        outline: none !important;
    }

    button[data-testid="stNumberInputStepUp"],
    button[data-testid="stNumberInputStepDown"] {
        background-color: #1a1a1a !important;
        color: #C4D600 !important;
        border: none !important;
        border-radius: 3px !important;
    }

    div[data-baseweb="select"] > div {
        border: 1.5px solid #d0d0d0 !important;
        border-radius: 4px !important;
        font-family: 'Inter', sans-serif !important;
    }
    div[data-baseweb="select"] > div:focus-within {
        border-color: #C4D600 !important;
        box-shadow: 0 0 0 2px rgba(196,214,0,0.18) !important;
    }

    div[data-testid="stDateInput"] input {
        border: 1.5px solid #d0d0d0 !important;
        border-radius: 4px !important;
    }
    div[data-testid="stDateInput"] input:focus {
        border-color: #C4D600 !important;
        box-shadow: 0 0 0 2px rgba(196,214,0,0.18) !important;
    }

    label[data-testid="stWidgetLabel"] p,
    div[data-testid="stWidgetLabel"] p {
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        color: #444 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    .wm-footer {
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 2px solid #C4D600;
        text-align: center;
        font-size: 0.75rem;
        color: #aaa;
    }
    .wm-footer strong { color: #1a1a1a; }
</style>

<div class="wm-header">
  <div class="wm-logo">WALTER MEIER</div>
  <div class="wm-subtitle">Zeiterfassung</div>
</div>
""", unsafe_allow_html=True)

# ── Dateien ───────────────────────────────────────────────────────────────────
ENTRIES_FILE   = "zeiterfassung_eintraege.csv"
PROJECTS_FILE  = "zeiterfassung_projekte.json"
PASSWORDS_FILE = "zeiterfassung_passwords.json"

ENTRY_COLS = ["id", "person", "projekt", "datum", "start", "ende", "stunden", "notiz", "erfasst_am"]
DEFAULT_PROJECTS = ["Meeting", "Tasks", "Workshop"]

def load_entries() -> pd.DataFrame:
    if os.path.exists(ENTRIES_FILE):
        df = pd.read_csv(ENTRIES_FILE, dtype=str)
        for c in ENTRY_COLS:
            if c not in df.columns:
                df[c] = ""
        return df[ENTRY_COLS]
    return pd.DataFrame(columns=ENTRY_COLS)

def save_entries(df: pd.DataFrame):
    df.to_csv(ENTRIES_FILE, index=False)

def load_projects() -> list:
    if os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE) as f:
            return json.load(f)
    return DEFAULT_PROJECTS.copy()

def save_projects(projects: list):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects, f)

def load_passwords() -> dict:
    if os.path.exists(PASSWORDS_FILE):
        with open(PASSWORDS_FILE) as f:
            return json.load(f)
    return {}

def save_passwords(passwords: dict):
    with open(PASSWORDS_FILE, "w") as f:
        json.dump(passwords, f)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def next_id(df: pd.DataFrame) -> str:
    if df.empty:
        return "1"
    return str(int(df["id"].astype(int).max()) + 1)

def float_to_hhmm(h: float) -> str:
    hours = int(h)
    minutes = round((h - hours) * 60)
    return f"{hours}h {minutes:02d}m"

# ── Session state ─────────────────────────────────────────────────────────────
for key in ["person", "authenticated"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key == "person" else False

# ── Login / Passwort ──────────────────────────────────────────────────────────
st.title("Zeiterfassung")

if not st.session_state.person or not st.session_state.authenticated:
    passwords = load_passwords()

    with st.form("login_form"):
        st.markdown("**Anmelden**")
        name_input = st.text_input("Name", placeholder="Max Mustermann")
        pw_input   = st.text_input("Passwort", type="password")
        submitted  = st.form_submit_button("[ > ] Anmelden", use_container_width=True)

    if submitted:
        name = name_input.strip()
        pw   = pw_input.strip()
        if not name:
            st.error("Bitte Namen eingeben.")
        elif not pw:
            st.error("Bitte Passwort eingeben.")
        elif name not in passwords:
            # Erstes Login: Passwort setzen
            passwords[name] = hash_pw(pw)
            save_passwords(passwords)
            st.session_state.person = name
            st.session_state.authenticated = True
            st.success(f"Willkommen {name}! Passwort wurde gesetzt.")
            st.rerun()
        elif passwords[name] == hash_pw(pw):
            st.session_state.person = name
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")

    st.caption("Erster Login: Passwort wird automatisch gesetzt.")
    st.stop()

person   = st.session_state.person
projects = load_projects()

col_title, col_logout = st.columns([6, 1])
col_title.caption(f"Eingeloggt als **{person}**")
if col_logout.button("Logout"):
    st.session_state.person = ""
    st.session_state.authenticated = False
    st.rerun()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_new, tab_my, tab_overview, tab_projects = st.tabs([
    "+ Zeit erfassen",
    "= Meine Einträge",
    "~ Auswertung",
    "# Projekte"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – ZEIT ERFASSEN
# ══════════════════════════════════════════════════════════════════════════════
with tab_new:
    st.subheader("Neue Zeit erfassen")

    with st.form("new_entry", clear_on_submit=True):
        projekt = st.selectbox("Projekt *", projects)
        datum   = st.date_input("Datum *", value=date.today())

        col1, col2 = st.columns(2)
        start_h = col1.number_input("Start – Stunde", min_value=0, max_value=23, value=8)
        start_m = col1.number_input("Start – Minute", min_value=0, max_value=59, value=0, step=15)
        ende_h  = col2.number_input("Ende – Stunde",  min_value=0, max_value=23, value=17)
        ende_m  = col2.number_input("Ende – Minute",  min_value=0, max_value=59, value=0, step=15)

        notiz     = st.text_input("Notiz (optional)", placeholder="Was habe ich gemacht?")
        submitted = st.form_submit_button("[ + ] Zeit speichern", use_container_width=True)

    if submitted:
        start_str = f"{start_h:02d}:{start_m:02d}"
        ende_str  = f"{ende_h:02d}:{ende_m:02d}"
        start_dt  = datetime.strptime(start_str, "%H:%M")
        ende_dt   = datetime.strptime(ende_str,  "%H:%M")

        if ende_dt <= start_dt:
            st.error("Endzeit muss nach der Startzeit liegen.")
        else:
            diff = (ende_dt - start_dt).seconds / 3600
            df = load_entries()
            new_row = {
                "id":         next_id(df),
                "person":     person,
                "projekt":    projekt,
                "datum":      datum.isoformat(),
                "start":      start_str,
                "ende":       ende_str,
                "stunden":    f"{diff:.2f}",
                "notiz":      notiz.strip(),
                "erfasst_am": datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_entries(df)
            st.success(f"[ok] {float_to_hhmm(diff)} auf **{projekt}** gespeichert!")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – MEINE EINTRÄGE
# ══════════════════════════════════════════════════════════════════════════════
with tab_my:
    st.subheader(f"Einträge von {person}")
    df   = load_entries()
    mine = df[df["person"] == person].copy()

    if mine.empty:
        st.info("Noch keine Einträge.")
    else:
        mine["stunden_num"] = pd.to_numeric(mine["stunden"], errors="coerce").fillna(0)
        total = mine["stunden_num"].sum()

        col_a, col_b = st.columns(2)
        col_a.metric("Total Stunden", float_to_hhmm(total))
        col_b.metric("Anzahl Einträge", len(mine))

        st.markdown("---")

        filter_proj = st.selectbox("Projekt filtern", ["Alle"] + sorted(mine["projekt"].unique().tolist()), key="my_filter")
        if filter_proj != "Alle":
            mine = mine[mine["projekt"] == filter_proj]

        for _, row in mine.sort_values("datum", ascending=False).iterrows():
            h = float(row["stunden"])
            with st.expander(f"**{row['datum']}** · {row['projekt']} · {float_to_hhmm(h)}", expanded=False):
                st.write(f"**Zeit:** {row['start']} – {row['ende']}")
                st.write(f"**Projekt:** {row['projekt']}")
                if row["notiz"]:
                    st.write(f"**Notiz:** {row['notiz']}")
                st.caption(f"Erfasst am {row['erfasst_am']}")
                if st.button("[ x ] Löschen", key=f"del_{row['id']}"):
                    df_all = load_entries()
                    df_all = df_all[df_all["id"] != row["id"]]
                    save_entries(df_all)
                    st.success("Eintrag gelöscht.")
                    st.rerun()

        st.markdown("---")
        export = mine[["datum","projekt","start","ende","stunden","notiz"]].copy()
        export.columns = ["Datum","Projekt","Start","Ende","Stunden","Notiz"]
        csv = export.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button("[ v ] Meine Einträge exportieren (CSV)", csv,
                           f"zeit_{person}_{date.today()}.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – AUSWERTUNG
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:
    st.subheader("Auswertung – alle Personen")
    df = load_entries()

    if df.empty:
        st.info("Noch keine Einträge vorhanden.")
    else:
        df["stunden_num"] = pd.to_numeric(df["stunden"], errors="coerce").fillna(0)
        df["datum_dt"]    = pd.to_datetime(df["datum"], errors="coerce")
        df["monat"]       = df["datum_dt"].dt.to_period("M").astype(str)

        # Zeitraum Filter
        col_f1, col_f2 = st.columns(2)
        date_from = col_f1.date_input("Von", value=date.today() - timedelta(days=90))
        date_to   = col_f2.date_input("Bis", value=date.today())

        mask     = (df["datum_dt"].dt.date >= date_from) & (df["datum_dt"].dt.date <= date_to)
        filtered = df[mask].copy()

        if filtered.empty:
            st.info("Keine Einträge im gewählten Zeitraum.")
        else:
            total_h = filtered["stunden_num"].sum()
            st.metric("Total Stunden im Zeitraum", float_to_hhmm(total_h))
            st.markdown("---")

            # ── Stunden pro Projekt (gesamt) ──────────────────────────────
            st.markdown("#### Stunden pro Projekt (gesamt)")
            proj_sum = (
                filtered.groupby("projekt")["stunden_num"]
                .sum().reset_index()
                .rename(columns={"stunden_num": "Stunden"})
                .sort_values("Stunden", ascending=False)
            )
            proj_sum["Formatiert"] = proj_sum["Stunden"].apply(float_to_hhmm)
            proj_sum["Anteil %"]   = (proj_sum["Stunden"] / proj_sum["Stunden"].sum() * 100).round(1)
            st.dataframe(
                proj_sum[["projekt","Formatiert","Anteil %"]].rename(columns={"projekt":"Projekt"}),
                use_container_width=True, hide_index=True
            )
            st.bar_chart(proj_sum.set_index("projekt")["Stunden"], color="#C4D600")

            st.markdown("---")

            # ── Stunden pro Projekt pro Monat ─────────────────────────────
            st.markdown("#### Stunden pro Projekt pro Monat")
            monat_proj = (
                filtered.groupby(["monat","projekt"])["stunden_num"]
                .sum().unstack(fill_value=0).round(2)
            )
            monat_proj.index.name = "Monat"
            st.dataframe(monat_proj, use_container_width=True)

            # Balkendiagramm pro Monat (total)
            monat_total = filtered.groupby("monat")["stunden_num"].sum().reset_index()
            monat_total.columns = ["Monat","Stunden"]
            st.bar_chart(monat_total.set_index("Monat")["Stunden"], color="#C4D600")

            st.markdown("---")

            # ── Pro Person & Projekt ───────────────────────────────────────
            st.markdown("#### Stunden pro Person & Projekt")
            pivot = (
                filtered.groupby(["person","projekt"])["stunden_num"]
                .sum().unstack(fill_value=0).round(2)
            )
            pivot.index.name = "Person"
            st.dataframe(pivot, use_container_width=True)

            st.markdown("---")
            export_all = filtered[["datum","person","projekt","start","ende","stunden","notiz"]].copy()
            export_all.columns = ["Datum","Person","Projekt","Start","Ende","Stunden","Notiz"]
            csv_all = export_all.to_csv(index=False, sep=";").encode("utf-8-sig")
            st.download_button("[ v ] Alle Einträge exportieren (CSV)", csv_all,
                               f"zeiterfassung_export_{date.today()}.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 – PROJEKTE VERWALTEN
# ══════════════════════════════════════════════════════════════════════════════
with tab_projects:
    st.subheader("Projekte verwalten")
    projects = load_projects()

    st.markdown("**Bestehende Projekte:**")
    for p in projects:
        col_p, col_d = st.columns([4, 1])
        col_p.write(f"[ - ] {p}")
        if p not in DEFAULT_PROJECTS:
            if col_d.button("[ x ]", key=f"dproj_{p}", help=f"{p} löschen"):
                projects.remove(p)
                save_projects(projects)
                st.success(f"Projekt '{p}' gelöscht.")
                st.rerun()

    st.markdown("---")
    st.markdown("**Neues Projekt erstellen:**")
    with st.form("new_project", clear_on_submit=True):
        new_proj = st.text_input("Projektname", placeholder="z.B. Kundenpräsentation")
        if st.form_submit_button("[ + ] Projekt hinzufügen", use_container_width=True):
            if not new_proj.strip():
                st.error("Bitte einen Projektnamen eingeben.")
            elif new_proj.strip() in projects:
                st.warning("Dieses Projekt existiert bereits.")
            else:
                projects.append(new_proj.strip())
                save_projects(projects)
                st.success(f"Projekt '{new_proj.strip()}' erstellt!")
                st.rerun()

    st.markdown("---")
    st.markdown("**Passwort ändern:**")
    with st.form("change_pw", clear_on_submit=True):
        old_pw  = st.text_input("Aktuelles Passwort", type="password")
        new_pw  = st.text_input("Neues Passwort", type="password")
        new_pw2 = st.text_input("Neues Passwort bestätigen", type="password")
        if st.form_submit_button("[ > ] Passwort ändern", use_container_width=True):
            passwords = load_passwords()
            if passwords.get(person) != hash_pw(old_pw):
                st.error("Aktuelles Passwort falsch.")
            elif not new_pw:
                st.error("Neues Passwort darf nicht leer sein.")
            elif new_pw != new_pw2:
                st.error("Passwörter stimmen nicht überein.")
            else:
                passwords[person] = hash_pw(new_pw)
                save_passwords(passwords)
                st.success("Passwort erfolgreich geändert.")

st.markdown('<div class="wm-footer"><strong>WALTER MEIER</strong> · Zeiterfassung</div>', unsafe_allow_html=True)
       
