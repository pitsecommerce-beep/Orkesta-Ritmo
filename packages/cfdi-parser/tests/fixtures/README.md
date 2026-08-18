# Fixtures de test — cfdi-parser

## Fixtures sinteticos (en git)

Los archivos en este directorio son **sinteticos** — fabricados para probar la
logica de parseo. Contienen RFC genericos del SAT (`XAXX010101000`, `XBXX020202000`)
y datos inventados. No representan documentos reales.

| Archivo            | Tipo                      | Estado       |
|--------------------|---------------------------|--------------|
| `ingreso_pue.xml`  | CFDI 4.0 Ingreso (PUE)    | Sintetico    |
| `ingreso_ppd.xml`  | CFDI 4.0 Ingreso (PPD)    | Sintetico    |
| `pago_20.xml`      | Complemento de Pago 2.0   | Sintetico    |
| `nomina_12.xml`    | Complemento Nomina 1.2    | Sintetico    |
| `retencion_11.xml` | Retenciones 1.1            | Sintetico    |

## Fixtures reales (`reales/`)

El directorio `reales/` esta excluido de git (`.gitignore`). Aqui se colocan
CFDI reales para calibrar el parser contra documentos del SAT.

### Archivos necesarios para calibracion completa

| Archivo esperado            | Descripcion                                  | Estado   |
|-----------------------------|----------------------------------------------|----------|
| `ingreso_pue_real.xml`      | CFDI de ingreso real con pago en una sola exhibicion | Pendiente |
| `ingreso_ppd_real.xml`      | CFDI de ingreso real con pago en parcialidades | Pendiente |
| `pago_real.xml`             | Complemento de pago real                     | Pendiente |
| `nomina_real.xml`           | Recibo de nomina real (si aplica)            | Pendiente |

### Reglas

1. **Nunca subir XMLs reales al repositorio.** Contienen RFC, nombre, domicilio
   fiscal y datos bancarios del contribuyente.
2. **Los tests que dependen de fixtures reales se saltan automaticamente** si el
   archivo no existe (`@pytest.mark.skipif`).
3. Para agregar un fixture, copie el XML real a `reales/`. No lo renombre con
   datos que identifiquen al contribuyente.

### Como calibrar

```bash
cd packages/cfdi-parser
PYTHONPATH=src python scripts/calibrar_contra_reales.py
```
