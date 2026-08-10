-- Orkesta Ritmo - Initial Schema Migration
-- All tables include tenant_id for RLS isolation from day one.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE regimen_fiscal AS ENUM (
    'RESICO_PF',
    'RESICO_PF_SUELDOS',
    'ARRENDAMIENTO',
    'ARRENDAMIENTO_SUELDOS',
    'RESICO_PM'
);

CREATE TYPE tipo_persona AS ENUM ('fisica', 'moral');

CREATE TYPE estado_periodo AS ENUM (
    'borrador',
    'calculado',
    'contrastado',
    'preparado',
    'presentado',
    'cerrado',
    'con_diferencia',
    'requiere_revision',
    'omitido'
);

CREATE TYPE tipo_periodo AS ENUM ('mensual', 'trimestral', 'anual');

CREATE TYPE tipo_impuesto AS ENUM ('ISR', 'IVA');

CREATE TYPE estado_cfdi AS ENUM ('vigente', 'cancelado', 'pendiente_complemento');

CREATE TYPE tipo_comprobante AS ENUM ('I', 'E', 'P', 'N', 'T');

CREATE TYPE metodo_pago AS ENUM ('PUE', 'PPD');

CREATE TYPE resultado_iva_actividad AS ENUM (
    'IVA16', 'IVA0', 'EXENTO', 'NO_APLICA', 'SEPARAR', 'REVISAR'
);

CREATE TYPE confianza_nivel AS ENUM ('ALTA', 'MEDIA', 'BAJA', 'NO_CONFIABLE');

CREATE TYPE tipo_deduccion AS ENUM ('ciega', 'comprobable');

CREATE TYPE rol_usuario AS ENUM ('propietario', 'contador', 'lectura');

CREATE TYPE estado_documento AS ENUM ('recibido', 'procesando', 'validado', 'con_error');

CREATE TYPE estado_consentimiento AS ENUM ('aceptado', 'revocado');

-- ============================================================
-- TENANTS (contribuyentes)
-- ============================================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rfc VARCHAR(13) NOT NULL,
    nombre VARCHAR(500) NOT NULL,
    tipo_persona tipo_persona NOT NULL,
    regimen regimen_fiscal NOT NULL,
    tipo_deduccion tipo_deduccion NOT NULL DEFAULT 'ciega',
    presenta_anual BOOLEAN NOT NULL DEFAULT false,
    opcion_trimestral BOOLEAN NOT NULL DEFAULT false,
    onboarding_completado BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tenants_rfc ON tenants(rfc);

-- ============================================================
-- USERS & MEMBERSHIPS
-- ============================================================

CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(500) NOT NULL,
    nombre VARCHAR(500),
    es_invitado BOOLEAN NOT NULL DEFAULT false,
    invitado_expira_en TIMESTAMPTZ,
    invitado_email VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    rol rol_usuario NOT NULL DEFAULT 'lectura',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, user_id)
);

CREATE INDEX idx_memberships_tenant ON memberships(tenant_id);
CREATE INDEX idx_memberships_user ON memberships(user_id);

-- ============================================================
-- GUEST SESSIONS
-- ============================================================

CREATE TABLE guest_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(500),
    expires_at TIMESTAMPTZ NOT NULL,
    migrated_to_user_id UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_guest_sessions_token ON guest_sessions(token);
CREATE INDEX idx_guest_sessions_expires ON guest_sessions(expires_at);

-- ============================================================
-- PARAMETROS FISCALES POR EJERCICIO
-- ============================================================

CREATE TABLE ejercicios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anio INTEGER NOT NULL UNIQUE,
    uma_mensual NUMERIC(12,2) NOT NULL,
    uma_diaria NUMERIC(12,2) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tarifas_resico (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ejercicio_id UUID NOT NULL REFERENCES ejercicios(id),
    limite_superior NUMERIC(14,2) NOT NULL,
    tasa NUMERIC(6,4) NOT NULL,
    orden INTEGER NOT NULL,
    UNIQUE(ejercicio_id, orden)
);

CREATE TABLE tarifas_art96 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ejercicio_id UUID NOT NULL REFERENCES ejercicios(id),
    limite_inferior NUMERIC(14,2) NOT NULL,
    limite_superior NUMERIC(14,2),
    cuota_fija NUMERIC(14,2) NOT NULL,
    porcentaje NUMERIC(6,4) NOT NULL,
    orden INTEGER NOT NULL,
    UNIQUE(ejercicio_id, orden)
);

-- ============================================================
-- PERIODOS (OBLIGACIONES FISCALES)
-- ============================================================

