---
name: max-skill-factory
description: "Trigger: max-skill-factory, generar skill max, crear skill dominio. Genera skills LLM-first especializadas para portar código externo a Max MSP."
license: Apache-2.0
metadata:
  author: "OptimizandoParaMaxSDK"
  version: "1.1"
---

# Max Skill Factory

## Activation Contract

Cargar cuando el scout de proyectos identifique un dominio técnico especializado (microtonalismo, afinaciones, geometría de trastes, protocolos de síntesis) que requiera una skill LLM-first dedicada para gobernar la traducción a Max MSP.

## Hard Rules

- **Estándar Canónico LLM-first**: La skill generada DEBE contener exactamente las 7 secciones obligatorias en orden: Frontmatter, Activation Contract, Hard Rules, Decision Gates, Execution Steps, Output Contract, References.
- **Formato Estricto de Frontmatter**:
  - `name`, `description` en una sola línea física entre comillas dobles, comenzando con `Trigger: `, <= 160 caracteres (máximo absoluto 250).
  - Incluir `license` y bloque `metadata` (`author`, `version`). Prohibido agregar `Keywords`.
- **Presupuesto de Cuerpo**: Mantener el cuerpo entre 180 y 450 tokens (máximo 700). Extraer tutoriales y ejemplos a `references/` o `assets/`.
- **Tono Operativo Imperativo**: Redactar directivas imperativas de ejecución dirigidas al modelo; prohibido incluir explicaciones o tutoriales para humanos.

## Decision Gates

| Requerimiento del Proyecto Fuente | Tipo de Skill a Generar | Enfoque Contractual |
| :--- | :--- | :--- |
| Afinaciones / microtonalismo / acústica | Auditor de afinación y armónicos | Ratios, normalización de octava y cents |
| Grillas interactivas / trastes / Bézier | Experto en geometría vectorial | Coordenadas JGraphics (`ui_operator`) o `jsui` |
| Protocolos / ruteo de señales / DSP | Validador de contratos y tipos | Mapeo estricto de inlets/outlets y buffers |

## Execution Steps

1. Leer el reporte técnico y requerimientos de dominio generados por `max-project-scout`.
2. Aislar la responsabilidad técnica única de la skill a construir.
3. Redactar el contrato operativo, reglas duras, compuertas de decisión binarias y pasos de ejecución.
4. Extraer tablas extensas o conceptos de fondo hacia subdirectorios locales `references/` o `assets/`.
5. Guardar en `skills/<nombre-skill>/SKILL.md` o `meta-skills/<nombre-skill>/SKILL.md`.
6. Validar que el frontmatter YAML sea sintácticamente válido y cumpla la longitud de descripción.

## Output Contract

- Archivo `SKILL.md` funcional estructurado bajo la guía LLM-first.
- Archivos locales de soporte en `references/` o `assets/` si fueron necesarios.

## References

- `references/factory-standards.md` — Reglas de aislamiento de responsabilidades y checklist de calidad.
