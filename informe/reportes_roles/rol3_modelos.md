# Reporte Rol 3 — Modelos y diagnóstico

Responsable: **Amelie Ramírez** · Hito 2 (avance, lunes 16-11-2026).
Datos: `data/processed/lgd_2007_model.csv`; ajuste solo con entrenamiento (`split == "train"`, n = 3.153);
validación con `split == "valid"` (n = 803). Respuesta: `lgd` original (decisión A).

Scripts: `src/seleccion_modelos.py` (búsqueda de subconjuntos y aporte por variable) y `src/modelos.py` (ajuste de
los dos modelos, Tabla 2, diagnóstico, validación y Figura 2; tablas `outputs/tables/mod_*.csv`).
Decisiones: K y L en `informe/decisiones.md`.

## Paso 1 — Predictores del modelo completo

**LTV vs. CLTV (decisión K).**

> Entre LTV y CLTV (r = 0,85) se eligió el LTV. Su relación con la LGD es casi igual a la del CLTV (r = −0,22 frente a
> −0,25), y describe directamente la hipoteca sobre la que Freddie Mac registra la pérdida, mientras que el CLTV incluye
> además segundos créditos de otros acreedores. Además, como el seguro hipotecario se exige según el LTV (sobre 80 %),
> incluir el LTV permite interpretar el efecto del seguro a igual LTV. Se acepta el costo de una mayor colinealidad entre
> el LTV y el seguro (r = 0,77), que se evaluará con el VIF.

**Modelo completo.** Incluye los 14 bloques de predictores candidatos, todos conocidos al originar el crédito: log del
monto, LTV, seguro (indicadora + porcentaje), tasa, puntaje, DTI, propósito, ocupación, división censal, unidades,
primer comprador, número de deudores, tipo de propiedad y canal (27 parámetros). No se usan componentes de la pérdida
(fuga de información).

## Paso 2 — Modelo reducido y comparación (decisión L)

> El modelo completo incluye los 14 bloques de predictores candidatos. El modelo reducido excluye el DTI y la indicadora
> de primer comprador. En la búsqueda de todos los subconjuntos (16.384 modelos ajustados con entrenamiento), este
> modelo reducido es el único que está entre los tres mejores tanto por AIC como por BIC. El primer comprador no aporta
> una vez considerados los demás predictores (p = 0,31), y al sacarlo el AIC y el BIC disminuyen. El DTI tampoco es
> significativo al 5 % (p = 0,08); al sacarlo el BIC mejora y el AIC prácticamente no cambia. Además, el DTI tiene una
> relación débil con la LGD y una limitación en los datos: el código 999 impide saber si los excluidos tienen un DTI
> mayor que 65 %. La prueba F no rechaza que el DTI y la indicadora de primer comprador sean conjuntamente nulos
> (F = 2,13 con 2 y 3.126 grados de libertad, p = 0,12). Como el reducido se eligió tras una búsqueda de subconjuntos,
> este valor p puede estar sesgado; sin embargo, en el 20 % de validación ambos modelos tienen prácticamente el mismo
> error (RMSE de 0,359 en ambos), por lo que se prefiere el reducido, que es más simple.

| Modelo | Parámetros | R² | R² ajustado | F global (p) | RMSE val. | MAE val. |
|---|---|---|---|---|---|---|
| Completo | 27 | 0,377 | 0,371 | 72,63 (< 0,001) | 0,3586 | 0,2780 |
| Reducido | 25 | 0,376 | 0,371 | 78,45 (< 0,001) | 0,3587 | 0,2778 |
| Sin predictores (media de entrenamiento) | 1 | — | — | — | 0,4053 | 0,3154 |

AIC y BIC: completo −59,09 y 104,43; reducido −58,80 y 92,61 (`outputs/tables/mod_01_comparacion.csv`).

## Paso 3 — Diagnóstico (modelo reducido)

Fuentes: `outputs/figures/figura2.png` (paneles a–c), `outputs/tables/mod_03_vif.csv`, `outputs/tables/mod_07_pruebas_supuestos.csv`,
`mod_09_error_por_anio.csv` (residuo medio por año), `mod_10_errores_robustos_hc3.csv` (HC3) y
`mod_11_varianza_residuos.csv` (desv. est. de los residuos por quintil de ajustado).
Interpretación: Amelie.

