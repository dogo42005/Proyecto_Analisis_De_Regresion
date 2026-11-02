"""
prepare_model_data.py
=====================
Prepara la base de MODELAMIENTO a partir de data/processed/lgd_2007.csv
(la base "amplia" que genera build_dataset.py).

Qué hace, en orden:
  1. Lee lgd_2007.csv (códigos y fechas como texto, para no perder ceros).
  2. Excluye liquidaciones en los meses previos al corte de desempeño (D7).
  3. Se queda con los casos completos en los predictores candidatos (D5).
  4. Excluye estados sin división censal (Puerto Rico) (D3).
  5. Descarta variables sin información en 2007 (D6).
  6. Crea columnas nuevas SIN sobrescribir las originales:
       lgd_trunc, division, channel_grp, property_type_grp, n_units_grp, split.
  7. Verifica la base (se detiene si algo no calza) y guarda:
       - data/processed/lgd_2007_model.csv          (base de modelamiento)
       - outputs/tables/flujo_muestral.csv          (tabla para el informe)
       - outputs/prepare_model_data_report.txt      (el mismo reporte que se imprime)

Las decisiones (D1-D7) están como constantes en la sección "Decisiones".
Fueron elegidas el 02-11-2026 y deben ser ratificadas por el grupo; si alguna
cambia, basta con editar la constante y volver a correr el script.
Detalle de cada decisión: cleaning_log.md.

Uso (desde la raíz del repositorio, después de build_dataset.py):
    python src/prepare_model_data.py
"""

from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

# La lista de predictores candidatos se toma de build_dataset.py para que
# ambos scripts usen exactamente la misma (se define en un solo lugar).
from build_dataset import CANDIDATE_PREDICTORS

# ---------------------------------------------------------------------------
# Rutas (relativas a la raíz del repo)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
IN_DATA = ROOT / "data" / "processed" / "lgd_2007.csv"
IN_BUILD_REPORT = ROOT / "outputs" / "build_dataset_report.txt"
OUT_DATA = ROOT / "data" / "processed" / "lgd_2007_model.csv"
OUT_FLOW = ROOT / "outputs" / "tables" / "flujo_muestral.csv"
OUT_REPORT = ROOT / "outputs" / "prepare_model_data_report.txt"

# Columnas que se leen como número; todo lo demás queda como texto.
NUMERIC_COLS = [
    "credit_score", "mi_pct", "n_units", "cltv", "dti", "orig_upb", "ltv",
    "orig_interest_rate", "orig_loan_term", "n_borrowers", "loan_age",
    "current_interest_rate", "zero_balance_removal_upb", "net_sale_proceeds",
    "mi_recoveries", "non_mi_recoveries", "total_expenses",
    "delinquent_accrued_interest", "actual_loss", "lgd",
]

# ---------------------------------------------------------------------------
# Decisiones (por ratificar en grupo)
# ---------------------------------------------------------------------------
# D7: se excluyen las liquidaciones de los meses 2026-01, 2026-02 y 2026-03
# (los tres meses previos al corte de desempeño 202603, incluido el del corte).
PERFORMANCE_CUTOFF = "202603"
MONTHS_BEFORE_CUTOFF = 3

# D5: análisis con casos completos en los predictores candidatos.
#     (La lista está en build_dataset.py: CANDIDATE_PREDICTORS.)

# D6: variables sin información en 2007 (100 % NA, sin variación o casi vacías).
DROP_COLS = ["vantage_score_4", "property_valuation_method", "amortization_type", "eltv"]

# D1: no se modifica 'lgd'; se agrega 'lgd_trunc' = lgd truncada a [0, 1].
LGD_TRUNC_RANGE = (0.0, 1.0)

# D4: partición temporal por mes de liquidación (zero_balance_effective_date).
#     Entrenamiento: liquidaciones hasta este mes (incluido). Validación: después.
TRAIN_LAST_MONTH = "201412"

