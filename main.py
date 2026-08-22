import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Portal EVMI - Control Industrial",
    page_icon="⚙️",
    layout="wide"
)

# Estilos CSS
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
        padding: 25px;
        background-color: #ffffff;
        font-family: Arial, sans-serif;
        position: relative;
        overflow: hidden;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar Base de Datos SQLite
def init_db():
    conn = sqlite3.connect("evmi_taller.db")
    c = conn.cursor()
    
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
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS cotizaciones_v3 (
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
            ref1_desc TEXT, ref1_precio REAL,
            ref2_desc TEXT, ref2_precio REAL,
            ref3_desc TEXT, ref3_precio REAL,
            ref4_desc TEXT, ref4_precio REAL,
            ref5_desc TEXT, ref5_precio REAL,
            tiempo_entrega TEXT,
            subtotal REAL,
            iva REAL,
            total REAL
        )
    ''')
    
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
                        st.success(f"Equipo guardado correctamente con Folio {nuevo_folio} el {fecha_actual}.")
                    else:
                        st.warning("Completa el nombre del cliente y la descripción del equipo.")

        elif sub_tab == "Generar Cotización Formal":
            st.header("📄 Generador de Cotizaciones Formales EVMI")
            df_rec = pd.read_sql_query("SELECT folio, cliente, equipo, no_salida FROM recepcion", conn)
            
            if not df_rec.empty:
                sel_folio = st.selectbox("Vincular con Folio de Recepción:", df_rec["folio"] + " - " + df_rec["cliente"] + " (" + df_rec["equipo"] + ")")
                folio_id = sel_folio.split(" - ")[0]
                rec_data = df_rec[df_rec["folio"] == folio_id].iloc[0]

                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM cotizaciones_v3")
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
                    st.subheader("1. Desglose de Servicios Principales")

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        val_mecanica = st.text_area("Valoración Mecánica:", value="-ENCASQUILLADO Y AJUSTE MECANICO TAPA LADO CARGA\n-ENCASQUILLADO Y AJUSTE MECANICO TAPA LADO CONTRA CARGA\n-APLICACION DE SOLDADURA")
                    with col_costo:
                        costo_val_mecanica = st.number_input("Costo Val. Mecánica ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        estator = st.text_area("Motor Estator (Embobinado / Servicio):", value="-EMBOBINADO, APLICACIÓN DE ALAMBRE CLASE TÉRMICA 'H'\n-APLICACIÓN DE AISLANTES ENTRE ESPIRAS Y BARNIZ A TEMPERATURA CONTROLADA")
                    with col_costo:
                        costo_estator = st.number_input("Costo Estator ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        balanceo = st.text_area("Balanceo Dinámico:", value="")
                    with col_costo:
                        costo_balanceo = st.number_input("Costo Balanceo ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        ensamble = st.text_area("Ensamble de Equipo y Detallado Final:", value="-INSTALACIÓN DE RODAMIENTOS\n-LIMPIEZA GENERAL Y PINTURA GENERAL")
                    with col_costo:
                        costo_ensamble = st.number_input("Costo Ensamble ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        pruebas = st.text_area("Pruebas Eléctricas Finales:", value="-PRUEBAS AMP, RESISTENCIA DE AISLAMIENTO, MEDICIÓN DE OHMS Y FASES")
                    with col_costo:
                        costo_pruebas = st.number_input("Costo Pruebas ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc:
                        otros = st.text_area("Otros Servicios / Maniobras:", value="")
                    with col_costo:
                        costo_otros = st.number_input("Costo Otros ($):", min_value=0.0, step=100.0)

                    st.markdown("---")
                    st.subheader("2. Desglose de Refacciones (Individual con Precio cada una)")
                    
                    r1_col1, r1_col2 = st.columns([3, 1])
                    with r1_col1:
                        ref1_desc = st.text_input("Refacción 1:", value="RODAMIENTO LC 6102")
                    with r1_col2:
                        ref1_precio = st.number_input("Precio Ref. 1 ($):", min_value=0.0, value=0.0, step=10.0)

                    r2_col1, r2_col2 = st.columns([3, 1])
                    with r2_col1:
                        ref2_desc = st.text_input("Refacción 2:", value="RODAMIENTO LCC 6000")
                    with r2_col2:
                        ref2_precio = st.number_input("Precio Ref. 2 ($):", min_value=0.0, value=0.0, step=10.0)

                    r3_col1, r3_col2 = st.columns([3, 1])
                    with r3_col1:
                        ref3_desc = st.text_input("Refacción 3:", value="RETEN 12X22X4")
                    with r3_col2:
                        ref3_precio = st.number_input("Precio Ref. 3 ($):", min_value=0.0, value=0.0, step=10.0)

                    r4_col1, r4_col2 = st.columns([3, 1])
                    with r4_col1:
                        ref4_desc = st.text_input("Refacción 4:", value="CAPACITOR DE TRABAJO 8 MICROFARADIOS")
                    with r4_col2:
                        ref4_precio = st.number_input("Precio Ref. 4 ($):", min_value=0.0, value=0.0, step=10.0)

                    r5_col1, r5_col2 = st.columns([3, 1])
                    with r5_col1:
                        ref5_desc = st.text_input("Refacción 5:", value="")
                    with r5_col2:
                        ref5_precio = st.number_input("Precio Ref. 5 ($):", min_value=0.0, value=0.0, step=10.0)

                    if st.form_submit_button("Generar y Guardar Cotización"):
                        total_refacciones = ref1_precio + ref2_precio + ref3_precio + ref4_precio + ref5_precio
                        subtotal = costo_val_mecanica + costo_estator + costo_balanceo + costo_ensamble + costo_pruebas + costo_otros + total_refacciones
                        iva = subtotal * 0.16
                        total = subtotal + iva
                        fecha_hoy = datetime.now().strftime("%d/%m/%Y")

                        c = conn.cursor()
                        c.execute('''
                            INSERT OR REPLACE INTO cotizaciones_v3 (
                                folio_cotizacion, folio_recepcion, fecha, atencion_a, empresa, correo, ciudad, descripcion_equipo,
                                val_mecanica, costo_val_mecanica, estator, costo_estator, balanceo, costo_balanceo,
                                ensamble, costo_ensamble, pruebas, costo_pruebas, otros, costo_otros,
                                ref1_desc, ref1_precio, ref2_desc, ref2_precio, ref3_desc, ref3_precio, ref4_desc, ref4_precio, ref5_desc, ref5_precio,
                                tiempo_entrega, subtotal, iva, total
                            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        ''', (folio_cot, folio_id, fecha_hoy, atencion_a, empresa, correo, ciudad, desc_equipo,
                              val_mecanica, costo_val_mecanica, estator, costo_estator, balanceo, costo_balanceo,
                              ensamble, costo_ensamble, pruebas, costo_pruebas, otros, costo_otros,
                              ref1_desc, ref1_precio, ref2_desc, ref2_precio, ref3_desc, ref3_precio, ref4_desc, ref4_precio, ref5_desc, ref5_precio,
                              tiempo_entrega, subtotal, iva, total))
                        conn.commit()
                        st.success(f"¡Cotización {folio_cot} guardada! Ya puedes ver el formato en 'Historial de Cotizaciones'.")
            else:
                st.info("Registra primero un equipo en 'Recepción de Equipos'.")

        elif sub_tab == "Historial de Cotizaciones":
            st.header("📋 Formato Imprimible de Cotización EVMI")
            df_cot = pd.read_sql_query("SELECT * FROM cotizaciones_v3", conn)
            
            if not df_cot.empty:
                cot_sel = st.selectbox("Seleccionar Cotización para Visualizar / Imprimir:", df_cot["folio_cotizacion"] + " - " + df_cot["empresa"])
                id_cot = cot_sel.split(" - ")[0]
                row = df_cot[df_cot["folio_cotizacion"] == id_cot].iloc[0]

                # Construir Filas de Servicios y Refacciones Individuales
                filas_tabla = ""
                if row['costo_val_mecanica'] > 0:
                    filas_tabla += f"<tr><td style='padding:8px;'><b>VALORACIÓN MECÁNICA:</b><br>{row['val_mecanica'].replace('\n', '<br>')}</td><td style='padding:8px; text-align:right;'>${row['costo_val_mecanica']:,.2f}</td></tr>"
                if row['costo_estator'] > 0:
                    filas_tabla += f"<tr><td style='padding:8px;'><b>MOTOR ESTATOR:</b><br>{row['estator'].replace('\n', '<br>')}</td><td style='padding:8px; text-align:right;'>${row['costo_estator']:,.2f}</td></tr>"
                if row['costo_balanceo'] > 0:
                    filas_tabla += f"<tr><td style='padding:8px;'><b>BALANCEO DINÁMICO:</b><br>{row['balanceo'].replace('\n', '<br>')}</td><td style='padding:8px; text-align:right;'>${row['costo_balanceo']:,.2f}</td></tr>"
                if row['costo_ensamble'] > 0:
                    filas_tabla += f"<tr><td style='padding:8px;'><b>ENSAMBLE Y DETALLADO FINAL:</b><br>{row['ensamble'].replace('\n', '<br>')}</td><td style='padding:8px; text-align:right;'>${row['costo_ensamble']:,.2f}</td></tr>"
                if row['costo_pruebas'] > 0:
                    filas_tabla += f"<tr><td style='padding:8px;'><b>PRUEBAS ELÉCTRICAS FINALES:</b><br>{row['pruebas'].replace('\n', '<br>')}</td><td style='padding:8px; text-align:right;'>${row['costo_pruebas']:,.2f}</td></tr>"
                if row['costo_otros'] > 0:
                    filas_tabla += f"<tr><td style='padding:8px;'><b>OTROS SERVICIOS:</b><br>{row['otros'].replace('\n', '<br>')}</td><td style='padding:8px; text-align:right;'>${row['costo_otros']:,.2f}</td></tr>"

                # Refacciones individuales con sus precios
                if row['ref1_desc'] and row['ref1_precio'] > 0:
                    filas_tabla += f"<tr><td style='padding:8px;'><b>REFACCIÓN:</b> {row['ref1_desc']}</td><td style='padding:8px; text-align:right;'>${row['ref1_precio']:,.2f}</td></tr>"
                if row['ref2_desc'] and row['ref2_precio'] > 0:
                    filas_tabla += f"<tr><td style='padding:8px;'><b>REFACCIÓN:</b> {row['ref2_desc']}</td><td style='padding:8px; text-align:right;'>${row['ref2_precio']:,.2f}</td></tr>"
                if row['ref3_desc'] and row['ref3_precio'] > 0:
                    filas_tabla += f"<tr><td style='padding:8px;'><b>REFACCIÓN:</b> {row['ref3_desc']}</td><td style='padding:8px; text-align:right;'>${row['ref3_precio']:,.2f}</td></tr>"
                if row['ref4_desc'] and row['ref4_precio'] > 0:
                    filas_tabla += f"<tr><td style='padding:8px;'><b>REFACCIÓN:</b> {row['ref4_desc']}</td><td style='padding:8px; text-align:right;'>${row['ref4_precio']:,.2f}</td></tr>"
                if row['ref5_desc'] and row['ref5_precio'] > 0:
                    filas_tabla += f"<tr><td style='padding:8px;'><b>REFACCIÓN:</b> {row['ref5_desc']}</td><td style='padding:8px; text-align:right;'>${row['ref5_precio']:,.2f}</td></tr>"

                # Logo SVG con Motor Industrial y detalles en Azul Institucional #1a365d
                logo_svg = """<svg width="260" height="75" viewBox="0 0 260 75" xmlns="http://www.w3.org/2000/svg"><g fill="#1a365d"><path d="M5 15 h 25 v 10 h -15 v 10 h 12 v 10 h -12 v 15 h -10 Z"/><path d="M35 15 l 10 45 h 10 l 10 -45 h -10 l -5 28 l -5 -28 Z"/><path d="M68 15 h 10 l 8 25 l 8 -25 h 10 v 45 h -10 v -28 l -8 28 h -2 l -8 -28 v 28 h -10 Z"/><path d="M108 15 h 10 v 45 h -10 Z"/><g transform="translate(125,12) scale(0.7)"><rect x="20" y="10" width="40" height="40" rx="3" fill="#1a365d"/><line x1="25" y1="10" x2="25" y2="50" stroke="#ffffff" stroke-width="2"/><line x1="33" y1="10" x2="33" y2="50" stroke="#ffffff" stroke-width="2"/><line x1="41" y1="10" x2="41" y2="50" stroke="#ffffff" stroke-width="2"/><line x1="49" y1="10" x2="49" y2="50" stroke="#ffffff" stroke-width="2"/><rect x="5" y="18" width="15" height="24" fill="#1a365d"/><rect x="60" y="24" width="20" height="12" fill="#1a365d"/><rect x="28" y="2" width="24" height="8" fill="#1a365d"/><rect x="15" y="50" width="10" height="8" fill="#1a365d"/><rect x="55" y="50" width="10" height="8" fill="#1a365d"/></g></g><text x="5" y="70" font-family="Arial, sans-serif" font-weight="bold" font-size="9.5" fill="#1a365d">ESPECIALISTAS EN VIBRACIONES Y MONTAJES INDUST</text></svg>"""

                # Esquina ornamental azul
                corner_svg = """<svg width="120" height="60" style="position:absolute; top:0; right:0;" viewBox="0 0 120 60"><path d="M 0 0 Q 60 0, 120 60 L 120 0 Z" fill="#1a365d"/></svg>"""

                html_cotizacion = f"""<div class="cotizacion-box">{corner_svg}<table width="100%"><tr><td width="60%">{logo_svg}</td><td width="40%" align="right" style="padding-right:20px;"><p style="color:#1a365d;"><b>Puebla, Pue. A {row['fecha']}</b><br><b>Folio:</b> {row['folio_cotizacion']}<br><b>Vigencia:</b> 30 días</p></td></tr></table><hr style="border:1px solid #1a365d;"><h3 style="text-align:center; color:#1a365d; margin-top:15px; margin-bottom:15px;"><b>SERVICIO CORRECTIVO: {row['descripcion_equipo']}</b></h3><table width="100%" style="background-color:#f8fafc; border: 1px solid #cbd5e1; padding:10px; border-radius:4px;"><tr><td><b>ATENCIÓN:</b> {row['atencion_a']}</td><td><b>CONTACTO EVMI:</b> serviciosindustriales.evmi@outlook.com</td></tr><tr><td><b>EMPRESA:</b> {row['empresa']}</td><td><b>TEL:</b> 22.29.20.62.30 / 22.12.20.07.48</td></tr><tr><td><b>CORREO:</b> {row['correo']}</td><td><b>CIUDAD:</b> {row['ciudad']}</td></tr></table><br><p style="color:#334155;">En atención a su solicitud, envío a usted la cotización correspondiente a los servicios de su interés:</p><table border="1" width="100%" style="border-collapse:collapse; text-align:left; border-color:#cbd5e1;"><tr style="background-color:#1a365d; color:white;"><th style="padding:10px;">DESCRIPCIÓN DE SERVICIOS / REFACCIONES</th><th width="25%" style="padding:10px; text-align:right;">PRECIO</th></tr>{filas_tabla}</table><br><table width="100%"><tr><td width="55%" style="vertical-align:top; color:#334155;"><b>TIEMPO DE ENTREGA:</b> {row['tiempo_entrega']}<br>RECOLECCIÓN Y ENTREGA DONDE EL USUARIO LO SOLICITE.</td><td width="45%"><table width="100%" border="1" style="border-collapse:collapse; border-color:#cbd5e1;"><tr style="padding:6px;"><td><b>SUBTOTAL:</b></td><td style="text-align:right;">${row['subtotal']:,.2f}</td></tr><tr style="padding:6px;"><td><b>IVA (16%):</b></td><td style="text-align:right;">${row['iva']:,.2f}</td></tr><tr style="background-color:#1a365d; color:white; padding:6px;"><td><b>TOTAL:</b></td><td style="text-align:right;"><b>${row['total']:,.2f}</b></td></tr></table></td></tr></table></div>"""

                st.markdown(html_cotizacion, unsafe_allow_html=True)
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
                trabajos = st.text_area("Trabajos Mecánicos Recomendados:")
                
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
                    aislamiento = st.text_input("Clase de Aislamiento")
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
