"""
=============================================================
Solemne II - FITO9017
Módulo: Visualizaciones con Matplotlib
Fuente: API Mercado Público Chile
=============================================================

Genera 4 gráficos que cubren el criterio "Presentación de datos"
de la rúbrica. Cada función retorna un objeto Figure de matplotlib
que puede ser mostrado en Streamlit con st.pyplot(fig).

Gráficos:
  1. Barras horizontales — Licitaciones por región
  2. Torta              — Distribución por tipo de licitación
  3. Barras verticales  — Top 10 organismos
  4. Histograma         — Distribución de días de cierre
=============================================================
"""

import matplotlib
matplotlib.use("Agg")        # backend sin pantalla (compatible con Streamlit)
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np

# ── Paleta y estilo base ─────────────────────────────────────
COLORES = ["#1a3a5c", "#2e6da4", "#4da6e0", "#a8d5f5",
           "#f0a500", "#e05c00", "#7ab648", "#c75bcb"]

def _formato_millones(x, _):
    """Formateador de eje Y para valores en millones de CLP."""
    if x >= 1_000_000:
        return f"${x/1_000_000:.0f}M"
    return f"${x:,.0f}"


# ── GRÁFICO 1: Licitaciones por región ──────────────────────
def grafico_por_region(df):
    """
    Barras horizontales con cantidad de licitaciones por región.
    Excluye 'No especificada' para mayor claridad.

    Parámetros:
        df (pd.DataFrame): dataset de licitaciones

    Retorna:
        matplotlib.figure.Figure
    """
    df_filtrado = df[df["region_corta"] != "No especificada"].copy()
    conteo = (
        df_filtrado.groupby("region_corta")
        .size()
        .sort_values(ascending=True)
        .reset_index(name="cantidad")
    )

    fig, ax = plt.subplots(figsize=(9, max(4, len(conteo) * 0.5)))
    bars = ax.barh(conteo["region_corta"], conteo["cantidad"],
                   color=COLORES[1], edgecolor="white", linewidth=0.5)

    # Etiquetas dentro de las barras
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.1, bar.get_y() + bar.get_height() / 2,
                f" {int(w)}", va="center", ha="left", fontsize=9)

    ax.set_xlabel("Número de licitaciones", fontsize=10)
    ax.set_title("Licitaciones activas por Región", fontsize=13, fontweight="bold", pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, conteo["cantidad"].max() * 1.25)
    fig.tight_layout()
    return fig


# ── GRÁFICO 2: Distribución por tipo ───────────────────────
def grafico_por_tipo(df):
    """
    Gráfico de torta con la distribución porcentual por tipo de licitación.
    Agrupa tipos con < 5% en 'Otros' para mayor legibilidad.

    Parámetros:
        df (pd.DataFrame): dataset de licitaciones

    Retorna:
        matplotlib.figure.Figure
    """
    conteo = df["tipo_descripcion"].value_counts()

    # Agrupar tipos pequeños en "Otros"
    umbral = len(df) * 0.05
    otros  = conteo[conteo < umbral].sum()
    conteo = conteo[conteo >= umbral]
    if otros > 0:
        conteo["Otros"] = otros

    fig, ax = plt.subplots(figsize=(7, 5))
    wedges, texts, autotexts = ax.pie(
        conteo.values,
        labels=None,
        autopct="%1.1f%%",
        colors=COLORES[:len(conteo)],
        startangle=140,
        pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color("white")
        at.set_fontweight("bold")

    ax.legend(
        wedges, conteo.index,
        title="Tipo de licitación",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=8,
    )
    ax.set_title("Distribución por tipo de licitación", fontsize=13,
                 fontweight="bold", pad=12)
    fig.tight_layout()
    return fig


# ── GRÁFICO 3: Top organismos ───────────────────────────────
def grafico_top_organismos(df, n=8):
    """
    Barras verticales con los organismos que más licitaciones publican.

    Parámetros:
        df (pd.DataFrame): dataset de licitaciones
        n  (int): número de organismos a mostrar

    Retorna:
        matplotlib.figure.Figure
    """
    top = (
        df[df["organismo"] != ""]
        .groupby("organismo")
        .size()
        .sort_values(ascending=False)
        .head(n)
        .reset_index(name="cantidad")
    )

    # Acortar nombres largos para el eje X
    top["org_corto"] = top["organismo"].apply(
        lambda x: x[:35] + "…" if len(x) > 35 else x
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(
        top["org_corto"], top["cantidad"],
        color=COLORES[:len(top)], edgecolor="white"
    )

    # Etiquetas sobre las barras
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05,
                f"{int(h)}", ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("Número de licitaciones", fontsize=10)
    ax.set_title(f"Top {n} organismos con más licitaciones activas",
                 fontsize=13, fontweight="bold", pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=35, ha="right", fontsize=8)
    ax.set_ylim(0, top["cantidad"].max() * 1.2)
    fig.tight_layout()
    return fig


# ── GRÁFICO 4: Histograma días de cierre ───────────────────
def grafico_dias_cierre(df):
    """
    Histograma de la distribución de días disponibles antes del cierre.
    Permite entender los plazos habituales del proceso licitatorio.

    Parámetros:
        df (pd.DataFrame): dataset de licitaciones

    Retorna:
        matplotlib.figure.Figure
    """
    dias = df["dias_cierre"].dropna()

    if dias.empty:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.text(0.5, 0.5, "Sin datos de días de cierre",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    fig, ax = plt.subplots(figsize=(7, 4))
    n, bins, patches = ax.hist(
        dias, bins=min(15, int(dias.nunique())),
        color=COLORES[2], edgecolor="white", linewidth=0.8
    )

    # Línea de la media
    media = dias.mean()
    ax.axvline(media, color=COLORES[5], linestyle="--", linewidth=1.8,
               label=f"Promedio: {media:.0f} días")

    ax.set_xlabel("Días antes del cierre", fontsize=10)
    ax.set_ylabel("Número de licitaciones", fontsize=10)
    ax.set_title("Distribución de plazos de cierre", fontsize=13,
                 fontweight="bold", pad=12)
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.tight_layout()
    return fig


# ── Ejecución de prueba ─────────────────────────────────────
if __name__ == "__main__":
    import os
    from analisis import cargar_datos

    print("=" * 55)
    print("  Solemne II — Generación de visualizaciones")
    print("=" * 55)

    df = cargar_datos("licitaciones.csv")
    os.makedirs("graficos", exist_ok=True)

    graficos = [
        ("1_licitaciones_por_region.png",  grafico_por_region(df)),
        ("2_distribucion_tipo.png",         grafico_por_tipo(df)),
        ("3_top_organismos.png",            grafico_top_organismos(df)),
        ("4_dias_cierre.png",               grafico_dias_cierre(df)),
    ]

    for nombre, fig in graficos:
        ruta = f"graficos/{nombre}"
        fig.savefig(ruta, dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"  ✅ Guardado: {ruta}")

    print("\n✅ Todos los gráficos generados correctamente")
