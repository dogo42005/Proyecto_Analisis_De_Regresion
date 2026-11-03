# Reporte de rol — Rol 1: Ingeniero/a de datos y limpieza (Hito 2)

## 1. Responsable y fecha

| Campo | Valor |
|---|---|
| Responsable | **Joaquin Ortuzar** |
| Fecha de este borrador | 02-11-2026 |
| Rama | `rol1-datos` |
| Commits | `888ecb9` — base de modelamiento, corte de desempeño 202603 y documentación de limpieza; el commit de este reporte (borrador) |

---

## 2. Qué se hizo (en orden)

1. **Datos crudos.** Se descomprimió `data/raw/sample_2007.zip` en `data/raw/sample_2007/` (ambos ignorados por
   git). Se verificó que todas las líneas tienen 31 campos (originación, 50.000) y 35 (desempeño, 3.015.985).
2. **Versión de los datos.** El archivo descargado trae desempeño hasta **202606**, mientras que el build original
   se hizo con una entrega hasta 202603. La diferencia (3.924 filas) corresponde exactamente a los meses
   202604–202606.
3. **Reproducción del build.** Se agregó a `build_dataset.py` un corte de desempeño (`PERF_CUTOFF`). Con
   `"202603"`, el archivo nuevo reproduce la misma población que la entrega anterior (50.000 → 4.484 → 4.043 →
   3.960, mismos `loan_id`). Diferencia: Freddie Mac corrigió la pérdida de 5 créditos. Se adoptó la entrega nueva
   con corte fijo en 202603 (decisión del 02-11, ver sección 3).
5. **Regla CLTV < LTV.** Se implementó en `build_dataset.py` (estaba en el log pero no en el código). Resultado:
   0 casos en los 50.000.
6. **Verificaciones en la guía de usuario** (julio 2026): DTI (p. 5), CLTV (p. 5), `channel` (p. 6) y rezago de
   Actual Loss (p. 13). Ver sección 5.
7. **Tabla de divisiones censales.** Se comparó automáticamente el diccionario del script con el PDF oficial del
   U.S. Census Bureau: coincide en las 9 divisiones y los 50 estados + DC.
8. **Base de modelamiento.** Se realizo el script `prepare_model_data.py`: aplica D7, D5, exclusión de PR y D6; crea
   `lgd_trunc`, `division`, `channel_grp`, `property_type_grp`, `n_units_grp` y `split`; ejecuta 12
   verificaciones que detienen el script si algo no calza.
9. **Documentación.** `cleaning_log.md` actualizado: versión de datos (sección 0), verificaciones de la guía
   (secciones 2 y 3) y secciones nuevas 4 a 10 (LGD fuera de rango, D6, divisiones censales, casos completos,
   agrupaciones, partición y flujo muestral).

---

## 3. Decisiones aplicadas

| # | Tema | Opción aplicada | Tipo | 
|---|---|---|---|
| — | Versión de datos | Entrega nueva con corte de desempeño 202603 | Criterio técnico del rol (reproducibilidad) | 
| — | Regla CLTV < LTV | Implementada en el código (0 casos) | Criterio técnico (alinear código y log) |
| D7 | Meses previos al corte | Excluir liquidaciones 2026-01 a 2026-03 (0 casos) | Decisión de grupo |
| D5 | Faltantes `dti` / `credit_score` | Casos completos (−83) | Decisión de grupo |
| D6 | Variables sin información | Descartar `vantage_score_4`, `property_valuation_method`, `amortization_type`, `eltv` | Decisión de grupo |
| D4 | Corte 80/20 | Entrenamiento ≤ 2014-12; validación ≥ 2015-01 | Decisión de grupo |
| D3 | Estados | 9 divisiones censales; excluir PR (−4) | Decisión de grupo | 
| D3 | Factores escasos | `channel` R/TPO; CP → CO; `n_units` 1 / 2-4 | Decisión de grupo | Por ratificar (Reunión 2) |
| D1 | LGD fuera de [0, 1] | Mantener `lgd` y crear `lgd_trunc` | Criterio tecnico del rol