# D3: estados -> 9 divisiones censales.
# Fuente: U.S. Census Bureau, "Census Regions and Divisions of the United States"
# https://www2.census.gov/geo/pdfs/maps-data/maps/reference/us_regdiv.pdf
# Verificado el 02-11-2026: 9 divisiones, 50 estados + DC, sin repetidos y con
# los mismos nombres de división que el PDF (ver cleaning_log.md).
CENSUS_DIVISIONS = {
    "New England": ["CT", "ME", "MA", "NH", "RI", "VT"],
    "Middle Atlantic": ["NJ", "NY", "PA"],
    "East North Central": ["IL", "IN", "MI", "OH", "WI"],
    "West North Central": ["IA", "KS", "MN", "MO", "NE", "ND", "SD"],
    "South Atlantic": ["DE", "DC", "FL", "GA", "MD", "NC", "SC", "VA", "WV"],
    "East South Central": ["AL", "KY", "MS", "TN"],
    "West South Central": ["AR", "LA", "OK", "TX"],
    "Mountain": ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY"],
    "Pacific": ["AK", "CA", "HI", "OR", "WA"],
}
STATE_TO_DIVISION = {st: div for div, states in CENSUS_DIVISIONS.items() for st in states}
# Los estados sin división (p. ej. PR = Puerto Rico) se excluyen.

# D3: agrupación de niveles escasos. Se crean columnas nuevas (*_grp).
# channel: R = retail; B (broker), C (correspondent) y T (TPO no especificado)
# se unen como originación por terceros (verificado en la guía, p. 6). Ojo: T
# también se usa cuando el canal no está disponible, así que "TPO" incluye
# algunos créditos de canal desconocido (ver cleaning_log.md).
CHANNEL_MAP = {"R": "R", "B": "TPO", "C": "TPO", "T": "TPO"}
# property_type: CP (cooperativa, 3 casos) se une con CO (condominio).
PROPERTY_TYPE_MAP = {"SF": "SF", "PU": "PU", "CO": "CO", "CP": "CO", "MH": "MH"}
# n_units: 1 unidad vs. 2 a 4 unidades.
N_UNITS_MAP = {1: "1", 2: "2-4", 3: "2-4", 4: "2-4"}


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
report_lines = []
flow = []  # filas de la tabla de flujo muestral


def log(msg=""):
    """Imprime en pantalla y guarda la línea para el archivo de reporte."""
    print(msg)
    report_lines.append(msg)


def add_flow(step, n_left, n_excluded, rule):
    """Agrega un paso a la tabla de flujo muestral y lo imprime."""
    flow.append({"paso": step, "quedan": n_left, "excluidos": n_excluded, "regla": rule})
    excl = "" if n_excluded is None else f"  (excluidos: {n_excluded:,})"
    log(f"  {step:<55} {n_left:>7,}{excl}")