> El diagnóstico del modelo reducido no muestra problemas de linealidad global: la tendencia de los residuos frente a
> los valores ajustados es prácticamente nula. Sin embargo, los residuos aún muestran la forma no monótona del LTV. La
> varianza de los residuos aumenta levemente con el valor ajustado (desviación estándar de 0,21 a 0,26; Breusch-Pagan,
> p < 0,001), lo que debe tenerse en cuenta, aunque con errores estándar robustos (HC3) ningún coeficiente cambia su
> significancia al 5 %. Los residuos son simétricos, pero con colas algo más pesadas que la normal (curtosis en exceso
> 1,04), lo que no es grave con n = 3.153. No hay multicolinealidad relevante (GVIF máximo 2,88, del LTV). Los residuos
> muestran un patrón en el tiempo: el modelo sobreestima la LGD de los créditos liquidados en 2008–2009 (residuo medio
> de −0,19 y −0,10). Una posible explicación es el ciclo de precios de las viviendas durante la crisis, ya que esos
> créditos se liquidaron antes de que los precios tocaran fondo, aunque el modelo no incluye variables que permitan
> comprobarlo.

Datos de apoyo: residuo medio por año de liquidación (entrenamiento): 2008 −0,185 (n = 30) · 2009 −0,100 (215) ·
2010 −0,045 (516) · 2011 +0,026 · 2012 +0,024 · 2013 −0,006 · 2014 +0,042 (383). LOWESS de residuos vs. LTV:
de −0,15 a +0,04; vs. log(monto): hasta +0,20 en los extremos. Residuos estudentizados fuera de ±3: 16 (≈ 9 esperados
bajo normalidad).

## Paso 4 — Atípicos e influyentes

Fuentes: `outputs/figures/figura2.png` (panel d), `outputs/tables/mod_04_influyentes.csv`,
`mod_05_resumen_influencia.csv`, `mod_06_sensibilidad_atipicos.csv`. Interpretación: Amelie.

> Ningún crédito resulta influyente por sí solo: la distancia de Cook máxima es 0,024, muy por debajo de 1. Un 6,4 % de
> los créditos tiene alto apalancamiento (h > 2p/n = 0,016), es decir, combinaciones poco comunes de predictores, y 16
> tienen residuos estudentizados mayores que 3 en valor absoluto. La mayoría de los 21 créditos con LGD atípica tiene
> residuos altos pero bajo apalancamiento (18 de 21 bajo el umbral), por lo que su capacidad de modificar el ajuste es
> limitada, aunque los tres créditos con mayor distancia de Cook pertenecen a este grupo. Al reajustar el modelo sin
> ellos, los coeficientes cambian poco; solo cambia de signo el de condominio, que es prácticamente cero y no
> significativo (de −0,002 a 0,005; p = 0,88). El mayor cambio en un coeficiente relevante es el de la indicadora de
> seguro (de 0,032 a 0,035). Por lo tanto, se mantienen: son pérdidas reales y aportan información sobre los casos
> extremos.

Nota de concepto: el apalancamiento indica si un crédito *podría* mover el ajuste (predictores poco comunes); la
distancia de Cook indica si *efectivamente* lo mueve.

## Paso 5 — Validación

Fuentes: `outputs/tables/mod_01_comparacion.csv`, `mod_08_errores.csv` (entrenamiento, validación, modelo nulo y
R² fuera de muestra) y `mod_09_error_por_anio.csv` (error por año), todas de `src/modelos.py` (modelo reducido).
Interpretación: Amelie.

> En validación (n = 803), el modelo reducido tiene un error mayor que en entrenamiento (RMSE 0,359 frente a 0,238;
> MAE 0,278 frente a 0,187), pero menor que el de predecir siempre la LGD promedio (RMSE 0,405; MAE 0,315), y explica
> un 22 % de la variabilidad fuera de muestra (R² de 0,38 en entrenamiento). El mayor error se explica en parte porque
> la LGD de validación es más dispersa (desviación estándar 0,40 frente a 0,30) y su composición regional es distinta.
> En promedio, el modelo subestima levemente la LGD (error medio +0,013), pero el sesgo cambia con el tiempo: subestima
> en 2015–2016, que concentran el 59 % de la validación, y sobreestima desde 2018. Por lo tanto, el modelo sirve para
> orientar la pérdida esperada según las características del crédito, pero no para predecir con precisión casos
> individuales, y su sesgo temporal debe revisarse.

Error medio (observado − predicho) por año de liquidación: 2015 +0,054 (n = 261) · 2016 +0,106 (212) · 2017 +0,011 (108) ·
2018 −0,061 (65) · 2019 −0,061 (42) · 2020 −0,186 (37) · 2021 −0,316 (34) · 2022–2025 entre −0,03 y −0,09 (n = 7 a 16).

## Texto para main.tex (sección 4)

Archivo listo para pegar: `informe/avance/seccion4_rol3.tex` (Tabla 2, Figura 2 con su pie y este párrafo).

