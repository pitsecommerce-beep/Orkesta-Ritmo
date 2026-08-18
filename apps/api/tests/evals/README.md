# Evals del modulo conversacional

## Estado: listo para recibir casos reales y llave de proveedor

El modulo conversacional (`chat.py`) **no tiene proveedor de IA conectado**.
Hoy devuelve un string fijo. No hay modelo al que evaluar.

Este directorio contiene la estructura del harness de evals, con 3-5 casos
ilustrativos marcados como ejemplos estructurales. **No son evals reales.**

## Prerequisitos para activar evals reales

1. Francisco decide el proveedor (`OPENAI_API_KEY` o `ANTHROPIC_API_KEY`)
2. Se configura `LLM_PROVIDER` en variables de entorno
3. Se implementa la llamada al proveedor en `chat.py`, obligatoriamente
   pasando por `pii_masking.py` (middleware de enmascaramiento)
4. Se escriben 30-50 casos reales basados en consultas reales de
   contribuyentes RESICO PF y Arrendamiento

## Formato de caso

Cada caso es un dict con:
- `id`: identificador unico
- `categoria`: tipo de consulta (fiscal, onboarding, general, limite)
- `entrada`: mensaje del usuario
- `salida_esperada`: patron o contenido esperado en la respuesta
- `criterios`: lista de criterios de evaluacion
- `es_ejemplo_estructural`: True si es solo un ejemplo de formato

## Como correr

```bash
cd apps/api
PYTHONPATH=. python tests/evals/run_evals.py
```
