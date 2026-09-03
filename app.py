import streamlit as st
import pandas as pd
import os
import json
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Zeiterfassung", page_icon="⏱️", layout="centered")

st.markdown("""
<style>
    .metric-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
    }
    .metric-label { font-size: 0.78rem; color: #888; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 1.6rem; font-weight: 700; color: #1a1a2e; }
    .metric-sub { font-size: 0.8rem; color: #aaa; }
    div[data-testid="stForm"] { border: none; padding: 0; }
</style>
""", unsafe_allow_html=True)

# ── Data ─────────────────────────────────────────────────────────────────────
ENTRIES_FILE  = "zeiterfassung_eintraege.csv"
PROJECTS_FILE = "zeiterfassung_projekte.json"

ENTRY_COLS = ["id", "person", "projekt", "datum", "start", "ende", "stunden", "notiz", "erfasst_am"]

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
    return ["Allgemein"]

def save_projects(projects: list):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects, f)

def next_id(df: pd.DataFrame) -> str:
    if df.empty:
        return "1"
    return str(int(df["id"].astype(int).max()) + 1)

def hhmm_to_float(t: str) -> float:
    h, m = map(int, t.split(":"))
    return round(h + m / 60, 2)

def float_to_hhmm(h: float) -> str:
    hours = int(h)
    minutes = round((h - hours) * 60)
    return f"{hours}h {minutes:02d}m"

# ── Session state ─────────────────────────────────────────────────────────────
if "person" not in st.session_state:
    st.session_state.person = ""

# ── Header ────────────────────────────────────────────────────────────────────
st.title("⏱️ Zeiterfassung")

# Person eingeben (persistent in session)
with st.expander("👤 Wer bist du?" if not st.session_state.person else f"👤 Eingeloggt als: **{st.session_state.person}**", expanded=not st.session_state.person):
    name_input = st.text_input("Dein Name", value=st.session_state.person, placeholder="Max Mustermann")
    if st.button("Bestätigen"):
        if name_input.strip():
            st.session_state.person = name_input.strip()
            st.rerun()
        else:
            st.error("Bitte Namen eingeben.")

if not st.session_state.person:
    st.info("Bitte zuerst deinen Namen eingeben.")
    st.stop()