CREATE TABLE periodos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    impuesto tipo_impuesto NOT NULL,
    tipo_periodo tipo_periodo NOT NULL,
    ejercicio INTEGER NOT NULL,
    numero_periodo INTEGER NOT NULL,
    fecha_limite DATE NOT NULL,
    estado estado_periodo NOT NULL DEFAULT 'borrador',
    es_candidato_complementaria BOOLEAN NOT NULL DEFAULT false,
    resultado_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, impuesto, tipo_periodo, ejercicio, numero_periodo)
);

CREATE INDEX idx_periodos_tenant ON periodos(tenant_id);
CREATE INDEX idx_periodos_estado ON periodos(estado);
CREATE INDEX idx_periodos_ejercicio ON periodos(ejercicio, numero_periodo);

-- ============================================================
-- CFDIS
-- ============================================================

CREATE TABLE cfdis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    uuid_fiscal VARCHAR(36) NOT NULL,
    tipo tipo_comprobante NOT NULL,
    metodo_pago metodo_pago,
    fecha_emision TIMESTAMPTZ NOT NULL,
    fecha_pago TIMESTAMPTZ,
    rfc_emisor VARCHAR(13) NOT NULL,
    nombre_emisor VARCHAR(500),
    rfc_receptor VARCHAR(13) NOT NULL,
    nombre_receptor VARCHAR(500),
    subtotal NUMERIC(14,2) NOT NULL,
    total NUMERIC(14,2) NOT NULL,
    moneda VARCHAR(3) NOT NULL DEFAULT 'MXN',
    tipo_cambio NUMERIC(14,6) DEFAULT 1.0,
    uso_cfdi VARCHAR(10),
    objeto_imp VARCHAR(2),
    estado estado_cfdi NOT NULL DEFAULT 'vigente',
    actividad_id UUID,
    xml_storage_path VARCHAR(1000),
    documento_id UUID,
    periodo_id UUID REFERENCES periodos(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, uuid_fiscal)
);

CREATE INDEX idx_cfdis_tenant ON cfdis(tenant_id);
CREATE INDEX idx_cfdis_uuid_fiscal ON cfdis(uuid_fiscal);
CREATE INDEX idx_cfdis_tipo ON cfdis(tipo);
CREATE INDEX idx_cfdis_estado ON cfdis(estado);
CREATE INDEX idx_cfdis_fecha ON cfdis(fecha_emision);
CREATE INDEX idx_cfdis_actividad ON cfdis(actividad_id);

-- ============================================================
-- IMPUESTOS DE CFDI
-- ============================================================

CREATE TABLE cfdi_impuestos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cfdi_id UUID NOT NULL REFERENCES cfdis(id) ON DELETE CASCADE,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('traslado', 'retencion')),
    impuesto VARCHAR(3) NOT NULL,
    tasa NUMERIC(8,6) NOT NULL,
    importe NUMERIC(14,2) NOT NULL,
    base NUMERIC(14,2) NOT NULL
);

CREATE INDEX idx_cfdi_impuestos_cfdi ON cfdi_impuestos(cfdi_id);

-- ============================================================
-- COMPLEMENTOS DE PAGO
-- ============================================================

CREATE TABLE complementos_pago (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cfdi_id UUID NOT NULL REFERENCES cfdis(id) ON DELETE CASCADE,
    fecha_pago TIMESTAMPTZ NOT NULL,
    forma_pago VARCHAR(2),
    monto NUMERIC(14,2) NOT NULL,
    moneda VARCHAR(3) NOT NULL DEFAULT 'MXN'
);

