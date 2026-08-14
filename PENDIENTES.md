# Pendientes

Elementos que quedaron fuera de la iteración 1 o bloqueados por dependencias externas.

## Bloqueados por credenciales o servicios externos

- [ ] **Conexión Supabase real.** Se necesitan `SUPABASE_URL`, `SUPABASE_ANON_KEY` y `SUPABASE_SERVICE_ROLE_KEY` para ejecutar las migraciones. Las migraciones están listas en `supabase/migrations/`. Los 15 routers de la API ya están conectados a Supabase con JWT propagation — solo falta ejecutar las migraciones y configurar las variables de entorno.
- [ ] **Proveedor de IA.** Se necesita `OPENAI_API_KEY` o `ANTHROPIC_API_KEY`. El módulo de IA está detrás de configuración `LLM_PROVIDER`.
- [ ] **Despliegue en Railway.** Se necesita crear los tres servicios (`web`, `api`, `redis`) y configurar las variables de entorno. Los `Dockerfile` y `railway.json` están listos.

## Activos de marca

- [ ] **SVG vectoriales del logo.** Los archivos actuales en `apps/web/public/brand/` son PNG con trazo blanco sobre fondo transparente. Se necesitan los SVG originales para un componente `<Logo>` limpio. Mientras tanto se usa un filtro CSS para producir la variante en tinta.

## Motor de cálculo

- [ ] **Tarifa Art 96 ejercicio 2026.** El sistema muestra alerta cuando se intenta calcular un periodo 2026 sin tarifa capturada. Un humano debe capturar la tabla cuando el SAT la publique. Banner de alerta visible en el dashboard (`TarifaAlertBanner`). El motor lanza `EjercicioNoDisponibleError` si se intenta calcular con tarifas vacías.
- [ ] **Deducciones comprobables en Arrendamiento.** Solo se implementó `tipo_deduccion = 'ciega'` (35%). La opción comprobable queda deshabilitada en la interfaz.
- [ ] **Régimen de Plataformas Tecnológicas.** Estructura de datos para complemento existe en el parser, pero no hay cálculo ni flujo.

## Parseo

- [ ] **Parsing de Constancia de Situación Fiscal.** El módulo `constancia.py` tiene la estructura de extracción y el mapeo de claves SAT, pero `extraer_constancia()` necesita un PDF real del SAT para calibrar los patrones regex. Los PDFs del SAT varían entre años. Subir un documento real y ajustar los patrones.
- [ ] **Descarga masiva vía PAC.** La abstracción `CfdiSource` existe con `PacSource` que levanta `NotImplementedError`. Se necesita contrato con un PAC autorizado.
- [ ] **Adaptadores bancarios.** Solo Mercado Pago está implementado. Esqueletos de Santander, BBVA, Nu y Revolut creados.

## Integraciones

- [ ] **YCloud / WhatsApp.** El simulador de WhatsApp funciona en la web pero no hay conexión real. El motor conversacional es agnóstico al canal.
- [ ] **Cobro y procesamiento de pagos.** Los planes se muestran y la intención de compra se registra, pero no hay pasarela de pago conectada.

## Legal

- [ ] **Aviso de privacidad definitivo.** Se publicó un marcador de posición en `/privacidad`. Requiere revisión por abogado contra la LFPDPPP vigente. Banner de revisión visible en el dashboard (`PrivacyReviewBanner`).
- [ ] **Términos y condiciones definitivos.** Marcador de posición en `/terminos`. Incluye la frase de que Ritmo no es despacho contable. Mismo banner de revisión cubre ambos documentos.

## Seguridad

- [ ] **Auditoría de seguridad externa** antes del lanzamiento público.
- [ ] **Rotación de llave maestra de e.firma.** Procedimiento documentado en `SEGURIDAD.md`, pendiente de primera ejecución.
- [ ] **Certificado SSL propio** para el dominio de producción.