---

## 4. Archivos creados o modificados

| Archivo | Estado | Commit | Contenido |
|---|---|---|---|
| `src/build_dataset.py` | Modificado | `888ecb9` | `PERF_CUTOFF = "202603"`; regla CLTV < LTV |
| `src/prepare_model_data.py` | Nuevo | `888ecb9` | Base de modelamiento y 12 verificaciones |
| `data/processed/lgd_2007.csv` | Regenerado | `888ecb9` | 4.043 filas, 50 columnas (5 pérdidas corregidas) |
| `data/processed/lgd_2007_model.csv` | Nuevo | `888ecb9` | 3.956 filas, 52 columnas |
| `outputs/build_dataset_report.txt` | Regenerado | `888ecb9` | Conteos del build |
| `outputs/prepare_model_data_report.txt` | Nuevo | `888ecb9` | Conteos de la preparación |
| `outputs/tables/flujo_muestral.csv` | Nuevo | `888ecb9` | Tabla de flujo para el informe |
| `cleaning_log.md` | Modificado | `888ecb9` | Secciones 0, 2, 3 y 4–10 |
| `informe/reportes_roles/rol1_datos.md` | Nuevo | este commit | Este reporte |

Columnas nuevas en `lgd_2007_model.csv` (las originales se conservan): `lgd_trunc`, `division`, `channel_grp`,
`property_type_grp`, `n_units_grp`, `split`.

Para reproducir (desde la raíz del repositorio, con los datos crudos en `data/raw/sample_2007/`):

```bash
python src/build_dataset.py        # ~25 s
python src/prepare_model_data.py   # segundos
```

---

## 5. Cifras entregadas y su fuente

### Flujo muestral

| Paso | Quedan | Excluidos | Fuente |
|---|---|---|---|
| Créditos en la muestra 2007 | 50.000 | – | `outputs/build_dataset_report.txt` (a) |
| `zero_balance_code` ∈ {02, 03, 09, 15} | 4.484 | 45.516 | `build_dataset_report.txt` (b) |
| `actual_loss` informado | 4.043 | 441 | `build_dataset_report.txt` (c) |
| Sin liquidaciones en 2026-01 a 2026-03 (D7) | 4.043 | 0 | `outputs/tables/flujo_muestral.csv` |
| Casos completos (D5) | 3.960 | 83 (81 `dti`, 2 `credit_score`) | `flujo_muestral.csv`; `cleaning_log.md` §7 |
| Estados con división censal (sin PR) | 3.956 | 4 | `flujo_muestral.csv`; `cleaning_log.md` §6 |
| Entrenamiento (≤ 2014-12) (Posible) | 3.153 (79,7 %) | – | `prepare_model_data_report.txt` |
| Validación (≥ 2015-01) (Posible) | 803 (20,3 %) | – | `prepare_model_data_report.txt` |

### Otras cifras

| Cifra | Valor | Fuente |
|---|---|---|
| LGD < 0 / > 1 en la base de modelamiento | 76 / 329 | `cleaning_log.md` §4 |
| — en entrenamiento / validación | 57 y 209 / 19 y 120 | `cleaning_log.md` §4 |
| Meses de entrenamiento / validación | 2008-03 a 2014-12 / 2015-01 a 2025-12 | `prepare_model_data_report.txt` |
| LGD media, entrenamiento / validación | 0,5301 / 0,5853 | `prepare_model_data_report.txt` |
| LGD d.e., entrenamiento / validación | 0,3011 / 0,4018 | `prepare_model_data_report.txt` |
| `channel_grp` R / TPO | 1.441 / 2.515 | `cleaning_log.md` §8 |
| `property_type_grp` SF / PU / CO / MH | 2.887 / 569 / 430 / 70 | `cleaning_log.md` §8 |
| `n_units_grp` 1 / 2-4 | 3.841 / 115 | `cleaning_log.md` §8 |
| Pérdidas corregidas por Freddie Mac | 5 créditos (todos en validación) | `cleaning_log.md` §0 |

