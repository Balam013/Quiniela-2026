import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# Configuración de la página web
st.set_page_config(page_title="Quiniela Mundial 2026", layout="wide")
st.title("🏆 Quiniela Mundial 2026")

# Estructura oficial de llaves a partir de 4tos (Hora de Guatemala)
ESTRUCTURA_PARTIDOS = {
    "Octavos 1": {"fase": "1/8", "e1_key": "O1_E1", "e2_key": "O1_E2", "dep": None, "inicio": "2026-06-27 14:00"},
    "Octavos 2": {"fase": "1/8", "e1_key": "O2_E1", "e2_key": "O2_E2", "dep": None, "inicio": "2026-06-27 18:00"},
    "Octavos 3": {"fase": "1/8", "e1_key": "O3_E1", "e2_key": "O3_E2", "dep": None, "inicio": "2026-06-28 14:00"},
    "Octavos 4": {"fase": "1/8", "e1_key": "O4_E1", "e2_key": "O4_E2", "dep": None, "inicio": "2026-06-28 18:00"},
    "Octavos 5": {"fase": "1/8", "e1_key": "O5_E1", "e2_key": "O5_E2", "dep": None, "inicio": "2026-06-29 14:00"},
    "Octavos 6": {"fase": "1/8", "e1_key": "O6_E1", "e2_key": "O6_E2", "dep": None, "inicio": "2026-06-29 18:00"},
    "Octavos 7": {"fase": "1/8", "e1_key": "O7_E1", "e2_key": "O7_E2", "dep": None, "inicio": "2026-06-30 14:00"},
    "Octavos 8": {"fase": "1/8", "e1_key": "O8_E1", "e2_key": "O8_E2", "dep": None, "inicio": "2026-06-30 18:00"},
    
    "Cuartos 1": {"fase": "1/4", "dep": ("Octavos 2", "Octavos 1"), "tipo_dep": "ganadores", "inicio": "2026-07-03 14:00"},
    "Cuartos 2": {"fase": "1/4", "dep": ("Octavos 6", "Octavos 5"), "tipo_dep": "ganadores", "inicio": "2026-07-03 18:00"},
    "Cuartos 3": {"fase": "1/4", "dep": ("Octavos 3", "Octavos 4"), "tipo_dep": "ganadores", "inicio": "2026-07-04 14:00"},
    "Cuartos 4": {"fase": "1/4", "dep": ("Octavos 7", "Octavos 8"), "tipo_dep": "ganadores", "inicio": "2026-07-04 18:00"},
    
    "Semifinal 1": {"fase": "Semis", "dep": ("Cuartos 1", "Cuartos 2"), "tipo_dep": "ganadores", "inicio": "2026-07-08 18:00"},
    "Semifinal 2": {"fase": "Semis", "dep": ("Cuartos 3", "Cuartos 4"), "tipo_dep": "ganadores", "inicio": "2026-07-09 18:00"},
    
    "Tercer Lugar": {"fase": "3er Lugar", "dep": ("Semifinal 1", "Semifinal 2"), "tipo_dep": "perdedores", "inicio": "2026-07-18 14:00"},
    "Gran Final": {"fase": "Final", "dep": ("Semifinal 1", "Semifinal 2"), "tipo_dep": "ganadores", "inicio": "2026-07-19 15:00"}
}

PARTIDOS_LISTA = list(ESTRUCTURA_PARTIDOS.keys())

BANDERAS = {
    "canada": "🇨🇦", "canadá": "🇨🇦",
    "marruecos": "🇲🇦",
    "paraguay": "🇵🇾",
    "francia": "🇫🇷",
    "brasil": "🇧🇷", "brazil": "🇧🇷",
    "noruega": "🇳🇴",
    "mexico": "🇲🇽", "méxico": "🇲🇽",
    "inglaterra": "🇬🇧",
    "suiza": "🇨🇭",
    "usa": "🇺🇸", "estados unidos": "🇺🇸",
    "belgica": "🇧🇪", "bélgica": "🇧🇪",
    "españa": "🇪🇸", "espana": "🇪🇸",
    "portugal": "🇵🇹",
    "argentina": "🇦🇷",
    "cabo verde": "🇨🇻",
    "colombia": "🇨🇴",
    "ghana": "🇬🇭",
    "australia": "🇦🇺",
    "egipto": "🇪🇬"
}

