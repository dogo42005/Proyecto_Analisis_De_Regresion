# Reporte de rol — Rol 2: Análisis exploratorio (Hito 2)

Responsable: **Diego Olivares** (pasos 1 a 4) y **Amelie Ramírez** (desde el paso 5, 14-11-2026, porque Diego no puede seguir) · Código: `src/eda.py` · Figuras: `outputs/figures/eda_*` · Tablas: `outputs/tables/eda_*`

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

### Paso 5 — Transformaciones de los predictores (entrenamiento)

Fuentes: `outputs/figures/eda_05_transformaciones_monto.png`, `outputs/figures/eda_05_boxcox_perfil_monto.png`,
`outputs/figures/eda_05_transformaciones_ltv_cltv.png`, `outputs/tables/eda_05_transformaciones.csv`.
Interpretación: Amelie. Decisiones H, I y J en `informe/decisiones.md`.

**Monto original — distribución.**

> El monto original presenta una asimetría moderada (0,63), con cola hacia la derecha. Además, muestra una acumulación
> de 57 créditos en 417 mil USD, el límite de préstamo que podía comprar Freddie Mac en 2007, y solo 4 créditos por
> sobre ese valor, que quedan separados del resto. Como el máximo supera más de 10 veces al mínimo (razón 21,8), la
> regla del logaritmo sugiere evaluar esa transformación. En escala logarítmica la distribución queda aproximadamente
> simétrica (−0,49), aunque se corrige de más y aparece una cola leve hacia la izquierda; los extremos quedan más cerca
> del resto. Con Box-Cox (λ = 0,35) la asimetría es prácticamente nula (−0,04). El hueco sobre 417 mil USD persiste en
> las tres escalas. En términos de simetría, Box-Cox es la mejor opción.

**Monto original — perfil de Box-Cox.**

> Según el perfil de verosimilitud de Box-Cox, el λ estimado para el monto original es 0,35, con un IC 95 % angosto
> (0,29 a 0,41) que no incluye el 0 (logaritmo) ni el 1 (sin transformar). Por lo tanto, para acercar la distribución
> del monto a la simetría conviene transformarlo, y la transformación óptima en este sentido está entre la raíz y el
> logaritmo. Aun así, el logaritmo queda bastante más cerca del óptimo que la escala original (la log-verosimilitud
> baja 72 puntos con el log y 209 sin transformar). Dado el tamaño de la muestra, el intervalo es muy preciso, así que
> este criterio por sí solo no descarta el log.

**Monto original — relación con la LGD.**

> En los gráficos de dispersión, la tendencia suavizada (LOWESS) de la LGD es más cercana a una recta cuando el monto
> está en escala logarítmica, aunque se aplana en los montos más altos. En la escala original, en cambio, la LGD cae
> fuerte en los montos bajos y luego es casi constante. La correlación lineal con la LGD cambia poco entre escalas
> (r = −0,31 original, −0,36 log y −0,35 Box-Cox), y la diferencia entre log y Box-Cox es irrelevante en la práctica.
> Además, la LGD es más variable en los montos bajos: su desviación estándar baja de 0,35 en el 20 % de montos más bajos
> a 0,22 en el 20 % más alto, y la proporción de LGD > 1 cae de 20,3 % a 0,5 %. Esta variabilidad no constante no
> depende de la escala del monto, por lo que se revisará en el diagnóstico del modelo.

**Monto original — decisión (H).**

> Se decidió usar el monto original en escala logarítmica. Aunque Box-Cox (λ = 0,35) deja la distribución del monto
> más simétrica, la simetría de un predictor no es un requisito del modelo lineal. En el criterio principal, la
> linealidad de la relación con la LGD, el logaritmo rinde igual o mejor: su tendencia suavizada es la más cercana a
> una recta y su correlación con la LGD es similar a la de Box-Cox (r = −0,36 frente a −0,35). Además, la regla del
> logaritmo lo respalda (razón máx/mín = 21,8) y su coeficiente se interpreta directamente en términos de cambios
> porcentuales del monto, mientras que la escala de Box-Cox no tiene una interpretación intuitiva.

