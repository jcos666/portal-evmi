st.markdown("---")
                    st.subheader("🛠️ Inspección de Componentes y Daños")
                    
                    comp_prev = json.loads(prev['componentes_json']) if (prev is not None and prev['componentes_json']) else {}
                    datos_comp = {}
                    
                    # Encabezados
                    h_comp, h_trae, h_dano, h_med = st.columns([2.5, 2.2, 2.2, 3.1])
                    h_comp.markdown("**COMPONENTE**")
                    h_trae.markdown("**TRAE**")
                    h_dano.markdown("**DAÑOS**")
                    h_med.markdown("**MEDIDAS O EXTRAS**")

                    for item in LISTA_COMPONENTES:
                        item_prev = comp_prev.get(item, {})
                        
                        col_item, col_trae, col_dano, col_med = st.columns([2.5, 2.2, 2.2, 3.1])
                        
                        col_item.write(f"**{item}**")
                        
                        # Carga selección previa si existe, si no, inicia sin nada seleccionado (index=None)
                        idx_trae = None
                        if item_prev.get("trae_si"):
                            idx_trae = 0
                        elif item_prev.get("trae_no"):
                            idx_trae = 1
                            
                        idx_dano = None
                        if item_prev.get("dano_si"):
                            idx_dano = 0
                        elif item_prev.get("dano_no"):
                            idx_dano = 1

                        # Al usar index=None las casillas aparecen desmarcadas por defecto
                        trae_val = col_trae.radio(
                            f"t_{item}",
                            options=["SI", "NO"],
                            index=idx_trae,
                            key=f"v4_t_{item}",
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                        
                        dano_val = col_dano.radio(
                            f"d_{item}",
                            options=["SI", "NO"],
                            index=idx_dano,
                            key=f"v4_d_{item}",
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                        
                        medida_val = col_med.text_input(
                            "", 
                            value=item_prev.get("medidas", ""), 
                            key=f"v4_m_{item}", 
                            label_visibility="collapsed"
                        )
                        
                        # Mapeo idéntico para la base de datos
                        datos_comp[item] = {
                            "trae_si": (trae_val == "SI"),
                            "trae_no": (trae_val == "NO"),
                            "dano_si": (dano_val == "SI"),
                            "dano_no": (dano_val == "NO"),
                            "medidas": medida_val
                        }
