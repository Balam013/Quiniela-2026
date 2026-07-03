import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import pytz

# =====================================================================
# CONFIGURACIÓN, HORARIOS Y CONEXIÓN
# =====================================================================
st.set_page_config(page_title="Quiniela Familiar 2026", page_icon="🏆", layout="centered")

# Configurar Zona Horaria de Guatemala
ZONA_GT = pytz.timezone("America/Guatemala")
ahora_gt = datetime.now(ZONA_GT)

conn = st.connection("gsheets", type=GSheetsConnection)

# FUNCIÓN DE CARGA CON CACHÉ INTELIGENTE (EVITA EL ERROR 429)
def cargar_datos(nombre_hoja):
    return conn.read(worksheet=nombre_hoja, ttl=10)

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
# REGLAS DE PUNTAJE (LÓGICA AUTOMÁTICA)
# =====================================================================
def calcular_puntos(pronostico, resultado_real):
    if pd.isna(pronostico) or pd.isna(resultado_real) or resultado_real == "" or pronostico == "":
        return 0
    try:
        goles_pro_a, goles_pro_b = map(int, pronostico.split("-"))
        goles_real_a, goles_real_b = map(int, resultado_real.split("-"))
        
        # 1. Marcador Exacto -> 3 Puntos
        if goles_pro_a == goles_real_a and goles_pro_b == goles_real_b:
            return 3
        # 2. Acertar Ganador o Empate -> 1 Punto
        elif (goles_pro_a > goles_pro_b and goles_real_a > goles_real_b) or \
             (goles_pro_a < goles_pro_b and goles_real_a < goles_real_b) or \
             (goles_pro_a == goles_pro_b and goles_real_a == goles_real_b):
            return 1
    except:
        pass
    return 0

# =====================================================================
# CARGAR BASES DE DATOS ESENCIALES (CORREGIDO A MAYÚSCULAS)
# =====================================================================
try:
    df_partidos = cargar_datos("PARTIDOS")  
except Exception as e:
    st.error(f"⚠️ Error al leer la pestaña PARTIDOS: {e}")
    df_partidos = pd.DataFrame(columns=["ID", "EquipoA", "EquipoB", "FechaHora"])

try:
    df_resultados = cargar_datos("RESULTADOS")
except Exception:
    df_resultados = pd.DataFrame(columns=["ID", "ResultadoReal"])

