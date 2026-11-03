# Cleaning log

Registro de cada decisión de limpieza: **qué** se hizo, **cuántos casos** afectó y **por qué**.
Los números salen de `python src/build_dataset.py` (reporte en `outputs/build_dataset_report.txt`) y, desde la
sección 4 en adelante, de `python src/prepare_model_data.py` (reporte en `outputs/prepare_model_data_report.txt`).
Si cambia una regla, se actualiza esta tabla y se vuelve a correr el script.

Fuente: Freddie Mac Single-Family Loan-Level Dataset, muestra 2007 (`sample_orig_2007.txt`, `sample_perf_2007.txt`),
documentación: `file_layout_july_2026.xlsx` y *General User Guide* (julio 2026), ambas en `data/raw/`.

---

## 0. Layout de columnas

| Qué | Resultado |
|---|---|
| Campos en la 1ª línea | originación = **31**, desempeño = **35** → **layout NUEVO (julio 2026)** |
| Consistencia | Las 50.000 líneas de originación tienen 31 campos y las 3.015.985 de desempeño tienen 35 (se revisaron todas, no solo la 1ª). |
| Versión del archivo (02-11-2026) | El `sample_2007.zip` descargado hoy trae desempeño **hasta 202606** (3.015.985 filas). El build original se hizo con una entrega anterior, con desempeño hasta 202603 (3.012.061 filas). La diferencia (3.924 filas) son exactamente los meses 202604–202606. |
| Corte de desempeño | `PERF_CUTOFF = "202603"` en `build_dataset.py`: se ignoran las filas posteriores a 202603, para mantener el periodo de análisis definido por el grupo (desempeño hasta marzo de 2026). Quedan 3.012.061 filas. |
| Reproducción | Con el corte, el archivo nuevo reproduce **la misma población** que la entrega anterior: 50.000 → 4.484 → 4.043 → 3.960, mismos `loan_id`, mismos tramos de LGD y misma distribución por código y año de cierre. |
| Pérdidas corregidas por la fuente | En la entrega nueva Freddie Mac corrigió montos de **5 créditos** (gastos o recuperaciones). LGD anterior → nueva: F07Q20424808 (cierre 202512) 0,136 → 0,287; F07Q40062505 (202512) 0,097 → 0,342; F07Q40095936 (202511) 0,8070 → 0,8073; F07Q40290698 (202411) 0,1377 → 0,1379; F07Q30305927 (202002) 1,227 → 1,214. Ninguno cruza 0 ni 1; los 5 quedan en el tramo de validación. **Se usa la entrega nueva** (decisión 02-11-2026), porque es la que cualquiera puede descargar hoy y tiene los valores corregidos. |
| Contra el XLSX | Las 31 + 35 posiciones coinciden con la lista del grupo. Única diferencia de nombre: la pos. 1 de originación se llama "Classic FICO®" en el XLSX (nosotros: `credit_score`). Pos. 26 "Pre-HARP Loan Sequence Number" = `pre_harp_loan_id`. |

## 1. Unión de archivos

| Paso | Casos | Por qué |
|---|---|---|
| Última fila (mayor `period`) de cada crédito en desempeño | 50.000 créditos (de 3.012.061 filas) | La fila de cierre trae el `zero_balance_code` y los montos de pérdida. Se verificó que ningún crédito tiene más de una fila con `zero_balance_code`, y que esa fila es siempre la última. |
| Unión con originación por `loan_id` (inner) | 50.000 / 50.000 | Ningún crédito quedó sin pareja. |

## 2. Códigos "no disponible" → NaN

Conteos sobre los 50.000 créditos unidos.