**Resto de los predictores — decisión (I).**

> Los demás predictores positivos se mantienen en su escala original. El DTI es el único que cumple la regla del
> logaritmo (razón 21,7), pero su λ de Box-Cox es cercano a 1 (1,20), el log aumenta su asimetría (de −0,21 a −1,78) y
> su correlación con la LGD no cambia (r = −0,10). El LTV y el CLTV tienen asimetría negativa (−0,77 y −0,97) y λ
> mayores que 1, pero su relación con la LGD no es monótona: la tendencia LOWESS sube hasta un LTV de 70–80 % y luego
> baja. Como Box-Cox solo cambia la escala del eje sin alterar el orden de los datos, no puede enderezar esta forma, y en
> los gráficos la tendencia es la misma en ambas escalas; el leve aumento de la correlación (de −0,22 a −0,26 y de −0,25
> a −0,30) no se debe a una relación más lineal. Por ello, se mantienen en su escala original, y la forma curva se
> considera una limitación del modelo lineal que se evaluará en el diagnóstico. El puntaje de crédito y la tasa de
> interés no muestran cambios en su relación con la LGD al transformarlos.

**Seguro hipotecario — decisión (J).**

> El seguro hipotecario vale 0 en el 65,7 % de los créditos de entrenamiento, por lo que no admite el logaritmo ni
> Box-Cox. Se decidió incluirlo con dos términos: una variable indicadora de tener seguro y el porcentaje de cobertura.
> Los datos muestran ambos efectos: la LGD mediana es menor con seguro que sin él (0,384 frente a 0,578) y, entre los
> créditos asegurados, la LGD disminuye a mayor cobertura (r = −0,32). Usar solo la indicadora perdería la información
> de la cobertura, y dejar el porcentaje solo mezclaría ambos efectos en un coeficiente. Las alternativas de sumar una
> constante antes del logaritmo o agrupar en tramos se descartaron por depender de elecciones arbitrarias. Como el
> seguro se exige casi exclusivamente con LTV mayor que 80 %, su colinealidad con el LTV se evaluará con el VIF.

### Paso 6 — LGD de los créditos sin DTI vs. el resto

Fuentes: `outputs/figures/eda_06_lgd_sin_dti.png`, `outputs/tables/eda_06_lgd_sin_dti.csv` (base `lgd_2007.csv`, 4.043 créditos).
Interpretación: Amelie.

> Se comparó la LGD de los 81 créditos sin DTI, excluidos por el criterio de casos completos, con la del resto de la
> base con LGD (4.043 créditos). Ambos grupos son muy similares: en entrenamiento y validación las medias difieren en
> 0,009 y las medianas entre 0,026 y 0,035, y ni la prueba t de Welch ni la de Mann-Whitney muestran diferencias
> (p ≥ 0,75). Los créditos con DTI muestran mayor dispersión y más LGD > 1, pero con tan pocos créditos sin DTI (66 en
> entrenamiento y 15 en validación) estos porcentajes cambian mucho con uno o dos casos, por lo que la diferencia no es
> concluyente. Con muestras tan pequeñas, el problema es la imprecisión: las pruebas tienen poca capacidad para detectar
> diferencias. Excluirlos prácticamente no altera la distribución de la LGD (media de 0,5413 con ellos y 0,5415 sin
> ellos), así que el sesgo en la respuesta es bajo. La limitación principal es otra: según la guía, el código 999
> corresponde a un DTI mayor que 65 % o no disponible, por lo que podrían quedar fuera los deudores más endeudados. Como
> el modelo se estima con DTI de hasta 65 %, no debería usarse para deudores con un DTI mayor, ya que eso sería
> extrapolar fuera del rango observado.

