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
# CARGA DINÁMICA DE BANDERAS DESDE GOOGLE SHEETS
# =====================================================================
try:
    df_banderas_sheets = cargar_datos("BANDERAS")
    # Creamos el diccionario combinando la columna Seleccion y Emoji
    BANDERAS = dict(zip(df_banderas_sheets["Seleccion"].astype(str).str.strip(), df_banderas_sheets["Emoji"].astype(str).str.strip()))
except Exception:
    # Respaldo por si aún no has creado la pestaña en Sheets
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
    1. **📝 Registrar Pronósticos:** Aquí metes tus marcadores. Si eres nuevo, selecciona *"Registrarme por primera vez"*, escribe tu nombre y confírmalo. Si vas a corregir algún gol de partidos que no han empezado, cambia a *"Actualizar mis pronósticos existentes"* y búscate en la lista. ¡No olvides darle al botón **`Guardar mis Pronósticos 💾`** al final!
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
# PESTAÑA 1: REGISTRAR / ACTUALIZAR PRONÓSTICOS (PROTEGIDA POR SESIÓN)
# ---------------------------------------------------------------------
with tab1:
    st.header("Completa o Actualiza tu Quiniela")
    
    # Cargar participantes para validar
    try:
        df_participantes = cargar_datos("PARTICIPANTES")
    except Exception:
        df_participantes = pd.DataFrame(columns=["Nombre"])

    # Lógica de Autenticación de Sesión
    if "usuario_logueado" not in st.session_state:
        st.info("👋 Por seguridad, identifícate para gestionar tu quiniela.")
        nombre_input = st.text_input("Ingresa tu Nombre Completo:", placeholder="Ej. Álvaro Torres")
        
        if st.button("Iniciar Sesión 🚀"):
            if nombre_input.strip() != "":
                st.session_state["usuario_logueado"] = nombre_input.strip()
                st.rerun()
            else:
                st.error("Por favor, escribe un nombre válido.")
    else:
        nombre = st.session_state["usuario_logueado"]
        st.success(f"Estás editando la quiniela de: **{nombre}**")
        if st.button("Cerrar Sesión 🚪"):
            del st.session_state["usuario_logueado"]
            st.rerun()

        # El usuario ya está identificado, procedemos a mostrar sus pronósticos
        st.subheader("⚽ Tus Pronósticos")
        
        pronosticos_usuario = {}
        al_menos_uno_disponible = False

        # Verificamos si existe en la base de datos
        es_usuario_existente = nombre in df_participantes["Nombre"].astype(str).values

        for _, fila in df_partidos.iterrows():
            id_partido = str(fila["ID"])
            eq_a_original = str(fila["EquipoA"]).strip()
            eq_b_original = str(fila["EquipoB"]).strip()
            
            try:
                id_numerico = int(float(id_partido))
            except:
                id_numerico = 0
            
            es_eliminatorio = ("tipo" in df_partidos.columns and str(fila.get("Tipo", "")).lower() == "eliminatorio") or (id_numerico > 48)
            palabras_bloqueo = ["por definir", "grupo", "ganador", "perdedor", "p89", "p90", "p91", "p92", "p93", "p94", "p95", "p96", "p97", "p98", "p99", "p100", "p101", "p102"]
            esta_bloqueado_por_etapa = any(palabra in eq_a_original.lower() or palabra in eq_b_original.lower() for palabra in palabras_bloqueo)
            
            eq_a_con_bandera = obtener_nombre_con_bandera(fila["EquipoA"])
            eq_b_con_bandera = obtener_nombre_con_bandera(fila["EquipoB"])
            
            hora_partido = ZONA_GT.localize(datetime.strptime(str(fila["FechaHora"]), "%Y-%m-%d %H:%M"))
            limite_cierre = hora_partido - timedelta(minutes=5)
            
            st.markdown(f"**Partido {id_partido}: {eq_a_con_bandera} vs {eq_b_con_bandera}**")
            
            if esta_bloqueado_por_etapa:
                st.info("⏳ Bloqueado: Esperando equipos.")
            elif ahora_gt > limite_cierre:
                st.warning("🔒 Pronósticos cerrados.")
            else:
                al_menos_uno_disponible = True
                
                valor_defecto_a, valor_defecto_b = 0, 0
                defecto_clasifica = eq_a_original
                col_partido = f"Partido_{id_partido}"
                
                # Cargar datos desde Sheets si ya existen
                if es_usuario_existente and col_partido in df_participantes.columns:
                    val_list = df_participantes.loc[df_participantes["Nombre"] == nombre, col_partido].values
                    if len(val_list) > 0 and pd.notna(val_list[0]):
                        valor_anterior = str(val_list[0])
                        if "-" in valor_anterior:
                            try:
                                if "|" in valor_anterior:
                                    marcador_ant, clas_ant = map(str.strip, valor_anterior.split("|"))
                                    valor_defecto_a, valor_defecto_b = map(int, marcador_ant.split("-"))
                                    defecto_clasifica = eq_a_original if clas_ant == "A" else eq_b_original
                                else:
                                    valor_defecto_a, valor_defecto_b = map(int, valor_anterior.split("-"))
                            except: pass

                col1, col2 = st.columns(2)
                with col1:
                    g_a = st.number_input(f"Goles {eq_a_con_bandera}", min_value=0, max_value=15, value=valor_defecto_a, key=f"a_{id_partido}")
                with col2:
                    g_b = st.number_input(f"Goles {eq_b_con_bandera}", min_value=0, max_value=15, value=valor_defecto_b, key=f"b_{id_partido}")
                
                if es_eliminatorio and g_a == g_b:
                    quien_pasa = st.selectbox("💥 ¿Quién clasifica?", options=[eq_a_original, eq_b_original], index=0 if defecto_clasifica == eq_a_original else 1, key=f"clas_{id_partido}")
                    pronosticos_usuario[id_partido] = f"{g_a}-{g_b} | {'A' if quien_pasa == eq_a_original else 'B'}"
                else:
                    pronosticos_usuario[id_partido] = f"{g_a}-{g_b}"
            st.write("---")

        # Botón de Guardar
        if al_menos_uno_disponible and st.button("Guardar mis Pronósticos 💾"):
            df_fresco = conn.read(worksheet="PARTICIPANTES")
            fila_usuario_idx = df_fresco[df_fresco["Nombre"].astype(str).str.strip() == nombre].index
            
            if len(fila_usuario_idx) > 0:
                idx = fila_usuario_idx[0]
                for k, v in pronosticos_usuario.items():
                    if v is not None: df_fresco.at[idx, f"Partido_{k}"] = v
            else:
                nueva_fila = {"Nombre": nombre}
                for k, v in pronosticos_usuario.items():
                    if v is not None: nueva_fila[f"Partido_{k}"] = v
                df_fresco = pd.concat([df_fresco, pd.DataFrame([nueva_fila])], ignore_index=True)
            
            conn.update(worksheet="PARTICIPANTES", data=df_fresco.fillna(""))
            st.cache_data.clear()
            st.success("¡Pronósticos guardados correctamente!")
            st.balloons()

