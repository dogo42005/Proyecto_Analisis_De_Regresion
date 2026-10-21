# Proyecto Análisis de Regresión — LGD en créditos hipotecarios

Proyecto final del curso **Análisis de Regresión (EYP2307 / EYP230i, PUC Chile, 2º semestre 2026)**,
profesor Ricardo Olea.

## La idea

Estimar la **pérdida dado el incumplimiento (LGD, *Loss Given Default*)** de créditos hipotecarios
a partir de características conocidas al originar el crédito (puntaje de crédito, LTV, DTI, tasa,
tipo de propiedad, propósito del crédito, etc.).

- **Respuesta (continua):** `LGD = actual_loss / zero_balance_removal_upb`, para créditos que cerraron
  con pérdida (`zero_balance_code` ∈ {02, 03, 09, 15}) y con `actual_loss` informado.
- **Datos:** [Freddie Mac Single-Family Loan-Level Dataset](https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset),
  muestra de créditos originados en 2007 (50.000 créditos, desempeño mensual hasta marzo 2026).
- **Validación:** 80/20 respetando el orden temporal (el 20 % de validación es el tramo más reciente).

Estado actual: **etapa 1 — infraestructura de datos** (carga, limpieza, conteos). Ver `cleaning_log.md`.

## Integrantes

| Nombre | Correo |
|---|---|
| Diego Olivares | |
| _(por completar)_ | |
| _(por completar)_ | |
| _(por completar)_ | |

## Hitos

| Hito | Fecha | Entrega |
|---|---|---|
| 1. Inscripción y propuesta (1 pág.) | viernes 23 de octubre | Fuente, respuesta, predictores, pregunta |
| 2. Avance (2 págs.) | lunes 16 de noviembre | EDA, limpieza, modelo preliminar con diagnóstico |
| 3. Póster A0 + defensa oral | martes 15 de diciembre, 08:20 | PDF en Canvas + declaración de uso de IA |

## Distribución de archivos

```
.
├── README.md                 este archivo
├── CLAUDE.md                 contexto del proyecto para el asistente de IA (Claude Code)
├── cleaning_log.md           registro de cada decisión de limpieza (qué, cuántos casos, por qué)
├── requirements.txt          versiones de paquetes de Python
├── Contexto/                 enunciado del proyecto (PDF del curso)
├── data/
│   ├── raw/                  datos originales, NO se modifican
│   │   ├── sample_2007/
│   │   │   ├── sample_orig_2007.txt   originación: 1 fila por crédito (31 campos, sin encabezado, sep "|")
│   │   │   └── sample_perf_2007.txt   desempeño mensual (35 campos, sin encabezado, sep "|")
│   │   ├── file_layout_july_2026.xlsx       nombres y posiciones de las columnas
│   │   └── general_user_guide_july_2026.pdf definiciones y códigos de cada variable
│   └── processed/
│       └── lgd_2007.csv      base con LGD (generada por src/build_dataset.py)
├── src/
│   └── build_dataset.py      carga, une, limpia, calcula LGD y reporta conteos
├── notebooks/                análisis exploratorio y modelos (próximas etapas)
└── outputs/
    ├── build_dataset_report.txt  reporte de conteos del último build
    └── figures/              gráficos
```

Los `.txt` de `data/raw/` **no se suben a GitHub** (pesan ~350 MB). Para reproducir: descargar
`sample_2007.zip` desde la página de Freddie Mac (requiere registro), descomprimir en `data/raw/sample_2007/`.

## Cómo correr

```bash
pip install -r requirements.txt      # si falta algún paquete
python src/build_dataset.py          # ~30 segundos
```

## Uso de IA

Según el enunciado, la IA se permite solo como apoyo en programación/depuración, redacción de textos ya
escritos por el grupo y aclaración de conceptos. Se usó Claude Code para escribir el código de carga y
limpieza de datos. El análisis estadístico, las decisiones metodológicas, la interpretación y las
conclusiones son del grupo.
