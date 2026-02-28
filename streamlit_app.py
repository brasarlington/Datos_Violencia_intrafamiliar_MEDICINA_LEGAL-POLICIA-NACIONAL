import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="Dashboard Medicina Legal",
    layout="wide",
    page_icon="🏥"
)

st.title("🏥 Violencia Intrafamiliar - Medicina Legal")
st.markdown("Análisis de dictámenes medicolegales (Sexológicos y de Lesiones).")

# --- FUNCIÓN DE CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    # URL corregida (Cambiamos 'blob' por 'raw' automáticamente)
    url = "https://raw.githubusercontent.com/brasarlington/Datos_Violencia_intrafamiliar_MEDICINA_LEGAL-POLICIA-NACIONAL/main/datos_medicinal.csv"
    
    try:
        # Intentamos cargar. Si falla por separador, probamos con punto y coma
        try:
            df = pd.read_csv(url)
        except:
            df = pd.read_csv(url, sep=';')

        # 1. NORMALIZAR NOMBRES DE COLUMNAS (Quitar espacios y poner mayúsculas)
        df.columns = df.columns.str.strip().str.upper()
        
        # 2. LIMPIEZA DE AÑO Y MES (El problema de los puntos 4.0)
        # Rellenar vacíos con 0 y convertir a entero
        cols_numericas = ['AÑO', 'MES', 'EDAD']
        for col in cols_numericas:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)

        # 3. CREAR FECHA SINTÉTICA (Para poder graficar en el tiempo)
        if 'AÑO' in df.columns and 'MES' in df.columns:
            # Diccionario para convertir numero de mes a fecha
            # Asumimos dia 1 para todos para poder graficar
            df['FECHA_ARMADA'] = pd.to_datetime(
                df['AÑO'].astype(str) + '-' + df['MES'].astype(str) + '-01', 
                errors='coerce'
            )
            
            # Crear columna de Nombre de Mes para los gráficos
            mapa_meses = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                          7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic', 0: 'Sin Dato'}
            df['NOMBRE_MES'] = df['MES'].map(mapa_meses)

        return df
        
    except Exception as e:
        st.error(f"Error cargando los datos: {e}")
        return pd.DataFrame()

# Cargar
with st.spinner('Conectando con GitHub...'):
    df = cargar_datos()

# --- DASHBOARD ---
if not df.empty:
    
    # --- SIDEBAR (FILTROS) ---
    st.sidebar.header("🔍 Filtros")
    
    # Filtro Año
    if 'AÑO' in df.columns:
        anos = sorted(df['AÑO'].unique(), reverse=True)
        ano_sel = st.sidebar.selectbox("Selecciona Año", anos)
        df = df[df['AÑO'] == ano_sel]
    
    # Filtro Departamento (Busca variantes de nombre común en Medicina Legal)
    col_depto = None
    posibles_nombres_depto = ['DEPARTAMENTO', 'DEPARTAMENTO HECHO', 'DPTO_HECHO']
    for nombre in posibles_nombres_depto:
        if nombre in df.columns:
            col_depto = nombre
            break
            
    if col_depto:
        deptos = ['TODOS'] + sorted(df[col_depto].astype(str).unique())
        depto_sel = st.sidebar.selectbox("Departamento", deptos)
        if depto_sel != 'TODOS':
            df = df[df[col_depto] == depto_sel]

    # --- MÉTRICAS ---
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Total Exámenes", f"{len(df):,}")
    
    # Intentar buscar columna de EDAD para promedio
    if 'EDAD' in df.columns:
        promedio_edad = round(df[df['EDAD'] > 0]['EDAD'].mean())
        col_kpi2.metric("Edad Promedio Víctima", f"{promedio_edad} años")

    st.divider()

    # --- GRÁFICOS ---
    
    # 1. EVOLUCIÓN MENSUAL
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📅 Casos por Mes")
        if 'MES' in df.columns:
            # Agrupar y ordenar por número de mes para que Enero salga primero
            casos_mes = df.groupby(['MES', 'NOMBRE_MES']).size().reset_index(name='CANTIDAD')
            casos_mes = casos_mes.sort_values('MES')
            
            fig_mes = px.line(casos_mes, x='NOMBRE_MES', y='CANTIDAD', markers=True, title="Tendencia Mensual")
            st.plotly_chart(fig_mes, use_container_width=True)

    # 2. GÉNERO / SEXO
    with col2:
        st.subheader("⚧ Distribución por Sexo")
        col_sexo = 'SEXO' if 'SEXO' in df.columns else 'GENERO' # Busca cual existe
        if col_sexo in df.columns:
            fig_pie = px.pie(df, names=col_sexo, hole=0.4, title="Víctimas por Sexo")
            st.plotly_chart(fig_pie, use_container_width=True)

    # 3. CONTEXTO O MECANISMO
    st.subheader("📊 Contexto del Hecho")
    # Medicina legal suele tener columna 'ESCENARIO' o 'CONTEXTO'
    col_contexto = None
    for c in ['ESCENARIO', 'ESCENARIO HECHO', 'CONTEXTO', 'MECANISMO_AGRESION']:
        if c in df.columns:
            col_contexto = c
            break
    
    if col_contexto:
        top_contextos = df[col_contexto].value_counts().head(10).reset_index()
        top_contextos.columns = ['CONTEXTO', 'CANTIDAD']
        fig_bar = px.bar(top_contextos, x='CANTIDAD', y='CONTEXTO', orientation='h', color='CANTIDAD')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No se encontró columna de Escenario/Contexto para graficar.")

    # --- TABLA ---
    with st.expander("📂 Ver Datos Crudos"):
        st.dataframe(df)

else:
    st.warning("No se pudieron cargar datos. Verifica la URL.")