# ---------------------------------------------------------------------
# PESTAÑA 2: TABLA DE POSICIONES (MODIFICADA PARA MOSTRAR PUNTOS POR PARTIDO)
# ---------------------------------------------------------------------
with tab2:
    st.header("📈 Tabla General de la Familia")
    try:
        df_pos = cargar_datos("PARTICIPANTES")
        df_res = cargar_datos("RESULTADOS")
        
        if not df_pos.empty:
            # Lista para guardar los datos procesados
            datos_tabla = []
            
            for _, participante in df_pos.iterrows():
                fila_usuario = {"Nombre": participante["Nombre"]}
                puntos_totales = 0
                
                # Iteramos sobre los partidos para calcular puntos individuales
                for _, res in df_res.iterrows():
                    id_p = str(res["ID"])
                    col_partido = f"Partido_{id_p}"
                    
                    # Calculamos los puntos del partido
                    pts_partido = 0
                    if col_partido in participante:
                        pts_partido = calcular_puntos(participante[col_partido], res["ResultadoReal"])
                    
                    fila_usuario[f"Puntos_P{id_p}"] = pts_partido
                    puntos_totales += pts_partido
                
                fila_usuario["Puntos Totales"] = puntos_totales
                datos_tabla.append(fila_usuario)
            
            # Creamos el nuevo DataFrame para mostrar
            df_final_pos = pd.DataFrame(datos_tabla)
            df_final_pos = df_final_pos.sort_values(by="Puntos Totales", ascending=False).reset_index(drop=True)
            
            # Aplicamos los emojis de medallas
            for idx in df_final_pos.index:
                if idx == 0: df_final_pos.at[idx, "Nombre"] = f"🥇 {df_final_pos.at[idx, 'Nombre']}"
                elif idx == 1: df_final_pos.at[idx, "Nombre"] = f"🥈 {df_final_pos.at[idx, 'Nombre']}"
                elif idx == 2: df_final_pos.at[idx, "Nombre"] = f"🥉 {df_final_pos.at[idx, 'Nombre']}"
            
            # Ordenamos columnas: Nombre, Puntos Totales, y luego los puntos por partido
            columnas_ordenadas = ["Nombre", "Puntos Totales"] + [c for c in df_final_pos.columns if c.startswith("Puntos_P")]
            
            st.dataframe(df_final_pos[columnas_ordenadas], use_container_width=True, hide_index=True)
        else:
            st.info("No hay participantes registrados todavía.")
    except Exception as e:
        st.info("Registra el primer participante para activar la tabla.")

