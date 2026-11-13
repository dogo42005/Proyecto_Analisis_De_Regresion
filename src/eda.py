"""
eda.py
======
Análisis exploratorio (Rol 2) de la base de modelamiento de LGD.

Se construye paso a paso; cada paso es una función que guarda sus gráficos en
outputs/figures/ y sus tablas en outputs/tables/. Este script SOLO calcula y
grafica: la interpretación y las decisiones las toma el grupo.

Pasos implementados:
  1. Distribución de la LGD (histograma por tramo) y conteo por rangos.
  2. Descriptivos de los predictores (numéricos y factores) y dispersión de la
     LGD contra cada predictor numérico.
  3. LGD por nivel de cada factor (boxplots por tramo).
  4. Correlaciones entre la LGD y los predictores numéricos, y datos atípicos
     (solo entrenamiento).

Decisiones del grupo que aplica (informe/decisiones.md, 13-11-2026):
  - Se describe toda la base, separando entrenamiento y validación (columna 'split').
  - La respuesta es 'lgd' original (sin truncar).

Uso (desde la raíz del repositorio):
    python src/eda.py
"""

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")  # genera archivos sin abrir ventanas
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
IN_MODEL = ROOT / "data" / "processed" / "lgd_2007_model.csv"
FIG_DIR = ROOT / "outputs" / "figures"
TAB_DIR = ROOT / "outputs" / "tables"

# ---------------------------------------------------------------------------
# Estilo de los gráficos (igual en todos los pasos)
# ---------------------------------------------------------------------------
# Colores: entrenamiento azul, validación naranja (paleta categórica de
# referencia, apta para daltonismo). El color siempre sigue al tramo.
COLORS = {"train": "#2a78d6", "valid": "#eb6834"}
LABELS = {"train": "Entrenamiento (liquidación hasta 2014-12)",
          "valid": "Validación (liquidación desde 2015-01)"}
INK = "#0b0b0b"         # texto principal
INK_2 = "#52514e"       # texto secundario y ejes
GRID = "#e4e3df"        # grilla tenue

plt.rcParams.update({
    "font.size": 9,
    "axes.edgecolor": INK_2,
    "axes.labelcolor": INK,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
})

# ---------------------------------------------------------------------------
# Variables (predictores candidatos ratificados, con su nombre para gráficos)
# ---------------------------------------------------------------------------
NUM_PREDICTORS = {
    "credit_score": "Puntaje de crédito",
    "ltv": "LTV (%)",
    "cltv": "CLTV (%)",
    "dti": "DTI (%)",
    "mi_pct": "Seguro hipotecario (% cobertura)",
    "orig_upb": "Monto original (miles de USD)",
    "orig_interest_rate": "Tasa de interés (%)",
}
# Factores: se usan las versiones agrupadas por el Rol 1 (*_grp, division).
FACTORS = {
    "occupancy_status": "Ocupación",
    "loan_purpose": "Propósito",
    "property_type_grp": "Tipo de propiedad",
    "channel_grp": "Canal",
    "first_time_homebuyer": "Primera vivienda",
    "n_units_grp": "N.º de unidades",
    "n_borrowers": "N.º de deudores",
    "division": "División censal",
}

# Columnas numéricas del CSV; todo lo demás se lee como texto (así códigos
# como '02' conservan el cero inicial).
NUMERIC_COLS = ["lgd"] + list(NUM_PREDICTORS)


def load_model_data():
    """Lee la base de modelamiento (3.956 créditos)."""
    df = pd.read_csv(IN_MODEL, dtype=str)
    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c])
    # El monto se expresa en miles de USD para que los ejes sean legibles.
    df["orig_upb"] = df["orig_upb"] / 1000
    # n_borrowers viene como '1.0' / '2.0': se deja como texto '1' / '2' (factor).
    df["n_borrowers"] = df["n_borrowers"].str.replace(".0", "", regex=False)
    return df


def coma_decimal(ax, ejes="xy"):
    """Muestra los números de los ejes indicados con coma decimal (formato en
    español). En ejes con etiquetas de texto (p. ej. niveles de un factor) no
    se debe aplicar, porque reemplazaría las etiquetas por números."""
    fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
    if "x" in ejes:
        ax.xaxis.set_major_formatter(fmt)
    if "y" in ejes:
        ax.yaxis.set_major_formatter(fmt)


