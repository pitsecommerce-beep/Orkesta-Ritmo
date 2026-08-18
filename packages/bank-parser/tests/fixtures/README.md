# Fixtures de test — bank-parser

## Fixtures sinteticos (en git)

| Archivo                       | Tipo                         | Estado       |
|-------------------------------|------------------------------|--------------|
| `mercado_pago_sintetico.txt`  | Estado de cuenta Mercado Pago | Sintetico   |

El archivo `mercado_pago_sintetico.txt` contiene datos fabricados: titular
inventado, CLABE de relleno, movimientos generados. Sirve para probar la logica
de parseo y deteccion de espejos, pero **no es calibracion real**.

## Fixtures reales (`reales/`)

El directorio `reales/` esta excluido de git (`.gitignore`). Aqui se colocan
estados de cuenta reales para calibrar el parser contra documentos bancarios.

### Archivos necesarios para calibracion completa

| Archivo esperado              | Descripcion                                  | Estado    |
|-------------------------------|----------------------------------------------|-----------|
| `mercado_pago_real.pdf`       | Estado de cuenta real de Mercado Pago (PDF)  | Pendiente |
| `mercado_pago_real.txt`       | Estado de cuenta real de Mercado Pago (TXT)  | Pendiente |

Los adaptadores de Santander, BBVA, Nu y Revolut estan como esqueletos — no hay
calibracion posible hasta que se implemente la logica de parseo.

### Reglas

1. **Nunca subir estados de cuenta reales al repositorio.** Contienen nombre
   del titular, CLABE, saldos y movimientos reales.
2. **Los tests que dependen de fixtures reales se saltan automaticamente.**
3. Para agregar un fixture, copie el archivo real a `reales/`.

### Como calibrar

```bash
cd packages/bank-parser
PYTHONPATH=src python scripts/calibrar_contra_reales.py
```