def obtener_emoji_pais(nombre_pais):
    nombre_limpio = str(nombre_pais).strip().lower()
    for pais, emoji in BANDERAS.items():
        if pais in nombre_limpio: return f"{emoji} {nombre_pais}"
    return f"⚽ {nombre_pais}"

FILAS_EXCEL = []
for p in PARTIDOS_LISTA: FILAS_EXCEL.extend([f"{p}_g1", f"{p}_g2", f"{p}_avanza"])
EQUIPOS_OCTAVOS_KEYS = [f"O{i}_E{j}" for i in range(1, 9) for j in (1, 2)]
TODAS_LAS_FILAS = EQUIPOS_OCTAVOS_KEYS + FILAS_EXCEL

# Conectar a la hoja usando la configuración de secretos
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        df_cloud = conn.read(worksheet="Resultados", ttl=0)
        if not df_cloud.empty and "ID_Fila" in df_cloud.columns:
            df_cloud.set_index("ID_Fila", inplace=True)
            for fila in TODAS_LAS_FILAS:
                if fila not in df_cloud.index: df_cloud.loc[fila] = "-"
            return df_cloud
    except Exception as e:
        pass
    
    df_init = pd.DataFrame(index=TODAS_LAS_FILAS, columns=["Resultado Real"])
    df_init.fillna("-", inplace=True)
    df_init.index.name = "ID_Fila"
    conn.update(worksheet="Resultados", data=df_init.reset_index())
    return df_init

df = cargar_datos()

def guardar_datos(dataframe_actual):
    df_para_guardar = dataframe_actual.reset_index()
    conn.update(worksheet="Resultados", data=df_para_guardar)
    st.cache_data.clear()

def partido_esta_cerrado(fecha_inicio_str):
    try:
        hora_partido = datetime.strptime(fecha_inicio_str, "%Y-%m-%d %H:%M")
        return datetime.now() >= (hora_partido - timedelta(minutes=5))
    except:
        return False

def obtener_ganador_real(partido_id):
    g1, g2 = df.at[f"{partido_id}_g1", "Resultado Real"], df.at[f"{partido_id}_g2", "Resultado Real"]
    avanza = df.at[f"{partido_id}_avanza", "Resultado Real"]
    if g1 == "-" or g2 == "-": return None, None
    return avanza, avanza

def obtener_equipos_partido(partido_id):
    info = ESTRUCTURA_PARTIDOS[partido_id]
    if info["dep"] is None:
        e1_n, e2_n = df.at[info["e1_key"], "Resultado Real"], df.at[info["e2_key"], "Resultado Real"]
        e1 = e1_n if e1_n != "-" and str(e1_n).strip() != "" else f"Equipo 1 ({partido_id})"
        e2 = e2_n if e2_n != "-" and str(e2_n).strip() != "" else f"Equipo 2 ({partido_id})"
        return e1, e2
    
    p1, p2 = info["dep"]
    if info["tipo_dep"] == "ganadores":
        g1, _ = obtener_ganador_real(p1)
        g2, _ = obtener_ganador_real(p2)
        e1 = g1 if g1 else f"Ganador {p1}"
        e2 = g2 if g2 else f"Ganador {p2}"
    else: 
        s1_avanza = df.at[f"{p1}_avanza", "Resultado Real"]
        s1_e1, s1_e2 = obtener_equipos_partido(p1)
        s2_avanza = df.at[f"{p2}_avanza", "Resultado Real"]
        s2_e1, s2_e2 = obtener_equipos_partido(p2)
        
        e1 = f"Perdedor {p1}"
        if s1_avanza != "-": e1 = s1_e2 if str(s1_avanza).strip().lower() == str(s1_e1).strip().lower() else s1_e1
        e2 = f"Perdedor {p2}"
        if s2_avanza != "-": e2 = s2_e2 if str(s2_avanza).strip().lower() == str(s2_e1).strip().lower() else s2_e1
    return e1, e2

tab1, tab2, tab3 = st.tabs(["📝 Meter Marcadores", "📊 Tabla de Posiciones", "⚙️ Panel Administrador"])
participantes_actuales = [col for col in df.columns if col != "Resultado Real"]