# =====================================================================
# INTERFAZ PRINCIPAL
# =====================================================================
st.title("🏆 Quiniela Familiar 2026")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Registrar Pronósticos", 
    "📊 Tabla de Posiciones", 
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
    
    # Variable de estado para controlar la confirmación con botón sin alterar el flujo original
    if "nombre_confirmado" not in st.session_state:
        st.session_state["nombre_confirmado"] = ""

    nombre = ""
    es_usuario_existente = False
    
    if tipo_registro == "✨ Registrarme por primera vez":
        nombre_input = st.text_input("Tu Nombre Completo:", placeholder="Ej. Álvaro Torres")
        
        # AGREGADO: Botón físico para registrar/confirmar el nombre sin presionar Enter
        if st.button("Confirmar Nombre 👤"):
            if nombre_input.strip() != "":
                st.session_state["nombre_confirmado"] = nombre_input.strip()
                st.success(f"Nombre listo: {st.session_state['nombre_confirmado']}")
            else:
                st.error("❌ Por favor, escribe un nombre antes de confirmar.")
        
        # Mantenemos el valor ya sea del botón o del comportamiento nativo por Enter
        nombre = st.session_state["nombre_confirmado"] if st.session_state["nombre_confirmado"] else nombre_input
    else:
        if not df_participantes.empty and "Nombre" in df_participantes.columns:
            nombre = st.selectbox("Selecciona tu nombre de la lista:", df_participantes["Nombre"].unique())
            es_usuario_existente = True
            # Limpiamos el estado del nombre nuevo al cambiar de modo
            st.session_state["nombre_confirmado"] = ""
        else:
            st.warning("⚠️ No hay ningún usuario registrado todavía. Elige 'Registrarme por primera vez'.")

    st.subheader("⚽ Pronósticos disponibles")
    st.caption("Nota: Los partidos se bloquean automáticamente 5 minutos antes de su inicio y solo se activan cuando los equipos reales están definidos.")
    
    pronosticos_usuario = {}
    al_menos_uno_disponible = False

    for _, fila in df_partidos.iterrows():
        id_partido = str(fila["ID"])
        eq_a_original = str(fila["EquipoA"]).strip()
        eq_b_original = str(fila["EquipoB"]).strip()
        
        # Desbloqueo por etapas
        palabras_bloqueo = ["por definir", "grupo", "ganador", "perdedor", "p89", "p90", "p91", "p92", "p93", "p94", "p95", "p96", "p97", "p98", "p99", "p100", "p101", "p102"]
        esta_bloqueado_por_etapa = any(palabra in eq_a_original.lower() or palabra in eq_b_original.lower() for palabra in palabras_bloqueo)
        
        eq_a_con_bandera = obtener_nombre_con_bandera(fila["EquipoA"])
        eq_b_con_bandera = obtener_nombre_con_bandera(fila["EquipoB"])
        
        # Validar tiempo límite de cierre (5 minutos antes)
        hora_partido = ZONA_GT.localize(datetime.strptime(str(fila["FechaHora"]), "%Y-%m-%d %H:%M"))
        limite_cierre = hora_partido - timedelta(minutes=5)
        
        st.markdown(f"**Partido {id_partido}: {eq_a_con_bandera} vs {eq_b_con_bandera}**")
        
        if esta_bloqueado_por_etapa:
            st.info("⏳ Casilla bloqueada: Esperando a que se definan los equipos clasificados de la siguiente etapa.")
            pronosticos_usuario[id_partido] = None
        elif ahora_gt > limite_cierre:
            st.warning("🔒 Pronósticos cerrados para este partido (Tiempo límite alcanzado).")
            pronosticos_usuario[id_partido] = None
        else:
            al_menos_uno_disponible = True
            st.caption(f"📅 Cierra: {limite_cierre.strftime('%d/%m/%Y %I:%M %p')}")
            
            valor_defecto_a = 0
            valor_defecto_b = 0
            col_partido = f"Partido_{id_partido}"
            
            if es_usuario_existente and col_partido in df_participantes.columns:
                pronostico_anterior = df_participantes.loc[df_participantes["Nombre"] == nombre, col_partido].values
                if len(pronostico_anterior) > 0 and pd.notna(pronostico_anterior[0]) and "-" in str(pronostico_anterior[0]):
                    try:
                        valor_defecto_a, valor_defecto_b = map(int, str(pronostico_anterior[0]).split("-"))
                    except:
                        pass

            col1, col2 = st.columns(2)
            with col1:
                g_a = st.number_input(f"Goles {eq_a_con_bandera}", min_value=0, max_value=15, value=valor_defecto_a, key=f"in_a_{id_partido}")
            with col2:
                g_b = st.number_input(f"Goles {eq_b_con_bandera}", min_value=0, max_value=15, value=valor_defecto_b, key=f"in_b_{id_partido}")
            pronosticos_usuario[id_partido] = f"{g_a}-{g_b}"
        st.write("---")

    if al_menos_uno_disponible:
        if st.button("Guardar mi Quiniela 🚀"):
            if str(nombre).strip() == "":
                st.error("❌ Por favor, ingresa o selecciona un nombre.")
            else:
                nombre_limpio = str(nombre).strip()
                
                if es_usuario_existente:
                    idx = df_participantes[df_participantes["Nombre"] == nombre_limpio].index[0]
                    for k, v in pronosticos_usuario.items():
                        if v is not None:
                            col_p = f"Partido_{k}"
                            if col_p not in df_participantes.columns:
                                df_participantes[col_p] = None
                            df_participantes.at[idx, col_p] = v
                    df_actualizado = df_participantes
                    st.success(f"¡Tus pronósticos para {nombre_limpio} han sido actualizados!")
                else:
                    if nombre_limpio in df_participantes["Nombre"].values:
                        st.warning("⚠️ Este nombre ya existe. Si quieres cambiar tus apuestas, usa la opción 'Actualizar mis pronósticos existentes'.")
                        st.stop()
                        
                    nuevo_registro = {"Nombre": nombre_limpio}
                    for k, v in pronosticos_usuario.items():
                        if v is not None:
                            nuevo_registro[f"Partido_{k}"] = v
                    
                    df_nuevo = pd.DataFrame([nuevo_registro])
                    df_actualizado = pd.concat([df_participantes, df_nuevo], ignore_index=True)
                    st.success(f"¡Excelente {nombre_limpio}! Tus pronósticos se guardaron.")
                
                conn.update(worksheet="PARTICIPANTES", data=df_actualizado)
                # Reseteamos el estado para un próximo registro limpio
                st.session_state["nombre_confirmado"] = ""
                st.balloons()
                st.rerun()

