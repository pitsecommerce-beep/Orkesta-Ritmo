# Pendientes

Elementos que quedaron fuera de la iteración 1 o bloqueados por dependencias externas.

## Bloqueados por credenciales o servicios externos

- [ ] **Conexión Supabase real.** Se necesitan `SUPABASE_URL`, `SUPABASE_ANON_KEY` y `SUPABASE_SERVICE_ROLE_KEY` para ejecutar las migraciones. Las migraciones están listas en `supabase/migrations/`. Los 15 routers de la API ya están conectados a Supabase con JWT propagation — solo falta ejecutar las migraciones y configurar las variables de entorno.
- [ ] **Proveedor de IA.** Se necesita `OPENAI_API_KEY` o `ANTHROPIC_API_KEY`. El módulo de IA está detrás de configuración `LLM_PROVIDER`.
- [ ] **Despliegue en Railway.** Se necesita crear los tres servicios (`web`, `api`, `redis`) y configurar las variables de entorno. Los `Dockerfile` y `railway.json` están listos.

## Activos de marca

- [ ] **SVG vectoriales del logo.** Los archivos actuales en `apps/web/public/brand/` son PNG con trazo blanco sobre fondo transparente. Se necesitan los SVG originales para un componente `<Logo>` limpio. Mientras tanto se usa un filtro CSS para producir la variante en tinta.

## Motor de cálculo

- [x] **Tarifa Art 96 ejercicio 2026.** ~~El sistema muestra alerta cuando se intenta calcular un periodo 2026 sin tarifa capturada.~~ Resuelto: las tarifas 2026 están en el catálogo normativo (`catalogo_data.py`) con factor de actualización 1.1321. El motor las consume vía `catalogo_adapter.resolver_ejercicio()`. Verificado con tests end-to-end para enero y marzo 2026.
- [ ] **Deducciones comprobables en Arrendamiento.** Solo se implementó `tipo_deduccion = 'opcional'` (35%). La opción comprobable queda deshabilitada en la interfaz.
- [ ] **Régimen de Plataformas Tecnológicas.** Estructura de datos para complemento existe en el parser, pero no hay cálculo ni flujo.
- [ ] **Deprecar esquema viejo de tarifas (`ejercicios`/`tarifas_resico`/`tarifas_art96`).** El worker de cálculo ya usa el catálogo normativo como fuente de verdad. Las tablas viejas (migración 00003) no recibieron datos 2026 — se mantienen por compatibilidad con routers que las consultan directamente. Deuda técnica: migrar esos routers para leer del catálogo y eventualmente eliminar las tablas viejas. No se resolvió en esta sesión porque requiere verificar qué routers y qué consultas dependen de esas tablas.
- [ ] **Infraestructura de cola RQ para workers.** `calculo_worker.py` y `documento_worker.py` ahora se invocan via `BackgroundTasks` de FastAPI (sincrono dentro del proceso del API). Funcional para volumen bajo pero no escala: documentos con OCR pesado (Santander, ~15s por PDF) bloquean un thread del servidor. Migrar a RQ con Redis cuando el volumen lo justifique. Los routers ya no mienten sobre el estado ("processing" en vez de "enqueued").

## Parseo y calibración con documentos reales

### Constancia de situación fiscal

El módulo `constancia.py` tiene extracción completa vía pdfplumber. El **único PDF real calibrado** es de un contribuyente con Plataformas Tecnológicas + Sueldos — un régimen que el motor de cálculo **no soporta**. Cero fixtures reales existen para los cuatro regímenes del MVP.

Estado por régimen:

- [ ] **Constancia RESICO PF (solo)** — pendiente de PDF real de Francisco
- [ ] **Constancia RESICO PF + Sueldos** — pendiente de PDF real
- [ ] **Constancia Arrendamiento (solo)** — pendiente de PDF real
- [ ] **Constancia Arrendamiento + Sueldos** — pendiente de PDF real
- [x] **Constancia Plataformas Tecnológicas** — calibrada, pero el motor no soporta este régimen

Otros casos pendientes (no bloquean MVP):
  - [ ] Constancia PF con régimen dado de baja (no vigente)
  - [ ] Constancia PM (validar 12 caracteres de RFC)
  - [ ] Constancia con formato de tabla diferente entre años del SAT
  - [ ] Constancia con obligaciones que incluyan periodicidad bimestral

