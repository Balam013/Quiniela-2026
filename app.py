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

# =====================================================================
# FUNCIÓN DE CARGA CON CACHÉ DE VERDAD (EVITA EL ERROR 429)
# =====================================================================
@st.cache_data(ttl=60)  # Conserva los datos por 1 minuto para no saturar a Google
def cargar_datos(nombre_hoja):
    # Forzamos una nueva conexión limpia internamente
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
        # 1. Separar marcador y clasificado del Pronóstico ('1-1 | Argentina' o '2-1')
        pronostico_str = str(pronostico).strip()
        clasificado_pro = None
        if "|" in pronostico_str:
            marcador_pro, clasificado_pro = map(str.strip, pronostico_str.split("|"))
        else:
            marcador_pro = pronostico_str

        # 2. Separar marcador y clasificado del Resultado Real ('1-1 (4-3)' o '2-1')
        res_real_str = str(resultado_real).strip()
        clasificado_real = None
        
        if "(" in res_real_str:
            # Si hay paréntesis, hubo penales. El ganador de penales se define por quién metió más en el (X-Y)
            marcador_real = res_real_str.split("(")[0].strip()
            penales_str = res_real_str.split("(")[1].replace(")", "").strip()
            pen_a, pen_b = map(int, penales_str.split("-"))
            clasificado_real = "A" if pen_a > pen_b else "B"
        else:
            marcador_real = res_real_str

        # Extraer goles para tendencias
        goles_pro_a, goles_pro_b = map(int, marcador_pro.split("-"))
        goles_real_a, goles_real_b = map(int, marcador_real.split("-"))
        
        # Determinar ganador real en los 90/120 min si no fue por penales
        if clasificado_real is None:
            if goles_real_a > goles_real_b:
                clasificado_real = "A"
            elif goles_real_b > goles_real_a:
                clasificado_real = "B"
            else:
                clasificado_real = "Empate"

        # Evaluar Marcador Regular
        if goles_pro_a == goles_real_a and goles_pro_b == goles_real_b:
            puntos += 3  # Marcador exacto
        elif (goles_pro_a > goles_pro_b and goles_real_a > goles_real_b) or \
             (goles_pro_a < goles_pro_b and goles_real_a < goles_real_b) or \
             (goles_pro_a == goles_pro_b and goles_real_a == goles_real_b):
            puntos += 1  # Tendencia acertada

        # BONUS PRO: Puntos por acertar quién pasa de ronda en fases eliminatorias
        if clasificado_pro and clasificado_real:
            # Mapear la selección del usuario ('A' o 'B')
            if (clasificado_pro == "A" and clasificado_real == "A") or (clasificado_pro == "B" and clasificado_real == "B"):
                puntos += 1 # +1 Punto por pegarle al clasificado

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