## Texto para main.tex (sección 3)

Archivo listo para pegar: `informe/avance/seccion3_rol2.tex` (Figura 1 con su pie y un párrafo). El párrafo condensa
los textos de los pasos 1 a 6 de este reporte, sin interpretación nueva. **Pendiente:** que Diego (pasos 1–4) y
Amelie (pasos 5–6) lo aprueben antes de integrarlo.

## Uso de IA

| Herramienta | Propósito | Parte del trabajo | Verificación |
|---|---|---|---|
| Claude Code | Programación | `src/eda.py` (gráficos y tablas) | Revisión de los gráficos y cifras generadas |
| Claude Code | Aclaración de conceptos | Cómo leer media/mediana, asimetría, RIC y su relación con el error de validación | — |
| Claude Code | Redacción | Párrafo del paso 1, redactado a partir de las respuestas de Diego a un cuestionario; la IA avisó cuando una respuesta (pregunta 4) no calzaba con los datos y Diego la corrigió | Cifras contrastadas con `eda_01_*.csv` |
| Claude Code | Redacción | Párrafo del paso 2, con el mismo método (cuestionario); la IA avisó en las preguntas 2 y 3, que Diego corrigió | Cifras contrastadas con `eda_02_*.csv` |
| Claude Code | Redacción | Párrafo del paso 3, con el mismo método; la IA avisó que en la pregunta 1 faltaba el número de unidades y Diego decidió incluirlo | Cifras contrastadas con `eda_03_lgd_por_factor.csv` |
| Claude Code | Redacción | Párrafo del paso 4, con el mismo método (las 4 respuestas calzaron con los datos); la decisión de mantener los atípicos es de Diego | Cifras contrastadas con `eda_04_*.csv` |
| Claude Code | Programación | Paso 5 en `src/eda.py` (tabla de transformaciones, gráficos del monto, perfil de Box-Cox, LTV/CLTV) | Revisión de los gráficos; cifras contrastadas con `eda_05_transformaciones.csv` |
| Claude Code | Aclaración de conceptos | Lectura de histogramas, regla del logaritmo, perfil de Box-Cox, LOWESS, r de Pearson, interpretación de coeficientes según escala, transformaciones monótonas | — |
| Claude Code | Redacción | Párrafos del paso 5. **Método nuevo (desde el 14-11):** la IA entregó preguntas guía abiertas y explicó los criterios de lectura; para `mi_pct` presentó las alternativas típicas para variables con muchos ceros, con sus ventajas y desventajas. Amelie escribió su interpretación con sus palabras y eligió. La IA verificó las cifras y la lectura, avisó cuando algo no calzaba (perfil de Box-Cox: argumento circular; LTV/CLTV: la mejora de r no era nula y la tendencia no es monótona) y mejoró la redacción. Las decisiones H, I y J son de Amelie | Cifras contrastadas con `eda_05_*` |
| Claude Code | Programación | Paso 6 en `src/eda.py` (tabla y boxplots con/sin DTI, pruebas de Welch y Mann-Whitney); cálculo de la LGD con y sin los 81 | Cifras contrastadas con `eda_06_lgd_sin_dti.csv` |
| Claude Code | Redacción | Párrafo del paso 6 con el método nuevo. La IA avisó que: la diferencia en % LGD > 1 no es concluyente por el n chico; n chico implica imprecisión, no sesgo; "sesga bastante" no calzaba con los datos (la LGD casi no cambia sin los 81). La limitación por DTI > 65 % la propuso Amelie tras una pregunta guía | Cifras contrastadas con la tabla |
| Claude Code | Redacción | Párrafo de la sección 3 de `main.tex` y pie de la Figura 1 (15-11, sesión de Diego): la IA condensó los párrafos ya aprobados de los pasos 1 a 6, sin agregar interpretación nueva | Cifras contrastadas con `eda_0*.csv` y con los párrafos de los pasos 1 a 6 |
