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

