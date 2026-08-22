import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Portal EVMI - Sistema de Control y Cotización",
    page_icon="⚙️",
    layout="wide"
)

# Estilos CSS con paleta corporativa EVMI
st.markdown("""
    <style>
    .evmi-header {
        background-color: #1a365d;
        color: white;
        padding: 15px;
        text-align: center;
        border-radius: 5px;
        font-size: 26px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .cotizacion-box {
        border: 2px solid #1a365d;
        padding: 20px;
        background-color: #ffffff;
        font-family: Arial, sans-serif;
    }
    .cotizacion-header {
        color: #1a365d;
        font-weight: bold;
        border-bottom: 2px solid #1a365d;
        padding-bottom: 5px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar Base de Datos SQLite
def init_db():
    conn = sqlite3.connect("evmi_taller.db")
    c = conn.cursor()
    # Tabla de Equipos / Recepción
    c.execute('''
        CREATE TABLE IF NOT EXISTS recepcion (
            folio TEXT PRIMARY KEY,
            fecha_registro TEXT,
            cliente TEXT,
            equipo TEXT,
            potencia TEXT,
            rpm TEXT,
            prioridad TEXT,
            no_salida TEXT,
            estatus TEXT
        )
    ''')
    # Tabla de Cotizaciones
    c.execute('''
        CREATE TABLE IF NOT EXISTS cotizaciones (
            folio_cotizacion TEXT PRIMARY KEY,
            folio_recepcion TEXT,
            fecha TEXT,
            atencion_a TEXT,
            empresa TEXT,
            correo TEXT,
            ciudad TEXT,
            descripcion_equipo TEXT,
            val_mecanica TEXT, costo_val_mecanica REAL,
            estator TEXT, costo_estator REAL,
            balanceo TEXT, costo_balanceo REAL,
            ensamble TEXT, costo_ensamble REAL,
            pruebas TEXT, costo_pruebas REAL,
            otros TEXT, costo_otros REAL,
            refacciones TEXT, costo_refacciones REAL,
            tiempo_entrega TEXT,
            subtotal REAL,
            iva REAL,
            total REAL
        )
    ''')
    # Tablas mecánicas y embobinado
    c.execute('''
        CREATE TABLE IF NOT EXISTS taller (
            folio TEXT PRIMARY KEY,
            diagnostico TEXT,
            rodamientos TEXT,
            trabajos TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS embobinado (
            folio TEXT PRIMARY KEY,
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

st.markdown('<div class="evmi-header">⚙️ PORTAL INDUSTRIAL EVMI - CONTROL Y COTIZACIONES</div>', unsafe_allow_html=True)

if not st.session_state["autenticado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Acceso al Sistema")
        area_sel = st.selectbox("Área Operativa:", ["Oficina", "Taller", "Embobinado"])
        pwd = st.text_input("Contraseña:", type="password")
        if st.button("Ingresar al Sistema"):
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
        sub_tab = st.radio("Módulo de Oficina:", ["Recepción de Equipos", "Generar Cotización Formal", "Historial de Cotizaciones"], horizontal=True)

        if sub_tab == "Recepción de Equipos":
            st.header("📦 Recepción de Equipos")
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM recepcion")
            total = c.fetchone()[0]
            nuevo_folio = f"EVMI-2026-{total + 1:04d}"

            with st.form("form_recepcion"):
                st.subheader(f"Folio de Recepción: {nuevo_folio}")
                c1, c2 = st.columns(2)
                with c1:
                    cliente = st.text_input("Empresa / Cliente *")
                    equipo = st.text_input("Descripción del Equipo *")
                    potencia = st.text_input("Potencia (HP / kW)")
                with c2:
                    rpm = st.text_input("R.P.M.")
                    prioridad = st.selectbox("Prioridad", ["Normal", "Alta", "URGENTE"])
                    no_salida = st.text_input("Número de Salida / Referencia Interna")

                if st.form_submit_button("Guardar Recepción"):
                    if cliente and equipo:
                        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
                        c.execute('''
                            INSERT INTO recepcion (folio, fecha_registro, cliente, equipo, potencia, rpm, prioridad, no_salida, estatus)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (nuevo_folio, fecha_actual, cliente, equipo, potencia, rpm, prioridad, no_salida, "Recibido"))
                        conn.commit()
                        st.success(f"Equipo guardado correctamente con Folio {nuevo_folio} y fecha {fecha_actual}.")
                    else:
                        st.warning("Escribe el nombre del cliente y la descripción del equipo.")

        elif sub_tab == "Generar Cotización Formal":
            st.header("📄 Generador de Cotizaciones Formales EVMI")
            
            # Obtener folios registrados
            df_rec = pd.read_sql_query("SELECT folio, cliente, equipo, no_salida FROM recepcion", conn)
            
            if not df_rec.empty:
                sel_folio = st.selectbox("Vincular con Folio de Recepción / Taller:", df_rec["folio"] + " - " + df_rec["cliente"] + " (" + df_rec["equipo"] + ")")
                folio_id = sel_folio.split(" - ")[0]
                
                # Datos preexistentes de recepcion
                rec_data = df_rec[df_rec["folio"] == folio_id].iloc[0]

                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM cotizaciones")
                num_cot = c.fetchone()[0] + 1
                folio_cot = f"DAC-{num_cot:04d}"

                with st.form("form_cotizacion"):
                    st.subheader(f"Cotización Ref: {folio_cot} | Salida No: {rec_data['no_salida']}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        atencion_a = st.text_input("Atención A (Contacto):")
                        empresa = st.text_input("Empresa:", value=rec_data["cliente"])
                        correo = st.text_input("Correo Electrónico:")
                        ciudad = st.text_input("Ciudad / Estado:", value="Puebla, Pue.")
                    with c2:
                        desc_equipo = st.text_input("Descripción Equipo a Reparar:", value=rec_data["equipo"])
                        tiempo_entrega = st.text_input("Tiempo de Entrega del Servicio:", value="5 A 7 DIAS HABILES")

                    st.markdown("---")
                    st.subheader("Desglose de Servicios y Costos Unificados")

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        val_mecanica = st.text_area("1. Valoración Mecánica:", value="-ENCASQUILLADO Y AJUSTE MECANICO TAPA LADO CARGA Y CONTRA CARGA\n-APLICACION DE SOLDADURA")
                    with col_costo:
                        costo_val_mecanica = st.number_input("Costo Val. Mecánica ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        estator = st.text_area("2. Motor Estator (Embobinado / Servicio):", value="-EMBOBINADO A 9 PUNTAS, ALAMBRE CLASE TERMICA 'H', BARNIZ A TEMPERATURA CONTROLADA")
                    with col_costo:
                        costo_estator = st.number_input("Costo Estator ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        balanceo = st.text_area("3. Balanceo Dinámico:", value="-BALANCEO DINAMICO DE ROTOR EN DOS PLANOS")
                    with col_costo:
                        costo_balanceo = st.number_input("Costo Balanceo ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        ensamble = st.text_area("4. Ensamble de Equipo y Detallado Final:", value="-INSTALACION DE RODAMIENTOS CON DISPOSITIVO SKF\n-LIMPIEZA GENERAL Y PINTURA GENERAL")
                    with col_costo:
                        costo_ensamble = st.number_input("Costo Ensamble ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        pruebas = st.text_area("5. Pruebas Eléctricas Finales:", value="-PRUEBAS AMP 220VOLTS, RESISTENCIA DE AISLAMIENTO, MEDICION DE OHMS Y FASES")
                    with col_costo:
                        costo_pruebas = st.number_input("Costo Pruebas ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        otros = st.text_area("6. Otros Servicios / Maniobras:", value="")
                    with col_costo:
                        costo_otros = st.number_input("Costo Otros ($):", min_value=0.0, step=100.0)

                    st.markdown("---")
                    st.subheader("Refacciones")
                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        refacciones = st.text_area("Descripción de Refacciones (Rodamientos, Retenes, etc.):", value="-RODAMIENTO LC (6303 2ZC3)\n-RODAMIENTO LCC (6202 2ZC3)\n-RETEN (22X35X7)")
                    with col_costo:
                        costo_refacciones = st.number_input("Total Refacciones ($):", min_value=0.0, step=50.0)

                    if st.form_submit_button("Generar y Guardar Cotización"):
                        subtotal = costo_val_mecanica + costo_estator + costo_balanceo + costo_ensamble + costo_pruebas + costo_otros + costo_refacciones
                        iva = subtotal * 0.16
                        total = subtotal + iva
                        fecha_hoy = datetime.now().strftime("%d/%m/%Y")

                        c = conn.cursor()
                        c.execute('''
                            INSERT OR REPLACE INTO cotizaciones VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        ''', (folio_cot, folio_id, fecha_hoy, atencion_a, empresa, correo, ciudad, desc_equipo,
                              val_mecanica, costo_val_mecanica, estator, costo_estator, balanceo, costo_balanceo,
                              ensamble, costo_ensamble, pruebas, costo_pruebas, otros, costo_otros,
                              refacciones, costo_refacciones, tiempo_entrega, subtotal, iva, total))
                        conn.commit()
                        st.success(f"Cotización {folio_cot} generada exitosamente. Ve al 'Historial de Cotizaciones' para ver el formato imprimible.")
            else:
                st.info("Primero debes registrar un equipo en 'Recepción de Equipos'.")

        elif sub_tab == "Historial de Cotizaciones":
            st.header("📋 Formato Imprimible de Cotización EVMI")
            df_cot = pd.read_sql_query("SELECT * FROM cotizaciones", conn)
            
            if not df_cot.empty:
                cot_sel = st.selectbox("Seleccionar Cotización para Visualizar / Imprimir:", df_cot["folio_cotizacion"] + " - " + df_cot["empresa"])
                id_cot = cot_sel.split(" - ")[0]
                row = df_cot[df_cot["folio_cotizacion"] == id_cot].iloc[0]

                # Renderizado estilo documento oficial EVMI
                st.markdown(f"""
                <div class="cotizacion-box">
                    <table width="100%">
                        <tr>
                            <td width="60%"><h2><b>EVMI</b></h2><p>Especialistas en Vibraciones y Montajes Industriales</p></td>
                            <td width="40%" align="right">
                                <p><b>Puebla, Pue. A {row['fecha']}</b><br>
                                <b>Folio:</b> {row['folio_cotizacion']}<br>
                                <b>Vigencia:</b> 30 días</p>
                            </td>
                        </tr>
                    </table>
                    <hr>
                    <h3 style="text-align:center; color:#c00000;"><b>SERVICIO CORRECTIVO: {row['descripcion_equipo']}</b></h3>
                    
                    <table width="100%" style="background-color:#f2f2f2; padding:10px;">
                        <tr>
                            <td><b>ATENCIÓN:</b> {row['atencion_a']}</td>
                            <td><b>CONTACTO EVMI:</b> serviciosindustriales.evmi@outlook.com</td>
                        </tr>
                        <tr>
                            <td><b>EMPRESA:</b> {row['empresa']}</td>
                            <td><b>TEL:</b> 22.29.20.62.30 / 22.12.20.07.48</td>
                        </tr>
                        <tr>
                            <td><b>CORREO:</b> {row['correo']}</td>
                            <td><b>CIUDAD:</b> {row['ciudad']}</td>
                        </tr>
                    </table>
                    <br>
                    <p>En atención a su solicitud, envío a usted la cotización correspondiente a los servicios de su interés:</p>
                    
                    <table border="1" width="100%" style="border-collapse:collapse; text-align:left;">
                        <tr style="background-color:#1a365d; color:white;">
                            <th>DESCRIPCIÓN</th>
                            <th width="20%">PRECIO UNITARIO</th>
                        </tr>
                        {"<tr><td><b>VALORACIÓN MECÁNICA:</b><br>" + row['val_mecanica'].replace('\n', '<br>') + "</td><td>$" + str(row['costo_val_mecanica']) + "</td></tr>" if row['costo_val_mecanica'] > 0 else ""}
                        {"<tr><td><b>MOTOR ESTATOR:</b><br>" + row['estator'].replace('\n', '<br>') + "</td><td>$" + str(row['costo_estator']) + "</td></tr>" if row['costo_estator'] > 0 else ""}
                        {"<tr><td><b>BALANCEO DINÁMICO:</b><br>" + row['balanceo'].replace('\n', '<br>') + "</td><td>$" + str(row['costo_balanceo']) + "</td></tr>" if row['costo_balanceo'] > 0 else ""}
                        {"<tr><td><b>ENSAMBLE Y DETALLADO FINAL:</b><br>" + row['ensamble'].replace('\n', '<br>') + "</td><td>$" + str(row['costo_ensamble']) + "</td></tr>" if row['costo_ensamble'] > 0 else ""}
                        {"<tr><td><b>PRUEBAS ELÉCTRICAS FINALES:</b><br>" + row['pruebas'].replace('\n', '<br>') + "</td><td>$" + str(row['costo_pruebas']) + "</td></tr>" if row['costo_pruebas'] > 0 else ""}
                        {"<tr><td><b>OTROS SERVICIOS:</b><br>" + row['otros'].replace('\n', '<br>') + "</td><td>$" + str(row['costo_otros']) + "</td></tr>" if row['costo_otros'] > 0 else ""}
                        {"<tr><td><b>REFACCIONES:</b><br>" + row['refacciones'].replace('\n', '<br>') + "</td><td>$" + str(row['costo_refacciones']) + "</td></tr>" if row['costo_refacciones'] > 0 else ""}
                    </table>
                    <br>
                    <table width="100%">
                        <tr>
                            <td width="60%"><b>TIEMPO DE ENTREGA:</b> {row['tiempo_entrega']}<br>RECOLECCIÓN Y ENTREGA DONDE EL USUARIO LO SOLICITE.</td>
                            <td width="40%">
                                <table width="100%" border="1" style="border-collapse:collapse;">
                                    <tr><td><b>SUBTOTAL:</b></td><td>${row['subtotal']:,.2f}</td></tr>
                                    <tr><td><b>IVA (16%):</b></td><td>${row['iva']:,.2f}</td></tr>
                                    <tr style="background-color:#1a365d; color:white;"><td><b>TOTAL:</b></td><td><b>${row['total']:,.2f}</b></td></tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No hay cotizaciones registradas.")

    elif area == "Taller":
        st.header("🔧 Evaluación Mecánica")
        df_rec = pd.read_sql_query("SELECT folio, cliente, equipo FROM recepcion", conn)
        if not df_rec.empty:
            folio_sel = st.selectbox("Seleccionar Folio de Trabajo:", df_rec["folio"] + " - " + df_rec["cliente"] + " (" + df_rec["equipo"] + ")")
            folio_id = folio_sel.split(" - ")[0]

            with st.form("form_taller"):
                diag = st.text_area("Diagnóstico Falla Mecánica / Inspección de Tapas y Flecha:")
                rodam = st.text_input("Medidas / Marcas de Rodamientos Requeridos:")
                trabajos = st.text_area("Trabajos Mecánicos Recomendados (Maquinado, Ajustes, Soldadura):")
                
                if st.form_submit_button("Guardar Avance de Taller"):
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO taller VALUES (?,?,?,?)", (folio_id, diag, rodam, trabajos))
                    c.execute("UPDATE recepcion SET estatus=? WHERE folio=?", ("En Proceso Mecánico", folio_id))
                    conn.commit()
                    st.success("Información técnica actualizada.")
        else:
            st.info("No hay equipos en recepción.")

    elif area == "Embobinado":
        st.header("⚡ Datos Técnicos de Embobinado")
        df_rec = pd.read_sql_query("SELECT folio, cliente, equipo FROM recepcion", conn)
        if not df_rec.empty:
            folio_sel = st.selectbox("Seleccionar Folio de Trabajo:", df_rec["folio"] + " - " + df_rec["cliente"] + " (" + df_rec["equipo"] + ")")
            folio_id = folio_sel.split(" - ")[0]

            with st.form("form_embobinado"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    conexion = st.text_input("Conexión (Delta / Estrella / Puntas)")
                    calibre = st.text_input("Calibre Alambre AWG")
                with c2:
                    paso = st.text_input("Paso de Ranura")
                    vueltas = st.text_input("Vueltas por Bobina")
                with c3:
                    peso = st.text_input("Peso Cobre (kg)")
                    aislamiento = st.text_input("Clase de Aislamiento (ej. Clase H)")
                megger = st.text_input("Prueba Aislamiento / Megger")

                if st.form_submit_button("Guardar Ficha de Embobinado"):
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO embobinado VALUES (?,?,?,?,?,?,?,?)", 
                              (folio_id, conexion, calibre, paso, vueltas, peso, aislamiento, megger))
                    c.execute("UPDATE recepcion SET estatus=? WHERE folio=?", ("En Embobinado", folio_id))
                    conn.commit()
                    st.success("Datos de cobre guardados correctamente.")
        else:
            st.info("No hay equipos en recepción.")

    conn.close()