Ruta del fixture: `packages/tax-engine/tests/fixtures/reales/`
Script de calibración: `packages/tax-engine/scripts/calibrar_contra_reales.py`

### CFDI (parser XML)

El parser de CFDI tiene **cero fixtures reales**. Los 5 fixtures existentes son sintéticos (RFC genéricos `XAXX010101000`/`XBXX020202000`, emisor `"EMPRESA SINTETICA SA DE CV"`). 712+ líneas de tests pasan contra datos fabricados.

- [ ] **CFDI de ingreso real (PUE)** — pendiente de XML real de Francisco
- [ ] **CFDI de ingreso real (PPD)** — pendiente de XML real
- [ ] **Complemento de pago real** — pendiente de XML real
- [ ] **Recibo de nómina real** — pendiente de XML real (si aplica)

Ruta del fixture: `packages/cfdi-parser/tests/fixtures/reales/`
Script de calibración: `packages/cfdi-parser/scripts/calibrar_contra_reales.py`

### Estados de cuenta bancarios

El parser bancario tiene **cero fixtures reales**. El fixture `mercado_pago_sintetico.txt` contiene datos fabricados (titular inventado, CLABE de relleno). Solo Mercado Pago está implementado; esqueletos de Santander, BBVA, Nu y Revolut creados.

- [ ] **Estado de cuenta real de Mercado Pago** — pendiente de PDF/TXT real de Francisco
- [x] **Adaptador Santander (debito + credito).** Implementado con OCR via tesseract. Requiere `tesseract-ocr` y `tesseract-ocr-spa` instalados en el sistema. Validado contra fixtures sinteticos rasterizados. Pendiente de calibracion con documentos reales de Francisco.
- [ ] **Calibracion Santander con documentos reales** — cuando Francisco entregue sus estados de cuenta reales, van a `tests/fixtures/reales/` y se calibra contra ellos.
- [ ] **CONFIRMAR CON CONTADOR: tratamiento fiscal de movimientos TDC.** Los movimientos de tarjeta de credito no son equivalentes a flujo de efectivo. El criterio de "efectivamente pagado" para IVA acreditable tiene reglas propias. Ademas, el pago del estado de cuenta desde debito y los cargos de la TDC representan el mismo gasto visto dos veces — riesgo de duplicar gastos si ambos documentos se cargan al mismo periodo. NO implementar regla de deduccion sin confirmacion del contador.
- [ ] **Estado de cuenta de otro banco** — pendiente de que Francisco elija banco

Ruta del fixture: `packages/bank-parser/tests/fixtures/reales/`
Script de calibración: `packages/bank-parser/scripts/calibrar_contra_reales.py`

### Otros

- [ ] **Descarga masiva vía PAC.** La abstracción `CfdiSource` existe con `PacSource` que levanta `NotImplementedError`. Se necesita contrato con un PAC autorizado.

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

## Capa de sesión multi-tenant y permisos (Etapa 3)

- [x] **Selector de tenant activo.** `TenantProvider` reemplaza el hook roto que usaba `.maybeSingle()`. Soporta usuarios con múltiples membresías. El selector solo aparece en el sidebar cuando `tenants.length > 1`. Persistencia en `localStorage`.
- [x] **Permisos por rol en UI.** `usePermissions()` deriva capacidades del rol (`propietario`, `contador`, `lectura`). Aplicado a: documentos, CFDIs, extractos, cuenta, configuración, periodos (detalle). Botones deshabilitados con tooltip, nunca ocultos.
- [x] **Unificación de carga de documentos.** Wizard en `/dashboard/documentos` es el punto de entrada canónico. CFDIs y extractos redirigen al wizard. Constancia agregada como paso 0 del wizard.
- [x] **RFC y régimen read-only en cuenta.** Derivados de la constancia, no editables manualmente.
- [x] **Configuración con permisos.** Invite gated a propietario/contador, edición de workspace gated a propietario/contador, e.firma gated a propietario.
- [x] **RLS gap corregido.** `perfiles_obligacion` ahora tiene RLS habilitado con política de lectura pública (migración 00010).
- [x] **Build limpio.** `npm run build` pasa sin errores de TypeScript con todos los cambios de Etapa 3.
