# Decisiones de implementación

Registro de decisiones tomadas durante la construcción de Orkesta Ritmo, iteración 1.

## Base de datos

1. **UUIDs como llaves primarias en todas las tablas.** Facilita la generación distribuida sin coordinación y es consistente con Supabase Auth que ya usa UUIDs.

2. **`tenant_id` en todas las tablas de datos desde la primera migración**, incluso en `movimientos_bancarios` que ya tiene `extracto_id`. La redundancia permite políticas RLS directas sin joins.

3. **RLS con función helper `get_user_tenant_ids()`.** Centraliza la lógica de membresía. Marcada como `SECURITY DEFINER` y `STABLE` para que Postgres la optimice en el plan de consulta.

4. **Cuestionario IVA como grafo en base de datos** con nodos, opciones y transiciones. Los IDs de nodo son strings legibles (P1, A2, V-ALI) en vez de UUIDs para facilitar la referencia en código y documentación.

5. **Ejercicio 2025 como único ejercicio con tarifas completas.** El 2026 se deja vacío intencionalmente con alerta visible, como indica la especificación.

6. **Tarifa Art 96: último tramo sin límite superior (NULL).** La consulta usa `limite_superior IS NULL OR base <= limite_superior`.

## Arquitectura

7. **Monorepo sin herramienta de workspace** (ni Turborepo, ni Lerna). Los tres paquetes Python son independientes con sus propios `pyproject.toml`. La app web es Next.js independiente. La complejidad de un tool de monorepo no se justifica aún.

8. **FastAPI como API principal con workers RQ** en el mismo contenedor. Un solo Dockerfile con dos entrypoints (`api` y `worker`).

9. **pdfplumber para extracción de estados de cuenta** en vez de tabula-py. Es Python puro, no requiere Java, más fácil de empaquetar en Docker.

10. **lxml para parseo de CFDI** en vez de xml.etree. Mejor manejo de namespaces y validación de esquema.

## Motor de cálculo

11. **Todas las tasas se leen del documento, nunca se asumen.** Si la tasa difiere de la esperada, el periodo se marca para revisión en vez de fallar.

12. **IVA acreditable defaults a cero cuando no se puede probar el pago.** El periodo se marca `requiere_revision`. Nunca se estima.

13. **Arrendamiento: base del periodo es el ingreso del mes, no acumulado desde enero.** Esto contradice algunas guías pero es el tratamiento correcto para pagos provisionales mensuales.

## Frontend

14. **Montserrat para títulos, Lora para texto corrido.** Ambas de Google Fonts, cargadas con `next/font`.

15. **Logo con filtro CSS** para generar variante oscura del SVG blanco existente. Se usa `brightness(0)` que convierte el blanco a negro, más `sepia` y `hue-rotate` para llegar a la tinta `#17120b`.

16. **Landing page como ruta principal `/`** dentro de la app Next.js, no como sitio estático separado. Simplifica el despliegue.

17. **Chat lateral como componente persistente** en el layout del panel, no como página separada. Permite usarlo en contexto de cualquier pantalla.

## Seguridad

18. **Enmascaramiento de datos PII como middleware obligatorio** en el cliente de IA. Implementado como decorador que intercepta toda llamada saliente.

19. **Bóveda e.firma completa pero detrás de feature flag** `FEATURE_EFIRMA=false`. La estructura de cifrado existe, la interfaz de carga no se muestra.
