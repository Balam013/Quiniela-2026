import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import pytz

# =====================================================================
# CONFIGURACIÓN, HORARIOS Y CONEXIÓN
# =====================================================================
st.set_page_config(page_title="Quiniela 2026", page_icon="🏆", layout="centered")

# Configurar Zona Horaria de Guatemala
ZONA_GT = pytz.timezone("America/Guatemala")
ahora_gt = datetime.now(ZONA_GT)

conn = st.connection("gsheets", type=GSheetsConnection)

# FUNCIÓN DE CARGA CON CACHÉ DE VERDAD (EVITA EL ERROR 429)
@st.cache_data(ttl=60)
def cargar_datos(nombre_hoja):
    conexion = st.connection("gsheets", type=GSheetsConnection)
    return conexion.read(worksheet=nombre_hoja)

# =====================================================================
# DICCIONARIO DE BANDERAS
# =====================================================================
BANDERAS = {
    "Francia": "🇫🇷", "Paraguay": "🇵🇾", "Canadá": "🇨🇦", "Marruecos": "🇲🇦",
    "Brasil": "🇧🇷", "Noruega": "🇳🇴", "México": "🇲🇽", "Inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Portugal": "🇵🇹", "España": "🇪🇸", "EE.UU": "🇺🇸", "EEUU": "🇺🇸", "Bélgica": "🇧🇪",
    "Suiza": "🇨🇭", "Argentina": "🇦🇷", "Colombia": "🇨🇴", "Ghana": "🇬🇭",
    "Egipto": "🇪🇬", "Australia": "🇦🇺", "Cabo Verde": "🇨🇻"
}

def obtener_nombre_con_bandera(nombre_equipo):
    nombre_limpio = str(nombre_equipo).strip()
    if nombre_limpio in BANDERAS:
        return f"{nombre_limpio} {BANDERAS[nombre_limpio]}"
    return nombre_limpio

# =====================================================================
# REGLAS DE PUNTAJE MODO PRO (INCLUYE CLASIFICADO / PENALES)
# =====================================================================
def calcular_puntos(pronostico, resultado_real):
    if pd.isna(pronostico) or pd.isna(resultado_real) or resultado_real == "" or pronostico == "":
        return 0
    
    puntos = 0
    try:
        pronostico_str = str(pronostico).strip()
        clasificado_pro = None
        if "|" in pronostico_str:
            marcador_pro, clasificado_pro = map(str.strip, pronostico_str.split("|"))
        else:
            marcador_pro = pronostico_str

        res_real_str = str(resultado_real).strip()
        clasificado_real = None
        
        if "(" in res_real_str:
            marcador_real = res_real_str.split("(")[0].strip()
            penales_str = res_real_str.split("(")[1].replace(")", "").strip()
            pen_a, pen_b = map(int, penales_str.split("-"))
            clasificado_real = "A" if pen_a > pen_b else "B"
        else:
            marcador_real = res_real_str

        goles_pro_a, goles_pro_b = map(int, marcador_pro.split("-"))
        goles_real_a, goles_real_b = map(int, marcador_real.split("-"))
        
        if clasificado_real is None:
            if goles_real_a > goles_real_b:
                clasificado_real = "A"
            elif goles_real_b > goles_real_a:
                clasificado_real = "B"
            else:
                clasificado_real = "Empate"

        if goles_pro_a == goles_real_a and goles_pro_b == goles_real_b:
            puntos += 3  
        elif (goles_pro_a > goles_pro_b and goles_real_a > goles_real_b) or \
             (goles_pro_a < goles_pro_b and goles_real_a < goles_real_b) or \
             (goles_pro_a == goles_pro_b and goles_real_a == goles_real_b):
            puntos += 1  

        if clasificado_pro and clasificado_real:
            if (clasificado_pro == "A" and clasificado_real == "A") or (clasificado_pro == "B" and clasificado_real == "B"):
                puntos += 1 

    except:
        pass
    return puntos

# =====================================================================
# CARGAR BASES DE DATOS ESENCIALES
# =====================================================================
try:
    df_partidos = cargar_datos("PARTIDOS")  
except Exception as e:
    st.error(f"⚠️ Error al leer la pestaña PARTIDOS: {e}")
    df_partidos = pd.DataFrame(columns=["ID", "EquipoA", "EquipoB", "FechaHora", "Tipo"])

try:
    df_resultados = cargar_datos("RESULTADOS")
except Exception:
    df_resultados = pd.DataFrame(columns=["ID", "ResultadoReal"])