with tab1:
    st.header("Registra tus marcadores exactos")
    st.warning("⚠️ **¡Atención!** El ingreso de marcadores se bloquea automáticamente **5 minutos antes** de cada juego.")
    
    opcion_registro = st.radio("¿Qué deseas hacer?", ["Registrar un nombre NUEVO", "Actualizar mis marcadores"], horizontal=True)
    usuario = st.text_input("Escribe tu nombre y apellido:", key="nuevo_nombre").strip() if opcion_registro == "Registrar un nombre NUEVO" else (st.selectbox("Selecciona tu nombre:", participantes_actuales) if participantes_actuales else "")

    if usuario:
        if usuario not in df.columns: df[usuario] = "-"
            
        with st.form(key=f"form_{usuario}"):
            st.write(f"### Quiniela de: **{usuario}**")
            nuevos_datos = {}
            
            for fase in ["1/8", "1/4", "Semis", "3er Lugar", "Final"]:
                st.write(f"---")
                st.markdown(f"<h3 style='text-align: center; color: #1E3A8A;'>Fase: {fase}</h3>", unsafe_allow_html=True)
                
                for pid, info in ESTRUCTURA_PARTIDOS.items():
                    if info["fase"] == fase:
                        e1_raw, e2_raw = obtener_equipos_partido(pid)
                        e1, e2 = obtener_emoji_pais(e1_raw), obtener_emoji_pais(e2_raw)
                        cerrado = partido_esta_cerrado(info["inicio"])
                        
                        v1 = str(df.at[f"{pid}_g1", usuario]) if df.at[f"{pid}_g1", usuario] != "-" else ""
                        v2 = str(df.at[f"{pid}_g2", usuario]) if df.at[f"{pid}_g2", usuario] != "-" else ""
                        v_avanza = str(df.at[f"{pid}_avanza", usuario]) if df.at[f"{pid}_avanza", usuario] != "-" else ""
                        
                        nuevos_datos[f"{pid}_g1"] = v1 if v1 != "" else "-"
                        nuevos_datos[f"{pid}_g2"] = v2 if v2 != "" else "-"
                        nuevos_datos[f"{pid}_avanza"] = v_avanza if v_avanza != "" else "-"

                        col1, col2, col3, col4 = st.columns([4, 1, 1, 4])
                        with col1: st.markdown(f"<p style='text-align: right; font-size: 18px; margin-top: 5px;'><b>{e1}</b></p>", unsafe_allow_html=True)
                        with col2:
                            if cerrado: st.markdown(f"<p style='text-align: center; font-size: 18px;'>🔒 <b>{v1 if v1 != '' else '-'}</b></p>", unsafe_allow_html=True)
                            else: nuevos_datos[f"{pid}_g1"] = st.text_input("G1", value=v1, key=f"{usuario}_{pid}_g1", label_visibility="collapsed")
                        with col3:
                            if cerrado: st.markdown(f"<p style='text-align: center; font-size: 18px;'>🔒 <b>{v2 if v2 != '' else '-'}</b></p>", unsafe_allow_html=True)
                            else: nuevos_datos[f"{pid}_g2"] = st.text_input("G2", value=v2, key=f"{usuario}_{pid}_g2", label_visibility="collapsed")
                        with col4: st.markdown(f"<p style='text-align: left; font-size: 18px; margin-top: 5px;'><b>{e2}</b></p>", unsafe_allow_html=True)
                            
                        if cerrado:
                            st.markdown(f"<p style='text-align: center; color: #DC2626;'>🔒 Bloqueado. Clasifica: <b>{v_avanza if v_avanza != '' else '-'}</b></p>", unsafe_allow_html=True)
                        else:
                            _, sub_col2, _ = st.columns([2, 4, 2])
                            with sub_col2: nuevos_datos[f"{pid}_avanza"] = st.text_input(f"¿Quién avanza en {pid}?", value=v_avanza, key=f"{usuario}_{pid}_avanza")
            
            boton_guardar = st.form_submit_button("Guardar mi Quiniela Exacta")
            if boton_guardar:
                for clv, val in nuevos_datos.items():
                    df.at[clv, usuario] = val if (isinstance(val, str) and val.strip() != "") else "-"
                guardar_datos(df)
                st.success("¡Tus marcadores se guardaron en Google Sheets!")
                st.rerun()