with st.expander("📖 ¡Haz clic aquí para ver las INSTRUCCIONES DE USO MODO PRO! 🤔", expanded=True):
    st.markdown("""
    ### 🚀 Sistema de Puntuación Avanzado
    1. **🎯 Marcador Exacto (90'/120'):** **3 Puntos** si le pegas al score del partido regular.
    2. **⚽ Tendencia acertada:** **1 Punto** si adivinas si gana A, B o empatan.
    3. **🔥 ¡Bonus de Clasificación! (+1 Punto):** En partidos eliminatorios, si el juego queda empate y se va a penales, sumas **1 punto extra** si adivinaste de antemano qué equipo avanzaba a la siguiente ronda.
    """)

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
        
        # Identificar si el partido permite penales (Fase Eliminatoria)
        # --- AGREGADO: Validación Pro anti-errores para el ID ---
        try:
            id_numerico = int(float(id_partido)) # Convierte de forma segura incluso si viene como "49.0"
        except (ValueError, TypeError):
            id_numerico = 0 # Si está vacío o es texto, le asigna 0 para que no rompa el código
        
        # Identificar si el partido permite penales (Fase Eliminatoria)
        es_eliminatorio = True if ("tipo" in df_partidos.columns and str(fila.get("Tipo", "")).lower() == "eliminatorio") or id_numerico > 48 else False
        palabras_bloqueo = ["por definir", "grupo", "ganador", "perdedor", "p89", "p90", "p91", "p92", "p93", "p94", "p95", "p96", "p97", "p98", "p99", "p100", "p101", "p102"]
        esta_bloqueado_por_etapa = any(palabra in eq_a_original.lower() or palabra in eq_b_original.lower() for palabra in palabras_bloqueo)
        
        eq_a_con_bandera = obtener_nombre_con_bandera(fila["EquipoA"])
        eq_b_con_bandera = obtener_nombre_con_bandera(fila["EquipoB"])
        
        hora_partido = ZONA_GT.localize(datetime.strptime(str(fila["FechaHora"]), "%Y-%m-%d %H:%M"))
        limite_cierre = hora_partido - timedelta(minutes=5)
        
        st.markdown(f"**Partido {id_partido}: {eq_a_con_bandera} vs {eq_b_con_bandera}**")
        
        if esta_bloqueado_por_etapa:
            st.info("⏳ Casilla bloqueada: Esperando a que se definan los equipos clasificados.")
            pronosticos_usuario[id_partido] = None
        elif ahora_gt > limite_cierre:
            st.warning("🔒 Pronósticos cerrados para este partido.")
            pronosticos_usuario[id_partido] = None
        else:
            al_menos_uno_disponible = True
            st.caption(f"📅 Cierra: {limite_cierre.strftime('%d/%m/%Y %I:%M %p')}")
            
            valor_defecto_a = 0
            valor_defecto_b = 0
            defecto_clasifica = eq_a_original
            col_partido = f"Partido_{id_partido}"
            
            if es_usuario_existente and col_partido in df_participantes.columns:
                valor_anterior = str(df_participantes.loc[df_participantes["Nombre"] == nombre, col_partido].values[0])
                if "-" in valor_anterior:
                    try:
                        if "|" in valor_anterior:
                            marcador_ant, clas_ant = map(str.strip, valor_anterior.split("|"))
                            valor_defecto_a, valor_defecto_b = map(int, marcador_ant.split("-"))
                            defecto_clasifica = eq_a_original if clas_ant == "A" else eq_b_original
                        else:
                            valor_defecto_a, valor_defecto_b = map(int, valor_anterior.split("-"))
                    except:
                        pass

            col1, col2 = st.columns(2)
            with col1:
                g_a = st.number_input(f"Goles {eq_a_con_bandera}", min_value=0, max_value=15, value=valor_defecto_a, key=f"in_a_{id_partido}")
            with col2:
                g_b = st.number_input(f"Goles {eq_b_con_bandera}", min_value=0, max_value=15, value=valor_defecto_b, key=f"in_b_{id_partido}")
            
            # MODO PRO EN ACCIÓN: Si los goles son iguales y es fase eliminatoria, obligar a elegir quién pasa
            if es_eliminatorio and g_a == g_b:
                quien_pasa = st.selectbox(
                    "💥 Se van a penales... ¿Quién clasifica de ronda?", 
                    options=[eq_a_original, eq_b_original], 
                    index=0 if defecto_clasifica == eq_a_original else 1,
                    key=f"clas_{id_partido}"
                )
                cod_clasifica = "A" if quien_pasa == eq_a_original else "B"
                pronosticos_usuario[id_partido] = f"{g_a}-{g_b} | {cod_clasifica}"
            else:
                pronosticos_usuario[id_partido] = f"{g_a}-{g_b}"
        st.write("---")

    if al_menos_uno_disponible:
        if st.button("Guardar mi Quiniela Pro 🚀"):
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
                        st.warning("⚠️ Este nombre ya existe.")
                        st.stop()
                        
                    nuevo_registro = {"Nombre": nombre_limpio}
                    for k, v in pronosticos_usuario.items():
                        if v is not None:
                            nuevo_registro[f"Partido_{k}"] = v
                    
                    df_nuevo = pd.DataFrame([nuevo_registro])
                    df_actualizado = pd.concat([df_participantes, df_nuevo], ignore_index=True)
                    st.success(f"¡Excelente {nombre_limpio}! Tus pronósticos se guardaron.")
                
                conn.update(worksheet="PARTICIPANTES", data=df_actualizado)
                st.session_state["nombre_confirmado"] = ""
                st.balloons()
                st.rerun()