### Verificaciones en la guía de usuario (julio 2026)

| Punto | Texto de la guía | Resultado |
|---|---|---|
| DTI 999 (p. 5) | "Ratios > 65% will be disclosed as Not Available. All HARP loans … as Not Available." | Los 81 NaN no son HARP → DTI > 65 % o no disponible; **no son faltantes al azar** |
| CLTV (p. 5) | "If the CLTV is < LTV, CLTV will be disclosed as Not Available." | La fuente ya aplica la regla; 0 casos en el código |
| `channel` (p. 6) | R = Retail, B = Broker, C = Correspondent, T = Third Party Origination – Not Specified | B, C y T son terceros; T también incluye canal no disponible |
| Actual Loss (p. 13) | "set to null for loans disposed within the three months prior to the performance cutoff date" | Ventana = mes del corte y los dos anteriores (comprobado con la entrega de junio) |
| Divisiones censales | PDF del U.S. Census Bureau (`us_regdiv.pdf`) | Coincide en 9 divisiones y 50 estados + DC; fuera solo PR |

---

## 6. Qué se integró al informe

| Elemento | Sección del informe |
|---|---|
| Tabla de flujo muestral (≈ 7 filas, desde `flujo_muestral.csv`) | Datos y limpieza | 
| Párrafo de datos y limpieza (5–7 líneas) | Datos y limpieza | 

Elementos que conviene mencionar en el párrafo (datos, no redacción):

- Fuente: Freddie Mac Single-Family Loan-Level Dataset, muestra 2007; unión por *Loan Sequence Number*.
- Corte de desempeño 202603 y versión de los datos usada.
- Recodificación de códigos "no disponible" (cifras en `cleaning_log.md` §2).
- Exclusión de liquidaciones en 2026-01 a 2026-03 (0 casos).
- Casos completos (−83) y advertencia sobre DTI > 65 %.
- Exclusión de PR (−4), divisiones censales y agrupación de factores.
- Partición temporal por mes de liquidación (3.153 / 803).

---

## 7. Problemas, limitaciones y pendientes

Registrados durante el trabajo:

- **Versión de los datos:** el archivo de Freddie Mac cambia entre entregas. Con el corte fijo en 202603 la base
  es reproducible con el archivo actual; si Freddie Mac vuelve a corregir pérdidas, podrían cambiar valores.
- **Pérdidas recientes incompletas:** dos liquidaciones de 2025-12 casi triplicaron su LGD entre la entrega de
  marzo y la de junio (0,136 → 0,287 y 0,097 → 0,342). La ventana de 3 meses de la guía podría no bastar para que
  la pérdida de las liquidaciones más recientes esté completa. Llevado a la Reunión 1 como dato (D7).
- **Faltantes de DTI no al azar:** los 81 excluidos probablemente incluyen a los deudores más endeudados (DTI > 65 %).
- **`channel` = T** mezcla terceros no especificados con canal no disponible.
- **Finales de línea:** `.gitignore`, `CLAUDE.md`, `README.md` y `requirements.txt` aparecen modificados solo por
  CRLF/LF.

---

## 8. Uso de IA

Registro de uso (Para documentacion de usao de IA):

| Herramienta | Propósito | Parte del trabajo | Verificación realizada |
|---|---|---|---|
| Claude Code | Programación | `PERF_CUTOFF` y regla CLTV en `build_dataset.py`; script `prepare_model_data.py` | Creacion de ambos scripts; 12 verificaciones; comparación con el reporte versionado |
| Claude Code | Programación y depuración | Comparación de versiones de datos (corte 202603 vs. entrega anterior) | Comparación celda a celda de `lgd_2007.csv`; 5 diferencias identificadas |
| Claude Code | Planificación y opciones | Propuesta de opciones para D1–D7 (`ROADMAP.md` del Rol 1) | Las elecciones las hizo el integrante |
| Claude Code | Documentación | Redacción de entradas de `cleaning_log.md` y de la estructura de este reporte | |