| Variable | Código | Casos | Origen de la regla |
|---|---|---|---|
| `credit_score` | 9999 | 38 | Grupo + guía p. 4 |
| `dti` | 999 | 1.124 | Grupo + guía p. 5. **Verificado 02-11:** la guía dice "Ratios > 65% will be disclosed as Not Available. All HARP loans … as Not Available". En la base de LGD los 81 NaN de `dti` tienen `harp_indicator` = N, así que corresponden a DTI > 65 % o a dato no disponible (la guía no permite distinguirlos). Rango válido 0–65; hay 32 créditos con DTI = 65 exacto. → Los NaN de `dti` **no son faltantes al azar**. |
| `ltv` | 999 | 1 | Grupo + guía p. 6 |
| `cltv` | 999 | 2 | Grupo + guía p. 5 (también se marca NA si CLTV < LTV; ver fila siguiente) |
| `cltv` | CLTV < LTV | 0 | Guía p. 5. Implementada en `build_dataset.py` el 02-11-2026 (antes solo figuraba en este log). Se aplica después de recodificar 999. **0 casos en los 50.000**: `lgd_2007.csv` no cambia. **Verificado 02-11:** la guía dice "If the CLTV is < LTV, CLTV will be disclosed as Not Available"; la fuente ya aplica la regla y entrega esos casos como 999. La regla en el código queda como control. Rango válido hasta 2018Q1: 6 %–200 %. |
| `mi_pct` | 999 | 0 | Grupo + guía p. 5. **Ojo:** 0 = sin seguro hipotecario, es un valor válido, no NA. |
| `n_units` | 99 | 0 | Grupo |
| `n_borrowers` | 99 | 23 | Grupo + guía p. 8 |
| `occupancy_status` | 9 / 99 | 0 | Grupo + guía p. 5 |
| `loan_purpose` | 9 / 99 | 0 | Grupo + guía p. 8 |
| `first_time_homebuyer` | 9 / 99 | 13 | Grupo + guía p. 4 |
| `property_type` | 9 / 99 | 0 | Grupo |
| `vantage_score_4` | **9999** | **50.000 (100 %)** | Guía p. 9: "9999 = Not Available". En 2007 no existe el dato → variable inutilizable. |
| `channel` | 9 | 0 | *Agregado por nosotros* según guía p. 6. **Verificado 02-11:** R = Retail, B = Broker, C = Correspondent, T = "Third Party Origination – Not Specified". B, C y T son originación por terceros. **Matiz:** la guía indica que T también se usa cuando no hay designación de terceros ni de retail, así que T (2.557 de 4.043) mezcla terceros no especificados con canal desconocido. |
| `property_valuation_method` | 7 | 50.000 (100 %) | *Agregado* según guía p. 9 → inutilizable en 2007 |
| `eltv` (desempeño) | 999 | 48.197 | *Agregado* según guía p. 14 (solo existe desde abril 2017) |

## 3. Definición de la respuesta (LGD)

Confirmado con la guía (p. 13): Actual Loss se calcula **solo** para `zero_balance_code` ∈ {02, 03, 09, 15}
(02 venta a tercero, 03 short sale / charge-off, 09 venta de REO, 15 venta de cartera).

**LGD = actual_loss / zero_balance_removal_upb**

| Paso | Quedan | Excluidos | Por qué |
|---|---|---|---|
| (a) Total de créditos | 50.000 | – | |
| (b) `zero_balance_code` ∈ {02,03,09,15} | 4.484 | 45.516 | Solo estos cierres tienen pérdida calculada (01 = prepago, 16 = titulización, 96 = defecto, vacío = activo). |
| (c) `actual_loss` no nulo | 4.043 | 441 | Los 441 tienen `defect_settlement_date` (guía: Actual Loss = null "Not Applicable"). Cierres en los 3 meses previos al corte (202603): **0**. **Verificado 02-11 (D7):** la guía dice "The Actual Loss will be set to null for loans disposed within the three months prior to the performance cutoff date". En el archivo completo (corte 202606) los únicos `actual_loss` nulos sin defecto son 2 liquidaciones de 202604, lo que confirma que la ventana incluye el mes del corte y los dos anteriores. Con corte 202603 la ventana es 2026-01 a 2026-03, como aplica el código. |
| Denominador `zero_balance_removal_upb` > 0 | 4.043 | 0 | Necesario para dividir. |
| (d) Sin NaN en los predictores candidatos **provisionales** | 3.960 | 83 | 81 por `dti`, 2 por `credit_score`. Tratamiento: casos completos (D5), ver sección 7. |

