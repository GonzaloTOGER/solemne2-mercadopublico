# DataViz Mercado Público Chile — Solemne II FITO9017

Aplicación web que analiza licitaciones públicas del Estado de Chile
usando datos en tiempo real de la API oficial de Mercado Público.

## Estructura del proyecto

```
solemne2/
├── app.py                   # Aplicación principal Streamlit
├── api_mercadopublico.py    # Módulo de conexión a la API
├── analisis.py              # Módulo de análisis con Pandas
├── visualizaciones.py       # Módulo de gráficos con Matplotlib
├── requirements.txt         # Dependencias del proyecto
└── README.md                # Este archivo
```

## Cómo ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy en Streamlit Community Cloud

1. Subir este repositorio a GitHub (público)
2. Ir a https://share.streamlit.io
3. Conectar con tu cuenta de GitHub
4. Seleccionar el repositorio y `app.py` como archivo principal
5. Click en "Deploy"

## Fuente de datos

- **API:** https://api.mercadopublico.cl
- **Ticket de prueba:** F8537A18-6766-4DEF-9E59-426B4FEE2844
- **Documentación:** https://api.mercadopublico.cl/modules/api.aspx

## Librerías utilizadas

| Librería | Uso |
|---|---|
| `requests` | Consumo de la API REST |
| `json` | Procesamiento de respuestas JSON |
| `pandas` | Análisis y transformación de datos |
| `matplotlib` | Visualizaciones estáticas |
| `streamlit` | Interfaz web interactiva |