> Se ajustaron con entrenamiento dos OLS anidados: el completo, con 14 bloques de predictores, y el reducido, sin DTI ni primer comprador, elegido tras una búsqueda de todos los subconjuntos. La prueba F no rechaza que esas dos variables sean conjuntamente nulas (F = 2,13; p = 0,12), el reducido tiene menor BIC y ambos predicen igual en validación, por lo que se prefiere el reducido (Tabla 2). En su diagnóstico (Figura 2) la linealidad global es adecuada, aunque persiste la forma no monótona del LTV; la varianza crece levemente con el valor ajustado (Breusch-Pagan, p < 0,001), sin cambios de significancia con errores robustos, y las colas son algo pesadas. No hay multicolinealidad relevante (GVIF máximo 2,88) ni créditos influyentes (Cook máximo 0,024), por lo que se mantienen las 21 LGD atípicas. El modelo sobreestima la LGD de 2008–2009, posiblemente por el ciclo de precios de la crisis. En validación supera al promedio (RMSE 0,359 frente a 0,405; R² fuera de muestra 0,22), pero su sesgo cambia en el tiempo: sirve para orientar la pérdida esperada, no para predecir casos individuales.

## Uso de IA

| Herramienta | Propósito | Parte del trabajo | Verificación |
|---|---|---|---|
| Claude Code | Programación | `src/seleccion_modelos.py` (búsqueda de 16.384 subconjuntos, aporte por bloque con prueba F, AIC y BIC); cálculo de la F entre modelos, F global y error de validación | Prueba F verificada con `statsmodels` (`compare_f_test`) |
| Claude Code | Aclaración de conceptos | Fuga de información, multicolinealidad y VIF, efecto marginal vs. condicional, factores y nivel base, LTV vs. CLTV, AIC/BIC y ΔAIC, prueba F anidada vs. F global, sesgo de selección, RMSE y MAE | — |
| Claude Code | Redacción | Párrafos de los pasos 1 y 2 con el método nuevo: la IA explicó criterios y presentó datos y alternativas (LTV, CLTV o LTV + diferencia; argumento económico de tasa, puntaje y DTI); Amelie escribió su interpretación y eligió. La IA avisó lo que no calzaba (r de 0,03, no 0,003; `mi_pct` no es la variable más fuerte ni el foco de la pregunta; la relación LTV-seguro es un costo, no una ventaja; descartar por r marginal es débil; umbral de 0,05, no 0,001; la limitación del 65 % no aplica al primer comprador) y mejoró la redacción. Las decisiones K y L son de Amelie | Cifras contrastadas con `outputs/tables/sel_0*.csv` |
| Claude Code | Redacción | Párrafo del paso 3. La IA explicó los supuestos y cómo leer cada gráfico, calculó las pruebas (Breusch-Pagan, Jarque-Bera, HC3, residuo por año, LOWESS por predictor) y avisó lo que no calzaba (Breusch-Pagan rechaza varianza constante; hay 16 residuos fuera de ±3, no 5; sí hay patrón temporal en 2008–2009; la explicación de la crisis debe calzar con la dirección del error). Amelie escribió y aprobó la interpretación | Cifras contrastadas con `mod_0*.csv` |
| Claude Code | Redacción | Párrafo del paso 4. La IA explicó residuo estudentizado, apalancamiento y Cook, calculó la sensibilidad sin los 21 atípicos y avisó lo que no calzaba (se confundía alto apalancamiento con influencia; hay 16 casos con \|r\| > 3, no 7; 3 atípicos superan el umbral de h y el máximo es 0,025). Amelie escribió y aprobó la interpretación; la decisión de mantener los atípicos (G) se ratifica | Cifras contrastadas con `mod_04` a `mod_06` |
| Claude Code | Redacción | Párrafo del paso 5. La IA explicó RMSE, MAE, modelo nulo, R² fuera de muestra y sesgo, calculó el error por año y avisó lo que no calzaba ("no predice bien" era demasiado duro porque supera al promedio; entrenamiento y validación tienen la misma limpieza, no distintos filtros; signo del sesgo: positivo = subestima; el sesgo cercano a 0 en algunos años no implica error bajo). Amelie escribió y aprobó la interpretación | Cifras contrastadas con `mod_01_comparacion.csv` |
| Claude Code | Redacción | Párrafo de la sección 4 de `main.tex`: la IA condensó los párrafos de los pasos 1 a 5 ya escritos y aprobados por Amelie, sin agregar interpretación nueva; también propuso el pie de la Figura 2 (descriptivo) y armó la Tabla 2 en LaTeX | Cifras contrastadas con `mod_01_comparacion.csv` y los párrafos de los pasos 1 a 5 |
| Claude Code | Revisión y programación (15-11, sesión de Diego) | Revisión del commit: se volvieron a correr los scripts (21 tablas idénticas) y se recalcularon las cifras del reporte. Se agregaron a `src/modelos.py` las tablas `mod_08` a `mod_11` (errores y modelo nulo, error por año, HC3, varianza por quintil), que antes se calculaban fuera del script. Se corrigió en el paso 4 la frase "ninguno cambia de signo" (el de condominio sí cambia, aunque es ≈ 0 y no significativo) | Las tablas nuevas reproducen exactamente las cifras ya escritas |
