# Reporte de rol — Rol 2: Análisis exploratorio (Hito 2)

Responsable: **Diego Olivares** · Código: `src/eda.py` · Figuras: `outputs/figures/eda_*` · Tablas: `outputs/tables/eda_*`

## Hallazgos por paso (borradores para el párrafo del informe)

### Paso 1 — Distribución de la LGD

Fuentes: `outputs/figures/eda_01_hist_lgd.png`, `outputs/tables/eda_01_lgd_rangos.csv`, `outputs/tables/eda_01_lgd_resumen.csv`.

> La LGD de la base de modelamiento (n = 3.956) tiene una distribución con cola hacia la derecha: la media (0,541)
> supera a la mediana (0,522) y el coeficiente de asimetría es 0,55. La mitad central de los créditos tiene una LGD
> entre 0,31 y 0,75; el 1,9 % presenta LGD negativa y el 8,3 %, mayor que 1. Al comparar los tramos, la validación
> tiene un centro similar al del entrenamiento (mediana 0,543 frente a 0,518), pero es más dispersa (desviación
> estándar 0,402 frente a 0,301; RIC 0,550 frente a 0,414), más asimétrica (0,73 frente a 0,33) y con una mayor
> proporción de LGD sobre 1 (14,9 % frente a 6,6 %). Por ello, se espera que el error de predicción del modelo sea
> mayor en la muestra de validación que en la de entrenamiento, en especial el RMSE, que pondera más los casos extremos.

### Paso 2 — Descriptivos y dispersión

Fuentes: `outputs/figures/eda_02_dispersion_numericas.png`, `outputs/tables/eda_02_descriptivos_numericos.csv`,
`outputs/tables/eda_02_frecuencias_factores.csv`.

> En los gráficos de dispersión, la tendencia suavizada de la LGD (LOWESS, calculada con entrenamiento) cambia más a
> lo largo del monto original, la tasa de interés, el LTV y el CLTV. En particular, la LGD disminuye a medida que
> aumenta el monto original. El seguro hipotecario vale 0 en el 66,3 % de los créditos, por lo que no admite una
> transformación logarítmica directa. Además, la composición regional difiere entre tramos: Middle Atlantic
> representa el 3,4 % del entrenamiento y el 20,0 % de la validación, mientras que Mountain pasa de 16,3 % a 5,6 %.

### Paso 3 — LGD por factor

Fuentes: `outputs/figures/eda_03_boxplots_factores.png`, `outputs/tables/eda_03_lgd_por_factor.csv`
(medianas de entrenamiento, salvo donde se comparan tramos).

> En los factores, las mayores diferencias en la LGD mediana se observan según la ocupación (0,495 en vivienda
> principal frente a 0,745 en inversión), el propósito del crédito (0,391 en compra frente a 0,618 en
> refinanciamiento con retiro de efectivo) y el número de unidades (0,512 en una unidad frente a 0,761 en dos a
> cuatro). Los créditos de primera vivienda tienen una LGD mediana menor que el resto (0,395 frente a 0,536).
> Algunos niveles tienen pocos casos —casas prefabricadas (49 en entrenamiento) y viviendas de dos a cuatro unidades
> (69)—, por lo que sus efectos se estimarán con menor precisión. Por último, la LGD de algunas regiones cambia
> bastante entre tramos: en West South Central la mediana sube de 0,259 a 0,471, y en Pacific baja de 0,470 a 0,313.

### Paso 4 — Correlaciones y atípicos (entrenamiento)

Fuentes: `outputs/figures/eda_04_correlaciones.png`, `outputs/tables/eda_04_correlaciones_pearson.csv`,
`outputs/tables/eda_04_atipicos.csv`, `outputs/tables/eda_04_lgd_extremos.csv`.

> En entrenamiento, las correlaciones lineales de la LGD con los predictores numéricos son débiles a moderadas; las
> mayores en valor absoluto corresponden al seguro hipotecario (r = −0,33) y al monto original (r = −0,31). Entre
> predictores, el LTV está fuertemente correlacionado con el CLTV (r = 0,85) y con el seguro hipotecario (r = 0,77),
> lo que anticipa un problema de multicolinealidad que se revisará con el VIF. Según la regla del boxplot, 21 créditos
> (0,7 %) tienen una LGD atípica; los más altos (entre 1,53 y 2,41) corresponden a créditos de montos bajos (entre 24
> y 84 mil USD), en línea con lo observado en los gráficos de dispersión. Como son pérdidas reales con cierres
> normales, se mantienen en la base, y su influencia se evaluará en el diagnóstico del modelo.

## Uso de IA

| Herramienta | Propósito | Parte del trabajo | Verificación |
|---|---|---|---|
| Claude Code | Programación | `src/eda.py` (gráficos y tablas) | Revisión de los gráficos y cifras generadas |
| Claude Code | Aclaración de conceptos | Cómo leer media/mediana, asimetría, RIC y su relación con el error de validación | — |
| Claude Code | Redacción | Párrafo del paso 1, redactado a partir de las respuestas de Diego a un cuestionario; la IA avisó cuando una respuesta (pregunta 4) no calzaba con los datos y Diego la corrigió | Cifras contrastadas con `eda_01_*.csv` |
| Claude Code | Redacción | Párrafo del paso 2, con el mismo método (cuestionario); la IA avisó en las preguntas 2 y 3, que Diego corrigió | Cifras contrastadas con `eda_02_*.csv` |
| Claude Code | Redacción | Párrafo del paso 3, con el mismo método; la IA avisó que en la pregunta 1 faltaba el número de unidades y Diego decidió incluirlo | Cifras contrastadas con `eda_03_lgd_por_factor.csv` |
| Claude Code | Redacción | Párrafo del paso 4, con el mismo método (las 4 respuestas calzaron con los datos); la decisión de mantener los atípicos es de Diego | Cifras contrastadas con `eda_04_*.csv` |
