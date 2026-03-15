import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="Dashboard Violencia Intrafamiliar",
    layout="wide",
    page_icon="⚖️"
)

st.title("⚖️ Violencia Intrafamiliar en Colombia")
st.markdown("Análisis interactivo de reportes del **Instituto Nacional de Medicina Legal** y la **Policía Nacional**.")

# --- FUNCIÓN DE CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data
def cargar_y_limpiar_datos():
    url_pol = 'https://github.com/brasarlington/Datos_Violencia_intrafamiliar_MEDICINA_LEGAL-POLICIA-NACIONAL/raw/main/Reporte_Delito_Violencia_Intrafamiliar_Policia.csv.zip'
    url_med = 'https://github.com/brasarlington/Datos_Violencia_intrafamiliar_MEDICINA_LEGAL-POLICIA-NACIONAL/raw/main/Violencia_intrafamiliar_medicina%3Alegal.csv.zip'
    
    df_pol = pd.read_csv(url_pol, compression='zip')
    df_med = pd.read_csv(url_med, compression='zip')

    # Limpieza Policía
    df_pol['FECHA HECHO'] = pd.to_datetime(df_pol['FECHA HECHO'], dayfirst=True, errors='coerce')
    df_pol = df_pol[(df_pol['FECHA HECHO'].dt.year >= 2015) & (df_pol['FECHA HECHO'].dt.year <= 2024)]
    df_pol['AÑO'] = df_pol['FECHA HECHO'].dt.year
    df_pol['MES'] = df_pol['FECHA HECHO'].dt.month
    
    grupo_col_pol = ['DEPARTAMENTO', 'MUNICIPIO', 'ARMAS MEDIOS', 'GENERO', 'GRUPO ETARIO', 'AÑO', 'MES']
    df_pol = df_pol.groupby(grupo_col_pol)['CANTIDAD'].sum().reset_index()
    
    df_pol = df_pol.rename(columns={
        'ARMAS MEDIOS': 'MECANISMO_VIOLENCIA',
        'GENERO': 'SEXO',
        'GRUPO ETARIO': 'GRUPO_ETARIO'
    })

    # Limpieza Medicina Legal
    grupo_col_med = ['Departamento del hecho DANE', 'Municipio del hecho DANE', 
                     'Mecanismo Causal de la Lesión no Fatal', 'Sexo de la victima', 
                     'Ciclo Vital', 'Año del hecho', 'Mes del hecho']
    df_med = df_med.groupby(grupo_col_med).size().reset_index(name='CANTIDAD')
    
    df_med = df_med.rename(columns={
        'Departamento del hecho DANE': 'DEPARTAMENTO',
        'Municipio del hecho DANE': 'MUNICIPIO',
        'Mecanismo Causal de la Lesión no Fatal': 'MECANISMO_VIOLENCIA',
        'Sexo de la victima': 'SEXO',
        'Ciclo Vital': 'GRUPO_ETARIO',
        'Año del hecho': 'AÑO',
        'Mes del hecho': 'MES'
    })

    # Normalización
    for df in [df_pol, df_med]:
        df['DEPARTAMENTO'] = df['DEPARTAMENTO'].str.upper()
        df['MUNICIPIO'] = df['MUNICIPIO'].str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    
    df_med['DEPARTAMENTO'] = df_med['DEPARTAMENTO'].replace({
        'ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA': 'SAN ANDRÉS',
        'BOGOTÁ, D.C.': 'CUNDINAMARCA', 'QUINDIO': 'QUINDÍO'
    })
    df_pol['DEPARTAMENTO'] = df_pol['DEPARTAMENTO'].replace({'GUAJIRA': 'LA GUAJIRA', 'VALLE': 'VALLE DEL CAUCA'})
    df_med = df_med[df_med['DEPARTAMENTO'] != 'SIN INFORMACIÓN']
    
    df_pol['MECANISMO_VIOLENCIA'] = df_pol['MECANISMO_VIOLENCIA'].replace({
        'ARMA BLANCA / CORTOPUNZANTE': 'CORTOPUNZANTE', 'CORTANTES': 'CORTOPUNZANTE',
        'CORTOPUNZANTES': 'CORTOPUNZANTE', 'PUNZANTES': 'CORTOPUNZANTE',
        'CONTUNDENTES': 'CONTUNDENTE', 'ESCOPOLAMINA': 'OTROS'
    })
    
    rep_med_mec = {
        'Contundente': 'CONTUNDENTE', 'Corto contundente': 'CONTUNDENTE',
        'Cortante': 'CORTOPUNZANTE', 'Corto punzante': 'CORTOPUNZANTE', 'Punzante': 'CORTOPUNZANTE',
        'Proyectil de arma de fuego': 'ARMA DE FUEGO', 'Por determinar': 'NO REPORTADO',
        'SIN EMPLEO DE ARMAS': 'OTROS'
    }
    df_med['MECANISMO_VIOLENCIA'] = df_med['MECANISMO_VIOLENCIA'].replace(rep_med_mec)
    mechs_pol = df_pol['MECANISMO_VIOLENCIA'].unique()
    df_med['MECANISMO_VIOLENCIA'] = df_med['MECANISMO_VIOLENCIA'].apply(lambda x: x if x in mechs_pol else 'OTROS')

    df_med['SEXO'] = df_med['SEXO'].replace({'Hombre': 'MASCULINO', 'Mujer': 'FEMENINO'})
    df_med['GRUPO_ETARIO'] = df_med['GRUPO_ETARIO'].replace({
        '(12 a 17) Adolescencia': 'ADOLESCENTES', '(29 a 59) Adultez': 'ADULTOS',
        '(00 a 05) Primera Infancia': 'MENORES', '(06 a 11) Infancia': 'MENORES',
        '(Más de 60) Adulto Mayor': 'ADULTOS', '(18 a 28) Juventud': 'ADULTOS', 'Sin información': 'ADULTOS'
    })

    return df_med, df_pol