person = st.session_state.person
projects = load_projects()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_new, tab_my, tab_overview, tab_projects = st.tabs([
    "➕ Zeit erfassen",
    "📋 Meine Einträge",
    "📊 Auswertung",
    "🗂️ Projekte"
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

        notiz = st.text_input("Notiz (optional)", placeholder="Was habe ich gemacht?")

        submitted = st.form_submit_button("⏱️ Zeit speichern", type="primary", use_container_width=True)

    if submitted:
        start_str = f"{start_h:02d}:{start_m:02d}"
        ende_str  = f"{ende_h:02d}:{ende_m:02d}"
        start_dt  = datetime.strptime(start_str, "%H:%M")
        ende_dt   = datetime.strptime(ende_str,  "%H:%M")

        if ende_dt <= start_dt:
            st.error("⚠️ Endzeit muss nach der Startzeit liegen.")
        else:
            diff = (ende_dt - start_dt).seconds / 3600
            df = load_entries()
            new_row = {
                "id":          next_id(df),
                "person":      person,
                "projekt":     projekt,
                "datum":       datum.isoformat(),
                "start":       start_str,
                "ende":        ende_str,
                "stunden":     f"{diff:.2f}",
                "notiz":       notiz.strip(),
                "erfasst_am":  datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_entries(df)
            st.success(f"✅ {float_to_hhmm(diff)} auf **{projekt}** gespeichert!")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – MEINE EINTRÄGE
# ══════════════════════════════════════════════════════════════════════════════
with tab_my:
    st.subheader(f"Einträge von {person}")
    df = load_entries()
    mine = df[df["person"] == person].copy()

    if mine.empty:
        st.info("Noch keine Einträge. Erfasse deine erste Zeit im Tab '➕ Zeit erfassen'.")
    else:
        mine["stunden_num"] = pd.to_numeric(mine["stunden"], errors="coerce").fillna(0)
        total = mine["stunden_num"].sum()

        col_a, col_b = st.columns(2)
        col_a.metric("Total Stunden", float_to_hhmm(total))
        col_b.metric("Anzahl Einträge", len(mine))

        st.markdown("---")

        # Filter
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

                if st.button("🗑️ Löschen", key=f"del_{row['id']}"):
                    df_all = load_entries()
                    df_all = df_all[df_all["id"] != row["id"]]
                    save_entries(df_all)
                    st.success("Eintrag gelöscht.")
                    st.rerun()

        st.markdown("---")
        # CSV Export
        export = mine[["datum","projekt","start","ende","stunden","notiz"]].copy()
        export.columns = ["Datum","Projekt","Start","Ende","Stunden","Notiz"]
        csv = export.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button("⬇️ Meine Einträge exportieren (CSV)", csv,
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

        # Zeitraum Filter
        col_f1, col_f2 = st.columns(2)
        date_from = col_f1.date_input("Von", value=date.today() - timedelta(days=30))
        date_to   = col_f2.date_input("Bis", value=date.today())

        mask = (df["datum_dt"].dt.date >= date_from) & (df["datum_dt"].dt.date <= date_to)
        filtered = df[mask].copy()

        if filtered.empty:
            st.info("Keine Einträge im gewählten Zeitraum.")
        else:
            total_h = filtered["stunden_num"].sum()
            st.metric("Total Stunden im Zeitraum", float_to_hhmm(total_h))
            st.markdown("---")

            # Pro Projekt
            st.markdown("#### ⏱️ Stunden pro Projekt")
            proj_sum = (
                filtered.groupby("projekt")["stunden_num"]
                .sum()
                .reset_index()
                .rename(columns={"stunden_num": "Stunden"})
                .sort_values("Stunden", ascending=False)
            )
            proj_sum["Stunden (formatiert)"] = proj_sum["Stunden"].apply(float_to_hhmm)
            proj_sum["Anteil %"] = (proj_sum["Stunden"] / proj_sum["Stunden"].sum() * 100).round(1)
            st.dataframe(
                proj_sum[["projekt","Stunden (formatiert)","Anteil %"]].rename(columns={"projekt":"Projekt"}),
                use_container_width=True, hide_index=True
            )
            st.bar_chart(proj_sum.set_index("projekt")["Stunden"])

            st.markdown("---")

            # Pro Person pro Projekt
            st.markdown("#### 👥 Stunden pro Person & Projekt")
            pivot = (
                filtered.groupby(["person","projekt"])["stunden_num"]
                .sum()
                .unstack(fill_value=0)
                .round(2)
            )
            pivot.index.name = "Person"
            st.dataframe(pivot, use_container_width=True)

            st.markdown("---")
            # Vollexport
            export_all = filtered[["datum","person","projekt","start","ende","stunden","notiz"]].copy()
            export_all.columns = ["Datum","Person","Projekt","Start","Ende","Stunden","Notiz"]
            csv_all = export_all.to_csv(index=False, sep=";").encode("utf-8-sig")
            st.download_button("⬇️ Alle Einträge exportieren (CSV)", csv_all,
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
        col_p.write(f"📁 {p}")
        if p != "Allgemein":
            if col_d.button("🗑️", key=f"dproj_{p}", help=f"{p} löschen"):
                projects.remove(p)
                save_projects(projects)
                st.success(f"Projekt '{p}' gelöscht.")
                st.rerun()

    st.markdown("---")
    st.markdown("**Neues Projekt erstellen:**")
    with st.form("new_project", clear_on_submit=True):
        new_proj = st.text_input("Projektname", placeholder="z.B. Website Relaunch")
        if st.form_submit_button("➕ Projekt hinzufügen", type="primary"):
            if not new_proj.strip():
                st.error("Bitte einen Projektnamen eingeben.")
            elif new_proj.strip() in projects:
                st.warning("Dieses Projekt existiert bereits.")
            else:
                projects.append(new_proj.strip())
                save_projects(projects)
                st.success(f"Projekt '{new_proj.strip()}' erstellt!")
                st.rerun()