CREATE TABLE doctos_relacionados (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complemento_id UUID NOT NULL REFERENCES complementos_pago(id) ON DELETE CASCADE,
    uuid_docto VARCHAR(36) NOT NULL,
    num_parcialidad INTEGER,
    imp_saldo_ant NUMERIC(14,2),
    imp_pagado NUMERIC(14,2),
    imp_saldo_insoluto NUMERIC(14,2),
    objeto_imp_dr VARCHAR(2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE impuestos_dr (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    docto_id UUID NOT NULL REFERENCES doctos_relacionados(id) ON DELETE CASCADE,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('traslado', 'retencion')),
    impuesto_dr VARCHAR(3) NOT NULL,
    tasa_dr NUMERIC(8,6) NOT NULL,
    importe_dr NUMERIC(14,2) NOT NULL,
    base_dr NUMERIC(14,2) NOT NULL
);

-- ============================================================
-- NOMINA (para acumulación de sueldos)
-- ============================================================

CREATE TABLE cfdi_nomina (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cfdi_id UUID NOT NULL REFERENCES cfdis(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    total_percepciones NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_deducciones NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_otros_pagos NUMERIC(14,2) NOT NULL DEFAULT 0,
    ejercicio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_cfdi_nomina_tenant ON cfdi_nomina(tenant_id);

-- ============================================================
-- ACTIVIDADES Y CUESTIONARIO IVA
-- ============================================================

CREATE TABLE actividades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    descripcion VARCHAR(500) NOT NULL,
    resultado resultado_iva_actividad,
    cuestionario_completado BOOLEAN NOT NULL DEFAULT false,
    respuestas_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_actividades_tenant ON actividades(tenant_id);

CREATE TABLE cuestionario_nodos (
    id VARCHAR(20) PRIMARY KEY,
    version INTEGER NOT NULL DEFAULT 1,
    texto TEXT NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('pregunta', 'resultado', 'filtro')),
    resultado resultado_iva_actividad,
    metadata JSONB,
    activo BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE cuestionario_opciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nodo_id VARCHAR(20) NOT NULL REFERENCES cuestionario_nodos(id),
    texto VARCHAR(500) NOT NULL,
    orden INTEGER NOT NULL,
    metadata JSONB
);

CREATE TABLE cuestionario_transiciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nodo_origen VARCHAR(20) NOT NULL REFERENCES cuestionario_nodos(id),
    opcion_id UUID NOT NULL REFERENCES cuestionario_opciones(id),
    nodo_destino VARCHAR(20) NOT NULL REFERENCES cuestionario_nodos(id),
    condicion JSONB
);

CREATE INDEX idx_transiciones_origen ON cuestionario_transiciones(nodo_origen);

-- ============================================================
-- REGLAS DE MAPEO CFDI -> ACTIVIDAD
-- ============================================================

CREATE TABLE reglas_mapeo_cfdi (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('manual', 'clave_prodserv', 'rfc_receptor')),
    valor VARCHAR(500) NOT NULL,
    actividad_id UUID NOT NULL REFERENCES actividades(id) ON DELETE CASCADE,
    prioridad INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_reglas_mapeo_tenant ON reglas_mapeo_cfdi(tenant_id);

-- ============================================================
-- ESTADOS DE CUENTA BANCARIOS
-- ============================================================

CREATE TABLE extractos_bancarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    institucion VARCHAR(100) NOT NULL,
    titular VARCHAR(500) NOT NULL,
    identificador_cuenta VARCHAR(100) NOT NULL,
    periodo_inicio DATE NOT NULL,
    periodo_fin DATE NOT NULL,
    saldo_inicial NUMERIC(14,2) NOT NULL,
    saldo_final NUMERIC(14,2) NOT NULL,
    total_abonos_declarado NUMERIC(14,2) NOT NULL,
    total_cargos_declarado NUMERIC(14,2) NOT NULL,
    comisiones_declaradas NUMERIC(14,2) NOT NULL DEFAULT 0,
    es_confiable BOOLEAN NOT NULL DEFAULT true,
    alertas JSONB DEFAULT '[]',
    documento_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_extractos_tenant ON extractos_bancarios(tenant_id);

CREATE TABLE movimientos_bancarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extracto_id UUID NOT NULL REFERENCES extractos_bancarios(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    hora TIME,
    descripcion VARCHAR(500) NOT NULL,
    identificador_transaccion VARCHAR(100),
    monto NUMERIC(14,2) NOT NULL,
    comision NUMERIC(14,2) NOT NULL DEFAULT 0,
    moneda VARCHAR(3) NOT NULL DEFAULT 'MXN',
    detalle JSONB,
    es_espejo BOOLEAN NOT NULL DEFAULT false,
    categoria VARCHAR(100),
    confianza confianza_nivel NOT NULL DEFAULT 'ALTA',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_movimientos_extracto ON movimientos_bancarios(extracto_id);
CREATE INDEX idx_movimientos_tenant ON movimientos_bancarios(tenant_id);
CREATE INDEX idx_movimientos_espejo ON movimientos_bancarios(es_espejo);

-- ============================================================
-- CONCILIACIÓN
-- ============================================================

CREATE TABLE conciliaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    periodo_id UUID NOT NULL REFERENCES periodos(id),
    movimiento_id UUID REFERENCES movimientos_bancarios(id),
    cfdi_id UUID REFERENCES cfdis(id),
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('cobrado_sin_factura', 'facturado_sin_cobro', 'conciliado')),
    monto NUMERIC(14,2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_conciliaciones_tenant ON conciliaciones(tenant_id);
CREATE INDEX idx_conciliaciones_periodo ON conciliaciones(periodo_id);

-- ============================================================
-- DOCUMENTOS (archivos cargados)
-- ============================================================

CREATE TABLE documentos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    nombre_archivo VARCHAR(500) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    estado estado_documento NOT NULL DEFAULT 'recibido',
    storage_path VARCHAR(1000) NOT NULL,
    tamano_bytes BIGINT,
    hash_sha256 VARCHAR(64),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_documentos_tenant ON documentos(tenant_id);

-- ============================================================
-- BOVEDA E.FIRMA
-- ============================================================

CREATE TABLE boveda_efirma (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    cer_storage_path VARCHAR(1000) NOT NULL,
    key_storage_path VARCHAR(1000) NOT NULL,
    password_cifrada BYTEA NOT NULL,
    data_key_cifrada BYTEA NOT NULL,
    cer_serie VARCHAR(40),
    cer_vigencia_fin TIMESTAMPTZ,
    activa BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id)
);

CREATE TABLE boveda_bitacora (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    boveda_id UUID NOT NULL REFERENCES boveda_efirma(id) ON DELETE CASCADE,
    accion VARCHAR(100) NOT NULL,
    proceso_solicitante VARCHAR(200) NOT NULL,
    finalidad VARCHAR(500) NOT NULL,
    ip_origen VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_boveda_bitacora_tenant ON boveda_bitacora(tenant_id);
CREATE INDEX idx_boveda_bitacora_boveda ON boveda_bitacora(boveda_id);

-- ============================================================
-- CONSENTIMIENTOS
-- ============================================================

CREATE TABLE consentimientos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id),
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('datos_financieros', 'efirma', 'comunicacion_voluntaria')),
    estado estado_consentimiento NOT NULL DEFAULT 'aceptado',
    texto_hash VARCHAR(64) NOT NULL,
    texto_version VARCHAR(20) NOT NULL,
    ip_origen VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revocado_en TIMESTAMPTZ
);

