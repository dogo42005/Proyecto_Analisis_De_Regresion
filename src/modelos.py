"""Modelos del Hito 2: OLS completo y reducido, diagnóstico y validación.

Uso:  python src/modelos.py

Decisiones aplicadas (informe/decisiones.md): A (lgd original), H (log monto), I (resto en
escala original), J (seguro = indicadora + mi_pct), K (LTV, no CLTV), L (completo con 14
bloques; reducido sin DTI ni primer comprador). Ajuste solo con entrenamiento.

Salidas:
  outputs/tables/mod_01_comparacion.csv     Tabla 2 (parámetros, R² aj., AIC, BIC, RMSE, MAE, F)
  outputs/tables/mod_02_coeficientes.csv    coeficientes del reducido (estimación, EE, t, p)
  outputs/tables/mod_03_vif.csv             VIF / GVIF por bloque del reducido
  outputs/tables/mod_04_influyentes.csv     créditos con mayor distancia de Cook
  outputs/tables/mod_05_resumen_influencia.csv  umbrales y conteos de apalancamiento, Cook y residuos
  outputs/tables/mod_06_sensibilidad_atipicos.csv  coeficientes con y sin las 21 LGD atípicas
  outputs/tables/mod_07_pruebas_supuestos.csv  Breusch-Pagan, Jarque-Bera, asimetría y curtosis
  outputs/tables/mod_08_errores.csv         RMSE/MAE en entrenamiento, validación y modelo nulo
  outputs/tables/mod_09_error_por_anio.csv  error medio por año de liquidación (ambos tramos)
  outputs/tables/mod_10_errores_robustos_hc3.csv  p-valores clásicos vs. robustos (HC3)
  outputs/tables/mod_11_varianza_residuos.csv  desv. est. de los residuos por quintil de ajustado
  outputs/figures/figura2.(png|pdf)         paneles de diagnóstico (+ copia en informe/avance/figuras)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.nonparametric.smoothers_lowess import lowess

ROOT = Path(__file__).resolve().parents[1]
IN_MODEL = ROOT / "data" / "processed" / "lgd_2007_model.csv"
TAB_DIR = ROOT / "outputs" / "tables"
FIG_DIR = ROOT / "outputs" / "figures"

COLORS = {"train": "#2a78d6", "valid": "#eb6834"}
INK, INK_2 = "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 9.5, "axes.titleweight": "bold"})

# Bloques del modelo: nombre -> término de la fórmula (factores con su nivel base)
BLOQUES = {
    "log_monto": "np.log(orig_upb)",
    "ltv": "ltv",
    "seguro": "con_seguro + mi_pct",
    "tasa": "orig_interest_rate",
    "puntaje": "credit_score",
    "dti": "dti",
    "propósito": "C(loan_purpose, Treatment('P'))",
    "ocupación": "C(occupancy_status, Treatment('P'))",
    "división": "C(division, Treatment('South Atlantic'))",
    "unidades": "C(n_units_grp, Treatment('1'))",
    "primer_comprador": "C(first_time_homebuyer, Treatment('N'))",
    "n_deudores": "C(n_borrowers, Treatment('1'))",
    "tipo_propiedad": "C(property_type_grp, Treatment('SF'))",
    "canal": "C(channel_grp, Treatment('R'))",
}
FUERA_REDUCIDO = ["dti", "primer_comprador"]


def coma(v, dec=2):
    return f"{v:.{dec}f}".replace(".", ",")


def coma_ejes(ax, ejes="xy"):
    fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
    if "x" in ejes:
        ax.xaxis.set_major_formatter(fmt)
    if "y" in ejes:
        ax.yaxis.set_major_formatter(fmt)


def cargar():
    df = pd.read_csv(IN_MODEL, dtype={"n_units_grp": str})
    df["con_seguro"] = (df["mi_pct"] > 0).astype(int)
    df["n_borrowers"] = df["n_borrowers"].astype(int).astype(str)
    fecha = df["zero_balance_effective_date"].astype(int).astype(str)
    df["fecha_liq"] = pd.to_datetime(fecha, format="%Y%m")
    return df


def formula(bloques):
    return "lgd ~ " + " + ".join(BLOQUES[b] for b in bloques)


def gvif(modelo, bloques):
    """VIF generalizado por bloque (Fox y Monette): det(R11)·det(R22)/det(R).
    Para comparar bloques con distinto n.º de columnas se usa GVIF^(1/(2·gl))."""
    X = pd.DataFrame(modelo.model.exog, columns=modelo.model.exog_names).drop(columns="Intercept")
    R = np.corrcoef(X.to_numpy(), rowvar=False)
    det_R = np.linalg.det(R)
    filas = []
    for b in bloques:
        terms = BLOQUES[b].split(" + ")
        idx = [i for i, c in enumerate(X.columns) if any(c.startswith(t) for t in terms)]
        resto = [i for i in range(X.shape[1]) if i not in idx]
        g = np.linalg.det(R[np.ix_(idx, idx)]) * np.linalg.det(R[np.ix_(resto, resto)]) / det_R
        filas.append({"bloque": b, "gl": len(idx), "GVIF": g, "GVIF_ajustado": g ** (1 / (2 * len(idx))),
                      "equivalente_VIF": (g ** (1 / (2 * len(idx)))) ** 2})
    return pd.DataFrame(filas)


def main():
    df = cargar()
    train, valid = df[df["split"] == "train"].copy(), df[df["split"] == "valid"].copy()
    completo_b = list(BLOQUES)
    reducido_b = [b for b in completo_b if b not in FUERA_REDUCIDO]
    m_c = smf.ols(formula(completo_b), data=train).fit()
    m_r = smf.ols(formula(reducido_b), data=train).fit()

    # --- Tabla 2: comparación ------------------------------------------------
    F, p_F, _ = m_c.compare_f_test(m_r)
    filas = []
    for nom, m in [("Completo", m_c), ("Reducido", m_r)]:
        e = valid["lgd"] - m.predict(valid)
        filas.append({"modelo": nom, "parametros": int(m.df_model + 1), "r2": m.rsquared,
                      "r2_ajustado": m.rsquared_adj, "aic": m.aic, "bic": m.bic,
                      "F_global": m.fvalue, "p_F_global": m.f_pvalue,
                      "rmse_valid": np.sqrt((e ** 2).mean()), "mae_valid": e.abs().mean()})
    tab = pd.DataFrame(filas)
    tab["F_reducido_vs_completo"] = [np.nan, F]
    tab["p_F_reducido_vs_completo"] = [np.nan, p_F]
    TAB_DIR.mkdir(parents=True, exist_ok=True)
    tab.round(4).to_csv(TAB_DIR / "mod_01_comparacion.csv", index=False)
    print("Tabla 2:\n", tab.round(4).to_string(index=False))

    # --- Coeficientes del reducido -------------------------------------------
    coef = pd.DataFrame({"estimacion": m_r.params, "ee": m_r.bse, "t": m_r.tvalues, "p": m_r.pvalues})
    coef.round(5).to_csv(TAB_DIR / "mod_02_coeficientes.csv")

    # --- VIF / GVIF ----------------------------------------------------------
    vif = gvif(m_r, reducido_b).round(3)
    vif.to_csv(TAB_DIR / "mod_03_vif.csv", index=False)
    print("\nGVIF (reducido):\n", vif.to_string(index=False))

    # --- Influencia: apalancamiento, residuos estudentizados, Cook ------------
    inf = m_r.get_influence()
    train["h"] = inf.hat_matrix_diag
    train["r_est"] = inf.resid_studentized_external
    train["cook"] = inf.cooks_distance[0]
    n, p = len(train), int(m_r.df_model + 1)
    q1, q3 = train["lgd"].quantile([0.25, 0.75])
    train["atipico_lgd"] = (train["lgd"] < q1 - 1.5 * (q3 - q1)) | (train["lgd"] > q3 + 1.5 * (q3 - q1))
    umbral_h, umbral_cook = 2 * p / n, 4 / n
    top = train.nlargest(15, "cook")[["loan_id", "lgd", "orig_upb", "ltv", "mi_pct", "h", "r_est", "cook", "atipico_lgd"]]
    top.round(4).to_csv(TAB_DIR / "mod_04_influyentes.csv", index=False)
    resumen_inf = {
        "n": n, "p": p, "umbral_h_2p/n": umbral_h, "n_h_alto": int((train["h"] > umbral_h).sum()),
        "umbral_cook_4/n": umbral_cook, "n_cook_alto": int((train["cook"] > umbral_cook).sum()),
        "cook_max": train["cook"].max(), "n_cook_mayor_1": int((train["cook"] > 1).sum()),
        "n_abs_r_est_mayor_3": int((train["r_est"].abs() > 3).sum()),
        "atipicos_lgd": int(train["atipico_lgd"].sum()),
        "atipicos_lgd_con_cook_alto": int((train["atipico_lgd"] & (train["cook"] > umbral_cook)).sum()),
    }
    pd.Series(resumen_inf).to_csv(TAB_DIR / "mod_05_resumen_influencia.csv", header=["valor"])
    print("\nInfluencia:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in resumen_inf.items()})

    # Sensibilidad: ¿cambian los coeficientes al sacar los 21 atípicos de LGD?
    m_sin = smf.ols(formula(reducido_b), data=train[~train["atipico_lgd"]]).fit()
    sens = pd.DataFrame({"con_atipicos": m_r.params, "sin_atipicos": m_sin.params})
    sens["cambio_relativo_%"] = 100 * (sens["sin_atipicos"] - sens["con_atipicos"]) / sens["con_atipicos"].abs()
    sens.round(4).to_csv(TAB_DIR / "mod_06_sensibilidad_atipicos.csv")

    # Pruebas formales de apoyo
    from statsmodels.stats.diagnostic import het_breuschpagan
    bp_stat, bp_p, _, _ = het_breuschpagan(m_r.resid, m_r.model.exog)
    jb = stats.jarque_bera(m_r.resid)
    pd.Series({"breusch_pagan_LM": bp_stat, "breusch_pagan_p": bp_p, "jarque_bera": jb.statistic,
               "jarque_bera_p": jb.pvalue, "asimetria_resid": stats.skew(m_r.resid),
               "curtosis_exceso_resid": stats.kurtosis(m_r.resid)}).round(5).to_csv(
        TAB_DIR / "mod_07_pruebas_supuestos.csv", header=["valor"])

    # --- Errores del reducido: entrenamiento, validación y modelo nulo --------
    # Error = observado − predicho (positivo = el modelo subestima la LGD).
    # Modelo nulo: predecir siempre la LGD promedio de entrenamiento.
    e_tr = train["lgd"] - m_r.fittedvalues
    e_va = valid["lgd"] - m_r.predict(valid)
    e_nulo = valid["lgd"] - train["lgd"].mean()

    def resumen_error(e):
        return {"n": len(e), "rmse": np.sqrt((e ** 2).mean()), "mae": e.abs().mean(),
                "error_medio": e.mean()}

    err = pd.DataFrame({"entrenamiento": resumen_error(e_tr), "validacion": resumen_error(e_va),
                        "nulo_en_validacion": resumen_error(e_nulo)}).T
    # R² fuera de muestra: 1 − MSE del modelo / MSE del modelo nulo, en validación
    err["r2_fuera_de_muestra"] = np.nan
    err.loc["validacion", "r2_fuera_de_muestra"] = 1 - (e_va ** 2).mean() / (e_nulo ** 2).mean()
    err.round(4).to_csv(TAB_DIR / "mod_08_errores.csv")
    print("\nErrores (reducido):\n", err.round(4).to_string())

    # Error medio por año de liquidación, en ambos tramos
    por_anio = []
    for tramo, d, e in [("entrenamiento", train, e_tr), ("validacion", valid, e_va)]:
        t = (pd.DataFrame({"anio": d["fecha_liq"].dt.year, "e": e}).groupby("anio")["e"]
             .agg(n="size", error_medio="mean", rmse=lambda x: np.sqrt((x ** 2).mean()))
             .reset_index())
        t.insert(0, "tramo", tramo)
        por_anio.append(t)
    pd.concat(por_anio).round(4).to_csv(TAB_DIR / "mod_09_error_por_anio.csv", index=False)

    # Errores estándar robustos (HC3): ¿algún coeficiente cambia de significancia al 5 %?
    m_hc3 = smf.ols(formula(reducido_b), data=train).fit(cov_type="HC3")
    hc3 = pd.DataFrame({"estimacion": m_r.params, "ee_clasico": m_r.bse, "p_clasico": m_r.pvalues,
                        "ee_hc3": m_hc3.bse, "p_hc3": m_hc3.pvalues})
    hc3["cambia_significancia_5pct"] = (hc3["p_clasico"] < 0.05) != (hc3["p_hc3"] < 0.05)
    hc3.round(5).to_csv(TAB_DIR / "mod_10_errores_robustos_hc3.csv")
    print("Coeficientes que cambian de significancia con HC3:",
          int(hc3["cambia_significancia_5pct"].sum()))

    # Varianza de los residuos según el valor ajustado (apoyo a Breusch-Pagan)
    quintil = pd.qcut(m_r.fittedvalues, 5, labels=[1, 2, 3, 4, 5])
    var_res = (pd.DataFrame({"quintil_ajustado": quintil, "residuo": m_r.resid})
               .groupby("quintil_ajustado", observed=True)["residuo"]
               .agg(n="size", desv_est="std").reset_index())
    var_res.round(4).to_csv(TAB_DIR / "mod_11_varianza_residuos.csv", index=False)

    # --- Figura 2: diagnóstico del reducido ------------------------------------
    fig, axes = plt.subplots(1, 4, figsize=(11, 2.9))
    ajust, res = m_r.fittedvalues, m_r.resid

    ax = axes[0]  # (a) residuos vs ajustados
    ax.scatter(ajust, res, s=3, color=COLORS["train"], alpha=0.25, linewidths=0, rasterized=True)
    s = lowess(res, ajust, frac=0.3)
    ax.plot(s[:, 0], s[:, 1], color=INK, linewidth=1.8)
    ax.axhline(0, color=INK_2, linestyle="--", linewidth=0.7)
    ax.set_xlabel("Valores ajustados")
    ax.set_ylabel("Residuos")
    ax.set_title("(a) Residuos vs. ajustados", loc="left")
    coma_ejes(ax)

    ax = axes[1]  # (b) QQ-plot de residuos estudentizados
    (osm, osr), (pend, inter, _) = stats.probplot(train["r_est"], dist="norm")
    ax.scatter(osm, osr, s=3, color=COLORS["train"], alpha=0.4, linewidths=0, rasterized=True)
    ax.plot(osm, pend * osm + inter, color=INK, linewidth=1.2)
    ax.set_xlabel("Cuantiles teóricos N(0, 1)")
    ax.set_ylabel("Residuos estudentizados")
    ax.set_title("(b) QQ-plot", loc="left")
    coma_ejes(ax)

    ax = axes[2]  # (c) residuos vs fecha de liquidación
    ax.scatter(train["fecha_liq"], res, s=3, color=COLORS["train"], alpha=0.25, linewidths=0, rasterized=True)
    x_num = matplotlib.dates.date2num(train["fecha_liq"])
    s = lowess(res, x_num, frac=0.3)
    ax.plot(matplotlib.dates.num2date(s[:, 0]), s[:, 1], color=INK, linewidth=1.8)
    ax.axhline(0, color=INK_2, linestyle="--", linewidth=0.7)
    ax.xaxis.set_major_locator(matplotlib.dates.YearLocator(2))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
    ax.set_xlabel("Fecha de liquidación")
    ax.set_title("(c) Residuos en el tiempo", loc="left")
    coma_ejes(ax, "y")

    ax = axes[3]  # (d) apalancamiento vs residuo estudentizado, tamaño = Cook
    tam = 3 + 150 * train["cook"] / train["cook"].max()  # tamaño proporcional a Cook
    ax.scatter(train["h"], train["r_est"], s=tam, color=COLORS["train"], alpha=0.35, linewidths=0, rasterized=True)
    ax.scatter(train.loc[train["atipico_lgd"], "h"], train.loc[train["atipico_lgd"], "r_est"], s=14,
               facecolors="none", edgecolors=INK, linewidths=0.7, label="LGD atípica (21)")
    ax.axvline(umbral_h, color=INK_2, linestyle="--", linewidth=0.7)
    for y0 in (-3, 3):
        ax.axhline(y0, color=INK_2, linestyle=":", linewidth=0.7)
    ax.set_xlabel("Apalancamiento (h)")
    ax.set_ylabel("Residuo estudentizado")
    ax.set_title("(d) Influencia", loc="left")
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    coma_ejes(ax)

    fig.tight_layout(w_pad=1.2)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"figura2.{ext}", dpi=150)
    dest = ROOT / "informe" / "avance" / "figuras"
    dest.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest / "figura2.pdf", bbox_inches="tight")
    plt.close(fig)
    print("\nFigura 2: outputs/figures/figura2.png / .pdf y informe/avance/figuras/figura2.pdf")


if __name__ == "__main__":
    main()
