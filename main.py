import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(
    page_title="Portal EVMI - Control Industrial",
    page_icon="⚙️",
    layout="wide"
)

# Estilos CSS generales y reglas de IMPRESIÓN
st.markdown("""
    <style>
    .evmi-header {
        background-color: #1a365d;
        color: white;
        padding: 15px;
        text-align: center;
        border-radius: 5px;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .cotizacion-container {
        max-width: 850px;
        margin: 0 auto;
        background: #ffffff;
        padding: 0px;
        border: 1px solid #ccc;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        font-family: Arial, sans-serif;
    }
    @media print {
        [data-testid="stSidebar"], header, footer, .stButton, .evmi-header, .no-print {
            display: none !important;
        }
        body, .main, .block-container {
            padding: 0 !important;
            margin: 0 !important;
            background: white !important;
        }
        .cotizacion-container {
            border: none !important;
            box-shadow: none !important;
            width: 100% !important;
            max-width: 100% !important;
            page-break-after: avoid !important;
            page-break-inside: avoid !important;
        }
        @page {
            size: letter portrait;
            margin: 8mm;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Base de Datos
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
        CREATE TABLE IF NOT EXISTS reportes_tecnicos (
            folio_recepcion TEXT PRIMARY KEY,
            tecnico TEXT,
            empresa TEXT,
            marca TEXT,
            ampers TEXT,
            fases TEXT,
            volts TEXT,
            rpm TEXT,
            kwhp TEXT,
            hz TEXT,
            tipo TEXT,
            rod_lc TEXT,
            rod_lcc TEXT,
            no_serie TEXT,
            componentes_json TEXT,
            observaciones TEXT,
            recomendaciones TEXT,
            in_megohms TEXT, in_volts TEXT, in_ampers TEXT, in_ohms TEXT,
            out_megohms TEXT, out_volts TEXT, out_ampers TEXT, out_ohms TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Componentes Estándar del Reporte Técnico
LISTA_COMPONENTES = [
    "TOLVA", "VENTILADOR", "TAPA DE CONEXIÓN", "CAJA DE CONEXIÓN", "POLEA",
    "ENGRANE", "TURBINA", "CASQUILLO L.C.", "CASQUILLO L.C.C.", "FLECHA LC",
    "FLECHA L.C.C.", "RETEN", "CUÑA", "CUÑERO", "PLATINO", "CENTRIFUGO",
    "CAPACITOR", "TORNILLOS", "IMPULSOR", "SELLOS MECANICOS", "TABLERO",
    "EMBOBINADO", "POLOS", "PUNTAS"
]

def generar_pdf_cotizacion(row):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 9
    normal_style.leading = 11

    title_style = ParagraphStyle('TitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=14, alignment=1, textColor=colors.HexColor('#1a365d'))
    header_title_style = ParagraphStyle('HeaderTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18, leading=20, textColor=colors.HexColor('#1a365d'))
    header_sub_style = ParagraphStyle('HeaderSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#1a365d'))

    story = []
    header_text = Paragraph("<b>EVMI</b>", header_title_style)
    sub_text = Paragraph("ESPECIALISTAS EN VIBRACIONES Y MONTAJES INDUSTRIALES", header_sub_style)
    info_derecha = Paragraph(f"<b>Puebla, Pue. A {row['fecha']}</b><br/><b>Folio:</b> {row['folio_cotizacion']}<br/><b>Vigencia:</b> 30 días", ParagraphStyle('RightInfo', parent=normal_style, alignment=2, textColor=colors.HexColor('#1a365d')))

    tabla_encabezado = Table([[header_text, info_derecha], [sub_text, ""]], colWidths=[340, 200])
    tabla_encabezado.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('SPAN', (1,0), (1,1))]))
    story.append(tabla_encabezado)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1a365d'), spaceBefore=1, spaceAfter=10))

    story.append(Paragraph(f"<b>SERVICIO CORRECTIVO: {row['descripcion_equipo']}</b>", title_style))
    story.append(Spacer(1, 10))

    datos_cliente = [
        [Paragraph(f"<b>ATENCIÓN:</b> {row['atencion_a']}", normal_style), Paragraph("<b>CONTACTO EVMI:</b> serviciosindustriales.evmi@outlook.com", normal_style)],
        [Paragraph(f"<b>EMPRESA:</b> {row['empresa']}", normal_style), Paragraph("<b>TEL:</b> 22.29.20.62.30 / 22.12.20.07.48", normal_style)],
        [Paragraph(f"<b>CORREO:</b> {row['correo']}", normal_style), Paragraph(f"<b>CIUDAD:</b> {row['ciudad']}", normal_style)]
    ]
    t_cliente = Table(datos_cliente, colWidths=[270, 270])
    t_cliente.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_cliente)
    story.append(Spacer(1, 10))

    story.append(Paragraph("En atención a su solicitud, envío a usted la cotización correspondiente a los servicios de su interés:", normal_style))
    story.append(Spacer(1, 8))

    tabla_items = [[Paragraph("<b>DESCRIPCIÓN DE SERVICIOS / REFACCIONES</b>", ParagraphStyle('WH', parent=normal_style, textColor=colors.white)),
                    Paragraph("<b>PRECIO</b>", ParagraphStyle('WH2', parent=normal_style, textColor=colors.white, alignment=2))]]

    def agregar_renglon(titulo, detalle, costo):
        if costo > 0:
            desc_html = f"<b>{titulo}:</b><br/>{detalle.replace('\n', '<br/>')}" if detalle else f"<b>{titulo}</b>"
            tabla_items.append([Paragraph(desc_html, normal_style), Paragraph(f"${costo:,.2f}", ParagraphStyle('RightCost', parent=normal_style, alignment=2))])

    agregar_renglon("VALORACIÓN MECÁNICA", row['val_mecanica'], row['costo_val_mecanica'])
    agregar_renglon("MOTOR ESTATOR", row['estator'], row['costo_estator'])
    agregar_renglon("BALANCEO DINÁMICO", row['balanceo'], row['costo_balanceo'])
    agregar_renglon("ENSAMBLE Y DETALLADO FINAL", row['ensamble'], row['costo_ensamble'])
    agregar_renglon("PRUEBAS ELÉCTRICAS FINALES", row['pruebas'], row['costo_pruebas'])
    agregar_renglon("OTROS SERVICIOS", row['otros'], row['costo_otros'])

    if row['ref1_desc'] and row['ref1_precio'] > 0: agregar_renglon("REFACCIÓN", row['ref1_desc'], row['ref1_precio'])
    if row['ref2_desc'] and row['ref2_precio'] > 0: agregar_renglon("REFACCIÓN", row['ref2_desc'], row['ref2_precio'])
    if row['ref3_desc'] and row['ref3_precio'] > 0: agregar_renglon("REFACCIÓN", row['ref3_desc'], row['ref3_precio'])
    if row['ref4_desc'] and row['ref4_precio'] > 0: agregar_renglon("REFACCIÓN", row['ref4_desc'], row['ref4_precio'])
    if row['ref5_desc'] and row['ref5_precio'] > 0: agregar_renglon("REFACCIÓN", row['ref5_desc'], row['ref5_precio'])

    t_items = Table(tabla_items, colWidths=[410, 130])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a365d')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 10))

    p_entrega = Paragraph(f"<b>TIEMPO DE ENTREGA:</b> {row['tiempo_entrega']}<br/>RECOLECCIÓN Y ENTREGA DONDE EL USUARIO LO SOLICITE.", normal_style)

    tabla_totales = Table([
        [Paragraph("<b>SUBTOTAL:</b>", normal_style), Paragraph(f"${row['subtotal']:,.2f}", ParagraphStyle('R1', parent=normal_style, alignment=2))],
        [Paragraph("<b>IVA (16%):</b>", normal_style), Paragraph(f"${row['iva']:,.2f}", ParagraphStyle('R2', parent=normal_style, alignment=2))],
        [Paragraph("<b>TOTAL:</b>", ParagraphStyle('W1', parent=normal_style, textColor=colors.white)), Paragraph(f"<b>${row['total']:,.2f}</b>", ParagraphStyle('R3', parent=normal_style, alignment=2, textColor=colors.white))]
    ], colWidths=[100, 100])

    tabla_totales.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#1a365d')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))

    t_footer = Table([[p_entrega, tabla_totales]], colWidths=[330, 210])
    t_footer.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_footer)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

USUARIOS = {"oficina": "oficina123", "taller": "taller123", "embobinado": "cobre123"}

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
                        st.success(f"Equipo guardado correctamente con Folio {nuevo_folio}.")
                    else:
                        st.warning("Completa los datos requeridos.")

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
                        tiempo_entrega = st.text_input("Tiempo de Entrega:", value="5 A 7 DIAS HABILES")

                    st.markdown("---")
                    st.subheader("Desglose de Servicios y Refacciones")

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc: val_mecanica = st.text_area("Valoración Mecánica:", value="-ENCASQUILLADO Y AJUSTE MECANICO TAPA LADO CARGA\n-ENCASQUILLADO Y AJUSTE MECANICO TAPA LADO CONTRA CARGA\n-APLICACION DE SOLDADURA")
                    with col_costo: costo_val_mecanica = st.number_input("Costo Val. Mecánica ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc: estator = st.text_area("Motor Estator:", value="-EMBOBINADO, APLICACIÓN DE ALAMBRE CLASE TÉRMICA 'H'\n-APLICACIÓN DE AISLANTES ENTRE ESPIRAS Y BARNIZ A TEMPERATURA CONTROLADA")
                    with col_costo: costo_estator = st.number_input("Costo Estator ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc: balanceo = st.text_area("Balanceo Dinámico:", value="")
                    with col_costo: costo_balanceo = st.number_input("Costo Balanceo ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc: ensamble = st.text_area("Ensamble y Detallado:", value="-INSTALACIÓN DE RODAMIENTOS\n-LIMPIEZA GENERAL Y PINTURA GENERAL")
                    with col_costo: costo_ensamble = st.number_input("Costo Ensamble ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc: pruebas = st.text_area("Pruebas Eléctricas:", value="-PRUEBAS AMP, RESISTENCIA DE AISLAMIENTO, MEDICIÓN DE OHMS Y FASES")
                    with col_costo: costo_pruebas = st.number_input("Costo Pruebas ($):", min_value=0.0, step=100.0)

                    col_desc, col_costo = st.columns([3, 1])
                    with col_desc: otros = st.text_area("Otros Servicios:", value="")
                    with col_costo: costo_otros = st.number_input("Costo Otros ($):", min_value=0.0, step=100.0)

                    st.markdown("---")
                    st.subheader("Refacciones Individuales")
                    r1_col1, r1_col2 = st.columns([3, 1])
                    with r1_col1: ref1_desc = st.text_input("Refacción 1:", value="RODAMIENTO LC 6102")
                    with r1_col2: ref1_precio = st.number_input("Precio Ref. 1 ($):", min_value=0.0, value=0.0)

                    r2_col1, r2_col2 = st.columns([3, 1])
                    with r2_col1: ref2_desc = st.text_input("Refacción 2:", value="RODAMIENTO LCC 6000")
                    with r2_col2: ref2_precio = st.number_input("Precio Ref. 2 ($):", min_value=0.0, value=0.0)

                    r3_col1, r3_col2 = st.columns([3, 1])
                    with r3_col1: ref3_desc = st.text_input("Refacción 3:", value="RETEN 12X22X4")
                    with r3_col2: ref3_precio = st.number_input("Precio Ref. 3 ($):", min_value=0.0, value=0.0)

                    r4_col1, r4_col2 = st.columns([3, 1])
                    with r4_col1: ref4_desc = st.text_input("Refacción 4:", value="CAPACITOR DE TRABAJO 8 MICROFARADIOS")
                    with r4_col2: ref4_precio = st.number_input("Precio Ref. 4 ($):", min_value=0.0, value=0.0)

                    r5_col1, r5_col2 = st.columns([3, 1])
                    with r5_col1: ref5_desc = st.text_input("Refacción 5:", value="")
                    with r5_col2: ref5_precio = st.number_input("Precio Ref. 5 ($):", min_value=0.0, value=0.0)

                    if st.form_submit_button("Guardar Cotización"):
                        total_refacciones = ref1_precio + ref2_precio + ref3_precio + ref4_precio + ref5_precio
                        subtotal = costo_val_mecanica + costo_estator + costo_balanceo + costo_ensamble + costo_pruebas + costo_otros + total_refacciones
                        iva = subtotal * 0.16
                        total = subtotal + iva
                        fecha_hoy = datetime.now().strftime("%d/%m/%Y")

                        c = conn.cursor()
                        c.execute('''
                            INSERT OR REPLACE INTO cotizaciones_v3 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        ''', (folio_cot, folio_id, fecha_hoy, atencion_a, empresa, correo, ciudad, desc_equipo,
                              val_mecanica, costo_val_mecanica, estator, costo_estator, balanceo, costo_balanceo,
                              ensamble, costo_ensamble, pruebas, costo_pruebas, otros, costo_otros,
                              ref1_desc, ref1_precio, ref2_desc, ref2_precio, ref3_desc, ref3_precio, ref4_desc, ref4_precio, ref5_desc, ref5_precio,
                              tiempo_entrega, subtotal, iva, total))
                        conn.commit()
                        st.success(f"Cotización {folio_cot} registrada exitosamente.")
            else:
                st.info("Registra primero un equipo.")

        elif sub_tab == "Historial de Cotizaciones":
            st.header("📋 Formato Imprimible / Generador PDF EVMI")
            df_cot = pd.read_sql_query("SELECT * FROM cotizaciones_v3", conn)
            
            if not df_cot.empty:
                cot_sel = st.selectbox("Seleccionar Cotización:", df_cot["folio_cotizacion"] + " - " + df_cot["empresa"])
                id_cot = cot_sel.split(" - ")[0]
                row = df_cot[df_cot["folio_cotizacion"] == id_cot].iloc[0]

                pdf_bytes = generar_pdf_cotizacion(row)
                col_pdf, col_hint = st.columns([1, 2])
                with col_pdf:
                    st.download_button(
                        label="📥 Descargar Cotización en PDF",
                        data=pdf_bytes,
                        file_name=f"Cotizacion_{row['folio_cotizacion']}_{row['empresa'].replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                with col_hint:
                    st.caption("💡 Tip: Haz clic en el botón para descargar el PDF oficial listo para enviar o imprimir en 1 sola hoja.")

                st.markdown("---")

                filas_tabla = ""
                if row['costo_val_mecanica'] > 0: filas_tabla += f"<tr><td style='padding:6px; font-size:12px;'><b>VALORACIÓN MECÁNICA:</b><br>{row['val_mecanica'].replace('\n', '<br>')}</td><td style='padding:6px; font-size:12px; text-align:right;'>${row['costo_val_mecanica']:,.2f}</td></tr>"
                if row['costo_estator'] > 0: filas_tabla += f"<tr><td style='padding:6px; font-size:12px;'><b>MOTOR ESTATOR:</b><br>{row['estator'].replace('\n', '<br>')}</td><td style='padding:6px; font-size:12px; text-align:right;'>${row['costo_estator']:,.2f}</td></tr>"
                if row['costo_balanceo'] > 0: filas_tabla += f"<tr><td style='padding:6px; font-size:12px;'><b>BALANCEO DINÁMICO:</b><br>{row['balanceo'].replace('\n', '<br>')}</td><td style='padding:6px; font-size:12px; text-align:right;'>${row['costo_balanceo']:,.2f}</td></tr>"
                if row['costo_ensamble'] > 0: filas_tabla += f"<tr><td style='padding:6px; font-size:12px;'><b>ENSAMBLE Y DETALLADO FINAL:</b><br>{row['ensamble'].replace('\n', '<br>')}</td><td style='padding:6px; font-size:12px; text-align:right;'>${row['costo_ensamble']:,.2f}</td></tr>"
                if row['costo_pruebas'] > 0: filas_tabla += f"<tr><td style='padding:6px; font-size:12px;'><b>PRUEBAS ELÉCTRICAS FINALES:</b><br>{row['pruebas'].replace('\n', '<br>')}</td><td style='padding:6px; font-size:12px; text-align:right;'>${row['costo_pruebas']:,.2f}</td></tr>"
                if row['costo_otros'] > 0: filas_tabla += f"<tr><td style='padding:6px; font-size:12px;'><b>OTROS SERVICIOS:</b><br>{row['otros'].replace('\n', '<br>')}</td><td style='padding:6px; font-size:12px; text-align:right;'>${row['costo_otros']:,.2f}</td></tr>"

                if row['ref1_desc'] and row['ref1_precio'] > 0: filas_tabla += f"<tr><td style='padding:6px; font-size:12px;'><b>REFACCIÓN:</b> {row['ref1_desc']}</td><td style='padding:6px; font-size:12px; text-align:right;'>${row['ref1_precio']:,.2f}</td></tr>"
                if row['ref2_desc'] and row['ref2_precio'] > 0: filas_tabla += f"<tr><td style='padding:6px; font-size:12px;'><b>REFACCIÓN:</b> {row['ref2_desc']}</td><td style='padding:6px; font-size:12px; text-align:right;'>${row['ref2_precio']:,.2f}</td></tr>"
                if row['ref3_desc'] and row['ref3_precio'] > 0: filas_tabla += f"<tr><td style='padding:6px; font-size:12px;'><b>REFACCIÓN:</b> {row['ref3_desc']}</td><td style='padding:6px; font-size:12px; text-align:right;'>${row['ref3_precio']:,.2f}</td></tr>"
                if row['ref4_desc'] and row['ref4_precio'] > 0: filas_tabla += f"<tr><td style='padding:6px; font-size:12px;'><b>REFACCIÓN:</b> {row['ref4_desc']}</td><td style='padding:6px; font-size:12px; text-align:right;'>${row['ref4_precio']:,.2f}</td></tr>"
                if row['ref5_desc'] and row['ref5_precio'] > 0: filas_tabla += f"<tr><td style='padding:6px; font-size:12px;'><b>REFACCIÓN:</b> {row['ref5_desc']}</td><td style='padding:6px; font-size:12px; text-align:right;'>${row['ref5_precio']:,.2f}</td></tr>"

                logo_header_html = """
                <div style="background-color: #0d0d0d; padding: 15px 20px; position: relative; border-radius: 4px 4px 0 0; overflow: hidden;">
                    <div style="position: absolute; top: 0; right: 0; width: 140px; height: 35px; background: #e07a1e; border-bottom-left-radius: 50px;"></div>
                    <table width="100%" style="border: none;">
                        <tr>
                            <td style="border: none; vertical-align: middle;">
                                <div style="display: flex; align-items: center;">
                                    <span style="font-family: Arial, sans-serif; font-weight: 900; font-size: 42px; color: #ffffff; letter-spacing: -1px; line-height: 1;">EVMI</span>
                                </div>
                                <div style="font-family: Arial, sans-serif; font-weight: bold; font-size: 10px; color: #e07a1e; letter-spacing: 0.5px; margin-top: 4px;">
                                    ESPECIALISTAS EN VIBRACIONES Y MONTAJES INDUSTRIALES
                                </div>
                            </td>
                            <td align="right" style="border: none; vertical-align: middle; padding-top: 20px;">
                                <p style="color: #ffffff; margin: 0; font-size: 12px; font-family: Arial, sans-serif;">
                                    <b>Puebla, Pue. A {fecha}</b><br>
                                    <b>Folio:</b> {folio}<br>
                                    <b>Vigencia:</b> 30 días
                                </p>
                            </td>
                        </tr>
                    </table>
                </div>
                """.format(fecha=row['fecha'], folio=row['folio_cotizacion'])

                html_cotizacion = f"""
                <div class="cotizacion-container">
                    {logo_header_html}
                    <div style="padding: 20px;">
                        <h3 style="text-align:center; color:#1a365d; font-size:15px; margin-top:5px; margin-bottom:15px; font-family:Arial, sans-serif;">
                            <b>SERVICIO CORRECTIVO: {row['descripcion_equipo']}</b>
                        </h3>
                        <table width="100%" style="background-color:#f8fafc; border: 1px solid #cbd5e1; padding:8px; border-radius:4px; font-size:12px; font-family:Arial, sans-serif;">
                            <tr>
                                <td style="padding:3px;"><b>ATENCIÓN:</b> {row['atencion_a']}</td>
                                <td style="padding:3px;"><b>CONTACTO EVMI:</b> serviciosindustriales.evmi@outlook.com</td>
                            </tr>
                            <tr>
                                <td style="padding:3px;"><b>EMPRESA:</b> {row['empresa']}</td>
                                <td style="padding:3px;"><b>TEL:</b> 22.29.20.62.30 / 22.12.20.07.48</td>
                            </tr>
                            <tr>
                                <td style="padding:3px;"><b>CORREO:</b> {row['correo']}</td>
                                <td style="padding:3px;"><b>CIUDAD:</b> {row['ciudad']}</td>
                            </tr>
                        </table>
                        <p style="color:#334155; font-size:12px; font-family:Arial, sans-serif; margin-top:12px; margin-bottom:12px;">
                            En atención a su solicitud, envío a usted la cotización correspondiente a los servicios de su interés:
                        </p>
                        <table border="1" width="100%" style="border-collapse:collapse; text-align:left; border-color:#cbd5e1; font-family:Arial, sans-serif;">
                            <tr style="background-color:#1a365d; color:white;">
                                <th style="padding:8px; font-size:12px;">DESCRIPCIÓN DE SERVICIOS / REFACCIONES</th>
                                <th width="25%" style="padding:8px; font-size:12px; text-align:right;">PRECIO</th>
                            </tr>
                            {filas_tabla}
                        </table>
                        <br>
                        <table width="100%" style="font-family:Arial, sans-serif;">
                            <tr>
                                <td width="55%" style="vertical-align:top; color:#334155; font-size:11px;">
                                    <b>TIEMPO DE ENTREGA:</b> {row['tiempo_entrega']}<br>
                                    RECOLECCIÓN Y ENTREGA DONDE EL USUARIO LO SOLICITE.
                                </td>
                                <td width="45%">
                                    <table width="100%" border="1" style="border-collapse:collapse; border-color:#cbd5e1; font-size:12px;">
                                        <tr style="padding:4px;">
                                            <td><b>SUBTOTAL:</b></td>
                                            <td style="text-align:right;">${row['subtotal']:,.2f}</td>
                                        </tr>
                                        <tr style="padding:4px;">
                                            <td><b>IVA (16%):</b></td>
                                            <td style="text-align:right;">${row['iva']:,.2f}</td>
                                        </tr>
                                        <tr style="background-color:#1a365d; color:white; padding:4px;">
                                            <td><b>TOTAL:</b></td>
                                            <td style="text-align:right;"><b>${row['total']:,.2f}</b></td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
                """
                st.markdown(html_cotizacion, unsafe_allow_html=True)
            else:
                st.info("No hay cotizaciones registradas.")

    elif area == "Taller":
        sub_taller = st.radio("Módulo de Taller:", ["Llenar Reporte Técnico", "Ver / Imprimir Reporte Formato Físico"], horizontal=True)

        if sub_taller == "Llenar Reporte Técnico":
            st.header("📋 Llenado de Reporte Técnico de Taller")
            df_rec = pd.read_sql_query("SELECT folio, cliente, equipo, potencia, rpm FROM recepcion", conn)
            
            if not df_rec.empty:
                sel_folio = st.selectbox("Buscar Equipo por Folio de Recepción:", df_rec["folio"] + " - " + df_rec["cliente"] + " (" + df_rec["equipo"] + ")")
                folio_id = sel_folio.split(" - ")[0]
                rec_data = df_rec[df_rec["folio"] == folio_id].iloc[0]

                # Cargar datos guardados previamente si existen
                df_rep_prev = pd.read_sql_query("SELECT * FROM reportes_tecnicos WHERE folio_recepcion = ?", conn, params=(folio_id,))
                prev = df_rep_prev.iloc[0] if not df_rep_prev.empty else None

                with st.form("form_reporte_tecnico"):
                    st.subheader(f"Reporte Técnico para Folio: {folio_id}")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        tecnico = st.text_input("Técnico que Desarmó:", value=prev['tecnico'] if prev is not None else "")
                        empresa = st.text_input("Empresa:", value=rec_data['cliente'])
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
                    
                    datos_comp = {}
                    col_header = st.columns([2, 1, 1, 3])
                    col_header[0].markdown("**COMPONENTE**")
                    col_header[1].markdown("**TRAE**")
                    col_header[2].markdown("**DAÑOS**")
                    col_header[3].markdown("**MEDIDAS O EXTRAS**")

                    for item in LISTA_COMPONENTES:
                        c_item, c_trae, c_danos, c_medidas = st.columns([2, 1, 1, 3])
                        c_item.text(item)
                        trae_val = c_trae.selectbox("", ["SI", "NO"], key=f"trae_{item}")
                        dano_val = c_danos.selectbox("", ["NO", "SI"], key=f"dano_{item}")
                        medida_val = c_medidas.text_input("", key=f"med_{item}", label_visibility="collapsed")
                        
                        datos_comp[item] = {"trae": trae_val, "danos": dano_val, "medidas": medida_val}

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
                        import json
                        comp_json = json.dumps(datos_comp)
                        c = conn.cursor()
                        c.execute('''
                            INSERT OR REPLACE INTO reportes_tecnicos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        ''', (folio_id, tecnico, empresa, marca, ampers, fases, volts, rpm, kwhp, hz, tipo,
                              rod_lc, rod_lcc, no_serie, comp_json, observaciones, recomendaciones,
                              in_megohms, in_volts, in_ampers, in_ohms, out_megohms, out_volts, out_ampers, out_ohms))
                        c.execute("UPDATE recepcion SET estatus=? WHERE folio=?", ("Inspeccionado en Taller", folio_id))
                        conn.commit()
                        st.success(f"Reporte técnico para {folio_id} guardado con éxito.")
            else:
                st.info("No hay equipos en recepción.")

        elif sub_taller == "Ver / Imprimir Reporte Formato Físico":
            st.header("🖨️ Formato de Imprimiendo de Reporte Técnico")
            df_rep = pd.read_sql_query("SELECT folio_recepcion, empresa, tecnico FROM reportes_tecnicos", conn)
            
            if not df_rep.empty:
                sel_rep = st.selectbox("Seleccionar Reporte a Mostrar/Imprimir:", df_rep["folio_recepcion"] + " - " + df_rep["empresa"])
                folio_id = sel_rep.split(" - ")[0]
                row = pd.read_sql_query("SELECT * FROM reportes_tecnicos WHERE folio_recepcion = ?", conn, params=(folio_id,)).iloc[0]
                import json
                comp_data = json.loads(row['componentes_json'])

                # Generación de Tabla de Componentes HTML estilo hoja física
                filas_comp = ""
                for item in LISTA_COMPONENTES:
                    info = comp_data.get(item, {"trae": "NO", "danos": "NO", "medidas": ""})
                    t_si = "X" if info['trae'] == "SI" else ""
                    t_no = "X" if info['trae'] == "NO" else ""
                    d_si = "X" if info['danos'] == "SI" else ""
                    d_no = "X" if info['danos'] == "NO" else ""
                    
                    filas_comp += f"""
                    <tr>
                        <td style='padding:2px 5px; font-size:10px; font-weight:bold;'>{item}</td>
                        <td style='padding:2px; text-align:center; font-size:10px;'>{t_si}</td>
                        <td style='padding:2px; text-align:center; font-size:10px;'>{t_no}</td>
                        <td style='padding:2px; text-align:center; font-size:10px;'>{d_si}</td>
                        <td style='padding:2px; text-align:center; font-size:10px;'>{d_no}</td>
                        <td style='padding:2px 5px; font-size:10px;'>{info['medidas']}</td>
                    </tr>
                    """

                html_reporte = f"""
                <div class="cotizacion-container" style="font-family: Arial, sans-serif; color: #000; padding: 15px;">
                    <!-- Encabezado con Nombre de Laura Alejandra y RFC -->
                    <table width="100%" style="border-bottom: 2px solid #000; padding-bottom: 5px;">
                        <tr>
                            <td width="20%">
                                <div style="font-weight:900; font-size:28px;">EVMI</div>
                            </td>
                            <td width="80%" align="center">
                                <div style="font-weight:bold; font-size:18px;">E V M I</div>
                                <div style="font-size:10px; font-weight:bold;">ESPECIALISTAS EN VIBRACIONES Y MONTAJES INDUSTRIALES</div>
                                <div style="font-size:9px;">LAURA ALEJANDRA OJEDA SANCHEZ &nbsp;&nbsp;&nbsp; R.F.C. OESL870111GP0</div>
                            </td>
                        </tr>
                    </table>

                    <div style="text-align:center; font-size:11px; font-weight:bold; margin: 8px 0;">REPORTE TECNICO ({row['folio_recepcion']})</div>

                    <!-- Datos Generales -->
                    <table width="100%" style="font-size:10px; border-collapse:collapse; margin-bottom:8px;">
                        <tr>
                            <td width="40%"><b>TECNICO QUE DESARMO:</b> {row['tecnico']}</td>
                            <td width="30%"><b>AMPERS:</b> {row['ampers']}</td>
                            <td width="30%"><b>RPM:</b> {row['rpm']}</td>
                        </tr>
                        <tr>
                            <td><b>EMPRESA:</b> {row['empresa']}</td>
                            <td><b>FASES:</b> {row['fases']}</td>
                            <td><b>KW/HP:</b> {row['kwhp']}</td>
                        </tr>
                        <tr>
                            <td><b>MARCA:</b> {row['marca']}</td>
                            <td><b>VOLTS:</b> {row['volts']}</td>
                            <td><b>HZ:</b> {row['hz']} &nbsp;&nbsp; <b>TIPO:</b> {row['tipo']}</td>
                        </tr>
                        <tr>
                            <td colspan="2"><b>RODAMIENTO LC:</b> {row['rod_lc']} &nbsp;&nbsp;&nbsp;&nbsp; <b>LCC:</b> {row['rod_lcc']}</td>
                            <td><b>N° DE SERIE:</b> {row['no_serie']}</td>
                        </tr>
                    </table>

                    <!-- Tabla Completa de Inspección -->
                    <table border="1" width="100%" style="border-collapse:collapse; border-color:#000; font-size:10px; margin-bottom:8px;">
                        <thead>
                            <tr style="background-color:#e2e8f0; text-align:center;">
                                <th rowspan="2" width="28%">TRAE</th>
                                <th colspan="2" width="16%">TRAE</th>
                                <th colspan="2" width="16%">DAÑOS</th>
                                <th rowspan="2" width="40%">MEDIDAS O EXTRAS</th>
                            </tr>
                            <tr style="background-color:#e2e8f0; text-align:center;">
                                <th width="8%">SI</th>
                                <th width="8%">NO</th>
                                <th width="8%">SI</th>
                                <th width="8%">NO</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filas_comp}
                        </tbody>
                    </table>

                    <!-- Observaciones y Recomendaciones -->
                    <div style="font-size:10px; margin-bottom:4px;"><b>OBSERVACIONES:</b> {row['observaciones']}</div>
                    <div style="border-bottom: 1px solid #000; margin-bottom:8px;"></div>
                    
                    <div style="font-size:10px; margin-bottom:4px;"><b>RECOMENDACIONES:</b> {row['recomendaciones']}</div>
                    <div style="border-bottom: 1px solid #000; margin-bottom:12px;"></div>

                    <!-- Valores Eléctricos -->
                    <div style="text-align:center; font-size:10px; font-weight:bold; margin-bottom:4px;">VALORES DE ENTRADA</div>
                    <table width="100%" style="font-size:9px; text-align:center; margin-bottom:8px;">
                        <tr>
                            <td><b>MEGAOHMS:</b> {row['in_megohms']}</td>
                            <td><b>VOLTS:</b> {row['in_volts']}</td>
                            <td><b>AMPERES:</b> {row['in_ampers']}</td>
                            <td><b>OHMS:</b> {row['in_ohms']}</td>
                        </tr>
                    </table>

                    <div style="text-align:center; font-size:10px; font-weight:bold; margin-bottom:4px;">VALORES DE SALIDA</div>
                    <table width="100%" style="font-size:9px; text-align:center;">
                        <tr>
                            <td><b>MEGAOHMS:</b> {row['out_megohms']}</td>
                            <td><b>VOLTS:</b> {row['out_volts']}</td>
                            <td><b>AMPERES:</b> {row['out_ampers']}</td>
                            <td><b>OHMS:</b> {row['out_ohms']}</td>
                        </tr>
                    </table>
                </div>
                """
                st.markdown(html_reporte, unsafe_allow_html=True)

            else:
                st.info("No hay reportes técnicos guardados.")

    elif area == "Embobinado":
        st.header("⚡ Datos Técnicos de Embobinado")
        df_rec = pd.read_sql_query("SELECT folio, cliente, equipo FROM recepcion", conn)
        if not df_rec.empty:
            folio_sel = st.selectbox("Seleccionar Folio de Trabajo:", df_rec["folio"] + " - " + df_rec["cliente"] + " (" + df_rec["equipo"] + ")")
            folio_id = folio_sel.split(" - ")[0]

            with st.form("form_embobinado"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    conexion = st.text_input("Conexión")
                    calibre = st.text_input("Calibre Alambre AWG")
                with c2:
                    paso = st.text_input("Paso de Ranura")
                    vueltas = st.text_input("Vueltas por Bobina")
                with c3:
                    peso = st.text_input("Peso Cobre (kg)")
                    aislamiento = st.text_input("Clase de Aislamiento")
                megger = st.text_input("Prueba Megger")

                if st.form_submit_button("Guardar Ficha"):
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO embobinado VALUES (?,?,?,?,?,?,?,?)", 
                              (folio_id, conexion, calibre, paso, vueltas, peso, aislamiento, megger))
                    c.execute("UPDATE recepcion SET estatus=? WHERE folio=?", ("En Embobinado", folio_id))
                    conn.commit()
                    st.success("Ficha técnica guardada.")
        else:
            st.info("No hay equipos registrados.")

    conn.close()