with tab2:
    st.header("🏆 Tabla General de Puntos")
    st.info("🎯 **Reglas:** 5 pts exacto | 3 pts ganador | 1 pt diferencia.\n⏳ *Bloqueo automático 5 minutos antes de cada juego.*")
    
    puntos = {p: 0 for p in participantes_actuales}
    for pid in PARTIDOS_LISTA:
        r1, r2 = df.at[f"{pid}_g1", "Resultado Real"], df.at[f"{pid}_g2", "Resultado Real"]
        r_avanza = str(df.at[f"{pid}_avanza", "Resultado Real"]).strip().lower()
        
        if r1 != "-" and r2 != "-":
            r1, r2 = int(r1), int(r2)
            dif_real = r1 - r2
            for p in participantes_actuales:
                p1, p2 = df.at[f"{pid}_g1", p], df.at[f"{pid}_g2", p]
                p_avanza = str(df.at[f"{pid}_avanza", p]).strip().lower()
                
                if p1 != "-" and p2 != "-":
                    p1, p2 = int(p1), int(p2)
                    if p1 == r1 and p2 == r2:
                        if p1 == p2:
                            if p_avanza == r_avanza: puntos[p] += 5
                        else: puntos[p] += 5
                    elif (p1 > p2 and r1 > r2) or (p2 > p1 and r2 > r1) or (p1 == p2 and p_avanza == r_avanza):
                        puntos[p] += 3
                    elif (p1 - p2) == dif_real: puntos[p] += 1

    df_puntos = pd.DataFrame(list(puntos.items()), columns=["Participante", "Puntos Totales"]).sort_values(by="Puntos Totales", ascending=False).reset_index(drop=True)
    st.table(df_puntos)

with tab3:
    st.header("⚙️ Panel Administrador")
    st.subheader("1. Configurar Clasificados Reales a Octavos")
    with st.form(key="form_equipos_octavos"):
        octavos_inputs = {}
        for i in range(1, 9):
            k1, k2 = f"O{i}_E1", f"O{i}_E2"
            v_e1 = str(df.at[k1, "Resultado Real"]) if df.at[k1, "Resultado Real"] != "-" else ""
            v_e2 = str(df.at[k2, "Resultado Real"]) if df.at[k2, "Resultado Real"] != "-" else ""
            st.write(f"**Definir Octavos {i}**")
            col_a, col_b = st.columns(2)
            with col_a: octavos_inputs[k1] = st.text_input(f"Local O{i}", value=v_e1, key=f"ad_in_{k1}")
            with col_b: octavos_inputs[k2] = st.text_input(f"Visitante O{i}", value=v_e2, key=f"ad_in_{k2}")
            st.write("---")
        if st.form_submit_button("Guardar Equipos de Octavos"):
            for clv, val in octavos_inputs.items(): df.at[clv, "Resultado Real"] = val if val.strip() != "" else "-"
            guardar_datos(df)
            st.success("¡Equipos iniciales configurados en la nube!")
            st.rerun()

    st.subheader("2. Cargar Resultados Oficiales")
    with st.form(key="form_admin_resultados"):
        admin_datos = {}
        for pid in PARTIDOS_LISTA:
            e1, e2 = obtener_equipos_partido(pid)
            v1 = str(df.at[f"{pid}_g1", "Resultado Real"]) if df.at[f"{pid}_g1", "Resultado Real"] != "-" else ""
            v2 = str(df.at[f"{pid}_g2", "Resultado Real"]) if df.at[f"{pid}_g2", "Resultado Real"] != "-" else ""
            v_avanza = str(df.at[f"{pid}_avanza", "Resultado Real"]) if df.at[f"{pid}_avanza", "Resultado Real"] != "-" else ""
            
            st.write(f"**{pid}**")
            col1, col2, col3, col4 = st.columns([3, 1, 1, 3])
            with col1: st.write(f"{e1}")
            with col2: admin_datos[f"{pid}_g1"] = st.text_input("G1", value=v1, key=f"ad_{pid}_g1", label_visibility="collapsed")
            with col3: admin_datos[f"{pid}_g2"] = st.text_input("G2", value=v2, key=f"ad_{pid}_g2", label_visibility="collapsed")
            with col4: st.write(f"{e2}")
            admin_datos[f"{pid}_avanza"] = st.text_input(f"Clasificó {pid}:", value=v_avanza, key=f"ad_{pid}_avanza")
            st.write("---")
        if st.form_submit_button("Guardar Resultados Oficiales"):
            for clv, val in admin_datos.items(): df.at[clv, "Resultado Real"] = val if val.strip() != "" else "-"
            guardar_datos(df)
            st.success("¡Resultados oficiales actualizados!")
            st.rerun()