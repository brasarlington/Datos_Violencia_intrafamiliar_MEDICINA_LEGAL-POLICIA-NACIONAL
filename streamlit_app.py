import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="Dashboard Violencia Intrafamiliar",
    layout="wide",
    page_icon="⚖️"
)

st.title("⚖️ Violencia Intrafamiliar en Colombia (2015 - 2024)")
st.markdown("Análisis comparativo de reportes del **Instituto Nacional de Medicina Legal** y la **Policía Nacional**.")

# --- FUNCIÓN DE CARGA Y LIMPIEZA DE DATOS (Basada en tu Notebook) ---
@st.cache_data
def cargar_y_limpiar_datos():
    # 1. URLs a los ZIPs
    url_pol = 'https://github.com/brasarlington/Datos_Violencia_intrafamiliar_MEDICINA_LEGAL-POLICIA-NACIONAL/raw/main/Reporte_Delito_Violencia_Intrafamiliar_Policia.csv.zip'
    url_med = 'https://github.com/brasarlington/Datos_Violencia_intrafamiliar_MEDICINA_LEGAL-POLICIA-NACIONAL/raw/main/Violencia_intrafamiliar_medicina%3Alegal.csv.zip'
    
    # 2. Cargar Datos
    df_pol = pd.read_csv(url_pol, compression='zip')
    df_med = pd.read_csv(url_med, compression='zip')

    # 3. Limpieza Policía
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

    # 4. Limpieza Medicina Legal
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

    # 5. Normalización Común (Departamentos)
    for df in [df_pol, df_med]:
        df['DEPARTAMENTO'] = df['DEPARTAMENTO'].str.upper()
        df['MUNICIPIO'] = df['MUNICIPIO'].str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    
    df_med['DEPARTAMENTO'] = df_med['DEPARTAMENTO'].replace({
        'ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA': 'SAN ANDRÉS',
        'BOGOTÁ, D.C.': 'CUNDINAMARCA', 'QUINDIO': 'QUINDÍO'
    })
    df_pol['DEPARTAMENTO'] = df_pol['DEPARTAMENTO'].replace({'GUAJIRA': 'LA GUAJIRA', 'VALLE': 'VALLE DEL CAUCA'})
    df_med = df_med[df_med['DEPARTAMENTO'] != 'SIN INFORMACIÓN']
    df_pol['MUNICIPIO'] = df_pol['MUNICIPIO'].str.replace(' (CT)', '', regex=False)

    # 6. Normalización (Mecanismos, Sexo, Etario)
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

    # 7. Regiones
    regiones = {
        "REGION ANDINA": ["ANTIOQUIA", "BOYACÁ", "CALDAS", "CUNDINAMARCA", "HUILA", "NORTE DE SANTANDER", "QUINDÍO", "RISARALDA", "SANTANDER", "TOLIMA"],
        "REGION CARIBE": ["ATLÁNTICO", "BOLÍVAR", "CESAR", "CÓRDOBA", "LA GUAJIRA", "MAGDALENA", "SUCRE"],
        "REGION PACÍFICA": ["CHOCÓ", "VALLE DEL CAUCA", "NARIÑO", "CAUCA"],
        "REGION ORINOQUÍA": ["ARAUCA", "CASANARE", "META", "VICHADA"],
        "REGION AMAZÓNICA": ["AMAZONAS", "CAQUETÁ", "GUAINÍA", "GUAVIARE", "PUTUMAYO", "VAUPÉS"],
        "REGION INSULAR": ["SAN ANDRÉS"]
    }
    region_map = {depto: region for region, deptos in regiones.items() for depto in deptos}
    df_med['REGION'] = df_med['DEPARTAMENTO'].apply(lambda x: region_map.get(x, 'OTRA REGION'))
    df_pol['REGION'] = df_pol['DEPARTAMENTO'].apply(lambda x: region_map.get(x, 'OTRA REGION'))

    return df_med, df_pol

