elif area == "Taller":
        sub_taller = st.radio("Módulo de Taller:", ["Llenar Reporte Técnico", "Ver / Imprimir Reporte Formato Físico"], horizontal=True)

        if sub_taller == "Llenar Reporte Técnico":
            st.header("📋 Llenado de Reporte Técnico de Taller")
            df_rec = pd.read_sql_query("SELECT * FROM recepcion", conn)
            
            if not df_rec.empty:
                sel_folio = st.selectbox("Buscar Equipo por Folio de Recepción:", df_rec["folio"] + " - " + df_rec["cliente"] + " (" + df_rec["equipo"] + ")")
                folio_id = sel_folio.split(" - ")[0]
                rec_data = df_rec[df_rec["folio"] == folio_id].iloc[0]

                df_cot = pd.read_sql_query("SELECT atencion_a FROM cotizaciones_v3 WHERE folio_recepcion = ?", conn, params=(folio_id,))
                contacto_ing = df_cot.iloc[0]['atencion_a'] if not df_cot.empty else "N/A"

                df_rep_prev = pd.read_sql_query("SELECT * FROM reportes_tecnicos WHERE folio_recepcion = ?", conn, params=(folio_id,))
                prev = df_rep_prev.iloc[0] if not df_rep_prev.empty else None

                st.info(f"📌 **CLIENTE:** {rec_data['cliente']} | **INGENIERO / CONTACTO:** {contacto_ing} | **NO. SALIDA:** {rec_data['no_salida']} | **FECHA RECEPCIÓN:** {rec_data['fecha_registro']}")

                with st.form("form_reporte_tecnico"):
                    st.subheader(f"Reporte Técnico para Folio: {folio_id}")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        fecha_reporte = st.text_input("Fecha de Elaboración de Reporte:", value=prev['fecha_reporte'] if prev is not None else datetime.now().strftime("%d/%m/%Y"))
                        tecnico = st.text_input("Técnico que Desarmó:", value=prev['tecnico'] if prev is not None else "")
                        empresa = st.text_input("Empresa / Cliente:", value=rec_data['cliente'])
                        marca = st.text_input("Marca del Equipo:", value=prev['marca'] if prev is not None else "")
                    with c2:
                        ampers = st.text_input("Ampers:", value=prev['ampers'] if prev is not None else "")
                        fases = st.text_input("Fases:", value=prev['fases'] if prev is not None else "")
                        volts = st.text_input("Volts:", value=prev['volts'] if prev is not None else "")
                        rpm = st.text_input("RPM:", value=rec_data['rpm'])
                    with c3:
                        kwhp = st.text_input("KW / HP:", value=rec_data['potencia'])
                        hz = st.text_input("HZ:", value=prev['hz'] if prev is not None else "60")
                        tipo = st.text_input("Tipo:", value=prev['tipo'] if prev is not None else "")
                        rod_lc = st.text_input("Rodamiento LC:", value=prev['rod_lc'] if prev is not None else "")
                        rod_lcc = st.text_input("Rodamiento LCC:", value=prev['rod_lcc'] if prev is not None else "")
                        no_serie = st.text_input("N° de Serie:", value=prev['no_serie'] if prev is not None else "")

                    st.markdown("---")
                    st.subheader("🛠️ Inspección de Componentes y Daños")
                    
                    comp_prev = json.loads(prev['componentes_json']) if (prev is not None and prev['componentes_json']) else {}
                    datos_comp = {}
                    
                    # Encabezados
                    h_comp, h_trae, h_dano, h_med = st.columns([2.5, 1.8, 1.8, 3.5])
                    h_comp.markdown("**COMPONENTE**")
                    h_trae.markdown("**TRAE**")
                    h_dano.markdown("**DAÑOS**")
                    h_med.markdown("**MEDIDAS O EXTRAS**")

                    for item in LISTA_COMPONENTES:
                        item_prev = comp_prev.get(item, {})
                        
                        col_item, col_trae, col_dano, col_med = st.columns([2.5, 1.8, 1.8, 3.5])
                        
                        col_item.write(f"**{item}**")
                        
                        # Valor previo para TRAE (Por defecto 'SI')
                        trae_default_idx = 1 if item_prev.get("trae_no", False) else 0
                        trae_val = col_trae.radio(f"trae_{item}", ["SI", "NO"], index=trae_default_idx, key=f"radio_t_{item}", horizontal=True, label_visibility="collapsed")
                        
                        # Valor previo para DAÑO (Por defecto 'NO')
                        dano_default_idx = 0 if item_prev.get("dano_si", False) else 1
                        dano_val = col_dano.radio(f"dano_{item}", ["SI", "NO"], index=dano_default_idx, key=f"radio_d_{item}", horizontal=True, label_visibility="collapsed")
                        
                        medida_val = col_med.text_input("", value=item_prev.get("medidas", ""), key=f"med_{item}", label_visibility="collapsed")
                        
                        # Guardamos los booleanos internamente para mantener compatibilidad con la impresión
                        datos_comp[item] = {
                            "trae_si": (trae_val == "SI"),
                            "trae_no": (trae_val == "NO"),
                            "dano_si": (dano_val == "SI"),
                            "dano_no": (dano_val == "NO"),
                            "medidas": medida_val
                        }

                    st.markdown("---")
                    observaciones = st.text_area("OBSERVACIONES:", value=prev['observaciones'] if prev is not None else "")
                    recomendaciones = st.text_area("RECOMENDACIONES:", value=prev['recomendaciones'] if prev is not None else "")

                    st.markdown("---")
                    st.subheader("⚡ Valores Eléctricos")
                    
                    st.write("**VALORES DE ENTRADA**")
                    ce1, ce2, ce3, ce4 = st.columns(4)
                    in_megohms = ce1.text_input("Megaohms (Entrada):", value=prev['in_megohms'] if prev is not None else "")
                    in_volts = ce2.text_input("Volts (Entrada):", value=prev['in_volts'] if prev is not None else "")
                    in_ampers = ce3.text_input("Amperes (Entrada):", value=prev['in_ampers'] if prev is not None else "")
                    in_ohms = ce4.text_input("Ohms 1-2-3-4 (Entrada):", value=prev['in_ohms'] if prev is not None else "")

                    st.write("**VALORES DE SALIDA**")
                    cs1, cs2, cs3, cs4 = st.columns(4)
                    out_megohms = cs1.text_input("Megaohms (Salida):", value=prev['out_megohms'] if prev is not None else "")
                    out_volts = cs2.text_input("Volts (Salida):", value=prev['out_volts'] if prev is not None else "")
                    out_ampers = cs3.text_input("Amperes (Salida):", value=prev['out_ampers'] if prev is not None else "")
                    out_ohms = cs4.text_input("Ohms 1-2-3-4 (Salida):", value=prev['out_ohms'] if prev is not None else "")

                    if st.form_submit_button("💾 Guardar Reporte Técnico"):
                        comp_json = json.dumps(datos_comp)
                        c = conn.cursor()
                        c.execute('''
                            INSERT OR REPLACE INTO reportes_tecnicos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        ''', (folio_id, fecha_reporte, tecnico, empresa, marca, ampers, fases, volts, rpm, kwhp, hz, tipo,
                              rod_lc, rod_lcc, no_serie, comp_json, observaciones, recomendaciones,
                              in_megohms, in_volts, in_ampers, in_ohms, out_megohms, out_volts, out_ampers, out_ohms))
                        c.execute("UPDATE recepcion SET estatus=? WHERE folio=?", ("Inspeccionado en Taller", folio_id))
                        conn.commit()
                        st.success(f"Reporte técnico para {folio_id} guardado con éxito.")
            else:
                st.info("No hay equipos en recepción.")
