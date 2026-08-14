# Fixtures de test

Este directorio contiene archivos PDF reales del SAT usados como fixtures
para calibrar y verificar la extracción de datos.

## Archivos esperados

| Archivo               | Descripción                                | Requerido |
|-----------------------|--------------------------------------------|-----------|
| `constancia_pf.pdf`   | Constancia de persona física               | Sí        |
| `constancia_pm.pdf`   | Constancia de persona moral                | Opcional  |

## Reglas

1. **Nunca subir PDFs al repositorio.** Contienen PII (RFC, nombre, CURP, domicilio).
   El `.gitignore` ya excluye `*.pdf` y `*_expected.json` de este directorio.

2. **Los tests que dependen de fixtures se saltan automáticamente** si el archivo
   no existe (`@pytest.mark.skipif`). Los tests del catálogo, normalización y
   periodicidad usan datos literales y siempre corren.

3. Para agregar un fixture, copia el PDF real a este directorio. No lo renombres
   con datos que identifiquen al contribuyente.

## Formato de `*_expected.json` (opcional)

Si se desea, se puede acompañar cada PDF de un JSON con los valores esperados
para validación automatizada:

```json
{
  "rfc": "...",
  "tipo_persona": "fisica",
  "regimenes": [{"clave_sat": "606", "descripcion": "..."}],
  "obligaciones_count": 5
}
```
