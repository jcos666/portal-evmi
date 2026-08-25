import streamlit as st
import sqlite3
import json
from datetime import datetime, date

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Portal EVMI - Control Industrial",
    page_icon="⚙️",
    layout="wide"
)

# Listas de componentes según el área
COMPONENTES_TALLER = [
    "CHAVETA", "CAJA DE CONEXIONES", "VENTILADOR", "CUBIERTA VENTILADOR",
    "TAPA LC", "TAPA LCC", "EMBOBINADO", "ROTOR / FLECHA", "CAPACITOR",
    "INTERRUPTOR CENTRÍFUGO", "PLATINAS", "CAJA DE TRANSMISIÓN / ENGRANES"
]

COMPONENTES_EMBOBINADO = [
    "DIÁMETRO DE NÚCLEO", "LARGO DE NÚCLEO", "NÚMERO DE RANURAS", "PASO DE BOBINA",
    "CALIBRE DE ALAMBRE", "NÚMERO DE HILOS", "CONEXIÓN (ESTRELLA / DELTA)", "ESPIRAS POR RANURA"
]

# ==========================================
# BASE DE DATOS (SQLITE)
# ==========================================
def init_db():
    conn = sqlite3.connect("evmi_control.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT,
            num_salida TEXT,
            cliente TEXT,
            equipo TEXT,
            marca TEXT,
            modelo TEXT,
            hp_kw TEXT,
            rpm TEXT,
            voltaje TEXT,
            amperaje TEXT,
            observaciones TEXT,
            componentes_json TEXT,
            area TEXT,
            falla_reportada TEXT,
            trabajo_realizado TEXT,
            fecha_recepcion TEXT,
            fecha_mecanica TEXT,
            fecha_embobinado TEXT,
            resp_recepcion TEXT,
            resp_mecanica TEXT,
            resp_embobinado TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def generar_folio_autoincremental():
    conn = sqlite3.connect("evmi_control.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT id FROM reportes ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    siguiente_id = (row[0] + 1) if row else 1
    anio_actual = datetime.now().year
    return f"EVMI-{anio_actual}-{siguiente_id:04d}"

def guardar_reporte(datos):
    conn = sqlite3.connect("evmi_control.db", check_same_thread=False)
    c = conn.cursor()
    
    # Obtener valores existentes para mantener historial de fechas y responsables
    c.execute("""
        SELECT fecha_recepcion, fecha_mecanica, fecha_embobinado, 
               resp_recepcion, resp_mecanica, resp_embobinado 
        FROM reportes WHERE folio = ? ORDER BY id DESC LIMIT 1
    """, (datos.get('folio'),))
    existente = c.fetchone()
    
    f_rec = datos.get('fecha_recepcion') or (existente[0] if existente else str(date.today()))
    f_mec = datos.get('fecha_mecanica') or (existente[1] if existente else "")
    f_emb = datos.get('fecha_embobinado') or (existente[2] if existente else "")
    
    r_rec = datos.get('resp_recepcion') or (existente[3] if existente else "")
    r_mec = datos.get('resp_mecanica') or (existente[4] if existente else "")
    r_emb = datos.get('resp_embobinado') or (existente[5] if existente else "")

    c.execute('''
        INSERT INTO reportes (
            folio, num_salida, cliente, equipo, marca, modelo, hp_kw, rpm, voltaje, amperaje,
            observaciones, componentes_json, area, falla_reportada, trabajo_realizado,
            fecha_recepcion, fecha_mecanica, fecha_embobinado,
            resp_recepcion, resp_mecanica, resp_embobinado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datos.get('folio'), datos.get('num_salida'), datos.get('cliente'), datos.get('equipo'),
        datos.get('marca'), datos.get('modelo'), datos.get('hp_kw'),
        datos.get('rpm'), datos.get('voltaje'), datos.get('amperaje'),
        datos.get('observaciones'), json.dumps(datos.get('componentes', {})),
        datos.get('area'), datos.get('falla_reportada'), datos.get('trabajo_realizado'),
        f_rec, f_mec, f_emb,
        r_rec, r_mec, r_emb
    ))
    conn.commit()
    conn.close()

def obtener_ultimo_reporte(folio):
    conn = sqlite3.connect("evmi_control.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM reportes WHERE folio = ? ORDER BY id DESC LIMIT 1", (folio,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0], "folio": row[1], "num_salida": row[2], "cliente": row[3],
            "equipo": row[4], "marca": row[5], "modelo": row[6], "hp_kw": row[7],
            "rpm": row[8], "voltaje": row[9], "amperaje": row[10], "observaciones": row[11],
            "componentes_json": row[12], "area": row[13], "falla_reportada": row[14],
            "trabajo_realizado": row[15], "fecha_recepcion": row[16],
            "fecha_mecanica": row[17], "fecha_embobinado": row[18],
            "resp_recepcion": row[19] if len(row) > 19 else "",
            "resp_mecanica": row[20] if len(row) > 20 else "",
            "resp_embobinado": row[21] if len(row) > 21 else "",
            "fecha": row[22] if len(row) > 22 else ""
        }
    return None

def calcular_dias(f_inicio, f_fin):
    if not f_inicio or not f_fin:
        return "-"
    try:
        d1 = datetime.strptime(f_inicio, "%Y-%m-%d")
        d2 = datetime.strptime(f_fin, "%Y-%m-%d")
        dias = (d2 - d1).days
        return f"{dias} día(s)" if dias >= 0 else "Fecha inconsistente"
    except Exception:
        return "-"

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("⚙️ Portal EVMI - Control Industrial")
st.write("Sistema de Gestión de Reportes Técnicos y Control Tiempos de Servicio")

menu = st.sidebar.radio("Navegación", ["Nuevo Reporte / Inspección", "Histórico de Reportes"])

if menu == "Nuevo Reporte / Inspección":
    st.header("📋 Registro de Servicio Técnico")
    
    col_f1, col_f2 = st.columns([2, 1])
    folio_input = col_f1.text_input("Buscar Folio / No. Orden para actualizar estado:")
    
    prev = None
    if folio_input:
        prev = obtener_ultimo_reporte(folio_input.strip())
        if prev:
            st.info(f"ℹ️ Se encontraron datos previos del Folio {folio_input}. Actualizando información...")
        else:
            st.caption("No se encontraron registros previos. Se iniciará una nueva orden.")

    area = st.radio(
        "Área que diligencia el formato:", 
        ["Recepción / Oficina", "Taller (Mecánica / Inspección)", "Embobinado"], 
        horizontal=True
    )

    with st.form("form_reporte"):
        st.subheader("📌 Datos Generales del Equipo, Cliente y Control de Fechas")
        
        folio_defecto = prev['folio'] if prev else (folio_input if folio_input else generar_folio_autoincremental())
        
        c1, c2, c3 = st.columns([2, 2, 2])
        folio = c1.text_input("Folio (Auto-generado / Modificable) *", value=folio_defecto)
        num_salida = c2.text_input("Número de Salida / Remisión", value=prev['num_salida'] if (prev and prev.get('num_salida')) else "")
        cliente = c3.text_input("Cliente *", value=prev['cliente'] if prev else "")
        
        # Bloque de Fechas y Responsables por Área
        st.markdown("**📅 Control de Fechas y Responsables de Registro**")
        
        f_col1, f_col2, f_col3 = st.columns(3)
        
        # 1. RECEPCIÓN / OFICINA
        str_f_rec = prev.get('fecha_recepcion') if (prev and prev.get('fecha_recepcion')) else str(date.today())
        d_rec = datetime.strptime(str_f_rec, "%Y-%m-%d").date() if str_f_rec else date.today()
        fecha_recepcion = f_col1.date_input("1. Fecha Recepción", value=d_rec)
        resp_recepcion = f_col1.text_input(
            "👤 Ingresó (Recepción/Oficina) *", 
            value=prev.get('resp_recepcion', '') if prev else "",
            placeholder="Ej: Laura Ojeda"
        )

        # 2. TALLER / MECÁNICA
        str_f_mec = prev.get('fecha_mecanica') if (prev and prev.get('fecha_mecanica')) else (str(date.today()) if area == "Taller (Mecánica / Inspección)" else "")
        d_mec = datetime.strptime(str_f_mec, "%Y-%m-%d").date() if str_f_mec else date.today()
        fecha_mecanica = f_col2.date_input(
            "2. Fecha Valoración Mecánica", 
            value=d_mec if (area == "Taller (Mecánica / Inspección)" or str_f_mec) else date.today(),
            disabled=(area == "Recepción / Oficina" and not str_f_mec)
        )
        resp_mecanica = f_col2.text_input(
            "👤 Ingresó (Mecánico / Inspector)", 
            value=prev.get('resp_mecanica', '') if prev else "",
            placeholder="Ej: Juan Carlos",
            disabled=(area == "Recepción / Oficina" and not prev.get('resp_mecanica'))
        )

        # 3. EMBOBINADO
        str_f_emb = prev.get('fecha_embobinado') if (prev and prev.get('fecha_embobinado')) else (str(date.today()) if area == "Embobinado" else "")
        d_emb = datetime.strptime(str_f_emb, "%Y-%m-%d").date() if str_f_emb else date.today()
        fecha_embobinado = f_col3.date_input(
            "3. Fecha Embobinado", 
            value=d_emb if (area == "Embobinado" or str_f_emb) else date.today(),
            disabled=(area != "Embobinado" and not str_f_emb)
        )
        resp_embobinado = f_col3.text_input(
            "👤 Ingresó (Técnico Embobinador)", 
            value=prev.get('resp_embobinado', '') if prev else "",
            placeholder="Ej: Tte. Embobinado",
            disabled=(area != "Embobinado" and not prev.get('resp_embobinado'))
        )

        st.markdown("---")
        c3, c4, c5 = st.columns(3)
        equipo = c3.text_input("Equipo / Motor", value=prev['equipo'] if prev else "")
        marca = c4.text_input("Marca", value=prev['marca'] if prev else "")
        modelo = c5.text_input("Modelo", value=prev['modelo'] if prev else "")
        
        c6, c7, c8, c9 = st.columns(4)
        hp_kw = c6.text_input("HP / kW", value=prev['hp_kw'] if prev else "")
        rpm = c7.text_input("RPM", value=prev['rpm'] if prev else "")
        voltaje = c8.text_input("Voltaje (V)", value=prev['voltaje'] if prev else "")
        amperaje = c9.text_input("Amperaje (A)", value=prev['amperaje'] if prev else "")
        
        falla_reportada = st.text_area("Falla Reportada por el Cliente", value=prev['falla_reportada'] if prev else "")

        datos_comp = {}
        
        # --- SECCIÓN TALLER ---
        if area == "Taller (Mecánica / Inspección)":
            st.markdown("---")
            st.subheader("🛠️ Inspección de Componentes y Daños (Taller)")
            
            comp_prev = json.loads(prev['componentes_json']) if (prev is not None and prev.get('componentes_json')) else {}
            
            h_comp, h_trae, h_dano, h_med = st.columns([2.5, 2.2, 2.2, 3.1])
            h_comp.markdown("**COMPONENTE**")
            h_trae.markdown("**TRAE (SI / NO)**")
            h_dano.markdown("**DAÑO (SI / NO)**")
            h_med.markdown("**MEDIDAS O EXTRAS**")

            for item in COMPONENTES_TALLER:
                item_prev = comp_prev.get(item, {})
                
                col_item, col_trae, col_dano, col_med = st.columns([2.5, 2.2, 2.2, 3.1])
                col_item.write(f"**{item}**")
                
                idx_trae = 0 if item_prev.get("trae_si") else (1 if item_prev.get("trae_no") else None)
                idx_dano = 0 if item_prev.get("dano_si") else (1 if item_prev.get("dano_no") else None)

                trae_val = col_trae.radio(
                    f"lbl_t_{item}",
                    options=["SI", "NO"],
                    index=idx_trae,
                    key=f"rk_t_{item}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                dano_val = col_dano.radio(
                    f"lbl_d_{item}",
                    options=["SI", "NO"],
                    index=idx_dano,
                    key=f"rk_d_{item}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                medida_val = col_med.text_input(
                    "", 
                    value=item_prev.get("medidas", ""), 
                    key=f"rk_m_{item}", 
                    label_visibility="collapsed"
                )
                
                datos_comp[item] = {
                    "trae_si": (trae_val == "SI"),
                    "trae_no": (trae_val == "NO"),
                    "dano_si": (dano_val == "SI"),
                    "dano_no": (dano_val == "NO"),
                    "medidas": medida_val
                }

        # --- SECCIÓN EMBOBINADO ---
        elif area == "Embobinado":
            st.markdown("---")
            st.subheader("⚡ Toma de Datos de Embobinado")
            
            comp_prev = json.loads(prev['componentes_json']) if (prev is not None and prev.get('componentes_json')) else {}
            
            for item in COMPONENTES_EMBOBINADO:
                val_prev = comp_prev.get(item, "")
                datos_comp[item] = st.text_input(f"**{item}**", value=val_prev, key=f"emb_{item}")

        st.markdown("---")
        trabajo_realizado = st.text_area("Diagnóstico / Trabajo Realizado", value=prev['trabajo_realizado'] if prev else "")
        observaciones = st.text_area("Observaciones Adicionales", value=prev['observaciones'] if prev else "")

        submitted = st.form_submit_button("💾 Guardar / Actualizar Reporte")
        
        if submitted:
            if not folio or not cliente:
                st.error("❌ El Folio y el Cliente son campos obligatorios.")
            else:
                payload = {
                    "folio": folio,
                    "num_salida": num_salida,
                    "cliente": cliente,
                    "equipo": equipo,
                    "marca": marca,
                    "modelo": modelo,
                    "hp_kw": hp_kw,
                    "rpm": rpm,
                    "voltaje": voltaje,
                    "amperaje": amperaje,
                    "observaciones": observaciones,
                    "componentes": datos_comp if area != "Recepción / Oficina" else (json.loads(prev['componentes_json']) if (prev and prev.get('componentes_json')) else {}),
                    "area": area,
                    "falla_reportada": falla_reportada,
                    "trabajo_realizado": trabajo_realizado,
                    "fecha_recepcion": str(fecha_recepcion),
                    "fecha_mecanica": str(fecha_mecanica) if (area == "Taller (Mecánica / Inspección)" or str_f_mec) else "",
                    "fecha_embobinado": str(fecha_embobinado) if (area == "Embobinado" or str_f_emb) else "",
                    "resp_recepcion": resp_recepcion if area == "Recepción / Oficina" or resp_recepcion else (prev.get('resp_recepcion', '') if prev else ""),
                    "resp_mecanica": resp_mecanica if area == "Taller (Mecánica / Inspección)" or resp_mecanica else (prev.get('resp_mecanica', '') if prev else ""),
                    "resp_embobinado": resp_embobinado if area == "Embobinado" or resp_embobinado else (prev.get('resp_embobinado', '') if prev else "")
                }
                guardar_reporte(payload)
                st.success(f"✅ ¡Reporte guardado exitosamente con Folio {folio}!")

elif menu == "Histórico de Reportes":
    st.header("📂 Histórico, Responsables y Tiempos de Atención")
    conn = sqlite3.connect("evmi_control.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        SELECT id, folio, num_salida, cliente, equipo, area, 
               fecha_recepcion, fecha_mecanica, fecha_embobinado,
               resp_recepcion, resp_mecanica, resp_embobinado
        FROM reportes ORDER BY id DESC
    """)
    rows = c.fetchall()
    conn.close()
    
    if rows:
        tabla_datos = []
        for r in rows:
            f_rec = r[6]
            f_mec = r[7]
            f_emb = r[8]
            
            dias_recep_mecanica = calcular_dias(f_rec, f_mec)
            dias_mecanica_embobinado = calcular_dias(f_mec, f_emb)
            dias_totales = calcular_dias(f_rec, f_emb if f_emb else f_mec)
            
            tabla_datos.append({
                "ID": r[0],
                "Folio": r[1],
                "No. Salida": r[2] if r[2] else "-",
                "Cliente": r[3],
                "Equipo": r[4],
                "F. Recepción": f_rec if f_rec else "-",
                "Resp. Oficina": r[9] if r[9] else "-",
                "F. Mecánica": f_mec if f_mec else "-",
                "Resp. Mecánica": r[10] if r[10] else "-",
                "F. Embobinado": f_emb if f_emb else "-",
                "Resp. Embobinado": r[11] if r[11] else "-",
                "Días a Mecánica": dias_recep_mecanica,
                "Días a Embobinado": dias_mecanica_embobinado,
                "Días Totales": dias_totales
            })
            
        st.dataframe(tabla_datos, use_container_width=True)
    else:
        st.info("No hay reportes registrados aún.")