Verificación: en los 4.043 casos, `actual_loss` = removal UPB + net sale proceeds + delinquent accrued interest
+ total expenses + MI recoveries + non-MI recoveries (fórmula de la guía), con diferencia < $1 en el 100 %.

## 4. LGD fuera de [0, 1] — se mantiene `lgd` y se agrega `lgd_trunc` (D1, por ratificar en grupo)

| Tramo | Casos completos (d) | Todos con LGD (c) | Base de modelamiento (3.956) |
|---|---|---|---|
| LGD < 0 | 76 | 77 | 76 (57 entrenamiento, 19 validación) |
| LGD = 0 | 1 | 1 | 1 |
| 0 < LGD < 1 | 3.554 | 3.631 | 3.550 |
| LGD = 1 | 0 | 0 | 0 |
| LGD > 1 | 329 | 334 | 329 (209 entrenamiento, 120 validación) |

| Qué | Casos | Por qué |
|---|---|---|
| `lgd` se mantiene sin cambios | 0 excluidos | Los valores fuera de [0, 1] no son errores: `actual_loss` calza con la fórmula de la guía en el 100 % (sección 3). LGD > 1 = gastos e intereses mayores que lo recuperado; LGD < 0 = recuperaciones mayores que el saldo. Excluirlos sesgaría la muestra. |
| Nueva columna `lgd_trunc` = `lgd` truncada a [0, 1] | 76 llevados a 0; 329 llevados a 1 | Respuesta para el modelo competidor (GLM de respuesta fraccional), que exige valores en [0, 1]. Se crea en `prepare_model_data.py`; `lgd` no se sobrescribe. |

Pendiente para el grupo: contra qué variable (`lgd` o `lgd_trunc`) se mide el error de validación, la misma para todos los modelos.

## 5. Variables descartadas por no tener información (D6, por ratificar en grupo)

Se eliminan de la base de modelamiento en `prepare_model_data.py`; siguen en `lgd_2007.csv`.

- `vantage_score_4`, `property_valuation_method`: 100 % NA en 2007.
- `amortization_type`: todos FRM en la base de LGD (sin variación).
- `eltv`: vacía en 3.825 de los 4.043 (solo existe desde 2017).

## 6. Estados → divisiones censales (D3, por ratificar en grupo)

Fuente: U.S. Census Bureau, *Census Regions and Divisions of the United States*,
https://www2.census.gov/geo/pdfs/maps-data/maps/reference/us_regdiv.pdf (consultado el 02-11-2026).
La tabla está en `src/prepare_model_data.py` (`CENSUS_DIVISIONS`) y crea la columna `division`; `property_state` se conserva.

| Qué | Casos | Por qué |
|---|---|---|
| Verificación de la tabla contra el PDF | 9 divisiones, 50 estados + DC | Comparación automática con la página 2 del PDF: mismos nombres de división, cada estado una sola vez, sin repetidos y ningún estado en una división distinta. Las siglas coinciden con las del mapa de la página 1. |
| Códigos de `property_state` sin división | **PR = 4** (en los 4.043 con LGD y en los 3.960 casos completos) | No aparecen GU, VI ni otros territorios. Si en otra versión de los datos aparecen, se tratan igual que PR y el conteo excluido cambia. |
| Exclusión de Puerto Rico | 3.960 → **3.956** (−4: 2 en entrenamiento y 2 en validación) | PR no pertenece a ninguna división censal y 4 casos no permiten estimar un efecto propio. |

Créditos por división (4.043 con LGD): New England 145, Middle Atlantic 277, East North Central 678,
West North Central 264, South Atlantic 1.146, East South Central 176, West South Central 198, Mountain 574, Pacific 581.

