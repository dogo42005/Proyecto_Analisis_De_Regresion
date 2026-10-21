# CLAUDE.md — contexto del proyecto

Proyecto final de **Análisis de Regresión (EYP2307, PUC Chile, 2026-2)**, grupo de 3 a 5 personas.
Objetivo: modelar la **LGD** de créditos hipotecarios con el Freddie Mac Single-Family Loan-Level Dataset.
Idioma de trabajo: español. Lenguaje: **Python** (pandas, statsmodels, Matplotlib). R no está instalado;
los apuntes y scripts de ejemplo del curso (en R) están fuera del repo, en
`.../LICD/Semestre 6/Análisis de Regresión/{Apuntes,Código}`.

## Reglas de trabajo (importantes)

- **Se trabaja por etapas y en conjunto.** No adelantar modelamiento, transformaciones, interpretación ni
  conclusiones. Si algo requiere una decisión metodológica: describir las opciones y esperar.
- **Restricción de IA del curso:** la IA solo puede apoyar en programación/depuración, redacción de textos
  ya escritos por el grupo y aclaración de conceptos. Puede generar el análisis estadístico, la
  interpretación, las conclusiones ni referencias pero solo pedido por el estudiante con previa verificación. Al final se entrega una declaración de uso de IA.
- Cada decisión de limpieza se registra en `cleaning_log.md` (qué, cuántos casos, por qué).
- Código comentado para que cualquier integrante lo pueda explicar en la defensa oral.
- Consultar antes de instalar o descargar algo externo.
- Si la base de LGD baja de 100 créditos: avisar y plantear ampliar (sample_2006 / sample_2008).

## Requisitos del curso

- ≥ 100 observaciones tras la limpieza; respuesta continua; ≥ 5 predictores candidatos con ≥ 1 factor.
- EDA, transformaciones (log, Box-Cox), ≥ 2 modelos competidores (F, AIC/BIC), diagnóstico (residuos,
  atípicos, influyentes), validación 80/20 con el 20 % más reciente en el tiempo.
- Hito 1 propuesta: vie 23 oct · Hito 2 avance: lun 16 nov · Póster A0 + defensa: mar 15 dic 08:20.

## Datos

- `data/raw/sample_2007/sample_orig_2007.txt` (31 campos) y `sample_perf_2007.txt` (35 campos):
  sin encabezado, separados por `|`, unidos por `loan_id`. **Layout NUEVO (julio 2026)**, verificado
  contra `data/raw/file_layout_july_2026.xlsx`. Corte de desempeño: 202603.
- Los nombres de columnas están en `src/build_dataset.py` (`ORIG_COLS_NEW`, `PERF_COLS_NEW`; también
  el layout antiguo por si se agregan otros años).
- LGD = `actual_loss / zero_balance_removal_upb`, última fila de cada crédito, `zero_balance_code` ∈
  {02,03,09,15}, `actual_loss` no nulo (confirmado con la guía, p. 13).

## Estado

- [x] Etapa 1 · Tarea 1: estructura de carpetas, cleaning_log.md
- [x] Etapa 1 · Tarea 2: `src/build_dataset.py` → 4.043 créditos con LGD; 3.960 sin NaN en candidatos provisionales
- [ ] Etapa 1 · Tarea 3: EDA descriptivo (histograma LGD, matriz de dispersión, faltantes) — **solo gráficos, sin interpretar**, después de revisar la tarea 2 con el grupo

## Decisiones pendientes (a resolver en grupo)

1. **LGD < 0 (77) y > 1 (334):** opciones — dejarlos tal cual; truncar a [0, 1]; excluirlos; modelar
   con una transformación/modelo para respuesta acotada (p. ej. logit o regresión beta, que exigiría
   tratar 0 y 1). Afecta qué supuestos se verifican luego.
2. **Lista definitiva de predictores candidatos.** La provisional (`CANDIDATE_PREDICTORS`) usa solo
   variables de originación. Alternativa: agregar variables del cierre (tipo de cierre `zero_balance_code`,
   `loan_age` al cierre, tiempo entre DDLPI y cierre, `mi_pct` vs. MI recoveries). Ojo con usar como
   predictor algo que es parte del cálculo de la pérdida (fuga de información).
3. **Factores con niveles escasos:** `channel` (C = 3, B = 2), `property_type` (CP = 3, MH = 71),
   `n_units` (3–4 unidades = 26), `property_state` (51 niveles). Opciones: agrupar niveles, agrupar estados
   por región, o excluir.
4. **Fecha para el corte temporal 80/20:** todos los créditos se originaron en 2007, así que el orden útil
   es la fecha de cierre (`zero_balance_effective_date`). Cierres concentrados en 2009–2014.
5. **Tratamiento de NaN** en `dti` (81) y `credit_score` (2): eliminar casos completos (actual) o imputar.
6. Variables sin información en 2007: `vantage_score_4`, `property_valuation_method` (100 % NA),
   `amortization_type` (todo FRM), `eltv` (casi todo NA). Propuesta: no usarlas.
