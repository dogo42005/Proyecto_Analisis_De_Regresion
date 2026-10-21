# Cleaning log

Registro de cada decisión de limpieza: **qué** se hizo, **cuántos casos** afectó y **por qué**.
Los números salen de `python src/build_dataset.py` (reporte completo en `outputs/build_dataset_report.txt`).
Si cambia una regla, se actualiza esta tabla y se vuelve a correr el script.

Fuente: Freddie Mac Single-Family Loan-Level Dataset, muestra 2007 (`sample_orig_2007.txt`, `sample_perf_2007.txt`),
documentación: `file_layout_july_2026.xlsx` y *General User Guide* (julio 2026), ambas en `data/raw/`.

---

## 0. Layout de columnas

| Qué | Resultado |
|---|---|
| Campos en la 1ª línea | originación = **31**, desempeño = **35** → **layout NUEVO (julio 2026)** |
| Consistencia | Las 50.000 líneas de originación tienen 31 campos y las 3.012.061 de desempeño tienen 35 (se revisaron todas, no solo la 1ª). |
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
| `dti` | 999 | 1.124 | Grupo + guía p. 5 |
| `ltv` | 999 | 1 | Grupo + guía p. 6 |
| `cltv` | 999 | 2 | Grupo + guía p. 5 (también se marca NA si CLTV < LTV) |
| `mi_pct` | 999 | 0 | Grupo + guía p. 5. **Ojo:** 0 = sin seguro hipotecario, es un valor válido, no NA. |
| `n_units` | 99 | 0 | Grupo |
| `n_borrowers` | 99 | 23 | Grupo + guía p. 8 |
| `occupancy_status` | 9 / 99 | 0 | Grupo + guía p. 5 |
| `loan_purpose` | 9 / 99 | 0 | Grupo + guía p. 8 |
| `first_time_homebuyer` | 9 / 99 | 13 | Grupo + guía p. 4 |
| `property_type` | 9 / 99 | 0 | Grupo |
| `vantage_score_4` | **9999** | **50.000 (100 %)** | Guía p. 9: "9999 = Not Available". En 2007 no existe el dato → variable inutilizable. |
| `channel` | 9 | 0 | *Agregado por nosotros* según guía p. 6 |
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
| (c) `actual_loss` no nulo | 4.043 | 441 | Los 441 tienen `defect_settlement_date` (guía: Actual Loss = null "Not Applicable"). Cierres en los 3 meses previos al corte (202603): **0**. |
| Denominador `zero_balance_removal_upb` > 0 | 4.043 | 0 | Necesario para dividir. |
| (d) Sin NaN en los predictores candidatos **provisionales** | 3.960 | 83 | 81 por `dti`, 2 por `credit_score`. La lista de candidatos aún no está decidida. |

Verificación: en los 4.043 casos, `actual_loss` = removal UPB + net sale proceeds + delinquent accrued interest
+ total expenses + MI recoveries + non-MI recoveries (fórmula de la guía), con diferencia < $1 en el 100 %.

## 4. LGD fuera de [0, 1] — **NO tratado todavía (decisión pendiente)**

| Tramo | Casos completos (d) | Todos con LGD (c) |
|---|---|---|
| LGD < 0 | 76 | 77 |
| LGD = 0 | 1 | 1 |
| 0 < LGD < 1 | 3.554 | 3.631 |
| LGD = 1 | 0 | 0 |
| LGD > 1 | 329 | 334 |

No se truncan ni se excluyen. Se decide en grupo (ver opciones en `CLAUDE.md`, sección "Decisiones pendientes").

## 5. Variables descartadas por no tener información (pendiente de confirmar en grupo)

- `vantage_score_4`, `property_valuation_method`: 100 % NA en 2007.
- `amortization_type`: todos FRM en la base de LGD (sin variación).
- `eltv`: casi todo NA (solo existe desde 2017).