CREATE INDEX idx_consentimientos_tenant ON consentimientos(tenant_id);

-- ============================================================
-- CONSUMO IA
-- ============================================================

CREATE TABLE consumo_ia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id),
    tarea VARCHAR(100) NOT NULL,
    proveedor VARCHAR(50) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    tokens_entrada INTEGER NOT NULL DEFAULT 0,
    tokens_salida INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_consumo_ia_tenant ON consumo_ia(tenant_id);
CREATE INDEX idx_consumo_ia_fecha ON consumo_ia(created_at);

-- ============================================================
-- INTENCIONES DE PAGO (validación de pricing)
-- ============================================================

CREATE TABLE intenciones_pago (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id),
    guest_session_id UUID REFERENCES guest_sessions(id),
    email VARCHAR(500),
    plan VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- LISTA DE ESPERA (régimenes no soportados)
-- ============================================================

CREATE TABLE lista_espera (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(500),
    regimen VARCHAR(100) NOT NULL,
    rfc VARCHAR(13),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_lista_espera_regimen ON lista_espera(regimen);

-- ============================================================
-- BITACORA DE PERIODOS
-- ============================================================

CREATE TABLE bitacora_periodos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    periodo_id UUID NOT NULL REFERENCES periodos(id),
    estado_anterior estado_periodo,
    estado_nuevo estado_periodo NOT NULL,
    acuse_storage_path VARCHAR(1000),
    notas TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_bitacora_periodos_tenant ON bitacora_periodos(tenant_id);

-- ============================================================
-- COOKIE PREFERENCES
-- ============================================================

CREATE TABLE cookie_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_profiles(id),
    guest_session_id UUID REFERENCES guest_sessions(id),
    analytics_enabled BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- CHAT MESSAGES
-- ============================================================

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id),
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('user', 'assistant', 'system')),
    contenido TEXT NOT NULL,
    canal VARCHAR(20) NOT NULL DEFAULT 'web' CHECK (canal IN ('web', 'whatsapp_sim')),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chat_messages_tenant ON chat_messages(tenant_id);

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_periodos_updated_at BEFORE UPDATE ON periodos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_cfdis_updated_at BEFORE UPDATE ON cfdis
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_documentos_updated_at BEFORE UPDATE ON documentos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_actividades_updated_at BEFORE UPDATE ON actividades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_cookie_preferences_updated_at BEFORE UPDATE ON cookie_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
