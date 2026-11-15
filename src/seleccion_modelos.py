"""Búsqueda de todos los subconjuntos de predictores (best subset) para la LGD.

Uso:  python src/seleccion_modelos.py

Solo con entrenamiento (split == "train"). Respeta las decisiones del grupo:
  - Respuesta: lgd original (decisión A)
  - Monto en log (H); resto de numéricos en escala original (I)
  - Seguro como bloque: indicadora (mi_pct > 0) + mi_pct (J); siempre entran juntos
  - LTV en vez de CLTV (K)
  - Cada factor entra o sale completo (todos sus niveles juntos)

Salidas (outputs/tables/):
  - sel_01_todos_los_modelos.csv: un modelo por fila con p, R² ajustado, AIC y BIC
  - sel_02_top_aic_bic.csv: los 10 mejores por AIC y los 10 mejores por BIC
  - sel_03_aporte_por_variable.csv: prueba F de sacar cada bloque del modelo con todos

OJO: elegir el "mejor" entre miles de modelos infla la significancia; las pruebas F
entre modelos elegidos así son optimistas. Esta búsqueda orienta, no reemplaza el
argumento estadístico y del problema.
"""
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
IN_MODEL = ROOT / "data" / "processed" / "lgd_2007_model.csv"
TAB_DIR = ROOT / "outputs" / "tables"

# Nivel base de cada factor (el más frecuente o el más "neutro")
FACTORES = {
    "loan_purpose": "P",              # compra
    "occupancy_status": "P",          # vivienda principal
    "division": "South Atlantic",     # la más grande
    "n_units_grp": "1",
    "first_time_homebuyer": "N",
    "n_borrowers": "1",
    "property_type_grp": "SF",        # unifamiliar
    "channel_grp": "R",               # retail
}


def bloques(train):
    """Arma un bloque de columnas de diseño por cada candidato."""
    b = {
        "log_monto": train[["orig_upb"]].apply(np.log).rename(columns={"orig_upb": "log_monto"}),
        "ltv": train[["ltv"]],
        "seguro": pd.DataFrame({"con_seguro": (train["mi_pct"] > 0).astype(float),
                                "mi_pct": train["mi_pct"]}),
        "tasa": train[["orig_interest_rate"]],
        "puntaje": train[["credit_score"]],
        "dti": train[["dti"]],
    }
    for f, base in FACTORES.items():
        x = train[f].astype(str).str.replace(r"\.0$", "", regex=True)
        d = pd.get_dummies(x, prefix=f, dtype=float)
        b[f] = d.drop(columns=f"{f}_{base}")  # el nivel base queda en el intercepto
    return b


def ajuste(y, X):
    """OLS por mínimos cuadrados; devuelve SCE (RSS) y número de coeficientes."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    rss = float(((y - X @ beta) ** 2).sum())
    return rss, X.shape[1]


def metricas(rss, p, n, tss):
    """AIC y BIC con la misma convención que statsmodels (p = n.º de coeficientes)."""
    llf = -n / 2 * (np.log(2 * np.pi * rss / n) + 1)
    return {"p": p, "r2_aj": 1 - (rss / (n - p)) / (tss / (n - 1)),
            "aic": -2 * llf + 2 * p, "bic": -2 * llf + p * np.log(n), "rss": rss}


def main():
    df = pd.read_csv(IN_MODEL)
    train = df[df["split"] == "train"].reset_index(drop=True)
    y = train["lgd"].to_numpy()
    n = len(y)
    tss = float(((y - y.mean()) ** 2).sum())
    b = bloques(train)
    nombres = list(b)
    mats = {k: v.to_numpy() for k, v in b.items()}
    uno = np.ones((n, 1))

    # (a) Todos los subconjuntos (2^14 = 16.384 modelos)
    filas = []
    for k in range(len(nombres) + 1):
        for sub in combinations(nombres, k):
            X = np.hstack([uno] + [mats[s] for s in sub])
            rss, p = ajuste(y, X)
            fila = {"variables": " + ".join(sub) if sub else "(solo intercepto)", "n_var": k}
            fila.update(metricas(rss, p, n, tss))
            filas.append(fila)
    todos = pd.DataFrame(filas)
    todos["delta_aic"] = todos["aic"] - todos["aic"].min()
    todos["delta_bic"] = todos["bic"] - todos["bic"].min()
    todos = todos.sort_values("aic").round(4)
    TAB_DIR.mkdir(parents=True, exist_ok=True)
    todos.to_csv(TAB_DIR / "sel_01_todos_los_modelos.csv", index=False)

    top = pd.concat([todos.nsmallest(10, "aic").assign(criterio="AIC"),
                     todos.nsmallest(10, "bic").assign(criterio="BIC")])
    top.to_csv(TAB_DIR / "sel_02_top_aic_bic.csv", index=False)
    print(f"Modelos ajustados: {len(todos):,} (n = {n:,})".replace(",", "."))
    for crit in ["aic", "bic"]:
        print(f"\nTop 5 por {crit.upper()}:")
        print(todos.nsmallest(5, crit)[["variables", "p", "r2_aj", "aic", "bic"]].to_string(index=False))

    # (b) Aporte de cada bloque: prueba F de sacarlo del modelo con todos
    X_full = np.hstack([uno] + [mats[s] for s in nombres])
    rss_f, p_f = ajuste(y, X_full)
    aporte = []
    for s in nombres:
        X_r = np.hstack([uno] + [mats[o] for o in nombres if o != s])
        rss_r, p_r = ajuste(y, X_r)
        q = p_f - p_r  # parámetros que se sacan
        F = ((rss_r - rss_f) / q) / (rss_f / (n - p_f))
        m_r = metricas(rss_r, p_r, n, tss)
        m_f = metricas(rss_f, p_f, n, tss)
        aporte.append({"bloque": s, "parametros": q, "F": F, "p_valor": stats.f.sf(F, q, n - p_f),
                       "delta_aic_al_sacar": m_r["aic"] - m_f["aic"],
                       "delta_bic_al_sacar": m_r["bic"] - m_f["bic"]})
    aporte = pd.DataFrame(aporte).sort_values("F", ascending=False).round(4)
    aporte.to_csv(TAB_DIR / "sel_03_aporte_por_variable.csv", index=False)
    print("\nAporte de cada bloque (sacarlo del modelo con todos):")
    print(aporte.to_string(index=False))
    print("\n(delta > 0 al sacar = el modelo empeora sin ese bloque)")


if __name__ == "__main__":
    main()
