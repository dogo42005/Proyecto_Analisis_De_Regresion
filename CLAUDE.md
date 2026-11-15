# CLAUDE.md — contexto del proyecto

Proyecto final de **Análisis de Regresión (EYP2307, PUC Chile, 2026-2)**, grupo de 3 a 5 personas.
Objetivo: modelar la **LGD** de créditos hipotecarios con el Freddie Mac Single-Family Loan-Level Dataset.
Idioma de trabajo: español. Lenguaje: **Python** (pandas, statsmodels, Matplotlib). R no está instalado;
los apuntes y scripts de ejemplo del curso (en R) están fuera del repo, en
`.../LICD/Semestre 6/Análisis de Regresión/{Apuntes,Código}`.

## Reglas de trabajo (importantes)

- **Se trabaja por etapas y en conjunto.** No adelantar modelamiento, transformaciones, interpretación ni
  conclusiones. Si algo requiere una decisión metodológica: describir las opciones y esperar.
- **Restricción de IA del curso (enunciado, sección "Uso de Inteligencia Artificial"):** el uso de IA es
  RESTRINGIDO. Se permite solo como apoyo en programación y depuración de código elaborado por el grupo,
  mejora de la redacción de textos previamente escritos por el grupo, o aclaración de conceptos o métodos.
  **No está permitido** usar IA para generar el análisis estadístico, la interpretación de resultados, las
  conclusiones, ni referencias no verificadas. Con el póster se entrega la declaración "Uso de Inteligencia
  Artificial" (máx. 1 página: herramienta, propósito, parte del trabajo y verificaciones realizadas).
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

## Estado (15-11-2026)

- [x] Hito 1 entregado (`entregas/hito1/`).
- [x] Rol 1 (datos, Joaquín): `build_dataset.py` + `prepare_model_data.py` → `data/processed/lgd_2007_model.csv`
  (3.956 créditos; 3.153 entrenamiento / 803 validación). Revisado y verificado.
- [x] Rol 2 (EDA, Diego pasos 1–4 y Amelie pasos 5–6): `src/eda.py` (pasos 1–6 y Figura 1). Párrafos en
  `informe/reportes_roles/rol2_eda.md`.
- [x] Rol 3 (modelos, Amelie): `src/seleccion_modelos.py` (16.384 subconjuntos) y `src/modelos.py` (Tabla 2,
  diagnóstico, validación, Figura 2, tablas `mod_01` a `mod_11`). Reporte en `informe/reportes_roles/rol3_modelos.md`.
  Revisado el 15-11: todo se reproduce.
- [ ] **Rol 4 (Enzo): integración del avance en `informe/avance/main.tex`** — entrega lun 16 nov.
  - Secciones listas para pegar: `seccion2_rol1.tex` (párrafo de limpieza, **borrador por revisar por
    Joaquín**), `seccion3_rol2.tex` (Figura 1 + párrafo, **por aprobar por Diego y Amelie**),
    `seccion4_rol3.tex` (Tabla 2, Figura 2 y párrafo).
  - Falta: motivación, conclusiones y ajustar a **2 páginas**. Prueba del 15-11: integrado todo y con textos
    de largo realista sale en 3 páginas, porque la Figura 1 no cabe al final de la página 1 y deja un
    hueco; hay que subirla, achicarla o acortar texto.
- [ ] Grupo: confirmar las decisiones del 13-11 y las H–L (el acta dice "pendiente de confirmar").
- [ ] Joaquín: revisar la sección "Uso de IA" de `rol1_datos.md` contra el enunciado.
- Método de trabajo con IA: Claude programa y explica conceptos; la persona del rol interpreta (cuestionario
  o preguntas guía); Claude avisa si algo no calza con los datos y redacta con sus respuestas.
- Los CSV versionados salieron de la entrega de Freddie Mac a 202606 con corte 202603. El crudo local
  de este PC es la entrega a 202603: si se vuelve a correr `build_dataset.py` aquí, cambian 5 valores de LGD.

## Decisiones tomadas (13-11-2026, detalle en `informe/decisiones.md`)

- Respuesta: `lgd` original (sin truncar); RMSE/MAE de validación contra `lgd`.
- Hito 2: dos OLS anidados (completo vs. reducido) con prueba F, AIC y BIC, ajustados solo con entrenamiento.
- Transformaciones: Rol 2 evalúa log/Box-Cox de predictores; la respuesta no se transforma en el Hito 2.
- EDA: describe toda la base; las decisiones se toman mirando solo entrenamiento.
- Faltantes: casos completos (−83), con comparación de la LGD de los 81 sin DTI como limitación.
- Ratificado lo del Rol 1: divisiones censales sin PR, agrupaciones de factores, corte ≤ 2014-12,
  variables descartadas (D6) y la lista `CANDIDATE_PREDICTORS`.
- G: se mantienen las 21 LGD atípicas. H: log(monto). I: resto en escala original. J: seguro = indicadora
  + `mi_pct`. K: LTV (no CLTV). L: completo (14 bloques) vs. reducido (sin DTI ni primer comprador); se
  prefiere el reducido.