# ---------------------------------------------------------------------
# 🔍 PESTAÑA: CONSULTAR PRONÓSTICOS INDIVIDUALES
# ---------------------------------------------------------------------
with tab_consulta:
    st.header("🔍 Consultar mis Pronósticos Guardados")
    try:
        df_partic = cargar_datos("PARTICIPANTES")
        df_res_oficial = cargar_datos("RESULTADOS")
        
        if not df_partic.empty and "Nombre" in df_partic.columns:
            usuario_elegido = st.selectbox("Elige tu nombre para ver tu hoja de juego:", df_partic["Nombre"].unique(), key="sb_consulta")
            
            fila_usuario = df_partic[df_partic["Nombre"] == usuario_elegido].iloc[0]
            
            lista_resumen = []
            
            for _, fila_p in df_partidos.iterrows():
                id_p = str(fila_p["ID"])
                col_p = f"Partido_{id_p}"
                
                eq_a_cb = obtener_nombre_con_bandera(fila_p["EquipoA"])
                eq_b_cb = obtener_nombre_con_bandera(fila_p["EquipoB"])
                
                tiro = fila_usuario.get(col_p, "No registrado")
                if pd.isna(tiro) or tiro == "":
                    tiro = "No registrado"
                
                tiro_visual = str(tiro)
                if "|" in str(tiro):
                    marcador_t, clas_t = map(str.strip, str(tiro).split("|"))
                    nom_clasifica = fila_p["EquipoA"] if clas_t == "A" else fila_p["EquipoB"]
                    tiro_visual = f"{marcador_t} (Pasa: {nom_clasifica})"
                
                res_oficial_row = df_res_oficial[df_res_oficial["ID"].astype(str) == id_p]
                res_real_visual = "Pendiente ⏳"
                puntos_ganados = "-"
                
                if not res_oficial_row.empty:
                    res_real_visual = str(res_oficial_row.iloc[0]["ResultadoReal"])
                    puntos_ganados = f"{calcular_puntos(tiro, res_real_visual)} pts"
                
                lista_resumen.append({
                    "Partido": f"Partido {id_p}",
                    "Enfrentamiento": f"{eq_a_cb} vs {eq_b_cb}",
                    "Tu Pronóstico 🎯": tiro_visual,
                    "Resultado Real ⚽": res_real_visual,
                    "Puntos Obtenidos": puntos_ganados
                })
                
            df_resumen_usuario = pd.DataFrame(lista_resumen)
            st.dataframe(df_resumen_usuario, use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay usuarios para consultar.")
    except Exception as e:
        st.info("La tabla de consultas se activará al registrar pronósticos.")

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
# PESTAÑA 5: ADMINISTRADOR (CON LIMPIEZA DE DUPLICADOS)
# ---------------------------------------------------------------------
with tab5:
    st.header("🔒 Panel del Administrador")
    password = st.text_input("Contraseña de Acceso:", type="password", key="admin_pass")
    
    if password == "FamiliaTorres2026":
        st.success("🔓 Acceso Concedido")
        
       # --- SECCIÓN: LIMPIEZA DE USUARIOS ---
        st.subheader("🧹 Mantenimiento de Base de Datos")
        
        # 1. Botón para eliminar duplicados (el que ya teníamos)
        if st.button("🧹 Eliminar Usuarios Duplicados Automáticamente"):
            df_p = cargar_datos("PARTICIPANTES")
            total_antes = len(df_p)
            df_p = df_p.drop_duplicates(subset=["Nombre"], keep="first")
            if total_antes > len(df_p):
                conn.update(worksheet="PARTICIPANTES", data=df_p.fillna(""))
                st.cache_data.clear()
                st.success(f"¡Limpieza lista! Se borraron {total_antes - len(df_p)} repetidos.")
            else:
                st.info("No se encontraron duplicados.")

        # 2. Selector para eliminar un participante específico
        st.write("---")
        df_p_borrar = cargar_datos("PARTICIPANTES")
        usuario_a_borrar = st.selectbox("Selecciona un participante para ELIMINAR:", df_p_borrar["Nombre"].unique())
        
        if st.button(f"🗑️ ELIMINAR a {usuario_a_borrar}"):
            df_p_nuevo = df_p_borrar[df_p_borrar["Nombre"] != usuario_a_borrar]
            conn.update(worksheet="PARTICIPANTES", data=df_p_nuevo.fillna(""))
            st.cache_data.clear()
            st.success(f"Usuario {usuario_a_borrar} eliminado permanentemente.")
            st.rerun()
        
        # --- SECCIÓN: INGRESAR MARCADORES ---
        st.subheader("⚽ Ingresar Marcadores Oficiales")
        with st.form("form_admin"):
            partido_a_actualizar = st.selectbox("Selecciona el partido:", df_partidos["ID"].astype(str))
            marcador_manual = st.text_input("Resultado Real (Ej: '2-1'):", value="0-0")
            
            if st.form_submit_button("Publicar Resultado Oficial 📢"):
                nuevo_res = pd.DataFrame([{"ID": partido_a_actualizar, "ResultadoReal": marcador_manual.strip()}])
                try:
                    df_res_actual = cargar_datos("RESULTADOS")
                    df_res_actual = df_res_actual[df_res_actual["ID"].astype(str) != partido_a_actualizar]
                    df_res_final = pd.concat([df_res_actual, nuevo_res], ignore_index=True)
                except:
                    df_res_final = nuevo_res
                
                conn.update(worksheet="RESULTADOS", data=df_res_final)
                st.cache_data.clear()
                st.success(f"¡Marcador actualizado!")
                st.rerun()