# =====================================================================
# INTERFAZ PRINCIPAL
# =====================================================================
st.title("🏆 Quiniela Pro 2026")

with st.expander("📖 ¡Haz clic aquí para ver las INSTRUCCIONES DE USO DE LA PÁGINA! 🤔", expanded=True):
    st.markdown("""
    ### 📱 Guía rápida para navegar por la plataforma:
    1. **📝 Registrar Pronósticos:** Aquí metes tus marcadores. Si eres nuevo, selecciona *"Registrarme por primera vez"*, escribe tu nombre y confírmalo. Si vas a corregir algún gol de partidos que no han empezado, cambia a *"Actualizar mis pronósticos existentes"* y búscate en la lista. ¡No olvides darle al botón **`Guardar mi Quiniela Pro 🚀`** al final!
    2. **📊 Tabla de Posiciones:** Revisa el ranking familiar en tiempo real. Aquí verás quién va a la cabeza con sus medallas correspondientes y el desglose de lo que metió cada quien.
    3. **🔍 Mis Pronósticos:** Tu espacio personal. Selecciona tu nombre en el menú desplegable para auditar toda tu hoja de juego, ver qué marcadores guardaste y verificar cuántos puntos ganaste en cada partido ya jugado.
    4. **📅 Horario de Partidos:** El calendario oficial con las horas configuradas para Guatemala. Los partidos se cierran automáticamente **5 minutos antes** de su pitazo inicial.
    5. **📜 Reglas del Juego:** Si tienes dudas de cómo suma el sistema automatizado o el bonus de los penales, dale una leída a esta pestaña.
    """)

tab1, tab2, tab_consulta, tab3, tab4, tab5 = st.tabs([
    "📝 Registrar Pronósticos", 
    "📊 Tabla de Posiciones", 
    "🔍 Mis Pronósticos", 
    "📅 Horario de Partidos",
    "📜 Reglas del Juego",
    "⚙️ Administrador"
])

# ---------------------------------------------------------------------
# PESTAÑA 1: REGISTRAR / ACTUALIZAR PRONÓSTICOS
# ---------------------------------------------------------------------
with tab1:
    st.header("Completa o Actualiza tu Quiniela")
    
    try:
        df_participantes = cargar_datos("PARTICIPANTES")
    except Exception:
        df_participantes = pd.DataFrame(columns=["Nombre"])

    tipo_registro = st.radio("¿Qué deseas hacer?", ["✨ Registrarme por primera vez", "🔄 Actualizar mis pronósticos existentes"])
    
    if "nombre_confirmado" not in st.session_state:
        st.session_state["nombre_confirmado"] = ""

    nombre = ""
    es_usuario_existente = False
    
    if tipo_registro == "✨ Registrarme por primera vez":
        nombre_input = st.text_input("Tu Nombre Completo:", placeholder="Ej. Álvaro Torres")
        
        if st.button("Confirmar Nombre 👤"):
            if nombre_input.strip() != "":
                st.session_state["nombre_confirmado"] = nombre_input.strip()
                st.success(f"Nombre listo: {st.session_state['nombre_confirmado']}")
            else:
                st.error("❌ Por favor, escribe un nombre antes de confirmar.")
        
        nombre = st.session_state["nombre_confirmado"] if st.session_state["nombre_confirmado"] else nombre_input
    else:
        if not df_participantes.empty and "Nombre" in df_participantes.columns:
            nombre = st.selectbox("Selecciona tu nombre de la lista:", df_participantes["Nombre"].unique())
            es_usuario_existente = True
            st.session_state["nombre_confirmado"] = ""
        else:
            st.warning("⚠️ No hay ningún usuario registrado todavía. Elige 'Registrarme por primera vez'.")

    st.subheader("⚽ Pronósticos disponibles")
    
    pronosticos_usuario = {}
    al_menos_uno_disponible = False

    for _, fila in df_partidos.iterrows():
        id_partido = str(fila["ID"])
        eq_a_original = str(fila["EquipoA"]).strip()
        eq_b_original = str(fila["EquipoB"]).strip()
        
        try:
            id_numerico = int(float(id_partido))
        except (ValueError, TypeError):
            id_numerico = 0
        
        es_eliminatorio = True if ("tipo" in df_partidos.columns and str(fila.get("Tipo", "")).lower() == "eliminatorio") or id_numerico > 48 else False
        
# Identificar si el partido permite penales (Fase Eliminatoria)
        es_eliminatorio = ("tipo" in df_partidos.columns and str(fila.get("Tipo", "")).lower() == "eliminatorio") or (id_numerico > 48)