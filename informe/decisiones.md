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

---

## Decisiones del 14-11-2026 (Hito 2)

Contexto: Diego Olivares (Rol 2) no puede seguir trabajando. **Amelie Ramírez** (Rol 3) asume también el Rol 2.
Las decisiones de la reunión del 13-11 (tomadas por Diego en representación del grupo) se enviaron al grupo para
su ratificación; **pendiente de confirmar** que nadie está en desacuerdo.

Decide: Amelie Ramírez (Rol 2 y Rol 3).

| # | Tema | Decisión | Por qué |
|---|---|---|---|
| H | Transformación del monto original (`orig_upb`) | **Se usa log(monto original)** en el modelo. | Evaluado solo con entrenamiento (Paso 5 del EDA). Box-Cox (λ = 0,35; IC 95 % 0,29–0,41) deja el monto más simétrico, pero la simetría de un predictor no es un requisito del modelo lineal. En linealidad con la LGD (criterio principal), el log rinde igual o mejor: la tendencia LOWESS es la más recta y r = −0,36 (log) vs. −0,35 (Box-Cox) y −0,31 (original). Además lo respalda la regla del logaritmo (máx/mín = 21,8) y su coeficiente se interpreta como efecto de cambios porcentuales del monto. Fuentes: `outputs/figures/eda_05_*.png`, `outputs/tables/eda_05_transformaciones.csv`. |
| I | Transformación del resto de los predictores numéricos | **Se mantienen en escala original** `dti`, `ltv`, `cltv`, `credit_score` y `orig_interest_rate`. | Evaluado solo con entrenamiento (Paso 5). DTI: único con razón máx/mín > 10 (21,7), pero λ de Box-Cox cercano a 1 (1,20), el log aumenta su asimetría (−0,21 → −1,78) y r con la LGD no cambia (−0,10). LTV y CLTV: asimetría negativa y λ > 1 (2,22 y 2,85); con Box-Cox r sube levemente (−0,22 → −0,26; −0,25 → −0,30), pero la tendencia LOWESS no es monótona (sube hasta LTV 70–80 % y luego baja) y una transformación monótona no puede enderezarla; además la potencia no tiene interpretación clara. Puntaje y tasa: r igual en todas las escalas. Fuentes: `outputs/tables/eda_05_transformaciones.csv`, `outputs/figures/eda_05_transformaciones_ltv_cltv.png`. |
| J | Seguro hipotecario (`mi_pct`, 66 % de ceros) | **Dos términos: indicadora de tener seguro (`mi_pct` > 0) + `mi_pct`.** | No admite log ni Box-Cox por los ceros. En entrenamiento hay salto (LGD mediana 0,578 sin seguro vs. 0,384 con seguro) y pendiente entre asegurados (r = −0,32). Solo la indicadora pierde la cobertura; solo `mi_pct` mezcla salto y pendiente; log(`mi_pct` + c) y tramos dependen de elecciones arbitrarias. Ojo: el seguro existe casi solo con LTV > 80 % (0 de 2.058 con LTV ≤ 80 %; 1.082 de 1.095 con LTV > 80 %) → revisar VIF con LTV. |

### Observaciones para el diagnóstico (Rol 3)

- La variabilidad de la LGD baja a medida que sube el monto (desv. est. 0,35 en el 20 % de montos más bajos vs.
  0,22 en el 20 % más alto). Posible varianza no constante: revisar en los residuos.
- Hay 57 créditos con monto exactamente 417 mil USD (límite de préstamo que podía comprar Freddie Mac en 2007) y solo
  4 por encima; ninguna transformación elimina ese hueco.
- La relación de la LGD con LTV y CLTV no es monótona (forma de loma): una recta la representará mal. Reportar como
  limitación en el Hito 2; para el póster el grupo puede evaluar un término cuadrático. LTV y CLTV tienen r = 0,85.

---

## Decisiones del 15-11-2026 (Hito 2, Rol 3)

Decide: Amelie Ramírez (Rol 3). Todo ajustado solo con entrenamiento (n = 3.153).

| # | Tema | Decisión | Por qué |
|---|---|---|---|
| K | LTV vs. CLTV (r = 0,85) | **Se usa el LTV**; el CLTV queda fuera del modelo. | Relación con la LGD casi igual (r = −0,22 vs. −0,25). El LTV describe la hipoteca sobre la que Freddie Mac registra la pérdida (el CLTV suma segundos créditos de otros acreedores). Como el seguro se exige según el LTV (> 80 %), incluirlo permite leer el efecto del seguro a igual LTV. Se acepta el costo de más colinealidad con el seguro (r = 0,77), que se evalúa con el VIF. Alternativa descartada: LTV + (CLTV − LTV), por complicar el modelo sin ganancia clara. |
| L | Modelos del Hito 2 | **Completo:** 14 bloques (log monto, LTV, seguro [indicadora + `mi_pct`], tasa, puntaje, DTI, propósito, ocupación, división, unidades, primer comprador, n.º de deudores, tipo de propiedad, canal). **Reducido:** el completo sin DTI ni primer comprador. **Se prefiere el reducido.** | Búsqueda de todos los subconjuntos (16.384 modelos, `src/seleccion_modelos.py`): el reducido es el único entre los 3 mejores por AIC y por BIC. Prueba F reducido vs. completo: F = 2,13 (2 y 3.126 gl), p = 0,12. Como el reducido se eligió tras la búsqueda, el p puede estar sesgado; en validación ambos predicen igual (RMSE 0,3586 vs. 0,3587; MAE 0,2780 vs. 0,2778). DTI: además, relación débil y limitación del código 999. Fuentes: `outputs/tables/sel_0*.csv`. |

Nota para el grupo (póster): si el DTI sale del modelo, los 81 créditos sin DTI podrían volver a la base. Para el Hito 2 no se
toca la base (la prueba F exige los mismos créditos en ambos modelos).
