# Modelo de seguridad - Orkesta Ritmo

## Clasificación de datos

| Nivel | Datos | Tratamiento |
|-------|-------|-------------|
| **Crítico** | e.firma (.key, .cer, contraseña) | Cifrado de sobre AES-256-GCM, solo en memoria del worker, nunca en logs ni endpoints |
| **Alto** | RFC, CLABE, estados de cuenta, CFDI | Cifrado en tránsito (TLS), cifrado en reposo (Supabase), RLS por tenant |
| **Medio** | Correo electrónico, nombre | Protegido por autenticación, sujeto a derechos ARCO |
| **Bajo** | Parámetros fiscales, tarifas | Información pública del SAT |

## Bóveda de e.firma

### Arquitectura de cifrado

```
Contribuyente → [archivo .key/.cer + contraseña]
                        ↓
              AES-256-GCM con Data Key única
                        ↓
              Data Key cifrada con Master Key
                        ↓
              Binarios cifrados → Supabase Storage (bucket privado)
              Data Key cifrada → tabla boveda_efirma
              Master Key → variable de entorno EFIRMA_MASTER_KEY
```

Cada contribuyente tiene su propia Data Key. Comprometer una no expone a los demás.

### Procedimiento de rotación de llave maestra

1. Generar nueva llave: `python -c "import secrets; print(secrets.token_hex(32))"`
2. En ventana de mantenimiento:
   a. Leer todas las Data Keys cifradas con la llave actual
   b. Descifrar cada Data Key con la llave actual
   c. Re-cifrar cada Data Key con la nueva llave
   d. Actualizar las filas en `boveda_efirma`
   e. Actualizar `EFIRMA_MASTER_KEY` en Railway
3. Verificar que al menos un descifrado funcione con la nueva llave
4. Registrar la rotación en la bitácora con fecha y responsable

**Frecuencia recomendada:** cada 90 días o ante sospecha de compromiso.

### Controles

- **Sin endpoints de exportación.** No existe ninguna ruta de API que devuelva bytes de la bóveda. Hay una prueba automatizada que recorre todas las rutas y falla si alguna puede devolver material cifrado.
- **Descifrado solo en worker.** El material se descifra exclusivamente en el proceso worker de RQ, en memoria, para la operación específica (futura firma de declaración).
- **Bitácora inmutable.** Cada acceso a la bóveda se registra con: momento, proceso solicitante, finalidad, IP de origen.
- **Consentimiento expreso.** Se requiere aceptación con hash del texto y sello de tiempo antes de cualquier carga.
- **Borrado permanente.** Destruye la Data Key del contribuyente, no solo el archivo. Los binarios en Storage quedan irrecuperables.
- **Nunca en logs.** Middleware de logging excluye cualquier campo que contenga material de la bóveda. Las trazas de excepción se sanitizan.

### Debilidad conocida del MVP

La llave maestra (`EFIRMA_MASTER_KEY`) vive como variable de entorno en Railway. Las personas con acceso al proyecto de Railway pueden leerla. Esta es la debilidad aceptada del MVP.

**Mitigación a corto plazo:**
- Limitar el acceso al proyecto de Railway al mínimo de personas
- Auditar quién tiene acceso mensualmente
- No compartir la llave por canales no cifrados

**Mitigación a mediano plazo:**
- Migrar a un HSM o servicio de gestión de llaves (AWS KMS, GCP KMS, Azure Key Vault)
- Implementar envelope encryption con el KMS como root of trust

### Personas con acceso al proyecto Railway

| Persona | Rol | Desde |
|---------|-----|-------|
| (Pendiente de registrar) | | |

## Enmascaramiento de datos para IA

Todo tráfico saliente hacia proveedores de IA pasa por un middleware obligatorio que:

1. Detecta y enmascara: RFC (patrón `[A-ZÑ&]{3,4}\d{6}[A-Z\d]{3}`), CLABE (18 dígitos), números de cuenta (10+ dígitos consecutivos), nombres de titulares.
2. Reemplaza con tokens reversibles para la sesión pero irreversibles fuera de ella.
3. Registra el evento de enmascaramiento en `consumo_ia`.

**La e.firma, su contraseña y cualquier credencial fiscal nunca se envían a un proveedor de IA. Sin excepciones.**

Hay una prueba automatizada que:
- Genera payloads con RFC y CLABE embebidos
- Los pasa por el middleware
- Verifica que ningún dato PII aparezca en la salida

## Row Level Security

Todas las tablas con `tenant_id` tienen RLS habilitado. Las políticas garantizan que un usuario autenticado solo ve datos de los tenants donde tiene membresía.

Hay una prueba automatizada que:
- Crea dos tenants con usuarios distintos
- Intenta acceder a datos cruzados
- Verifica que el acceso es denegado

## Autenticación

- Supabase Auth con magic link por correo. Sin contraseñas.
- Sesiones de invitado con token de vigencia de 7 días.
- Purga automática de sesiones expiradas.

## HTTPS

Todo el tráfico entre cliente y servidor va sobre TLS. Railway provee certificados automáticos.

## Dependencias

- Auditoría de dependencias con `npm audit` y `pip audit` en CI.
- Actualización de dependencias al menos mensualmente.
