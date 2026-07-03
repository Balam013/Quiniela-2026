import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# =====================================================================
# CONFIGURACIÓN DE LA PÁGINA Y CONEXIÓN
# =====================================================================
st.set_page_config(page_title="Quiniela Familiar 2026", page_icon="🏆", layout="centered")

# Conexión segura usando tu archivo de credenciales de Google
conn = st.connection("gsheets", type=GSheetsConnection, key_file="credenciales.json")

# Función crucial: ttl=0 obliga a la app a leer datos en vivo sin usar caché bloqueado
def cargar_datos(nombre_hoja):
    return conn.read(worksheet=nombre_hoja, ttl=0)

# =====================================================================
# INTERFAZ PRINCIPAL
# =====================================================================
st.title("🏆 Quiniela Familiar 2026")
st.write("¡Ingresa tus pronósticos, suma puntos y demuestra quién sabe más de fútbol!")

# Creamos las pestañas para ordenar la aplicación
tab1, tab2, tab3 = st.tabs(["📝 Registrar Pronósticos", "📊 Tabla de Posiciones", "⚙️ Administrador"])

# ---------------------------------------------------------------------
# PESTAÑA 1: REGISTRAR PRONÓSTICOS
# ---------------------------------------------------------------------
with tab1:
    st.header("Completa tu Quiniela")
    
    # Cargar participantes actuales para verificar si ya existen o crear la estructura
    try:
        df_participantes = cargar_datos("Participantes")
    except Exception:
        # Si la hoja está vacía, iniciamos con estas columnas por defecto
        df_participantes = pd.DataFrame(columns=["Nombre", "Puntos", "Partido1", "Partido2"])

    # Formulario para evitar que la página se recargue con cada número que escribe el usuario
    with st.form("formulario_quiniela", clear_on_submit=True):
        nombre = st.text_input("Tu Nombre Completo:", placeholder="Ej. Álvaro Torres")
        
        st.subheader("⚽ Pronósticos de los Partidos")
        st.write("Escribe cuántos goles crees que anotará cada equipo:")
        
        # --- PARTIDO 1 ---
        st.markdown("**Partido 1: Equipo A vs Equipo B**")
        col1, col2 = st.columns(2)
        with col1:
            pro_p1_eqA = st.number_input("Goles Equipo A", min_value=0, max_value=20, value=0, key="p1_a")
        with col2:
            pro_p1_eqB = st.number_input("Goles Equipo B", min_value=0, max_value=20, value=0, key="p1_b")
            
        # --- PARTIDO 2 ---
        st.markdown("**Partido 2: Equipo C vs Equipo D**")
        col3, col4 = st.columns(2)
        with col3:
            pro_p2_eqC = st.number_input("Goles Equipo C", min_value=0, max_value=20, value=0, key="p2_c")
        with col4:
            pro_p2_eqD = st.number_input("Goles Equipo D", min_value=0, max_value=20, value=0, key="p2_d")
            
        # Botón de envío del formulario
        boton_enviar = st.form_submit_button("Guardar mi Quiniela 🚀")
        
        if boton_enviar:
            if nombre.strip() == "":
                st.error("❌ Por favor, escribe tu nombre antes de enviar.")
            elif nombre.strip() in df_participantes["Nombre"].values:
                st.warning(f"⚠️ El nombre '{nombre.strip()}' ya registró una quiniela. Usa un segundo nombre o apellido.")
            else:
                # Darle formato a los pronósticos para guardarlos (Ej: '2-1')
                pronostico_p1 = f"{pro_p1_eqA}-{pro_p1_eqB}"
                pronostico_p2 = f"{pro_p2_eqC}-{pro_p2_eqD}"
                
                # Crear la nueva fila de datos
                nuevo_registro = pd.DataFrame([{
                    "Nombre": nombre.strip(),
                    "Puntos": 0,  # Inicia con cero puntos
                    "Partido1": pronostico_p1,
                    "Partido2": pronostico_p2
                }])
                
                # Combinar datos existentes con el nuevo participante
                df_actualizado = pd.concat([df_participantes, nuevo_registro], ignore_index=True)
                
                # Actualizar la hoja de cálculo de Google de inmediato
                conn.update(worksheet="Participantes", data=df_actualizado)
                
                st.success(f"¡Excelente {nombre}! Tus pronósticos se guardaron de forma segura en la nube. 📈")
                st.balloons()
                
                # Forzar recarga limpia para actualizar todas las vistas de la app
                st.rerun()

# ---------------------------------------------------------------------
# PESTAÑA 2: TABLA DE POSICIONES
# ---------------------------------------------------------------------
with tab2:
    st.header("📈 Tabla General de la Familia")
    try:
        df_posiciones = cargar_datos("Participantes")
        if not df_posiciones.empty:
            # Ordenar de mayor a menor puntaje
            df_posiciones = df_posiciones.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
            st.dataframe(df_posiciones[["Nombre", "Puntos", "Partido1", "Partido2"]], use_container_width=True)
        else:
            st.info("Aún no hay nadie registrado. ¡Sé el primero!")
    except Exception:
        st.info("La tabla se mostrará en cuanto se registre el primer participante.")

# ---------------------------------------------------------------------
# PESTAÑA 3: ADMINISTRADOR (PROTEGIDO CON CONTRASEÑA)
# ---------------------------------------------------------------------
with tab3:
    st.header("🔒 Área Restringida")
    
    # Input de contraseña seguro
    password = st.text_input("Introduce la contraseña de Administrador para desbloquear:", type="password")
    
    # Define aquí la clave secreta de tu preferencia
    CONTRASEÑA_SECRETA = "Torres2026"
    
    if password == CONTRASEÑA_SECRETA:
        st.success("🔓 Acceso Concedido como Administrador.")
        st.subheader("Actualizar Resultados Oficiales de los Partidos")
        
        # Intentar cargar los resultados reales actuales
        try:
            df_resultados = cargar_datos("Resultados")
        except Exception:
            df_resultados = pd.DataFrame(columns=["Partido", "ResultadoReal"])
            
        st.write("Define los marcadores finales de los partidos para que el sistema calcule los puntos:")
        
        # Inputs para el administrador
        res_p1 = st.text_input("Resultado Oficial Partido 1 (Formato: 'Ej. 2-1'):")
        res_p2 = st.text_input("Resultado Oficial Partido 2 (Formato: 'Ej. 0-2'):")
        
        if st.button("Publicar Resultados Oficiales y Calcular"):
            # Crear tabla con los marcadores reales
            datos_oficiales = pd.DataFrame([
                {"Partido": "Partido1", "ResultadoReal": res_p1.strip()},
                {"Partido": "Partido2", "ResultadoReal": res_p2.strip()}
            ])
            
            # Guardar resultados oficiales en su propia pestaña de Google Sheets
            conn.update(worksheet="Resultados", data=datos_oficiales)
            st.success("¡Resultados oficiales guardados en Google Sheets!")
            st.rerun()
            
    elif password != "":
        st.error("❌ Contraseña incorrecta. El acceso al panel de control sigue bloqueado.")