import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Portal EVMI - Control Industrial",
    page_icon="⚙️",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main-header {
        font-size: 32px;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E3A8A;
        color: white;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar Base de Datos SQLite
def init_db():
    conn = sqlite3.connect("evmi_taller.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS ordenes (
            folio TEXT PRIMARY KEY,
            fecha TEXT,
            cliente TEXT,
            equipo TEXT,
            hp_kw TEXT,
            rpm TEXT,
            voltaje TEXT,
            prioridad TEXT,
            monto REAL,
            oc TEXT,
            estatus TEXT,
            diag_mecanico TEXT,
            rodamientos TEXT,
            trabajos_mecanicos TEXT,
            conexion TEXT,
            calibre TEXT,
            paso TEXT,
            vueltas TEXT,
            peso_cobre TEXT,
            aislamiento TEXT,
            megger TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

USUARIOS = {
    "oficina": "oficina123",
    "taller": "taller123",
    "embobinado": "cobre123"
}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["area"] = None

st.markdown('<div class="main-header">⚙️ PORTAL INDUSTRIAL EVMI</div>', unsafe_allow_html=True)

if not st.session_state["autenticado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Acceso al Sistema")
        area_sel = st.selectbox("Área Operativa:", ["Oficina", "Taller", "Embobinado"])
        pwd = st.text_input("Contraseña:", type="password")
        if st.button("Iniciar Sesión"):
            if pwd == USUARIOS.get(area_sel.lower()):
                st.session_state["autenticado"] = True
                st.session_state["area"] = area_sel
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
else:
    st.sidebar.title(f"📌 Área: {st.session_state['area']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.session_state["area"] = None
        st.rerun()

    area = st.session_state["area"]
    conn = sqlite3.connect("evmi_taller.db")

    if area == "Oficina":
        st.header("🏢 Recepción de Equipos y Cotizaciones")
        
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM ordenes")
        total = c.fetchone()[0]
        nuevo_folio = f"EVMI-2026-{total + 1:04d}"

        with st.form("form_oficina"):
            st.subheader(f"Nuevo Folio: {nuevo_folio}")
            c1, c2 = st.columns(2)
            with c1:
                cliente = st.text_input("Empresa / Cliente *")
                equipo = st.text_input("Descripción del Equipo (ej. Motor Trifásico) *")
                hp_kw = st.text_input("Potencia (HP / kW)")
                rpm = st.text_input("RPM de Placa")
            with c2:
                voltaje = st.text_input("Voltaje (V) / Amperaje (A)")
                prioridad = st.selectbox("Prioridad", ["Normal", "Alta", "URGENTE"])
                monto = st.number_input("Monto Cotizado ($ MXN)", min_value=0.0, step=500.0)
                oc = st.text_input("Orden de Compra (O.C.)")

            if st.form_submit_button("Registrar Orden"):
                if cliente and equipo:
                    c.execute('''
                        INSERT INTO ordenes (folio, fecha, cliente, equipo, hp_kw, rpm, voltaje, prioridad, monto, oc, estatus)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (nuevo_folio, datetime.now().strftime("%d/%m/%Y %H:%M"), cliente, equipo, hp_kw, rpm, voltaje, prioridad, monto, oc, "Recibido"))
                    conn.commit()
                    st.success(f"Orden {nuevo_folio} registrada con éxito.")
                else:
                    st.warning("Por favor llena los campos obligatorios del cliente y equipo.")

    elif area == "Taller":
        st.header("🔧 Evaluación Mecánica y Diagnóstico")
        df = pd.read_sql_query("SELECT folio, cliente, equipo FROM ordenes", conn)
        if not df.empty:
            folio_sel = st.selectbox("Seleccionar Orden:", df["folio"] + " - " + df["cliente"] + " (" + df["equipo"] + ")")
            folio_id = folio_sel.split(" - ")[0]

            with st.form("form_taller"):
                diag = st.text_area("Diagnóstico Falla Mecánica / Inspección")
                rodam = st.text_input("Rodamientos Requeridos (ej. 6310 C3 / 6208)")
                mecanizados = st.text_area("Trabajos Mecánicos (Ajuste de flecha, encasquillado de tapas, etc.)")
                
                if st.form_submit_button("Actualizar Reporte Mecánico"):
                    c = conn.cursor()
                    c.execute('''
                        UPDATE ordenes SET diag_mecanico=?, rodamientos=?, trabajos_mecanicos=?, estatus=?
                        WHERE folio=?
                    ''', (diag, rodam, mecanizados, "En Proceso Mecánico", folio_id))
                    conn.commit()
                    st.success(f"Reporte mecánico de {folio_id} actualizado.")
        else:
            st.info("No hay ordenes registradas en el sistema.")

    elif area == "Embobinado":
        st.header("⚡ Hoja Técnica de Embobinado")
        df = pd.read_sql_query("SELECT folio, cliente, equipo FROM ordenes", conn)
        if not df.empty:
            folio_sel = st.selectbox("Seleccionar Orden:", df["folio"] + " - " + df["cliente"] + " (" + df["equipo"] + ")")
            folio_id = folio_sel.split(" - ")[0]

            with st.form("form_embobinado"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    conexion = st.text_input("Conexión (Delta, Estrella, YY, etc.)")
                    calibre = st.text_input("Calibre Alambre AWG")
                with c2:
                    paso = st.text_input("Paso de Ranura")
                    vueltas = st.text_input("Vueltas por Bobina")
                with c3:
                    peso = st.text_input("Peso de Cobre (kg)")
                    aislamiento = st.selectbox("Clase Aislamiento", ["Clase F (155°C)", "Clase H (180°C)", "Otro"])
                
                megger = st.text_input("Prueba de Aislamiento / Megger (MΩ)")

                if st.form_submit_button("Guardar Ficha Técnica de Cobre"):
                    c = conn.cursor()
                    c.execute('''
                        UPDATE ordenes SET conexion=?, calibre=?, paso=?, vueltas=?, peso_cobre=?, aislamiento=?, megger=?, estatus=?
                        WHERE folio=?
                    ''', (conexion, calibre, paso, vueltas, peso, aislamiento, megger, "En Embobinado", folio_id))
                    conn.commit()
                    st.success(f"Ficha técnica guardada para {folio_id}.")
        else:
            st.info("No hay ordenes registradas en el sistema.")

    st.divider()
    st.subheader("📋 Panel de Monitoreo y Búsqueda")
    df_todas = pd.read_sql_query("SELECT * FROM ordenes", conn)
    st.dataframe(df_todas, use_container_width=True)
    conn.close()