with st.spinner('Cargando datos...'):
    datos_med_crudos, datos_pol_crudos = cargar_y_limpiar_datos()

# ==========================================
# 🎛️ BARRA LATERAL (FILTROS INTERACTIVOS)
# ==========================================
st.sidebar.header("🔍 Filtros Globales")
st.sidebar.markdown("Usa estos filtros para explorar los datos.")

# 1. Filtro de Rango de Años (Slider)
min_year = int(min(datos_med_crudos['AÑO'].min(), datos_pol_crudos['AÑO'].min()))
max_year = int(max(datos_med_crudos['AÑO'].max(), datos_pol_crudos['AÑO'].max()))
anos_seleccionados = st.sidebar.slider("Rango de Años", min_year, max_year, (min_year, max_year))

# 2. Filtro de Departamento (Selectbox)
deptos_disponibles = sorted(list(set(datos_med_crudos['DEPARTAMENTO'].unique()) | set(datos_pol_crudos['DEPARTAMENTO'].unique())))
deptos_disponibles.insert(0, "TODOS LOS DEPARTAMENTOS")
depto_seleccionado = st.sidebar.selectbox("Departamento", deptos_disponibles)

# 3. Filtro de Sexo (Radio buttons)
sexo_seleccionado = st.sidebar.radio("Sexo de la Víctima", ["TODOS", "FEMENINO", "MASCULINO"])

# ==========================================
# 🔄 APLICAR FILTROS A LOS DATAFRAMES
# ==========================================
# Filtrar por año
df_med = datos_med_crudos[(datos_med_crudos['AÑO'] >= anos_seleccionados[0]) & (datos_med_crudos['AÑO'] <= anos_seleccionados[1])]
df_pol = datos_pol_crudos[(datos_pol_crudos['AÑO'] >= anos_seleccionados[0]) & (datos_pol_crudos['AÑO'] <= anos_seleccionados[1])]

# Filtrar por departamento
if depto_seleccionado != "TODOS LOS DEPARTAMENTOS":
    df_med = df_med[df_med['DEPARTAMENTO'] == depto_seleccionado]
    df_pol = df_pol[df_pol['DEPARTAMENTO'] == depto_seleccionado]

# Filtrar por sexo
if sexo_seleccionado != "TODOS":
    df_med = df_med[df_med['SEXO'] == sexo_seleccionado]
    df_pol = df_pol[df_pol['SEXO'] == sexo_seleccionado]

# Mostrar métricas rápidas de los filtros
col_m1, col_m2 = st.columns(2)
col_m1.metric("Total Casos Filtrados (Medicina Legal)", f"{df_med['CANTIDAD'].sum():,}")
col_m2.metric("Total Casos Filtrados (Policía Nacional)", f"{df_pol['CANTIDAD'].sum():,}")
st.divider()

# Validar que haya datos antes de graficar
if df_med.empty and df_pol.empty:
    st.warning("⚠️ No hay datos disponibles para la combinación de filtros seleccionada. Por favor, ajusta los filtros en la barra lateral.")