def save(fig, name):
    """Guarda la figura en PNG (para revisar) y PDF (para el informe en LaTeX)."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}")
    plt.close(fig)
    print(f"  figura: outputs/figures/{name}.png / .pdf")


# ---------------------------------------------------------------------------
# Paso 1: distribución de la LGD
# ---------------------------------------------------------------------------
def paso1_distribucion_lgd(df):
    """Histograma de la LGD por tramo y tabla de conteos por rango.

    Se usan dos paneles (uno por tramo) con el mismo eje x, porque los tramos
    tienen tamaños muy distintos (3.153 vs. 803) y superponerlos en conteos
    haría ver chico al de validación. Las líneas en 0 y 1 marcan los límites
    del rango [0, 1]; los casos fuera de él se cuentan en cada panel.
    """
    print("\nPaso 1: distribución de la LGD")

    # --- Tabla: conteo por rango y tramo ---------------------------------
    rangos = {
        "LGD < 0": lambda x: x < 0,
        "LGD = 0": lambda x: x == 0,
        "0 < LGD < 1": lambda x: (x > 0) & (x < 1),
        "LGD = 1": lambda x: x == 1,
        "LGD > 1": lambda x: x > 1,
    }
    filas = []
    for nombre, regla in rangos.items():
        fila = {"rango": nombre}
        for s in ["train", "valid"]:
            x = df.loc[df["split"] == s, "lgd"]
            fila[f"n_{s}"] = int(regla(x).sum())
            fila[f"pct_{s}"] = round(100 * regla(x).mean(), 1)
        x = df["lgd"]
        fila["n_total"] = int(regla(x).sum())
        fila["pct_total"] = round(100 * regla(x).mean(), 1)
        filas.append(fila)
    tabla = pd.DataFrame(filas)
    TAB_DIR.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(TAB_DIR / "eda_01_lgd_rangos.csv", index=False)
    print(tabla.to_string(index=False))
    print("  tabla: outputs/tables/eda_01_lgd_rangos.csv")

    # --- Tabla: resumen numérico de la LGD por tramo ---------------------
    # Media vs. mediana y asimetría sirven para describir la forma;
    # desviación estándar y rango intercuartílico (RIC), la dispersión.
    def resumen(x):
        q = x.quantile([0.05, 0.25, 0.50, 0.75, 0.95])
        return pd.Series({
            "n": len(x), "media": x.mean(), "mediana": q[0.50],
            "desv_est": x.std(), "q05": q[0.05], "q25": q[0.25], "q75": q[0.75],
            "q95": q[0.95], "RIC": q[0.75] - q[0.25], "min": x.min(), "max": x.max(),
            "asimetria": x.skew(),
        })
    res = pd.DataFrame({s: resumen(df.loc[df["split"] == s, "lgd"]) for s in ["train", "valid"]})
    res["total"] = resumen(df["lgd"])
    res = res.round(3)
    res.to_csv(TAB_DIR / "eda_01_lgd_resumen.csv")
    print("\n" + res.to_string())
    print("  tabla: outputs/tables/eda_01_lgd_resumen.csv")

    # --- Gráfico ---------------------------------------------------------
    # Bins de ancho 0,05 que caen exactamente en 0 y 1 (así los cortes del
    # rango [0, 1] coinciden con bordes de barra).
    bins = np.arange(-1.10, 2.75 + 0.05, 0.05)
    fig, axes = plt.subplots(2, 1, figsize=(7, 4.6), sharex=True)
    for ax, s in zip(axes, ["train", "valid"]):
        x = df.loc[df["split"] == s, "lgd"]
        ax.hist(x, bins=bins, color=COLORS[s], edgecolor="white", linewidth=0.5)
        # Límites del rango [0, 1]
        for v in (0, 1):
            ax.axvline(v, color=INK_2, linestyle="--", linewidth=0.9)
        n_neg, n_gt1 = int((x < 0).sum()), int((x > 1).sum())
        ax.set_title(f"{LABELS[s]}  ·  n = {len(x):,}".replace(",", "."),
                     loc="left", color=INK)
        ax.set_ylabel("Créditos")
        # Conteos fuera de [0, 1], escritos junto a cada límite
        ytop = ax.get_ylim()[1]
        ax.text(-0.03, ytop * 0.9, f"< 0: {n_neg}", ha="right", va="top", color=INK_2)
        ax.text(1.03, ytop * 0.9, f"> 1: {n_gt1}", ha="left", va="top", color=INK_2)
        coma_decimal(ax)
    axes[-1].set_xlabel("LGD = pérdida / saldo adeudado al cierre")
    axes[-1].set_xlim(bins[0], bins[-1])
    fig.tight_layout()
    save(fig, "eda_01_hist_lgd")


# ---------------------------------------------------------------------------
# Paso 2: descriptivos de los predictores y dispersión de la LGD
# ---------------------------------------------------------------------------
def paso2_descriptivos_y_dispersion(df):
    """Tablas de descriptivos (numéricos y factores) por tramo, y gráficos de
    dispersión de la LGD contra cada predictor numérico.

    La curva negra es un suavizado LOWESS calculado SOLO con entrenamiento
    (decisión D): muestra la tendencia promedio de la LGD a lo largo del eje x
    sin suponer una forma lineal. Sirve para ver si la relación parece lineal
    o curva (insumo para evaluar transformaciones en el paso 5).
    """
    from statsmodels.nonparametric.smoothers_lowess import lowess

    print("\nPaso 2: descriptivos y dispersión")

    # --- Tabla: descriptivos de los predictores numéricos -----------------
    filas = []
    for c, nombre in NUM_PREDICTORS.items():
        for s in ["train", "valid", "total"]:
            x = df[c] if s == "total" else df.loc[df["split"] == s, c]
            filas.append({
                "variable": c, "tramo": s, "n": len(x), "faltantes": int(x.isna().sum()),
                "media": x.mean(), "desv_est": x.std(), "min": x.min(),
                "q25": x.quantile(0.25), "mediana": x.median(), "q75": x.quantile(0.75),
                "max": x.max(), "asimetria": x.skew(), "pct_ceros": 100 * (x == 0).mean(),
            })
    num = pd.DataFrame(filas).round(3)
    num.to_csv(TAB_DIR / "eda_02_descriptivos_numericos.csv", index=False)
    print(num[num["tramo"] == "total"].drop(columns="tramo").to_string(index=False))
    print("  tabla: outputs/tables/eda_02_descriptivos_numericos.csv")

    # --- Tabla: frecuencias de los factores --------------------------------
    filas = []
    for c in FACTORS:
        tab = pd.crosstab(df[c], df["split"])
        tab["total"] = tab.sum(axis=1)
        for nivel, fila in tab.iterrows():
            filas.append({"factor": c, "nivel": nivel,
                          **{f"n_{s}": int(fila[s]) for s in ["train", "valid", "total"]},
                          "pct_total": round(100 * fila["total"] / len(df), 1)})
    fac = pd.DataFrame(filas)
    fac.to_csv(TAB_DIR / "eda_02_frecuencias_factores.csv", index=False)
    print("\n" + fac.to_string(index=False))
    print("  tabla: outputs/tables/eda_02_frecuencias_factores.csv")

    # --- Gráfico: LGD vs. cada predictor numérico (small multiples) --------
    fig, axes = plt.subplots(2, 4, figsize=(10, 5.2), sharey=True)
    axes = axes.ravel()
    train = df[df["split"] == "train"]
    for ax, (c, nombre) in zip(axes, NUM_PREDICTORS.items()):
        # Puntos: validación primero (queda debajo), luego entrenamiento.
        for s, alpha in [("valid", 0.35), ("train", 0.25)]:
            d = df[df["split"] == s]
            ax.scatter(d[c], d["lgd"], s=4, color=COLORS[s], alpha=alpha,
                       linewidths=0, rasterized=True)
        # Tendencia LOWESS con entrenamiento
        suav = lowess(train["lgd"], train[c], frac=0.3)
        ax.plot(suav[:, 0], suav[:, 1], color=INK, linewidth=2)
        # Referencias del rango [0, 1]
        for v in (0, 1):
            ax.axhline(v, color=INK_2, linestyle="--", linewidth=0.7)
        ax.set_xlabel(nombre)
        ax.grid(axis="x", visible=False)
        coma_decimal(ax)
    for ax in axes[::4]:
        ax.set_ylabel("LGD")
    # El 8.º panel se usa para la leyenda.
    axes[-1].axis("off")
    handles = [
        plt.Line2D([], [], marker="o", linestyle="", color=COLORS["train"], label="Entrenamiento"),
        plt.Line2D([], [], marker="o", linestyle="", color=COLORS["valid"], label="Validación"),
        plt.Line2D([], [], color=INK, linewidth=2, label="Tendencia LOWESS\n(entrenamiento)"),
        plt.Line2D([], [], color=INK_2, linestyle="--", linewidth=0.7, label="LGD = 0 y LGD = 1"),
    ]
    axes[-1].legend(handles=handles, loc="center", frameon=False)
    fig.tight_layout()
    save(fig, "eda_02_dispersion_numericas")


# ---------------------------------------------------------------------------
# Paso 3: LGD por nivel de cada factor
# ---------------------------------------------------------------------------
# Nombre de cada nivel en español (códigos según la General User Guide).
# El orden del diccionario es el orden en que aparecen en el gráfico.
LEVEL_NAMES = {
    "occupancy_status": {"P": "Vivienda principal", "S": "Segunda vivienda", "I": "Inversión"},
    "loan_purpose": {"P": "Compra", "N": "Refinanc. sin retiro", "C": "Refinanc. con retiro"},
    "property_type_grp": {"SF": "Unifamiliar", "PU": "Urbaniz. planificada",
                          "CO": "Condominio/coop.", "MH": "Prefabricada"},
    "channel_grp": {"R": "Directo (retail)", "TPO": "Terceros"},
    "first_time_homebuyer": {"N": "No", "Y": "Sí"},
    "n_units_grp": {"1": "1", "2-4": "2 a 4"},
    "n_borrowers": {"1": "1", "2": "2"},
    "division": {d: d for d in ["New England", "Middle Atlantic", "East North Central",
                                "West North Central", "South Atlantic", "East South Central",
                                "West South Central", "Mountain", "Pacific"]},
}


def paso3_lgd_por_factor(df):
    """Boxplots de la LGD por nivel de cada factor, con una caja por tramo, y
    tabla de resumen (n, media, mediana, desv. est., % LGD > 1) por nivel.

    Cómo leer una caja: la línea interior es la mediana; la caja va del
    percentil 25 al 75 (50 % central); los bigotes llegan hasta 1,5 veces el
    alto de la caja, y los puntos sueltos son valores más extremos.
    """
    print("\nPaso 3: LGD por factor")

    # --- Tabla ------------------------------------------------------------
    filas = []
    for c, niveles in LEVEL_NAMES.items():
        for cod, nombre in niveles.items():
            for s in ["train", "valid", "total"]:
                d = df[df[c] == cod] if s == "total" else df[(df[c] == cod) & (df["split"] == s)]
                x = d["lgd"]
                filas.append({"factor": c, "nivel": cod, "nombre": nombre, "tramo": s,
                              "n": len(x), "media": x.mean(), "mediana": x.median(),
                              "desv_est": x.std(), "pct_lgd_mayor_1": 100 * (x > 1).mean()})
    tab = pd.DataFrame(filas).round(3)
    tab.to_csv(TAB_DIR / "eda_03_lgd_por_factor.csv", index=False)
    print(tab[tab["tramo"] != "total"].pivot_table(
        index=["factor", "nombre"], columns="tramo", values=["n", "mediana"], sort=False).to_string())
    print("  tabla: outputs/tables/eda_03_lgd_por_factor.csv")

    # --- Gráfico ------------------------------------------------------------
    # La división censal (9 niveles) ocupa una columna entera a la derecha.
    fig = plt.figure(figsize=(11, 7.5))
    grid = fig.add_gridspec(4, 3, width_ratios=[1, 1, 1.15])
    paneles = {
        "occupancy_status": grid[0, 0], "loan_purpose": grid[0, 1],
        "property_type_grp": grid[1, 0], "channel_grp": grid[1, 1],
        "first_time_homebuyer": grid[2, 0], "n_units_grp": grid[2, 1],
        "n_borrowers": grid[3, 0], "division": grid[:, 2],
    }
    for c, pos in paneles.items():
        ax = fig.add_subplot(pos)
        niveles = list(LEVEL_NAMES[c])[::-1]          # el primero queda arriba
        for s, desplaz in [("train", 0.19), ("valid", -0.19)]:
            datos = [df.loc[(df[c] == cod) & (df["split"] == s), "lgd"] for cod in niveles]
            ax.boxplot(datos, positions=np.arange(len(niveles)) + desplaz, widths=0.32,
                       orientation="horizontal", patch_artist=True,
                       boxprops=dict(facecolor=COLORS[s], alpha=0.45, edgecolor=COLORS[s]),
                       medianprops=dict(color=INK, linewidth=1.5),
                       whiskerprops=dict(color=COLORS[s]), capprops=dict(color=COLORS[s]),
                       flierprops=dict(marker="o", markersize=2, markerfacecolor=COLORS[s],
                                       markeredgecolor="none", alpha=0.5))
        # Etiqueta de cada nivel con su n total
        etiquetas = [f"{LEVEL_NAMES[c][cod]} (n={int((df[c] == cod).sum()):,})".replace(",", ".")
                     for cod in niveles]
        ax.set_yticks(np.arange(len(niveles)), etiquetas)
        for v in (0, 1):
            ax.axvline(v, color=INK_2, linestyle="--", linewidth=0.7)
        ax.set_title(FACTORS[c], loc="left")
        ax.set_xlim(-1.1, 2.8)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
        coma_decimal(ax, ejes="x")
        ax.set_xlabel("LGD" if pos in (grid[3, 0], grid[:, 2]) else "")
    # Leyenda en el hueco de abajo al centro
    ax_leg = fig.add_subplot(grid[3, 1])
    ax_leg.axis("off")
    handles = [matplotlib.patches.Patch(facecolor=COLORS[s], alpha=0.45, edgecolor=COLORS[s],
                                        label=nombre)
               for s, nombre in [("train", "Entrenamiento"), ("valid", "Validación")]]
    handles.append(plt.Line2D([], [], color=INK, linewidth=1.5, label="Mediana"))
    ax_leg.legend(handles=handles, loc="center", frameon=False)
    fig.tight_layout()
    save(fig, "eda_03_boxplots_factores")


# ---------------------------------------------------------------------------
# Paso 4: correlaciones y datos atípicos (solo entrenamiento)
# ---------------------------------------------------------------------------
# Escala divergente: azul = correlación negativa, gris = cero, rojo = positiva.
DIVERGING = matplotlib.colors.LinearSegmentedColormap.from_list(
    "azul_rojo", ["#1c5cab", "#86b6ef", "#f0efec", "#ef9493", "#b42b2b"])


def paso4_correlaciones_y_atipicos(df):
    """Matriz de correlaciones (Pearson y Spearman) entre la LGD y los
    predictores numéricos, y tabla de datos atípicos por variable.

    Todo se calcula SOLO con entrenamiento (decisión D: las decisiones se
    toman sin mirar la validación).
    - Pearson mide asociación LINEAL; Spearman usa rangos y mide asociación
      monótona (menos sensible a valores extremos).
    - Atípico (regla del boxplot): valor bajo Q1 - 1,5·RIC o sobre Q3 + 1,5·RIC.
    """
    print("\nPaso 4: correlaciones y atípicos (entrenamiento)")
    train = df[df["split"] == "train"]
    cols = ["lgd"] + list(NUM_PREDICTORS)
    nombres = {"lgd": "LGD", **{c: n.split(" (")[0] for c, n in NUM_PREDICTORS.items()}}
    nombres["mi_pct"] = "Seguro hipot."
    nombres["orig_upb"] = "Monto original"
    nombres["orig_interest_rate"] = "Tasa de interés"

    # --- Tablas de correlación -------------------------------------------
    pearson = train[cols].corr(method="pearson").round(3)
    spearman = train[cols].corr(method="spearman").round(3)
    pearson.to_csv(TAB_DIR / "eda_04_correlaciones_pearson.csv")
    spearman.to_csv(TAB_DIR / "eda_04_correlaciones_spearman.csv")
    print("Pearson:\n" + pearson.rename(index=nombres, columns=nombres).to_string())
    # Pares de predictores con |r| >= 0,5 (útil para anticipar colinealidad)
    pares = [(a, b, pearson.loc[a, b]) for i, a in enumerate(cols[1:], 1)
             for b in cols[i + 1:] if abs(pearson.loc[a, b]) >= 0.5]
    print("Pares de predictores con |r| >= 0,5:", pares or "ninguno")
    print("  tablas: outputs/tables/eda_04_correlaciones_{pearson,spearman}.csv")

    # --- Gráfico: mapa de calor de Pearson ----------------------------------
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    m = pearson.values
    im = ax.imshow(m, cmap=DIVERGING, vmin=-1, vmax=1)
    etiquetas = [nombres[c] for c in cols]
    ax.set_xticks(range(len(cols)), etiquetas, rotation=40, ha="right")
    ax.set_yticks(range(len(cols)), etiquetas)
    ax.grid(False)
    for i in range(len(cols)):
        for j in range(len(cols)):
            # Texto blanco sobre celdas oscuras, negro sobre claras
            color = "white" if abs(m[i, j]) >= 0.6 else INK
            valor = round(m[i, j], 2) + 0.0   # + 0.0 evita que aparezca "-0,00"
            ax.text(j, i, f"{valor:.2f}".replace(".", ",").replace("-0,00", "0,00"),
                    ha="center", va="center", fontsize=8, color=color)
    barra = fig.colorbar(im, ax=ax, shrink=0.8)
    barra.set_label("Correlación de Pearson")
    barra.ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    n_train = f"{len(train):,}".replace(",", ".")
    ax.set_title(f"Correlaciones, entrenamiento (n = {n_train})", loc="left")
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    save(fig, "eda_04_correlaciones")

    # --- Tabla: atípicos por variable (regla del boxplot) --------------------
    filas = []
    for c in cols:
        x = train[c]
        q1, q3 = x.quantile(0.25), x.quantile(0.75)
        ric = q3 - q1
        lim_inf, lim_sup = q1 - 1.5 * ric, q3 + 1.5 * ric
        filas.append({"variable": c, "q1": q1, "q3": q3, "lim_inf": lim_inf, "lim_sup": lim_sup,
                      "n_bajo": int((x < lim_inf).sum()), "n_sobre": int((x > lim_sup).sum()),
                      "pct_atipicos": 100 * ((x < lim_inf) | (x > lim_sup)).mean(),
                      "min": x.min(), "max": x.max()})
    atip = pd.DataFrame(filas).round(3)
    atip.to_csv(TAB_DIR / "eda_04_atipicos.csv", index=False)
    print("\n" + atip.to_string(index=False))
    print("  tabla: outputs/tables/eda_04_atipicos.csv")

    # --- Tabla: los créditos con LGD más extrema (para revisarlos uno a uno) -
    extremos = pd.concat([train.nsmallest(5, "lgd"), train.nlargest(5, "lgd")])
    extremos = extremos[["loan_id", "lgd", "zero_balance_code", "zero_balance_effective_date",
                         "orig_upb", "ltv", "credit_score", "property_state"]]
    extremos.to_csv(TAB_DIR / "eda_04_lgd_extremos.csv", index=False)
    print("\nLGD más extremas (5 menores y 5 mayores):\n" + extremos.to_string(index=False))
    print("  tabla: outputs/tables/eda_04_lgd_extremos.csv")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    df = load_model_data()
    print(f"Base: {IN_MODEL.relative_to(ROOT).as_posix()} ({len(df):,} créditos)")
    TAB_DIR.mkdir(parents=True, exist_ok=True)
    paso1_distribucion_lgd(df)
    paso2_descriptivos_y_dispersion(df)
    paso3_lgd_por_factor(df)
    paso4_correlaciones_y_atipicos(df)


if __name__ == "__main__":
    main()
