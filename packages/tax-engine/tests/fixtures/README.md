# Fixtures de test — tax-engine

## Fixtures de constancia (en git: ninguno)

Los PDFs de constancia de situacion fiscal contienen PII (RFC, nombre, CURP,
domicilio) y estan excluidos de git via `.gitignore`.

### Estado de calibracion por regimen

| Regimen                          | Fixture calibrado | Estado          |
|----------------------------------|-------------------|-----------------|
| RESICO PF (solo)                 | No                | Pendiente       |
| RESICO PF + Sueldos              | No                | Pendiente       |
| Arrendamiento (solo)             | No                | Pendiente       |
| Arrendamiento + Sueldos          | No                | Pendiente       |
| Plataformas Tecnologicas         | Si*               | No soportado por motor |

*El unico PDF real calibrado (`constancia_pf.pdf`, excluido del repo) es de un
contribuyente con Plataformas Tecnologicas + Sueldos — un regimen que el motor
de calculo no soporta. No sirve como calibracion para el MVP.

## Fixtures reales (`reales/`)

El directorio `reales/` esta excluido de git (`.gitignore`). Aqui se colocan
PDFs de constancias reales del SAT.

### Archivos necesarios para calibracion completa

| Archivo esperado                 | Descripcion                                  | Estado    |
|----------------------------------|----------------------------------------------|-----------|
| `constancia_resico_pf.pdf`       | Constancia PF con RESICO como unico regimen  | Pendiente |
| `constancia_resico_sueldos.pdf`  | Constancia PF con RESICO + Sueldos           | Pendiente |
| `constancia_arrendamiento.pdf`   | Constancia PF con Arrendamiento solo         | Pendiente |
| `constancia_arrend_sueldos.pdf`  | Constancia PF con Arrendamiento + Sueldos    | Pendiente |

### Reglas

1. **Nunca subir PDFs al repositorio.** Contienen PII (RFC, nombre, CURP, domicilio).
   El `.gitignore` ya excluye `*.pdf` y `*_expected.json` de este directorio.

2. **Los tests que dependen de fixtures se saltan automaticamente** si el archivo
   no existe (`@pytest.mark.skipif`). Los tests del catalogo, normalizacion y
   periodicidad usan datos literales y siempre corren.

3. Para agregar un fixture, copie el PDF real a este directorio o a `reales/`.
   No lo renombre con datos que identifiquen al contribuyente.

### Como calibrar

```bash
cd packages/tax-engine
PYTHONPATH=src python scripts/calibrar_contra_reales.py
```

## Formato de `*_expected.json` (opcional)

Si se desea, se puede acompanar cada PDF de un JSON con los valores esperados
para validacion automatizada:

```json
{
  "rfc": "...",
  "tipo_persona": "fisica",
  "regimenes": [{"clave_sat": "606", "descripcion": "..."}],
  "obligaciones_count": 5
}
```