## 7. Faltantes: casos completos (D5, por ratificar en grupo)

| Qué | Casos | Por qué |
|---|---|---|
| Se excluyen créditos con NaN en algún predictor candidato | 4.043 → **3.960** (−83: 81 `dti`, 2 `credit_score`, ninguno con ambos) | Pérdida pequeña (≈ 2 %); imputar agregaría supuestos difíciles de justificar en esta etapa. |
| Distribución temporal de los excluidos | 67 con liquidación ≤ 2014-12 y 16 posteriores | Para saber cuánto afecta a cada tramo de la partición. |

**Advertencia para el informe:** según la guía (p. 5), `dti` = 999 significa DTI > 65 % o dato no disponible
(sección 2). Los 81 excluidos por `dti` **no son faltantes al azar**: probablemente incluyen a los deudores más
endeudados. Rol 2 compara su LGD con la del resto antes de cerrar la decisión.

## 8. Agrupación de factores con niveles escasos (D3, por ratificar en grupo)

Columnas nuevas en `prepare_model_data.py`; las originales (`channel`, `property_type`, `n_units`) se conservan.
Conteos sobre la base de modelamiento (3.956).

| Columna nueva | Agrupación | Antes → después | Por qué |
|---|---|---|---|
| `channel_grp` | R → R; B, C, T → TPO | R 1.441, T 2.510, C 3, B 2 → R 1.441, TPO 2.515 | B y C no permiten estimar efectos propios; B, C y T son originación por terceros (guía p. 6). T también incluye canal no disponible (sección 2). |
| `property_type_grp` | CP → CO; resto igual | CP 3, CO 427 → CO 430 (SF 2.887, PU 569, MH 70 sin cambio) | Cooperativa y condominio son viviendas en edificio compartido; CP tiene solo 3 casos. MH se mantiene porque tiene casos suficientes y es un tipo distinto. |
| `n_units_grp` | 1 → "1"; 2, 3, 4 → "2-4" | 1: 3.841; 2: 92, 3: 13, 4: 10 → 2-4: 115 | 3 y 4 unidades suman 23 casos en esta base. |
| `division` | Estado → 9 divisiones censales | 51 niveles → 9 | Ver sección 6. |

## 9. Partición temporal 80/20 (D4, por ratificar en grupo)

Eje temporal: mes de liquidación (`zero_balance_effective_date`, AAAAMM). Columna `split` en `prepare_model_data.py`.

| Tramo | Regla | Casos | Meses |
|---|---|---|---|
| Entrenamiento | liquidación ≤ 2014-12 | **3.153** (79,7 %) | 2008-03 a 2014-12 |
| Validación | liquidación ≥ 2015-01 | **803** (20,3 %) | 2015-01 a 2025-12 |

Por qué: el percentil 80 cae en 2015-01 (26 liquidaciones en los casos completos). Cortar en 2014-12 evita que un
mismo mes quede en ambos tramos y la regla se explica en una línea. El enunciado exige respetar el orden temporal,
no un 80,0 % exacto. Verificado en el script: ningún mes aparece en ambos tramos y todo el entrenamiento es anterior
a la validación.

## 10. Flujo muestral completo

Tabla para el informe: `outputs/tables/flujo_muestral.csv`.

| Paso | Quedan | Excluidos |
|---|---|---|
| Créditos en la muestra 2007 | 50.000 | – |
| `zero_balance_code` ∈ {02, 03, 09, 15} | 4.484 | 45.516 |
| `actual_loss` informado | 4.043 | 441 |
| Sin liquidaciones en 2026-01 a 2026-03 (D7) | 4.043 | 0 |
| Casos completos (D5) | 3.960 | 83 |
| Estados con división censal (sin PR) | 3.956 | 4 |
| → Entrenamiento / validación (D4) | 3.153 / 803 | – |
