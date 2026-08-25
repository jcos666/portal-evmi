import streamlit as st
import sqlite3
import json
from datetime import datetime

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
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def guardar_reporte(datos):
    conn = sqlite3.connect("evmi_control.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reportes (
            folio, cliente, equipo, marca, modelo, hp_kw, rpm, voltaje, amperaje,
            observaciones, componentes_json, area, falla_reportada, trabajo_realizado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datos.get('folio'), datos.get('cliente'), datos.get('equipo'),
        datos.get('marca'), datos.get('modelo'), datos.get('hp_kw'),
        datos.get('rpm'), datos.get('voltaje'), datos.get('amperaje'),
        datos.get('observaciones'), json.dumps(datos.get('componentes', {})),
        datos.get('area'), datos.get('falla_reportada'), datos.get('trabajo_realizado')
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
            "id": row[0], "folio": row[1], "cliente": row[2], "equipo": row[3],
            "marca": row[4], "modelo": row[5], "hp_kw": row[6], "rpm": row[7],
            "voltaje": row[8], "amperaje": row[9], "observaciones": row[10],
            "componentes_json": row[11], "area": row[12], "falla_reportada": row[13],
            "trabajo_realizado": row[14], "fecha": row[15]
        }
    return None

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("⚙️ Portal EVMI - Control Industrial")
st.write("Sistema de Gestión de Reportes Técnicos y Recepción")

menu = st.sidebar.radio("Navegación", ["Nuevo Reporte / Inspección", "Histórico de Reportes"])

if menu == "Nuevo Reporte / Inspección":
    st.header("📋 Registro de Servicio Técnico")
    
    col_f1, col_f2 = st.columns([2, 1])
    folio_input = col_f1.text_input("Ingrese Folio / No. Orden para buscar o actualizar:")
    
    prev = None
    if folio_input:
        prev = obtener_ultimo_reporte(folio_input.strip())
        if prev:
            st.info(f"ℹ️ Se encontraron datos previos del Folio {folio_input}. Puedes actualizar el reporte.")
        else:
            st.caption("No se encontraron registros previos con este folio. Se creará uno nuevo.")

    # Selección de Área de Trabajo
    area = st.radio(
        "Área que diligencia el formato:", 
        ["Recepción / Oficina", "Taller (Mecánica / Inspección)", "Embobinado"], 
        horizontal=True
    )

    with st.form("form_reporte"):
        st.subheader("📌 Datos Generales del Equipo y Cliente")
        c1, c2 = st.columns(2)
        
        folio = c1.text_input("Folio / Orden de Trabajo *", value=prev['folio'] if prev else (folio_input if folio_input else ""))
        cliente = c2.text_input("Cliente *", value=prev['cliente'] if prev else "")
        
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
                
                # Inicia sin selección (index=None) para marcar a 1 solo clic
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
            st.subheader("⚡ Datos de Embobinado y Tomade Datos")
            
            comp_prev = json.loads(prev['componentes_json']) if (prev is not None and prev.get('componentes_json')) else {}
            
            for item in COMPONENTES_EMBOBINADO:
                val_prev = comp_prev.get(item, "")
                datos_comp[item] = st.text_input(f"**{item}**", value=val_prev, key=f"emb_{item}")

        st.markdown("---")
        trabajo_realizado = st.text_area("Diagnóstico / Trabajo Realizado", value=prev['trabajo_realizado'] if prev else "")
        observaciones = st.text_area("Observaciones Adicionales", value=prev['observaciones'] if prev else "")

        submitted = st.form_submit_button("💾 Guardar Reporte")
        
        if submitted:
            if not folio or not cliente:
                st.error("❌ El Folio y el Cliente son campos obligatorios.")
            else:
                payload = {
                    "folio": folio,
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
                    "trabajo_realizado": trabajo_realizado
                }
                guardar_reporte(payload)
                st.success(f"✅ ¡Reporte guardado exitosamente bajo la sección {area}!")

elif menu == "Histórico de Reportes":
    st.header("📂 Histórico de Reportes Registrados")
    conn = sqlite3.connect("evmi_control.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT id, folio, cliente, equipo, area, fecha FROM reportes ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No hay reportes registrados aún.")
