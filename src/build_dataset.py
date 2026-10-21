"""
build_dataset.py
================
Construye la base de análisis de LGD (Loss Given Default) a partir del
Single-Family Loan-Level Dataset de Freddie Mac (muestra 2007).

Qué hace, en orden:
  0. Detecta el layout de columnas contando los campos de la primera línea
     de cada archivo (31/35 = layout nuevo jul-2026; 32/32 = layout antiguo).
  1. Carga el archivo de originación (1 fila por crédito).
  2. Carga el archivo de desempeño mensual por bloques (es grande: ~3 millones
     de filas) y se queda con la ÚLTIMA fila de cada crédito (la del cierre).
  3. Une ambas tablas por loan_id.
  4. Recodifica los códigos "no disponible" (9999, 999, 99, 9, ...) a NaN.
  5. Filtra cierres con pérdida (zero_balance_code en {02, 03, 09, 15}) y
     actual_loss no nulo, y calcula LGD = actual_loss / zero_balance_removal_upb.
  6. Reporta los conteos (a)-(f) pedidos y guarda:
       - data/processed/lgd_2007.csv      (base con LGD, SIN eliminar NaN)
       - outputs/build_dataset_report.txt (el mismo reporte que se imprime)

NO hace: truncar/excluir LGD fuera de [0, 1], elegir transformaciones,
ni separar entrenamiento/validación. Eso se decide en grupo más adelante.

Uso (desde la raíz del repositorio):
    python src/build_dataset.py
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Rutas (relativas a la raíz del repo, para que funcione en cualquier PC)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "sample_2007"
ORIG_FILE = RAW_DIR / "sample_orig_2007.txt"
PERF_FILE = RAW_DIR / "sample_perf_2007.txt"
OUT_DATA = ROOT / "data" / "processed" / "lgd_2007.csv"
OUT_REPORT = ROOT / "outputs" / "build_dataset_report.txt"

# Tamaño de bloque al leer el archivo de desempeño. Con 300.000 filas por
# bloque el uso de memoria se mantiene bajo (~1 GB) aunque el archivo pese 350 MB.
CHUNK_SIZE = 300_000

# ---------------------------------------------------------------------------
# Layouts de columnas (los archivos NO traen encabezado)
# Fuente: file_layout_july_2026.xlsx y General User Guide (julio 2026).
# ---------------------------------------------------------------------------
ORIG_COLS_NEW = [
    "credit_score", "first_payment_date", "first_time_homebuyer", "maturity_date",
    "msa", "mi_pct", "n_units", "occupancy_status", "cltv", "dti", "orig_upb",
    "ltv", "orig_interest_rate", "channel", "ppm_flag", "amortization_type",
    "property_state", "property_type", "postal_code", "loan_id", "loan_purpose",
    "orig_loan_term", "n_borrowers", "seller_name", "super_conforming_flag",
    "pre_harp_loan_id", "special_eligibility_program", "harp_indicator",
    "property_valuation_method", "io_indicator", "vantage_score_4",
]  # 31 campos

# Layout antiguo (guía enero 2026): igual hasta la posición 24, luego cambia.
ORIG_COLS_OLD = ORIG_COLS_NEW[:24] + [
    "servicer_name", "super_conforming_flag", "pre_relief_refi_loan_id",
    "special_eligibility_program", "relief_refi_indicator",
    "property_valuation_method", "io_indicator", "mi_cancellation_indicator",
]  # 32 campos

PERF_COLS_NEW = [
    "loan_id", "period", "current_actual_upb", "delinquency_status", "loan_age",
    "remaining_months_to_maturity", "defect_settlement_date", "modification_flag",
    "zero_balance_code", "zero_balance_effective_date", "current_interest_rate",
    "current_non_interest_bearing_upb", "ddlpi", "mi_recoveries",
    "net_sale_proceeds", "non_mi_recoveries", "total_expenses", "legal_costs",
    "maintenance_preservation_costs", "taxes_insurance", "misc_expenses",
    "actual_loss", "cumulative_modification_costs", "interest_rate_step_indicator",
    "payment_deferral_flag", "eltv", "zero_balance_removal_upb",
    "delinquent_accrued_interest", "delinquency_due_to_disaster",
    "borrower_assistance_plan", "current_period_modification_costs",
    "current_interest_bearing_upb", "mi_cancellation_indicator", "servicer_name",
    "bankruptcy_cramdown_costs",
]  # 35 campos

PERF_COLS_OLD = PERF_COLS_NEW[:32]  # 32 campos

# ---------------------------------------------------------------------------
# Definiciones del problema
# ---------------------------------------------------------------------------
# Códigos de cierre para los que Freddie Mac calcula Actual Loss (guía, p. 13):
# 02 = venta a tercero, 03 = short sale / charge off, 09 = venta de REO,
# 15 = venta de cartera (whole loan sale).
LOSS_CODES = ["02", "03", "09", "15"]

# Códigos "no disponible" -> NaN. Origen: indicaciones del grupo + guía de usuario.
# Las variables numéricas se comparan como número; las categóricas como texto.
NA_CODES_NUMERIC = {
    "credit_score": [9999],
    "vantage_score_4": [9999],      # guía p. 9: 9999 = Not Available
    "mi_pct": [999],
    "cltv": [999],
    "dti": [999],
    "ltv": [999],
    "n_units": [99],
    "n_borrowers": [99],
    "property_valuation_method": [7],  # guía p. 9: 7 = Not Available
    "eltv": [999],                  # guía p. 14: 999 = Not Available
}
NA_CODES_CATEGORICAL = {
    "occupancy_status": ["9", "99"],
    "loan_purpose": ["9", "99"],
    "first_time_homebuyer": ["9", "99"],
    "property_type": ["9", "99"],
    "channel": ["9"],               # guía p. 6: 9 = Not Available
}

# Columnas que deben ser numéricas (el resto queda como texto).
ORIG_NUMERIC = [
    "credit_score", "mi_pct", "n_units", "cltv", "dti", "orig_upb", "ltv",
    "orig_interest_rate", "orig_loan_term", "n_borrowers",
    "property_valuation_method", "vantage_score_4",
]
PERF_NUMERIC = [
    "current_actual_upb", "loan_age", "remaining_months_to_maturity",
    "current_interest_rate", "current_non_interest_bearing_upb", "mi_recoveries",
    "net_sale_proceeds", "non_mi_recoveries", "total_expenses", "legal_costs",
    "maintenance_preservation_costs", "taxes_insurance", "misc_expenses",
    "actual_loss", "cumulative_modification_costs", "eltv",
    "zero_balance_removal_upb", "delinquent_accrued_interest",
]

# Predictores candidatos PROVISIONALES (solo información de originación).
# Esta lista se usa únicamente para el conteo (d). La lista definitiva se
# decide en grupo; basta con editarla aquí y volver a correr el script.
CANDIDATE_PREDICTORS = [
    # numéricos
    "credit_score", "ltv", "cltv", "dti", "mi_pct", "orig_upb",
    "orig_interest_rate",
    # factores
    "occupancy_status", "loan_purpose", "property_type", "channel",
    "first_time_homebuyer", "n_units", "n_borrowers", "property_state",
]

# Variables del cierre que conviene conservar en la base procesada
# (para revisar después; NO son predictores decididos).
CLOSING_COLS = [
    "period", "loan_age", "zero_balance_code", "zero_balance_effective_date",
    "defect_settlement_date", "modification_flag", "delinquency_status",
    "current_interest_rate", "eltv", "zero_balance_removal_upb", "net_sale_proceeds",
    "mi_recoveries", "non_mi_recoveries", "total_expenses",
    "delinquent_accrued_interest", "actual_loss", "ddlpi",
]


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
report_lines = []


def log(msg=""):
    """Imprime en pantalla y guarda la línea para el archivo de reporte."""
    print(msg)
    report_lines.append(msg)


def count_fields(path):
    """Cuenta cuántos campos separados por '|' tiene la primera línea."""
    with open(path, encoding="latin-1") as f:
        first_line = f.readline().rstrip("\r\n")
    return len(first_line.split("|"))


def detect_layout():
    """Elige el layout según el número de campos. Si no calza, se detiene."""
    n_orig = count_fields(ORIG_FILE)
    n_perf = count_fields(PERF_FILE)
    log(f"Campos en la 1a línea: originación = {n_orig}, desempeño = {n_perf}")
    if n_orig == 31 and n_perf == 35:
        log("=> Layout NUEVO (julio 2026)")
        return ORIG_COLS_NEW, PERF_COLS_NEW
    if n_orig == 32 and n_perf == 32:
        log("=> Layout ANTIGUO (guía enero 2026)")
        return ORIG_COLS_OLD, PERF_COLS_OLD
    sys.exit(f"ERROR: combinación de campos no reconocida ({n_orig}, {n_perf}). "
             "Revisar el layout antes de seguir.")


def to_month_index(yyyymm):
    """Convierte fechas YYYYMM (texto) a un índice de meses: año*12 + mes.
    Sirve para restar fechas en meses."""
    s = pd.to_numeric(yyyymm, errors="coerce")
    return (s // 100) * 12 + (s % 100)


def load_origination(cols):
    """Lee el archivo de originación. Todo se lee como texto (dtype=str) para
    no perder ceros a la izquierda (p. ej. códigos '02'); luego se convierten
    a número solo las columnas numéricas."""
    df = pd.read_csv(ORIG_FILE, sep="|", header=None, names=cols, dtype=str,
                     encoding="latin-1")
    for c in ORIG_NUMERIC:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_last_performance_row(cols):
    """Lee el archivo de desempeño por bloques y devuelve la última fila
    (mayor 'period') de cada crédito. También cuenta filas y créditos."""
    last_rows = []
    n_rows = 0
    max_period = 0
    reader = pd.read_csv(PERF_FILE, sep="|", header=None, names=cols, dtype=str,
                         encoding="latin-1", chunksize=CHUNK_SIZE)
    for chunk in reader:
        n_rows += len(chunk)
        max_period = max(max_period, int(chunk["period"].max()))
        # Dentro del bloque: ordenar por crédito y período, y quedarse con la
        # última fila de cada crédito. Un crédito puede quedar partido entre
        # dos bloques; eso se resuelve abajo repitiendo la operación.
        chunk = chunk.sort_values(["loan_id", "period"])
        last_rows.append(chunk.drop_duplicates("loan_id", keep="last"))
    last = (pd.concat(last_rows)
            .sort_values(["loan_id", "period"])
            .drop_duplicates("loan_id", keep="last")
            .reset_index(drop=True))
    for c in PERF_NUMERIC:
        if c in last.columns:
            last[c] = pd.to_numeric(last[c], errors="coerce")
    return last, n_rows, max_period


def recode_not_available(df):
    """Reemplaza los códigos 'no disponible' por NaN y devuelve cuántos
    valores cambió en cada variable (para el cleaning_log)."""
    changes = {}
    for col, codes in NA_CODES_NUMERIC.items():
        if col in df.columns:
            mask = df[col].isin(codes)
            changes[col] = int(mask.sum())
            df.loc[mask, col] = np.nan
    for col, codes in NA_CODES_CATEGORICAL.items():
        if col in df.columns:
            mask = df[col].isin(codes)
            changes[col] = int(mask.sum())
            df.loc[mask, col] = np.nan
    return changes


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    # Evita caracteres raros (tildes) al imprimir en la consola de Windows.
    sys.stdout.reconfigure(encoding="utf-8")
    log("=" * 70)
    log("BUILD DATASET - LGD Freddie Mac, muestra 2007")
    log("=" * 70)

    # ---- 0. Layout -------------------------------------------------------
    orig_cols, perf_cols = detect_layout()

    # ---- 1. Originación --------------------------------------------------
    orig = load_origination(orig_cols)
    log(f"\nOriginación: {len(orig):,} filas, {orig['loan_id'].nunique():,} créditos únicos")

    # ---- 2. Desempeño: última fila de cada crédito -----------------------
    last, n_perf_rows, max_period = load_last_performance_row(perf_cols)
    log(f"Desempeño: {n_perf_rows:,} filas mensuales, {len(last):,} créditos")
    log(f"Último período del archivo (corte de desempeño): {max_period}")

    # ---- 3. Unión por loan_id -------------------------------------------
    # 'validate' hace que pandas se detenga si algún loan_id estuviera repetido.
    df = orig.merge(last, on="loan_id", how="inner", validate="one_to_one")
    log(f"Créditos presentes en ambos archivos: {len(df):,}")
    log(f"  sin desempeño: {len(orig) - len(df):,} | sin originación: {len(last) - len(df):,}")

    # ---- 4. Códigos 'no disponible' -> NaN ------------------------------
    changes = recode_not_available(df)
    log("\nRecodificación 'no disponible' -> NaN (sobre todos los créditos unidos):")
    for col, n in changes.items():
        log(f"  {col:<28} {n:>7,}")

    # ---- (a) Total de créditos -------------------------------------------
    log("\n" + "-" * 70)
    log(f"(a) Total de créditos: {len(df):,}")

    log("\nDistribución del zero_balance_code en la última fila:")
    zb_counts = df["zero_balance_code"].fillna("(vacío = activo al corte)").value_counts()
    for code, n in zb_counts.sort_index().items():
        log(f"  {code:<28} {n:>7,}")

    # ---- (b) Cierres con pérdida potencial -------------------------------
    is_loss_code = df["zero_balance_code"].isin(LOSS_CODES)
    closed = df[is_loss_code].copy()
    log(f"\n(b) Créditos con zero_balance_code en {{02,03,09,15}}: {len(closed):,}")

    # ---- (c) actual_loss no nulo ----------------------------------------
    has_loss = closed["actual_loss"].notna()
    log(f"(c) ... y con actual_loss no nulo: {int(has_loss.sum()):,}")

    # Por qué hay actual_loss nulo (reglas de la guía de usuario):
    # "Cierre reciente" = zero_balance_effective_date a menos de 3 meses del
    # último período del archivo (con corte 202603: 202601, 202602 o 202603).
    cutoff_idx = (max_period // 100) * 12 + (max_period % 100)
    closed["recent_close"] = (cutoff_idx - to_month_index(closed["zero_balance_effective_date"])) < 3
    null_loss = closed[~has_loss]
    has_defect = null_loss["defect_settlement_date"].notna()
    recent = null_loss["recent_close"]
    log(f"    actual_loss nulo: {len(null_loss):,}")
    log(f"      con defect_settlement_date:                {int(has_defect.sum()):,}")
    log(f"      cerrados en los 3 meses previos al corte:  {int(recent.sum()):,}")
    log(f"      sin ninguna de las dos explicaciones:      {int((~has_defect & ~recent).sum()):,}")
    log(f"    (en todo (b), cierres en los 3 meses previos al corte: {int(closed['recent_close'].sum()):,})")

    loss = closed[has_loss].copy()

    # Verificación de la fórmula de Actual Loss de la guía (p. 13):
    # actual_loss = removal_upb + net_sale_proceeds + delinquent_accrued_interest
    #               + total_expenses + mi_recoveries + non_mi_recoveries
    # (recuperaciones vienen con signo negativo; gastos con signo positivo).
    components = loss[["zero_balance_removal_upb", "net_sale_proceeds",
                       "delinquent_accrued_interest", "total_expenses",
                       "mi_recoveries", "non_mi_recoveries"]].fillna(0).sum(axis=1)
    ok_formula = (components - loss["actual_loss"]).abs() < 1
    log(f"    Verificación fórmula de la guía (dif. < $1): {int(ok_formula.sum()):,} de {len(loss):,}")

    # ---- Cálculo del LGD -------------------------------------------------
    # LGD = pérdida / saldo expuesto al momento del cierre.
    # Se necesita un denominador positivo para poder dividir.
    bad_den = ~(loss["zero_balance_removal_upb"] > 0)
    log(f"    zero_balance_removal_upb nulo o <= 0 (no se puede calcular LGD): {int(bad_den.sum()):,}")
    loss = loss[~bad_den].copy()
    loss["lgd"] = loss["actual_loss"] / loss["zero_balance_removal_upb"]

    log(f"\nTipo de cierre entre los {len(loss):,} créditos con LGD:")
    for code, n in loss["zero_balance_code"].value_counts().sort_index().items():
        log(f"  {code}  {n:>6,}")

    # ---- (d) NaN en predictores candidatos ------------------------------
    log("\n" + "-" * 70)
    log("(d) NaN por predictor candidato (lista PROVISIONAL) entre los créditos con LGD:")
    for col in CANDIDATE_PREDICTORS:
        n_na = int(loss[col].isna().sum())
        log(f"  {col:<24} {n_na:>6,}  ({100 * n_na / len(loss):5.2f}%)")
    complete = loss[CANDIDATE_PREDICTORS].notna().all(axis=1)
    loss["complete_case"] = complete
    log(f"  => Créditos sin NaN en ningún candidato: {int(complete.sum()):,} de {len(loss):,}")

    # ---- (e) Conteo por tramo de LGD ------------------------------------
    # Se calcula sobre los casos completos (d), que es la base que se modelaría.
    # Entre paréntesis, el mismo conteo sobre todos los créditos con LGD (c).
    log("\n" + "-" * 70)
    log("(e) Conteo de LGD por tramo   [casos completos (d)  |  todos con LGD (c)]")
    lgd_d = loss.loc[complete, "lgd"]
    lgd_c = loss["lgd"]
    bins = [
        ("LGD < 0", lambda x: x < 0),
        ("LGD = 0", lambda x: x == 0),
        ("0 < LGD < 1", lambda x: (x > 0) & (x < 1)),
        ("LGD = 1", lambda x: x == 1),
        ("LGD > 1", lambda x: x > 1),
    ]
    for name, rule in bins:
        log(f"  {name:<14} {int(rule(lgd_d).sum()):>6,}  |  {int(rule(lgd_c).sum()):>6,}")

    # ---- (f) Resumen del LGD --------------------------------------------
    log("\n" + "-" * 70)
    log("(f) Resumen del LGD   [casos completos (d)  |  todos con LGD (c)]")
    probs = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    stats = pd.DataFrame({
        "completos (d)": [lgd_d.count(), lgd_d.mean(), lgd_d.std(), lgd_d.min(),
                          *lgd_d.quantile(probs), lgd_d.max()],
        "todos (c)": [lgd_c.count(), lgd_c.mean(), lgd_c.std(), lgd_c.min(),
                      *lgd_c.quantile(probs), lgd_c.max()],
    }, index=["n", "media", "desv. est.", "mín"] + [f"q{int(p * 100):02d}" for p in probs] + ["máx"])
    stats.loc["mediana"] = [lgd_d.median(), lgd_c.median()]
    log(stats.round(4).to_string())

    # ---- Información útil para decisiones futuras (no se decide nada) ---
    log("\n" + "-" * 70)
    log("Año de cierre (zero_balance_effective_date) entre créditos completos (d):")
    year = loss.loc[complete, "zero_balance_effective_date"].str[:4]
    log(year.value_counts().sort_index().to_string())

    # ---- Guardar resultados ---------------------------------------------
    keep = orig_cols + [c for c in CLOSING_COLS if c not in orig_cols] + ["lgd", "complete_case"]
    keep = [c for c in keep if c in loss.columns]
    OUT_DATA.parent.mkdir(parents=True, exist_ok=True)
    loss[keep].to_csv(OUT_DATA, index=False)
    log(f"\nBase guardada: {OUT_DATA.relative_to(ROOT)}  ({len(loss):,} filas, {len(keep)} columnas)")

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Reporte guardado: {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