# Cargar Datos con Spinner
with st.spinner('Procesando millones de registros... Esto tomará unos segundos la primera vez.'):
    datos_med, datos_pol = cargar_y_limpiar_datos()

# --- TABS DE LA INTERFAZ ---
tab1, tab2, tab3 = st.tabs(["🏥 Medicina Legal", "🚓 Policía Nacional", "⚖️ Comparativa y Tasas"])

# ==========================================
# TAB 1: MEDICINA LEGAL
# ==========================================
with tab1:
    st.header("Análisis: Instituto Nacional de Medicina Legal")
    col1, col2 = st.columns(2)
    
    with col1:
        # Evolución Anual
        casos_anio = datos_med.groupby('AÑO')['CANTIDAD'].sum().reset_index()
        fig_line = px.line(casos_anio, x='AÑO', y='CANTIDAD', markers=True, 
                           title="Evolución de Violencia (2015-2024)",
                           color_discrete_sequence=['#ff7f0e'], template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)
        
        # Distribución por Región (Pie)
        casos_region = datos_med.groupby('REGION')['CANTIDAD'].sum().reset_index()
        fig_pie = px.pie(casos_region, values='CANTIDAD', names='REGION', hole=0.4,
                         title="Distribución por Región",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Grupo Etario vs Mecanismo
        bar_etario = datos_med.groupby(['GRUPO_ETARIO', 'MECANISMO_VIOLENCIA'])['CANTIDAD'].sum().reset_index()
        fig_bar_etario = px.bar(bar_etario, x='GRUPO_ETARIO', y='CANTIDAD', color='MECANISMO_VIOLENCIA',
                                title="Casos por Grupo Etario y Mecanismo", barmode='group',
                                color_discrete_sequence=px.colors.qualitative.Set2, template="plotly_white")
        st.plotly_chart(fig_bar_etario, use_container_width=True)
        
        # Casos por Sexo y Año
        casos_sexo = datos_med.groupby(['AÑO', 'SEXO'])['CANTIDAD'].sum().reset_index()
        fig_sexo = px.bar(casos_sexo, x='AÑO', y='CANTIDAD', color='SEXO', barmode='group',
                          title="Casos por Año y Sexo",
                          color_discrete_sequence=['#1f77b4', '#d62728'], template="plotly_white")
        st.plotly_chart(fig_sexo, use_container_width=True)

# ==========================================
# TAB 2: POLICÍA NACIONAL
# ==========================================
with tab2:
    st.header("Análisis: Reportes de Policía Nacional")
    
    # Top 10 Municipios
    top_mun = datos_pol.groupby('MUNICIPIO')['CANTIDAD'].sum().reset_index().sort_values('CANTIDAD', ascending=False).head(10)
    fig_mun = px.bar(top_mun, x='MUNICIPIO', y='CANTIDAD', color='MUNICIPIO',
                     title="Top 10 Municipios con Más Casos",
                     color_discrete_sequence=px.colors.qualitative.Prism, template="plotly_white")
    st.plotly_chart(fig_mun, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        # Departamentos por Grupo Etario
        dept_etario = datos_pol.groupby(['DEPARTAMENTO', 'GRUPO_ETARIO'])['CANTIDAD'].sum().reset_index()
        dept_totales = datos_pol.groupby('DEPARTAMENTO')['CANTIDAD'].sum().sort_values(ascending=False).index
        fig_dept_eta = px.bar(dept_etario, x='DEPARTAMENTO', y='CANTIDAD', color='GRUPO_ETARIO',
                              title="Violencia por Grupo Etario según Depto",
                              category_orders={"DEPARTAMENTO": list(dept_totales)},
                              color_discrete_sequence=px.colors.qualitative.Vivid)
        fig_dept_eta.update_xaxes(tickangle=45)
        st.plotly_chart(fig_dept_eta, use_container_width=True)

    with col4:
        # Departamentos por Mecanismo
        dept_mec = datos_pol.groupby(['DEPARTAMENTO', 'MECANISMO_VIOLENCIA'])['CANTIDAD'].sum().reset_index()
        fig_dept_mec = px.bar(dept_mec, x='DEPARTAMENTO', y='CANTIDAD', color='MECANISMO_VIOLENCIA',
                              title="Violencia por Mecanismo según Depto",
                              category_orders={"DEPARTAMENTO": list(dept_totales)},
                              color_discrete_sequence=px.colors.qualitative.Bold)
        fig_dept_mec.update_xaxes(tickangle=45)
        st.plotly_chart(fig_dept_mec, use_container_width=True)

# ==========================================
# TAB 3: COMPARATIVA Y TASAS
# ==========================================
with tab3:
    st.header("Comparativa y Tasas de Incidencia Poblacional")
    
    # Datos de Población
    poblacion_data = {
        'DEPARTAMENTO': [
            'AMAZONAS', 'ANTIOQUIA', 'ARAUCA', 'ATLÁNTICO', 'BOLÍVAR', 'BOYACÁ', 'CALDAS', 'CAQUETÁ', 'CASANARE',
            'CAUCA', 'CESAR', 'CHOCÓ', 'CUNDINAMARCA', 'CÓRDOBA', 'GUAINÍA', 'GUAVIARE', 'HUILA', 'LA GUAJIRA',
            'MAGDALENA', 'META', 'NARIÑO', 'NORTE DE SANTANDER', 'PUTUMAYO', 'QUINDÍO', 'RISARALDA', 'SAN ANDRÉS',
            'SANTANDER', 'SUCRE', 'TOLIMA', 'VALLE DEL CAUCA', 'VAUPÉS', 'VICHADA'
        ],
        'POBLACION': [
            84109, 6880799, 277883, 2836795, 2227181, 1283225, 1050126, 428162, 467565,
            1583095, 1440484, 586128, 11363004, 1969108, 57934, 84550, 1194754, 1057252,
            1526269, 1144286, 1704383, 1694970, 385400, 556880, 973879, 56309,
            2380650, 1019575, 1374384, 4693432, 47961, 143117
        ]
    }
    df_pob = pd.DataFrame(poblacion_data)
    
    # Calcular Tasa (Medicina Legal vs Población)
    casos_depto_med = datos_med.groupby('DEPARTAMENTO')['CANTIDAD'].sum().reset_index()
    df_tasas = pd.merge(casos_depto_med, df_pob, on='DEPARTAMENTO', how='inner')
    df_tasas['TASA_POR_100K'] = (df_tasas['CANTIDAD'] / df_tasas['POBLACION']) * 100000
    df_tasas = df_tasas.sort_values('TASA_POR_100K', ascending=False)
    
    fig_tasas = px.bar(df_tasas, x='DEPARTAMENTO', y='TASA_POR_100K', color='TASA_POR_100K',
                       title="Tasa de Violencia por 100,000 Habitantes (Medicina Legal)",
                       color_continuous_scale=px.colors.sequential.Sunset, template="plotly_white")
    st.plotly_chart(fig_tasas, use_container_width=True)

    # Gráfico Comparativo de Tendencia
    tendencia_med = datos_med.groupby('AÑO')['CANTIDAD'].sum().reset_index()
    tendencia_med['FUENTE'] = 'Medicina Legal'
    tendencia_pol = datos_pol.groupby('AÑO')['CANTIDAD'].sum().reset_index()
    tendencia_pol['FUENTE'] = 'Policía Nacional'
    
    df_comparativo = pd.concat([tendencia_med, tendencia_pol])
    
    fig_comp = px.line(df_comparativo, x='AÑO', y='CANTIDAD', color='FUENTE', markers=True,
                       title="Comparativa de Casos Totales: Policía Nacional vs Medicina Legal",
                       color_discrete_sequence=['#2ca02c', '#1f77b4'], template="plotly_white")
    st.plotly_chart(fig_comp, use_container_width=True)