else:
    # --- TABS DE LA INTERFAZ ---
    tab1, tab2, tab3 = st.tabs(["🏥 Medicina Legal", "🚓 Policía Nacional", "⚖️ Comparativa"])

    # ==========================================
    # TAB 1: MEDICINA LEGAL
    # ==========================================
    with tab1:
        st.header("Instituto Nacional de Medicina Legal")
        if not df_med.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                casos_anio = df_med.groupby('AÑO')['CANTIDAD'].sum().reset_index()
                fig_line = px.line(casos_anio, x='AÑO', y='CANTIDAD', markers=True, 
                                   title="Evolución Temporal de Casos", color_discrete_sequence=['#ff7f0e'])
                fig_line.update_layout(xaxis=dict(tickmode='linear', dtick=1)) # Forzar años enteros
                st.plotly_chart(fig_line, use_container_width=True)
                
            with col2:
                bar_etario = df_med.groupby(['GRUPO_ETARIO', 'MECANISMO_VIOLENCIA'])['CANTIDAD'].sum().reset_index()
                fig_bar_etario = px.bar(bar_etario, x='GRUPO_ETARIO', y='CANTIDAD', color='MECANISMO_VIOLENCIA',
                                        title="Víctimas por Grupo Etario y Mecanismo", barmode='group',
                                        color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(fig_bar_etario, use_container_width=True)
        else:
            st.info("No hay datos de Medicina Legal para estos filtros.")

    # ==========================================
    # TAB 2: POLICÍA NACIONAL
    # ==========================================
    with tab2:
        st.header("Reportes de Policía Nacional")
        if not df_pol.empty:
            # Si se seleccionó "TODOS", mostramos top municipios. Si se seleccionó un Depto, mostramos municipios de ese depto.
            titulo_mun = f"Top 10 Municipios ({depto_seleccionado.title()})" if depto_seleccionado != "TODOS LOS DEPARTAMENTOS" else "Top 10 Municipios a Nivel Nacional"
            top_mun = df_pol.groupby('MUNICIPIO')['CANTIDAD'].sum().reset_index().sort_values('CANTIDAD', ascending=False).head(10)
            
            fig_mun = px.bar(top_mun, x='CANTIDAD', y='MUNICIPIO', color='CANTIDAD', orientation='h',
                             title=titulo_mun, color_continuous_scale=px.colors.sequential.Blues)
            fig_mun.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_mun, use_container_width=True)

            col3, col4 = st.columns(2)
            with col3:
                dept_etario = df_pol.groupby(['GRUPO_ETARIO'])['CANTIDAD'].sum().reset_index()
                fig_dept_eta = px.pie(dept_etario, values='CANTIDAD', names='GRUPO_ETARIO', hole=0.4,
                                      title="Distribución por Grupo Etario", color_discrete_sequence=px.colors.qualitative.Vivid)
                st.plotly_chart(fig_dept_eta, use_container_width=True)

            with col4:
                dept_mec = df_pol.groupby(['MECANISMO_VIOLENCIA'])['CANTIDAD'].sum().reset_index()
                fig_dept_mec = px.pie(dept_mec, values='CANTIDAD', names='MECANISMO_VIOLENCIA',
                                      title="Distribución por Mecanismo", color_discrete_sequence=px.colors.qualitative.Bold)
                st.plotly_chart(fig_dept_mec, use_container_width=True)
        else:
            st.info("No hay datos de Policía Nacional para estos filtros.")

    # ==========================================
    # TAB 3: COMPARATIVA
    # ==========================================
    with tab3:
        st.header("Comparativa Institucional")
        
        tendencia_med = df_med.groupby('AÑO')['CANTIDAD'].sum().reset_index()
        tendencia_med['FUENTE'] = 'Medicina Legal'
        tendencia_pol = df_pol.groupby('AÑO')['CANTIDAD'].sum().reset_index()
        tendencia_pol['FUENTE'] = 'Policía Nacional'
        
        df_comparativo = pd.concat([tendencia_med, tendencia_pol])
        
        if not df_comparativo.empty:
            fig_comp = px.line(df_comparativo, x='AÑO', y='CANTIDAD', color='FUENTE', markers=True,
                               title=f"Comparativa de Casos ({anos_seleccionados[0]} - {anos_seleccionados[1]})",
                               color_discrete_sequence=['#2ca02c', '#1f77b4'])
            fig_comp.update_layout(xaxis=dict(tickmode='linear', dtick=1))
            st.plotly_chart(fig_comp, use_container_width=True)
            
            # Tabla de resumen combinada
            with st.expander("Ver Datos Resumidos por Año y Entidad"):
                tabla_resumen = df_comparativo.pivot(index='AÑO', columns='FUENTE', values='CANTIDAD').fillna(0).astype(int)
                st.dataframe(tabla_resumen, use_container_width=True)
        else:
            st.info("No hay datos suficientes para la comparativa.")
