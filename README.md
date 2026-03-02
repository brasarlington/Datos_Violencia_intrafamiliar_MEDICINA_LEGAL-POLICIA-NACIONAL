# 📊 Dashboard de Violencia Intrafamiliar en Colombia

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://datosviolenciaintrafamiliarmedicinalegal-policia-nacional-kmnz.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-orange)
![Plotly](https://img.shields.io/badge/Plotly-Visualization-green)

## 📝 Descripción del Proyecto

Este proyecto es una aplicación web interactiva diseñada para analizar y visualizar los datos de violencia intrafamiliar en Colombia. La herramienta consolida información reportada por entidades oficiales como la **Policía Nacional** y el **Instituto Nacional de Medicina Legal**.

El objetivo es facilitar la comprensión de patrones, tendencias temporales y distribución geográfica de los casos reportados, permitiendo a investigadores y ciudadanos explorar la data de manera intuitiva.

🔗 **[Ver la aplicación en vivo aquí](https://datosviolenciaintrafamiliarmedicinalegal-policia-nacional-kmnz.streamlit.app/)**

## ✨ Características Principales

* **📈 Tendencias Temporales:** Visualización de la evolución de casos por año y mes.
* **🗺️ Análisis Geográfico:** Distribución de reportes por departamentos.
* **👥 Demografía:** Desglose de víctimas por género y grupos de edad.
* **🔍 Filtros Interactivos:** Barra lateral para segmentar la información dinámicamente.
* **📥 Descarga de Datos:** Posibilidad de explorar las tablas de datos crudos.

## 🛠️ Tecnologías Utilizadas

El proyecto fue construido utilizando 100% Python con las siguientes librerías clave:

| Tecnología | Propósito |
|------------|-----------|
| **Streamlit** | Framework para la creación de la web app y la interfaz de usuario. |
| **Pandas** | Limpieza, transformación y manipulación de los datasets (CSV/ZIP). |
| **Plotly Express** | Generación de gráficos interactivos (mapas, líneas, barras). |
| **GitHub** | Alojamiento del código y los datos fuente. |

## 📂 Estructura del Repositorio

```text
├── streamlit_app.py                # Código fuente principal de la aplicación
├── requirements.txt      # Dependencias necesarias para ejecutar el proyecto
├── datos_medicinal.csv   # Dataset de Medicina Legal (o enlace al mismo)
├── README.md             # Documentación del proyecto
