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

20. **Tarifa trimestral de Arrendamiento: `_triplicar_tarifa()` multiplica límites y cuota fija por 3, mantiene el porcentaje.** La LISR Art. 106 establece que los contribuyentes con opción trimestral aplican la tarifa mensual "multiplicando" por el número de meses. Multiplicar solo los límites y cuota fija (no el porcentaje marginal) produce el mismo resultado que sumar tres meses de pago provisional mensual, lo cual es consistente con la interpretación del SAT en su calculadora en línea.

21. **La base de datos es la fuente de verdad para tarifas.** `tarifas.py` se renombró a `tarifas_fallback.py` y solo sirve como fallback para tests sin conexión a DB. El motor acepta un parámetro `ejercicio` inyectado; cuando la API invoca el cálculo, carga las tarifas de Supabase y las pasa al motor. Un test de sincronización (`test_tarifas_sync.py`) verifica que los valores del fallback coinciden con el seed SQL, con conversión fracción→porcentaje.

22. **DB almacena tasa/porcentaje como fracción decimal (0.0100 = 1%), Python usa porcentaje (1.00 = 1%).** La columna `NUMERIC(6,4)` del esquema cabe mejor con fracciones. La capa API convierte al cargar.

## API

23. **JWT del usuario propagado a Supabase para RLS.** Cada request crea un `Client` con el Bearer token del usuario vía `client.postgrest.auth(token)`. La service role key nunca se usa para operaciones de usuario.

24. **`guest_or_auth` para endpoints públicos con contexto opcional.** El cuestionario IVA funciona sin autenticación; si hay JWT, se extrae el `user_id` para tracking.

25. **Onboarding crea tenant + membership en `confirmar-regimen`.** El paso de confirmación del régimen es el punto donde se persiste el contribuyente, no al final del flujo completo.

26. **Bóveda e.firma: RLS restringe a `propietario`, feature flag en la API.** Doble barrera: la política `user_has_role(tenant_id, 'propietario')` en la DB y `FEATURE_EFIRMA` en la API.

## Frontend

14. **Montserrat para títulos, Lora para texto corrido.** Ambas de Google Fonts, cargadas con `next/font`.

15. **Logo con filtro CSS** para generar variante oscura del SVG blanco existente. Se usa `brightness(0)` que convierte el blanco a negro, más `sepia` y `hue-rotate` para llegar a la tinta `#17120b`.

16. **Landing page como ruta principal `/`** dentro de la app Next.js, no como sitio estático separado. Simplifica el despliegue.

17. **Chat lateral como componente persistente** en el layout del panel, no como página separada. Permite usarlo en contexto de cualquier pantalla.

## Seguridad

18. **Enmascaramiento de datos PII como middleware obligatorio** en el cliente de IA. Implementado como decorador que intercepta toda llamada saliente.

19. **Bóveda e.firma completa pero detrás de feature flag** `FEATURE_EFIRMA=false`. La estructura de cifrado existe, la interfaz de carga no se muestra.

## Corrección 1.2 — Bloque 5

27. **`tipo_deduccion` default en `PerfilFiscal`**: Cambiado de `"ciega"` a `"opcional"`. El valor `"ciega"` no existe en la ley; el término correcto es "deducción opcional del 35%" (Art. 115 LISR).

28. **`isr_a_pagar` → `isr_a_cargo`**: Renombrado en `DesgloseISR`, motores (resico_pf, resico_pm, arrendamiento), y todos los tests. "ISR a cargo" es el término del SAT para el impuesto resultante después de restar retenciones.

29. **RESICO PM eliminado de todos los selectores de UI** (landing, onboarding, configuración, cuenta, IntroQuestionnaire): Aunque la desactivación formal del motor es Bloque 1, los selectores de régimen no deben ofrecer esta opción al usuario.

30. **"Obtener línea de captura" → "Presenta en el SAT"** en documentos/page.tsx: Ritmo no genera líneas de captura; solo prepara la declaración.

31. **"ISR — Pago definitivo" → "ISR — Desglose del periodo"** en detalle de periodo: El texto anterior asumía RESICO (pago definitivo). Para arrendamiento son pagos provisionales. El título neutro aplica a ambos regímenes.

32. **Fixtures de test actualizados**: `perfil_arrendamiento` y `perfil_arrendamiento_trimestral` en conftest.py usan `tipo_deduccion="opcional"` en lugar de `"ciega"`, consistente con el nuevo default.

## Corrección 1.2 — Bloque 1

33. **RESICO PM deshabilitado con `RegimenEnValidacionError`**: El engine lanza esta excepción antes de intentar calcular. El módulo `resico_pm.py` se conserva para cuando se implemente la tarifa correcta, pero no es invocado.

34. **Eliminado fallback de estimación en RESICO PF**: Cuando el ingreso excede todos los tramos, `impuesto_determinado` queda en 0 y se genera alerta. No se aplica la tasa del último tramo como estimación — producir un número incorrecto es peor que no producir ninguno.

35. **Tests de RESICO PM reescritos**: Los 8 tests directos del motor se reemplazaron por 2 tests que verifican que el engine rechaza RESICO PM con `RegimenEnValidacionError`.

## Corrección 1.2 — Bloque 7

36. **Validación de tarifas movida a cada función de cálculo**: `calcular_isr_resico_pf` y `calcular_isr_arrendamiento` ahora validan que reciben tarifas no vacías y lanzan `EjercicioNoDisponibleError` directamente. El engine mantiene su validación como segunda línea de defensa. IVA no usa tarifas, no necesita esta validación.