def to_month_index(yyyymm):
    """Convierte fechas AAAAMM (texto) a un índice de meses: año*12 + mes."""
    s = pd.to_numeric(yyyymm, errors="coerce")
    return (s // 100) * 12 + (s % 100)


def read_build_counts():
    """Lee del reporte de build_dataset.py los conteos previos a lgd_2007.csv
    (total, códigos de pérdida, actual_loss informado), para que la tabla de
    flujo muestral parta desde los 50.000 créditos."""
    text = IN_BUILD_REPORT.read_text(encoding="utf-8")
    patterns = {
        "a": r"\(a\) Total de créditos: ([\d,]+)",
        "b": r"\(b\) Créditos con zero_balance_code en .*?: ([\d,]+)",
        "c": r"\(c\) \.\.\. y con actual_loss no nulo: ([\d,]+)",
    }
    counts = {}
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m is None:
            sys.exit(f"ERROR: no se encontró el conteo ({key}) en {IN_BUILD_REPORT.name}. "
                     "Volver a correr build_dataset.py.")
        counts[key] = int(m.group(1).replace(",", ""))
    return counts


def check(condition, msg):
    """Detiene el script si una verificación falla (en vez de seguir con una
    base incorrecta)."""
    if not condition:
        sys.exit(f"ERROR en verificación: {msg}")
    log(f"  OK  {msg}")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    log("=" * 70)
    log("PREPARE MODEL DATA - base de modelamiento LGD, muestra 2007")
    log("=" * 70)

    # ---- 1. Lectura ------------------------------------------------------
    # Todo como texto y luego solo las numéricas a número: así '02' sigue
    # siendo '02' y las fechas AAAAMM no se convierten en decimales.
    df = pd.read_csv(IN_DATA, dtype=str)
    for c in NUMERIC_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    lgd_original = df.set_index("loan_id")["lgd"].copy()  # para verificar al final
    log(f"Leído: {IN_DATA.relative_to(ROOT)}  ({len(df):,} filas, {df.shape[1]} columnas)")

    # ---- Flujo previo (desde el reporte de build_dataset.py) -------------
    build = read_build_counts()
    log("\nFlujo muestral:")
    add_flow("Créditos en la muestra 2007", build["a"], None, "build_dataset_report.txt")
    add_flow("zero_balance_code en {02, 03, 09, 15}", build["b"], build["a"] - build["b"],
             "Solo estos cierres tienen pérdida calculada (guía p. 13)")
    add_flow("actual_loss informado (base lgd_2007.csv)", build["c"], build["b"] - build["c"],
             "actual_loss nulo: créditos con defect_settlement_date")
    if len(df) != build["c"]:
        sys.exit(f"ERROR: lgd_2007.csv tiene {len(df):,} filas y el reporte dice {build['c']:,}. "
                 "Volver a correr build_dataset.py.")

    # ---- 2. D7: liquidaciones en los meses previos al corte --------------
    # Diferencia en meses entre el corte y la liquidación < 3  =>  2026-01..03.
    months_to_cutoff = (to_month_index(pd.Series([PERFORMANCE_CUTOFF])).iloc[0]
                        - to_month_index(df["zero_balance_effective_date"]))
    recent = months_to_cutoff < MONTHS_BEFORE_CUTOFF
    n0 = len(df)
    df = df[~recent].copy()
    add_flow("Sin liquidaciones en los 3 meses previos al corte (D7)", len(df), n0 - len(df),
             f"Corte de desempeño {PERFORMANCE_CUTOFF}: se excluyen 2026-01 a 2026-03")

    # ---- 3. D5: casos completos ------------------------------------------
    log("\n  NaN por predictor candidato (antes de excluir):")
    for c in CANDIDATE_PREDICTORS:
        n_na = int(df[c].isna().sum())
        if n_na:
            log(f"    {c:<24} {n_na:>5,}")
    complete = df[CANDIDATE_PREDICTORS].notna().all(axis=1)
    n0 = len(df)
    df = df[complete].copy()
    add_flow("Casos completos en los predictores candidatos (D5)", len(df), n0 - len(df),
             "Se excluyen créditos con NaN en dti o credit_score")

    # ---- 4. D3: estados sin división censal ------------------------------
    df["division"] = df["property_state"].map(STATE_TO_DIVISION)
    no_div = df["division"].isna()
    log(f"\n  Estados sin división censal: "
        f"{df.loc[no_div, 'property_state'].value_counts().to_dict()}")
    n0 = len(df)
    df = df[~no_div].copy()
    add_flow("Estados con división censal (D3)", len(df), n0 - len(df),
             "Se excluye Puerto Rico (PR): no pertenece a ninguna división censal")

    # ---- 5. D6: variables sin información --------------------------------
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
    log(f"\n  Columnas descartadas (D6): {', '.join(DROP_COLS)}")

    # ---- 6. Columnas nuevas (no se sobrescriben las originales) ----------
    # D1: respuesta truncada para el modelo competidor.
    df["lgd_trunc"] = df["lgd"].clip(*LGD_TRUNC_RANGE)
    log(f"  lgd_trunc: {int((df['lgd'] < LGD_TRUNC_RANGE[0]).sum()):,} casos llevados a 0, "
        f"{int((df['lgd'] > LGD_TRUNC_RANGE[1]).sum()):,} llevados a 1")

    # D3: agrupación de niveles escasos.
    df["channel_grp"] = df["channel"].map(CHANNEL_MAP)
    df["property_type_grp"] = df["property_type"].map(PROPERTY_TYPE_MAP)
    df["n_units_grp"] = df["n_units"].map(N_UNITS_MAP)

    # D4: partición temporal. Comparar texto AAAAMM funciona porque tiene
    # siempre 6 dígitos (el orden alfabético coincide con el cronológico).
    df["split"] = np.where(df["zero_balance_effective_date"] <= TRAIN_LAST_MONTH, "train", "valid")
    n_train = int((df["split"] == "train").sum())
    n_valid = int((df["split"] == "valid").sum())
    add_flow(f"  Entrenamiento (liquidación <= {TRAIN_LAST_MONTH}) (D4)", n_train, None,
             "Liquidaciones más antiguas")
    add_flow(f"  Validación (liquidación > {TRAIN_LAST_MONTH}) (D4)", n_valid, None,
             "Liquidaciones más recientes")

    # ---- Resumen de la base final ----------------------------------------
    log("\n" + "-" * 70)
    log("Partición temporal:")
    for s in ["train", "valid"]:
        months = df.loc[df["split"] == s, "zero_balance_effective_date"]
        log(f"  {s:<6} {(df['split'] == s).sum():>6,}  ({100 * (df['split'] == s).mean():5.1f} %)  "
            f"meses {months.min()} a {months.max()}")

    log("\nNiveles de los factores por tramo:")
    for c in ["channel_grp", "property_type_grp", "n_units_grp", "division",
              "occupancy_status", "loan_purpose", "first_time_homebuyer", "n_borrowers"]:
        tab = pd.crosstab(df[c], df["split"])
        log(f"\n  {c}")
        log("    " + tab.to_string().replace("\n", "\n    "))

    log("\nLGD por tramo   [lgd original | lgd_trunc]")
    summary = df.groupby("split")[["lgd", "lgd_trunc"]].describe().T.round(4)
    log(summary.to_string())

    # ---- 7. Verificaciones -----------------------------------------------
    log("\n" + "-" * 70)
    log("Verificaciones:")
    check(df["loan_id"].is_unique, "un crédito por fila (loan_id único)")
    check(df[CANDIDATE_PREDICTORS].notna().all().all(), "sin NaN en los predictores candidatos")
    for c in ["division", "channel_grp", "property_type_grp", "n_units_grp"]:
        check(df[c].notna().all(), f"'{c}' sin niveles sin asignar")
    train_months = set(df.loc[df["split"] == "train", "zero_balance_effective_date"])
    valid_months = set(df.loc[df["split"] == "valid", "zero_balance_effective_date"])
    check(not (train_months & valid_months), "ningún mes de liquidación está en ambos tramos")
    check(max(train_months) < min(valid_months), "todo el entrenamiento es anterior a la validación")
    check(np.allclose(df["lgd"], lgd_original.loc[df["loan_id"]].values),
          "'lgd' sin cambios respecto de lgd_2007.csv")
    check(df["lgd_trunc"].between(*LGD_TRUNC_RANGE).all(), "'lgd_trunc' dentro de [0, 1]")
    check(df["zero_balance_code"].isin(["02", "03", "09", "15"]).all(),
          "zero_balance_code conserva el formato '02', '03', '09', '15'")
    check(not any(c in df.columns for c in DROP_COLS), "variables de D6 descartadas")

    # ---- Guardar resultados ----------------------------------------------
    OUT_DATA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DATA, index=False)
    log(f"\nBase guardada: {OUT_DATA.relative_to(ROOT).as_posix()}  "
        f"({len(df):,} filas, {df.shape[1]} columnas)")

    OUT_FLOW.parent.mkdir(parents=True, exist_ok=True)
    # Int64 = entero que admite vacíos (sin él, 45516 se guardaría como 45516.0).
    pd.DataFrame(flow).astype({"excluidos": "Int64"}).to_csv(OUT_FLOW, index=False)
    log(f"Flujo muestral: {OUT_FLOW.relative_to(ROOT).as_posix()}")

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Reporte guardado: {OUT_REPORT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
