import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(page_title="Portal EVMI - Taller", layout="wide")

USUARIOS = {
    "oficina": "oficina123",
    "taller": "taller123",
    "embobinado": "cobre123"
}

ARCHIVO_DATOS = "datos_evmi_web.json"

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

datos = cargar_datos()

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["area"] = None

if not st.session_state["autenticado"]:
    st.title("⚙️ Portal EVMI - Control de Acceso")
    col1, col2 = st.columns(2)
    with col1:
        area_seleccionada = st.selectbox("Selecciona tu Área:", ["Oficina", "Taller", "Embobinado"])
        password = st.text_input("Contraseña de acceso:", type="password")
        
        if st.button("Ingresar al Portal"):
            clave_area = area_seleccionada.lower()
            if password == USUARIOS.get(clave_area):
                st.session_state["autenticado"] = True
                st.session_state["area"] = area_seleccionada
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
else:
    st.sidebar.title(f"Área: {st.session_state['area']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.session_state["area"] = None
        st.rerun()

    area = st.session_state["area"]

    if area == "Oficina":
        st.header("🏢 Módulo de Oficina - Recepción y Cotización")
        with st.form("form_oficina"):
            num_folio = f"EVMI-{len(datos) + 1:04d}"
            st.subheader(f"Folio Sugerido: {num_folio}")
            cliente = st.text_input("Nombre de Empresa / Cliente:")
            equipo = st.text_input("Descripción del Equipo (ej. Motor 25 HP):")
            tipo_servicio = st.selectbox("Tipo de Servicio:", ["Servicio Normal", "Solo Cotización", "URGENTE"])
            costo_cotizado = st.number_input("Monto Cotizado ($ MXN):", min_value=0.0)
            orden_compra = st.text_input("Folio de Orden de Compra (O.C.):")
            
            guardar = st.form_submit_button("Registrar Orden")
            if guardar:
                if num_folio not in datos:
                    datos[num_folio] = {}
                datos[num_folio]["oficina"] = {
                    "fecha": datetime.now().strftime("%d/%m/%Y"),
                    "cliente": cliente,
                    "equipo": equipo,
                    "prioridad": tipo_servicio,
                    "monto": costo_cotizado,
                    "oc": orden_compra
                }
                guardar_datos(datos)
                st.success(f"Orden {num_folio} guardada.")

    elif area == "Taller":
        st.header("🔧 Módulo de Taller - Evaluación Mecánica")
        folio_sel = st.selectbox("Selecciona Folio a Trabajar:", list(datos.keys()) if datos else ["No hay folios"])
        if folio_sel in datos:
            st.info(f"Cliente: {datos[folio_sel].get('oficina', {}).get('cliente', 'S/D')} | Equipo: {datos[folio_sel].get('oficina', {}).get('equipo', 'S/D')}")
            with st.form("form_taller"):
                diagnostico = st.text_area("Diagnóstico Falla / Evaluación:")
                rodamientos = st.text_input("Medidas de Rodamientos:")
                refacciones = st.text_area("Refacciones Requeridas:")
                
                guardar = st.form_submit_button("Guardar Datos de Taller")
                if guardar:
                    datos[folio_sel]["taller"] = {
                        "diagnostico": diagnostico,
                        "rodamientos": rodamientos,
                        "refacciones": refacciones
                    }
                    guardar_datos(datos)
                    st.success(f"Datos guardados para {folio_sel}.")

    elif area == "Embobinado":
        st.header("⚡ Módulo de Embobinado - Toma de Datos")
        folio_sel = st.selectbox("Selecciona Folio a Trabajar:", list(datos.keys()) if datos else ["No hay folios"])
        if folio_sel in datos:
            st.info(f"Cliente: {datos[folio_sel].get('oficina', {}).get('cliente', 'S/D')} | Equipo: {datos[folio_sel].get('oficina', {}).get('equipo', 'S/D')}")
            with st.form("form_embobinado"):
                col1, col2 = st.columns(2)
                with col1:
                    conexion = st.text_input("Conexión:")
                    calibre = st.text_input("Calibre Alambre AWG:")
                    paso = st.text_input("Paso de Ranura:")
                with col2:
                    vueltas = st.text_input("Vueltas por Bobina:")
                    aislamiento = st.text_input("Clase de Aislamiento:")
                    megger = st.text_input("Prueba Megger:")
                
                guardar = st.form_submit_button("Guardar Embobinado")
                if guardar:
                    datos[folio_sel]["embobinado"] = {
                        "conexion": conexion, "calibre": calibre, "paso": paso,
                        "vueltas": vueltas, "aislamiento": aislamiento, "megger": megger
                    }
                    guardar_datos(datos)
                    st.success(f"Ficha guardada para {folio_sel}.")

    st.divider()
    st.subheader("📋 Consultar Orden / Ficha Unificada")
    if datos:
        folio_ver = st.selectbox("Buscar Folio:", list(datos.keys()), key="consulta")
        if folio_ver:
            st.json(datos[folio_ver])