# ---------------------------------------------------------------------
# PESTAÑA 2: TABLA DE POSICIONES (CON MEDALLAS Y EVALUACIÓN PRO)
# ---------------------------------------------------------------------
with tab2:
    st.header("📈 Tabla General de la Familia")
    try:
        # ❌ Se eliminó st.cache_data.clear() que causaba el Error 429
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
            
            for idx in df_pos.index:
                if idx == 0:
                    df_pos.at[idx, "Nombre"] = f"🥇 {df_pos.at[idx, 'Nombre']}"
                elif idx == 1:
                    df_pos.at[idx, "Nombre"] = f"🥈 {df_pos.at[idx, 'Nombre']}"
                elif idx == 2:
                    df_pos.at[idx, "Nombre"] = f"🥉 {df_pos.at[idx, 'Nombre']}"
            
            columnas_partidos = [c for c in df_pos.columns if "Partido_" in c]
            columnas_partidos = sorted(columnas_partidos, key=lambda x: int(x.split("_")[1]) if x.split("_")[1].isdigit() else 0)
            
            columnas_visibles = ["Nombre", "Puntos Totales"] + columnas_partidos
            columnas_finales = [c for c in columnas_visibles if c in df_pos.columns]
            
            st.dataframe(df_pos[columnas_finales], use_container_width=True, hide_index=True)
        else:
            st.info("No hay participantes registrados todavía.")
    except Exception as e:
        st.info("Registra el primer participante para activar la tabla.")

# ---------------------------------------------------------------------
# PESTAÑA 3: HORARIO DE PARTIDOS
# ---------------------------------------------------------------------
with tab3:
    st.header("📅 Calendario Oficial y Equipos Clasificados")
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
    * **🎯 3 Puntos (Marcador Exacto):** Si aciertas exactamente los goles en tiempo reglamentario.
    * **⚽ 1 Punto (Acertar Tendencia):** Si adivinas quién gana o si hay empate.
    * **🔥 +1 Punto Extra Pro (Clasificación en Penales):** Si el partido termina empatado en llaves finales, y aciertas cuál equipo clasifica en la tanda de penales.
    """)

# ---------------------------------------------------------------------
# PESTAÑA 5: ADMINISTRADOR
# ---------------------------------------------------------------------
with tab5:
    st.header("🔒 Panel del Administrador")
    password = st.text_input("Contraseña de Acceso:", type="password", key="admin_pass")
    
    if password == "FamiliaTorres2026":
        st.success("🔓 Acceso Concedido")
        st.subheader("Ingresar Marcadores Oficiales del Torneo")
        st.caption("💡 Si el partido se va a penales, escribe el marcador regular y la tanda entre paréntesis. Ejemplo: `1-1 (5-4)`. El sistema sabrá que el primero avanzó.")
        
        with st.form("form_admin"):
            partido_a_actualizar = st.selectbox("Selecciona el partido jugado:", df_partidos["ID"].astype(str))
            marcador_manual = st.text_input("Resultado Real (Ej: '2-1' o '1-1 (4-3)'):", value="0-0")
            
            if st.form_submit_button("Publicar Resultado Oficial 📢"):
                nuevo_res = pd.DataFrame([{"ID": partido_a_actualizar, "ResultadoReal": marcador_manual.strip()}])
                
                try:
                    df_res_actual = cargar_datos("RESULTADOS")
                    df_res_actual = df_res_actual[df_res_actual["ID"].astype(str) != partido_a_actualizar]
                    df_res_final = pd.concat([df_res_actual, nuevo_res], ignore_index=True)
                except:
                    df_res_final = nuevo_res
                
                conn.update(worksheet="RESULTADOS", data=df_res_final)
                st.success(f"¡Marcador del Partido {partido_a_actualizar} actualizado a '{marcador_manual}'!")
                st.rerun()