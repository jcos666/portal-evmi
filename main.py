for item in LISTA_COMPONENTES:
                        item_prev = comp_prev.get(item, {})
                        
                        col_item, col_trae, col_dano, col_med = st.columns([2.5, 2.2, 2.2, 3.1])
                        
                        col_item.write(f"**{item}**")
                        
                        # Si hay datos guardados previamente recuperamos el índice, si no, se queda en None (en blanco)
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

                        # index=None hace que empiece 100% en blanco
                        trae_val = col_trae.radio(
                            f"lbl_t_{item}",
                            options=["SI", "NO"],
                            index=idx_trae,
                            key=f"v3_t_{item}",
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                        
                        dano_val = col_dano.radio(
                            f"lbl_d_{item}",
                            options=["SI", "NO"],
                            index=idx_dano,
                            key=f"v3_d_{item}",
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                        
                        medida_val = col_med.text_input(
                            "", 
                            value=item_prev.get("medidas", ""), 
                            key=f"v3_m_{item}", 
                            label_visibility="collapsed"
                        )
                        
                        # Guardado de la respuesta
                        datos_comp[item] = {
                            "trae_si": (trae_val == "SI"),
                            "trae_no": (trae_val == "NO"),
                            "dano_si": (dano_val == "SI"),
                            "dano_no": (dano_val == "NO"),
                            "medidas": medida_val
                        }