# ---------------------------------------------------------------------
# PESTAÑA 2: TABLA DE POSICIONES
# ---------------------------------------------------------------------
with tab2:
    st.header("📈 Tabla General de la Familia")
    try:
        st.cache_data.clear() 
        df_pos = cargar_datos("PARTICIPANTES")
        df_res = cargar_datos("RESULTADOS")
        
        if not df_pos.empty:
            puntos_totales = []
            for _, participante in df_pos.iterrows():
                puntos = 0
                for _, res in df_res.iterrows():
                    id_p = str(res["ID"])
                    col_partido = f"Partido_{id_p}"
                    if col_partido in df_pos.columns:
                        puntos += calcular_puntos(participante[col_partido], res["ResultadoReal"])
                puntos_totales.append(puntos)
            
            df_pos["Puntos Totales"] = puntos_totales
            df_pos = df_pos.sort_values(by="Puntos Totales", ascending=False).reset_index(drop=True)
            
            columnas_partidos = [c for c in df_pos.columns if "Partido_" in c]
            columnas_partidos = sorted(columnas_partidos, key=lambda x: int(x.split("_")[1]) if x.split("_")[1].isdigit() else 0)
            
            columnas_visibles = ["Nombre", "Puntos Totales"] + columnas_partidos
            columnas_finales = [c for c in columnas_visibles if c in df_pos.columns]
            
            st.dataframe(df_pos[columnas_finales], use_container_width=True)
        else:
            st.info("No hay participantes registrados todavía.")
    except Exception as e:
        st.info("Registra el primer participante para activar la tabla.")

# ---------------------------------------------------------------------
# PESTAÑA 3: HORARIO DE PARTIDOS
# ---------------------------------------------------------------------
with tab3:
    st.header("📅 Calendario Oficial y Equipos Clasificados")
    st.caption("🔄 Los equipos se actualizan automáticamente según los nombres que pongas en tu Google Sheets.")
    
    for _, fila in df_partidos.iterrows():
        eq_a_cb = obtener_nombre_con_bandera(fila["EquipoA"])
        eq_b_cb = obtener_nombre_con_bandera(fila["EquipoB"])
        hora_p = datetime.strptime(str(fila["FechaHora"]), "%Y-%m-%d %H:%M").strftime("%d/%m/%Y %I:%M %p")
        st.info(f"**Partido {fila['ID']}** | ⏰ {hora_p} (Hora GT)  \n⚽ **{eq_a_cb} vs {eq_b_cb}**")

# ---------------------------------------------------------------------
# PESTAÑA 4: REGLAS DEL JUEGO
# ---------------------------------------------------------------------
with tab4:
    st.header("📜 Sistema de Puntos")
    st.markdown("""
    Los puntos se calculan de la siguiente manera de forma automática:
    * **🎯 3 Puntos (Marcador Exacto):** Si aciertas exactamente los goles de ambos equipos.
    * **⚽ 1 Punto (Acertar Tendencia):** Si adivinas quién gana o si hay empate, pero no los goles exactos.
    * **❌ 0 Puntos:** Si no aciertas nada.
    """)

# ---------------------------------------------------------------------
# PESTAÑA 5: ADMINISTRADOR
# ---------------------------------------------------------------------
with tab5:
    st.header("🔒 Panel del Administrador")
    password = st.text_input("Contraseña de Acceso:", type="password")
    
    if password == "FamiliaTorres2026":
        st.success("🔓 Acceso Concedido")
        st.subheader("Ingresar Marcadores Oficiales del Torneo")
        
        with st.form("form_admin"):
            partido_a_actualizar = st.selectbox("Selecciona el partido jugado:", df_partidos["ID"].astype(str))
            goles_real_a = st.number_input("Goles Reales Equipo A", min_value=0, max_value=20, value=0)
            goles_real_b = st.number_input("Goles Reales Equipo B", min_value=0, max_value=20, value=0)
            
            if st.form_submit_button("Publicar Resultado Oficial 📢"):
                nuevo_res = pd.DataFrame([{"ID": partido_a_actualizar, "ResultadoReal": f"{goles_real_a}-{goles_real_b}"}])
                
                try:
                    df_res_actual = cargar_datos("RESULTADOS")
                    df_res_actual = df_res_actual[df_res_actual["ID"].astype(str) != partido_a_actualizar]
                    df_res_final = pd.concat([df_res_actual, nuevo_res], ignore_index=True)
                except:
                    df_res_final = nuevo_res
                
                conn.update(worksheet="RESULTADOS", data=df_res_final)
                st.success(f"¡Marcador del Partido {partido_a_actualizar} actualizado!")
                st.rerun()