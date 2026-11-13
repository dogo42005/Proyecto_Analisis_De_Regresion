# Acta de decisiones del grupo

Registro de las decisiones metodológicas del proyecto: qué se decidió, cuándo y qué implica para cada rol.
Las cifras de limpieza están en `cleaning_log.md`; aquí solo se registra la decisión.

**Uso de IA:** las opciones de cada decisión (con sus ventajas y desventajas) las propuso Claude Code;
la elección la hizo el grupo. Esto debe quedar en la declaración de uso de IA.

---

## Reunión del 13-11-2026 (Hito 2)

Decide: Diego Olivares (Rol 2), en representación del grupo.

| # | Tema | Decisión | Por qué |
|---|---|---|---|
| A | Variable respuesta | **`lgd` original**, sin truncar. El error de validación (RMSE, MAE) se mide **contra `lgd`** en todos los modelos. | Los valores fuera de [0, 1] son pérdidas reales (la fórmula de la guía calza en el 100 %). `lgd_trunc` queda en la base, pero no se usa en el Hito 2. |
| B | Modelos del Hito 2 | **Dos OLS anidados**: completo vs. reducido, misma respuesta y mismos casos de entrenamiento. Se comparan con prueba F, AIC y BIC. | Cumple desde ya el requisito de modelos competidores con criterios formales. |
| C | Transformaciones | **Rol 2 evalúa log / Box-Cox de los predictores** en el EDA. La respuesta no se transforma en el Hito 2. | La LGD tiene valores ≤ 0 (77 en la base de modelamiento), así que no admite log ni Box-Cox directo. Se retoma para el póster. |
| D | Datos para el EDA | **Se describe toda la base** (mostrando entrenamiento y validación por separado), pero **las decisiones** (transformar, agrupar, atípicos) **se toman mirando solo entrenamiento**. | La validación debe ser una prueba independiente del modelo. |
| E | Faltantes de DTI y puntaje (D5) | **Casos completos** (−83). El Rol 2 compara la LGD de los 81 sin DTI con la del resto; se reporta como limitación. | Los 81 probablemente son deudores con DTI > 65 % (no son faltantes al azar). Para el póster se puede revisar una variable indicadora según lo que muestre la comparación. |
| F1 | Estados (D3) | Ratificado: 9 divisiones censales; se excluye Puerto Rico (−4). | `cleaning_log.md` §6 |
| F2 | Factores escasos (D3) | Ratificado: `channel_grp` R / TPO; CP → CO; `n_units_grp` 1 / 2-4. | `cleaning_log.md` §8 |
| F3 | Partición 80/20 (D4) | Ratificado: entrenamiento ≤ 2014-12 (3.153); validación ≥ 2015-01 (803). | `cleaning_log.md` §9 |
| F4 | Variables sin información (D6) | Ratificado: se descartan `vantage_score_4`, `property_valuation_method`, `amortization_type`, `eltv`. | `cleaning_log.md` §5 |
| F5 | Predictores candidatos | Ratificado: la lista de `CANDIDATE_PREDICTORS`, incluidos `first_time_homebuyer` y `n_borrowers` (no estaban en la propuesta del Hito 1). | No eliminan ningún caso (0 NaN en la base de LGD). |
| D1 / D7 | LGD fuera de [0, 1] / liquidaciones recientes | Ratificado: no se excluye ningún caso fuera de [0, 1]; D7 excluye 0 casos. | `cleaning_log.md` §3 y §4 |
| G | LGD atípicas (regla del boxplot, entrenamiento) | **Se mantienen** los 21 créditos (0,7 %). El Rol 3 evalúa su influencia (Cook, apalancamiento) en el diagnóstico. Decidido por Diego (Rol 2) en el EDA. | Son pérdidas reales con cierres normales y calzan con la fórmula de la guía; coherente con la decisión A. `outputs/tables/eda_04_atipicos.csv` |

### Qué implica para cada rol

**Rol 2 (EDA)**, sobre `data/processed/lgd_2007_model.csv` (columna `split`):
- Histograma de `lgd`, marcando los casos < 0 y > 1.
- Descriptivos; dispersión (o matriz de dispersión) de `lgd` contra los predictores numéricos; boxplots de `lgd` por factor.
- Correlaciones entre predictores y datos atípicos (decidir con entrenamiento).
- Evaluar log / Box-Cox de los predictores positivos. Ojo: `mi_pct` tiene muchos ceros y no admite log directo.
- Comparar la LGD de los 81 créditos sin DTI con la del resto, usando `data/processed/lgd_2007.csv` (4.043 créditos).
- Entrega: Figura 1 y un párrafo.

**Rol 3 (modelos)**, ajustando **solo con entrenamiento** (`split == "train"`):
- Respuesta `lgd`. Modelo completo y reducido (anidados), con las transformaciones que proponga el Rol 2.
- `n_borrowers` se trata como factor (viene como 1.0 / 2.0).
- Prueba F, AIC y BIC.
- Diagnóstico: residuos vs. ajustados, QQ-plot, residuos vs. fecha de liquidación, VIF (GVIF para factores con varios niveles), apalancamiento y distancia de Cook.
- Validación: RMSE y MAE contra `lgd` en `split == "valid"`.
- Entrega: tabla de modelos, Figura 2 y un párrafo.

**Rol 4 (integración)**:
- Introducción, frecuencia y periodo, conclusiones breves.
- Juntar todo en 2 páginas con nombres y cita de la fuente; revisar cada cifra contra `outputs/`.
- Llevar el registro de uso de IA para la declaración del Hito 3.

### Pendientes

- Formato del informe: **Overleaf** (decidido 13-11). Esqueleto en `informe/avance/main.tex`.
- Avance para el Rol 4: Diego (Rol 2) dejó en `main.tex` un borrador de la introducción, los datos y la
  frecuencia y periodo, redactado a partir de la propuesta del Hito 1. Falta la motivación (1–2 líneas),
  que debe escribir el grupo. El Rol 4 lo revisa y lo termina.
- Regla de trabajo propuesta: todos usan los CSV versionados del repo. No volver a correr `build_dataset.py` con un crudo distinto
  al de la entrega a 202606 (con el crudo a 202603 cambian 5 valores de LGD; ver `cleaning_log.md` §0).
- Revisar la sección "Uso de IA" del reporte del Rol 1 y la regla de IA de `CLAUDE.md` contra el enunciado
  (el enunciado no permite usar IA para generar el análisis estadístico).
