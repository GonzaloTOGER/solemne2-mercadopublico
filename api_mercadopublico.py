"""
=============================================================
Solemne II - FITO9017
Módulo: Conexión y extracción de datos desde API Mercado Público
Fuente oficial: https://api.mercadopublico.cl
Ticket prueba: F8537A18-6766-4DEF-9E59-426B4FEE2844
=============================================================

ARQUITECTURA DE LA API:
La API de Mercado Público opera en dos capas:

  Capa 1 - Listado (GET /licitaciones.json?estado=...):
    Retorna: CodigoExterno, Nombre, CodigoEstado, FechaCierre
    Uso: obtener la lista de códigos para consultar detalles

  Capa 2 - Detalle (GET /licitaciones.json?codigo=...):
    Retorna: todos los campos (Comprador, Fechas, Monto, Tipo, etc.)
    Uso: enriquecer cada licitación con sus datos completos

Esta arquitectura N+1 requiere una pausa entre requests (time.sleep)
para respetar el rate limit de la API y evitar error HTTP 429.
=============================================================
"""

import requests
import pandas as pd
import time

# ── Configuración ────────────────────────────────────────────
TICKET   = "F8537A18-6766-4DEF-9E59-426B4FEE2844"
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
PAUSA_SEGUNDOS = 0.8   # pausa entre requests para respetar rate limit


def obtener_listado(estado="activas", cantidad=50):
    """
    PASO 1 — Capa 1 de la API.
    Obtiene la lista básica de licitaciones (solo código, nombre y estado).

    Parámetros:
        estado   (str): "activas" | "adjudicadas" | "cerradas" | "todas"
        cantidad (int): número máximo de registros a solicitar

    Retorna:
        list[dict]: lista con los 4 campos básicos de cada licitación
    """
    params = {"estado": estado, "ticket": TICKET, "cantidad": cantidad}
    print(f"[API] GET licitaciones — estado='{estado}', cantidad={cantidad}")

    r = requests.get(BASE_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    if data.get("Codigo") == 203:
        raise ValueError(f"Ticket inválido: {data.get('Mensaje')}")

    listado = data.get("Listado", [])
    print(f"[OK]  {len(listado)} licitaciones recibidas "
          f"(total disponible en API: {data.get('Cantidad', '?')})")
    return listado


def obtener_detalle(codigo):
    """
    PASO 2 — Capa 2 de la API.
    Obtiene todos los campos de una licitación consultando por su código.

    Parámetros:
        codigo (str): código único de licitación (ej: '1000-10-LE26')

    Retorna:
        dict | None: objeto completo con Comprador, Fechas, Monto, etc.
                     Retorna None si la solicitud falla (no interrumpe el flujo)
    """
    try:
        r = requests.get(BASE_URL,
                         params={"codigo": codigo, "ticket": TICKET},
                         timeout=15)
        r.raise_for_status()
        listado = r.json().get("Listado", [])
        return listado[0] if listado else None
    except Exception as e:
        print(f"  [WARN] No se obtuvo detalle de {codigo}: {e}")
        return None


def construir_dataframe(estado="activas", cantidad=20):
    """
    FUNCIÓN PRINCIPAL.
    Combina listado + detalle para armar un DataFrame completo y limpio.

    Proceso:
        1. Solicita el listado de códigos (Capa 1).
        2. Por cada código, solicita el detalle completo (Capa 2).
        3. Aplana los sub-objetos anidados (Comprador → región, Fechas → datetime).
        4. Convierte tipos: fechas → datetime64, montos → float64.

    Parámetros:
        estado   (str): estado de las licitaciones a consultar
        cantidad (int): número de licitaciones a obtener

    Retorna:
        pd.DataFrame: tabla lista para análisis con pandas y matplotlib
    """
    listado_basico = obtener_listado(estado=estado, cantidad=cantidad)
    total = len(listado_basico)
    print(f"\n[INFO] Obteniendo detalle de {total} licitaciones...")

    registros = []
    for i, item in enumerate(listado_basico, 1):
        codigo = item["CodigoExterno"]
        print(f"  [{i:>3}/{total}] {codigo}", end="\r")

        detalle = obtener_detalle(codigo)
        if detalle is None:
            continue

        comprador = detalle.get("Comprador") or {}
        fechas    = detalle.get("Fechas")    or {}

        registros.append({
            # Identificación
            "codigo":             codigo,
            "nombre":             detalle.get("Nombre", ""),
            # Clasificación
            "estado":             detalle.get("Estado", ""),
            "tipo":               detalle.get("Tipo", ""),
            # Valores
            "moneda":             detalle.get("Moneda", "CLP"),
            "monto_estimado":     detalle.get("MontoEstimado"),
            # Organismo comprador
            "organismo":          comprador.get("NombreOrganismo", ""),
            "region":             (comprador.get("RegionUnidad") or "").strip(),
            "comuna":             comprador.get("ComunaUnidad", ""),
            # Fechas clave
            "fecha_publicacion":  fechas.get("FechaPublicacion"),
            "fecha_cierre":       fechas.get("FechaCierre"),
            "fecha_adjudicacion": fechas.get("FechaAdjudicacion"),
            # Indicadores
            "dias_cierre":        detalle.get("DiasCierreLicitacion"),
            "reclamos":           detalle.get("CantidadReclamos", 0),
        })

        time.sleep(PAUSA_SEGUNDOS)  # respetar rate limit

    print(f"\n[OK]  DataFrame construido con {len(registros)} registros")

    # ── Construir y limpiar DataFrame ────────────────────────
    df = pd.DataFrame(registros)

    # Convertir fechas
    for col in ["fecha_publicacion", "fecha_cierre", "fecha_adjudicacion"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Convertir numéricos
    df["monto_estimado"] = pd.to_numeric(df["monto_estimado"], errors="coerce")
    df["dias_cierre"]    = pd.to_numeric(df["dias_cierre"],    errors="coerce")

    return df


# ── Ejecución de prueba ──────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  Solemne II — Prueba API Mercado Público Chile")
    print("=" * 55)

    df = construir_dataframe(estado="activas", cantidad=5)

    print("\n--- Vista previa ---")
    cols = ["codigo", "estado", "tipo", "region", "organismo"]
    print(df[cols].to_string(index=False))

    print(f"\n--- Tipos de columnas ---")
    print(df.dtypes)

    print(f"\n--- Resumen general ---")
    print(f"  Filas          : {len(df)}")
    print(f"  Regiones únicas: {df['region'].nunique()}")
    print(f"  Tipos únicos   : {sorted(df['tipo'].dropna().unique())}")
    print(f"  Con monto      : {df['monto_estimado'].notna().sum()}")
