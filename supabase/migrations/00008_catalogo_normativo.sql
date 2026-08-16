-- Orkesta Ritmo - Catalogo Normativo Versionado
-- Tablas para reglas fiscales, tarifas e indicadores con vigencia por rango
-- de fechas y jerarquia de fundamento legal.
--
-- Las tablas de catalogo son datos de referencia (lectura publica).
-- resolucion_calculo es tenant-scoped con RLS.

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE tipo_norma AS ENUM (
    'LEY', 'RESOLUCION', 'DECRETO', 'LEY_INGRESOS', 'ANEXO_RMF', 'DOF'
);

CREATE TYPE jerarquia_norma AS ENUM (
    'BASE', 'SUSTITUYE', 'DETALLA', 'EXIME'
);

CREATE TYPE estado_confirmacion AS ENUM (
    'CONFIRMADO', 'NO_CONFIRMADO', 'PENDIENTE_CONTADOR'
);

CREATE TYPE tipo_tarifa_cat AS ENUM (
    'ART96_MENSUAL', 'ART152_ANUAL',
    'ARRENDAMIENTO_MENSUAL', 'ARRENDAMIENTO_TRIMESTRAL',
    'RESICO_PF_MENSUAL'
);

CREATE TYPE tipo_indicador AS ENUM (
    'UMA_DIARIA', 'UMA_MENSUAL', 'UMA_ANUAL', 'INPC'
);

-- ============================================================
-- NORMA FUENTE — Documento publicado que fundamenta una regla
-- ============================================================

CREATE TABLE norma_fuente (
    id VARCHAR(50) PRIMARY KEY,
    tipo tipo_norma NOT NULL,
    identificador VARCHAR(500) NOT NULL,
    fecha_publicacion_dof DATE NOT NULL,
    url VARCHAR(1000) DEFAULT '',
    hash_pdf VARCHAR(128) DEFAULT '',
    descripcion TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- REGLA FISCAL — Concepto estable con clave que nunca cambia
-- ============================================================

CREATE TABLE regla_fiscal (
    clave VARCHAR(100) PRIMARY KEY,
    descripcion TEXT NOT NULL,
    regimen VARCHAR(100) DEFAULT ''
);

-- ============================================================
-- REGLA VERSION — Valor concreto con vigencia y jerarquia
-- Vigencia: [vigencia_desde, vigencia_hasta)
-- vigencia_hasta = NULL → vigente sin fecha de termino conocida
-- ============================================================

CREATE TABLE regla_version (
    id VARCHAR(100) PRIMARY KEY,
    regla_clave VARCHAR(100) NOT NULL REFERENCES regla_fiscal(clave),
    valor NUMERIC(18,8) NOT NULL,
    unidad VARCHAR(50) DEFAULT '',
    vigencia_desde DATE NOT NULL DEFAULT '2000-01-01',
    vigencia_hasta DATE,
    jerarquia jerarquia_norma NOT NULL DEFAULT 'BASE',
    norma_fuente_id VARCHAR(50) REFERENCES norma_fuente(id),
    articulo VARCHAR(200) DEFAULT '',
    estado estado_confirmacion NOT NULL DEFAULT 'CONFIRMADO',
    nota_confirmacion TEXT DEFAULT '',
    capturado_por VARCHAR(200) DEFAULT '',
    aprobado_por VARCHAR(200) DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_regla_version_clave ON regla_version(regla_clave);
CREATE INDEX idx_regla_version_vigencia ON regla_version(vigencia_desde, vigencia_hasta);
CREATE INDEX idx_regla_version_estado ON regla_version(estado);

-- ============================================================
-- TARIFA CATALOGO — Tabla de tarifa progresiva con vigencia
-- ============================================================

CREATE TABLE tarifa_catalogo (
    id VARCHAR(100) PRIMARY KEY,
    tipo tipo_tarifa_cat NOT NULL,
    vigencia_desde DATE NOT NULL,
    vigencia_hasta DATE,
    norma_fuente_id VARCHAR(50) REFERENCES norma_fuente(id),
    articulo VARCHAR(200) DEFAULT '',
    estado estado_confirmacion NOT NULL DEFAULT 'CONFIRMADO',
    nota_confirmacion TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tarifa_catalogo_tipo ON tarifa_catalogo(tipo);
CREATE INDEX idx_tarifa_catalogo_vigencia ON tarifa_catalogo(vigencia_desde, vigencia_hasta);

-- ============================================================
-- TARIFA TRAMO CATALOGO — Un tramo de una tarifa progresiva
-- limite_superior = NULL en el ultimo tramo (sin tope)
-- porcentaje como porcentaje: 1.92 = 1.92%
-- tasa para RESICO: tasa directa en porcentaje
-- ============================================================

CREATE TABLE tarifa_tramo_catalogo (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tarifa_id VARCHAR(100) NOT NULL REFERENCES tarifa_catalogo(id) ON DELETE CASCADE,
    orden INTEGER NOT NULL,
    limite_inferior NUMERIC(18,2) NOT NULL,
    limite_superior NUMERIC(18,2),
    cuota_fija NUMERIC(18,2) NOT NULL DEFAULT 0,
    porcentaje NUMERIC(8,4) NOT NULL DEFAULT 0,
    tasa NUMERIC(8,4),
    UNIQUE(tarifa_id, orden)
);

CREATE INDEX idx_tarifa_tramo_tarifa ON tarifa_tramo_catalogo(tarifa_id);

-- ============================================================
-- INDICADOR — Indicador economico con vigencia por rango
-- UMA cambia el 1 de febrero, no el 1 de enero
-- ============================================================

CREATE TABLE indicador (
    id VARCHAR(100) PRIMARY KEY,
    tipo tipo_indicador NOT NULL,
    valor NUMERIC(18,8) NOT NULL,
    vigencia_desde DATE NOT NULL,
    vigencia_hasta DATE,
    norma_fuente_id VARCHAR(50) REFERENCES norma_fuente(id),
    estado estado_confirmacion NOT NULL DEFAULT 'CONFIRMADO',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_indicador_tipo ON indicador(tipo);
CREATE INDEX idx_indicador_vigencia ON indicador(vigencia_desde, vigencia_hasta);

-- ============================================================
-- RESOLUCION CALCULO — Log append-only de cada calculo fiscal
-- Tenant-scoped con RLS
-- ============================================================

CREATE TABLE resolucion_calculo (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    ejercicio INTEGER NOT NULL,
    periodo INTEGER NOT NULL,
    regimen regimen_fiscal NOT NULL,
    fecha_causacion DATE NOT NULL,
    -- Snapshot de las reglas y tarifas usadas
    reglas_usadas JSONB NOT NULL DEFAULT '[]',
    tarifas_usadas JSONB NOT NULL DEFAULT '[]',
    indicadores_usados JSONB NOT NULL DEFAULT '[]',
    -- Resultado
    resultado_json JSONB NOT NULL,
    -- Metadata
    version_motor VARCHAR(50) DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_resolucion_calculo_tenant ON resolucion_calculo(tenant_id);
CREATE INDEX idx_resolucion_calculo_periodo ON resolucion_calculo(ejercicio, periodo);
CREATE INDEX idx_resolucion_calculo_fecha ON resolucion_calculo(created_at);

-- ============================================================
-- RLS — Tablas de catalogo son lectura publica
-- ============================================================

ALTER TABLE norma_fuente ENABLE ROW LEVEL SECURITY;
ALTER TABLE regla_fiscal ENABLE ROW LEVEL SECURITY;
ALTER TABLE regla_version ENABLE ROW LEVEL SECURITY;
ALTER TABLE tarifa_catalogo ENABLE ROW LEVEL SECURITY;
ALTER TABLE tarifa_tramo_catalogo ENABLE ROW LEVEL SECURITY;
ALTER TABLE indicador ENABLE ROW LEVEL SECURITY;
ALTER TABLE resolucion_calculo ENABLE ROW LEVEL SECURITY;

-- Catalogo: lectura publica (igual que ejercicios, tarifas_resico, etc.)
CREATE POLICY norma_fuente_select ON norma_fuente FOR SELECT USING (true);
CREATE POLICY regla_fiscal_select ON regla_fiscal FOR SELECT USING (true);
CREATE POLICY regla_version_select ON regla_version FOR SELECT USING (true);
CREATE POLICY tarifa_catalogo_select ON tarifa_catalogo FOR SELECT USING (true);
CREATE POLICY tarifa_tramo_catalogo_select ON tarifa_tramo_catalogo FOR SELECT USING (true);
CREATE POLICY indicador_select ON indicador FOR SELECT USING (true);

-- resolucion_calculo: tenant-scoped (mismas policies que periodos, cfdis, etc.)
CREATE POLICY resolucion_calculo_tenant_select ON resolucion_calculo FOR SELECT
    USING (tenant_id IN (SELECT get_user_tenant_ids()));

CREATE POLICY resolucion_calculo_tenant_insert ON resolucion_calculo FOR INSERT
    WITH CHECK (tenant_id IN (SELECT get_user_tenant_ids()));

-- No UPDATE ni DELETE: es append-only

-- ============================================================
-- SEED DATA — Normas fuente
-- ============================================================

INSERT INTO norma_fuente (id, tipo, identificador, fecha_publicacion_dof, descripcion) VALUES
    ('LISR_2025', 'LEY', 'Ley del Impuesto sobre la Renta', '2024-11-12', 'LISR vigente para ejercicio 2025-2026'),
    ('LIVA_2025', 'LEY', 'Ley del Impuesto al Valor Agregado', '2024-11-12', 'LIVA vigente para ejercicio 2025-2026'),
    ('ANEXO8_RMF_2025', 'ANEXO_RMF', 'Anexo 8 de la RMF 2025', '2024-12-29', 'Tarifas de ISR ejercicio 2025'),
    ('ANEXO8_RMF_2026', 'ANEXO_RMF', 'Anexo 8 de la RMF 2026', '2025-12-28', 'Tarifas de ISR ejercicio 2026, factor actualizacion 1.1321'),
    ('DOF_UMA_2025', 'DOF', 'DOF UMA 2025', '2025-01-10', 'Valor UMA 2025: $113.14 diario'),
    ('DOF_UMA_2026', 'DOF', 'DOF UMA 2026', '2026-01-09', 'Valor UMA 2026: $117.31 diario'),
    ('DOF_UMA_2024', 'DOF', 'DOF UMA 2024', '2024-01-10', 'Valor UMA 2024: $108.57 diario'),
    ('LIF_2026', 'LEY_INGRESOS', 'Ley de Ingresos de la Federacion para el ejercicio 2026', '2025-11-14', 'LIF 2026 con Art. 25 fr. VI que sustituye tasas de plataformas');

-- ============================================================
-- SEED DATA — Indicadores UMA
-- ============================================================

INSERT INTO indicador (id, tipo, valor, vigencia_desde, vigencia_hasta, norma_fuente_id, estado) VALUES
    ('UMA_DIARIA_2024', 'UMA_DIARIA', 108.57, '2024-02-01', '2025-02-01', 'DOF_UMA_2024', 'CONFIRMADO'),
    ('UMA_DIARIA_2025', 'UMA_DIARIA', 113.14, '2025-02-01', '2026-02-01', 'DOF_UMA_2025', 'CONFIRMADO'),
    ('UMA_DIARIA_2026', 'UMA_DIARIA', 117.31, '2026-02-01', '2027-02-01', 'DOF_UMA_2026', 'CONFIRMADO');

-- ============================================================
-- SEED DATA — Reglas fiscales
-- ============================================================

INSERT INTO regla_fiscal (clave, descripcion, regimen) VALUES
    ('RESICO_PF.LIMITE_INGRESOS_ANUAL', 'Limite de ingresos anuales para permanecer en RESICO PF', 'RESICO_PF'),
    ('RESICO_PF.TOPE_INGRESOS_MENSUALES_UMA', 'Tope en UMAs mensuales para RESICO PF', 'RESICO_PF'),
    ('ARRENDAMIENTO.DEDUCCION_OPCIONAL_PCT', 'Porcentaje de deduccion ciega para arrendamiento', 'ARRENDAMIENTO'),
    ('ARRENDAMIENTO.RETENCION_ISR_PCT', 'Porcentaje de retencion ISR arrendamiento PM', 'ARRENDAMIENTO'),
    ('ARRENDAMIENTO.RETENCION_IVA_FRACCION', 'Fraccion de IVA retenida por PM arrendataria', 'ARRENDAMIENTO'),
    ('ARRENDAMIENTO.UMBRAL_TRIMESTRAL', 'Umbral para opcion trimestral en UMAs mensuales', 'ARRENDAMIENTO'),
    ('IVA.TASA_GENERAL', 'Tasa general de IVA', ''),
    ('IVA.TASA_FRONTERA', 'Tasa de IVA en zona fronteriza', ''),
    ('PLATAFORMAS.RETENCION_ISR_TRANSPORTE', 'Retencion ISR plataformas transporte', 'PLATAFORMAS'),
    ('PLATAFORMAS.RETENCION_ISR_HOSPEDAJE', 'Retencion ISR plataformas hospedaje', 'PLATAFORMAS'),
    ('PLATAFORMAS.RETENCION_ISR_ENAJENACION_SERVICIOS', 'Retencion ISR enajenacion/servicios Art. 113-A fr. III', 'PLATAFORMAS'),
    ('PLATAFORMAS.RETENCION_IVA_CON_RFC', 'Retencion IVA plataformas con RFC', 'PLATAFORMAS'),
    ('PLATAFORMAS.RETENCION_IVA_SIN_RFC', 'Retencion IVA plataformas sin RFC', 'PLATAFORMAS');

-- ============================================================
-- SEED DATA — Versiones de reglas
-- ============================================================

-- RESICO PF
INSERT INTO regla_version (id, regla_clave, valor, unidad, vigencia_desde, norma_fuente_id, articulo, estado, jerarquia) VALUES
    ('RESICO.LIMITE_ANUAL', 'RESICO_PF.LIMITE_INGRESOS_ANUAL', 3500000, 'MXN', '2025-01-01', 'LISR_2025', 'Art. 113-E LISR', 'CONFIRMADO', 'BASE'),
    ('RESICO.TOPE_UMA', 'RESICO_PF.TOPE_INGRESOS_MENSUALES_UMA', 40, 'UMAs mensuales', '2025-01-01', 'LISR_2025', 'Art. 113-E LISR', 'CONFIRMADO', 'BASE');

-- Arrendamiento
INSERT INTO regla_version (id, regla_clave, valor, unidad, vigencia_desde, norma_fuente_id, articulo, estado, jerarquia) VALUES
    ('ARREND.DEDUCCION_OPT', 'ARRENDAMIENTO.DEDUCCION_OPCIONAL_PCT', 35, '%', '2025-01-01', 'LISR_2025', 'Art. 115 LISR', 'CONFIRMADO', 'BASE'),
    ('ARREND.RETENCION_ISR', 'ARRENDAMIENTO.RETENCION_ISR_PCT', 10, '%', '2025-01-01', 'LISR_2025', 'Art. 116 LISR', 'CONFIRMADO', 'BASE'),
    ('ARREND.RETENCION_IVA', 'ARRENDAMIENTO.RETENCION_IVA_FRACCION', 0.66666667, 'fraccion de IVA', '2025-01-01', 'LIVA_2025', 'Art. 1-A LIVA', 'CONFIRMADO', 'BASE');

-- Arrendamiento — pendientes contador
INSERT INTO regla_version (id, regla_clave, valor, unidad, vigencia_desde, norma_fuente_id, articulo, estado, jerarquia, nota_confirmacion) VALUES
    ('ARREND.UMBRAL_TRIM', 'ARRENDAMIENTO.UMBRAL_TRIMESTRAL', 10, 'UMAs mensuales', '2025-01-01', 'LISR_2025', 'Art. 116 LISR', 'PENDIENTE_CONTADOR', 'BASE',
     'Pendiente: verificar si el umbral de opcion trimestral es 10 UMAs mensuales o diarias. LISR Art. 116 dice "diez veces el salario minimo" que con la reforma se lee como UMA.');

-- IVA
INSERT INTO regla_version (id, regla_clave, valor, unidad, vigencia_desde, norma_fuente_id, articulo, estado, jerarquia) VALUES
    ('IVA.GENERAL', 'IVA.TASA_GENERAL', 16, '%', '2025-01-01', 'LIVA_2025', 'Art. 1 LIVA', 'CONFIRMADO', 'BASE'),
    ('IVA.FRONTERA', 'IVA.TASA_FRONTERA', 8, '%', '2025-01-01', 'LIVA_2025', 'Decreto zona fronteriza', 'CONFIRMADO', 'BASE');

-- Plataformas — tasas base LISR
INSERT INTO regla_version (id, regla_clave, valor, unidad, vigencia_desde, norma_fuente_id, articulo, estado, jerarquia) VALUES
    ('PLAT.ISR_TRANSPORTE', 'PLATAFORMAS.RETENCION_ISR_TRANSPORTE', 2.1, '%', '2025-01-01', 'LISR_2025', 'Art. 113-A fr. I LISR', 'CONFIRMADO', 'BASE'),
    ('PLAT.ISR_HOSPEDAJE', 'PLATAFORMAS.RETENCION_ISR_HOSPEDAJE', 4, '%', '2025-01-01', 'LISR_2025', 'Art. 113-A fr. II LISR', 'CONFIRMADO', 'BASE'),
    ('PLAT.ISR_ENAJENACION_BASE', 'PLATAFORMAS.RETENCION_ISR_ENAJENACION_SERVICIOS', 1, '%', '2025-01-01', 'LISR_2025', 'Art. 113-A fr. III LISR', 'CONFIRMADO', 'BASE');

-- Plataformas — LIF 2026 override (SUSTITUYE la tasa base para 2026)
INSERT INTO regla_version (id, regla_clave, valor, unidad, vigencia_desde, vigencia_hasta, norma_fuente_id, articulo, estado, jerarquia, nota_confirmacion) VALUES
    ('PLAT.ISR_ENAJENACION_LIF2026', 'PLATAFORMAS.RETENCION_ISR_ENAJENACION_SERVICIOS', 2.5, '%', '2026-01-01', '2027-01-01', 'LIF_2026', 'Art. 25 fr. VI LIF 2026', 'PENDIENTE_CONTADOR', 'SUSTITUYE',
     'Pendiente: confirmar con contador que LIF 2026 Art. 25 fr. VI sustituye la tasa del Art. 113-A fr. III LISR de 1% a 2.5% para enajenacion y servicios durante 2026.');

-- Plataformas — IVA
INSERT INTO regla_version (id, regla_clave, valor, unidad, vigencia_desde, norma_fuente_id, articulo, estado, jerarquia, nota_confirmacion) VALUES
    ('PLAT.IVA_CON_RFC', 'PLATAFORMAS.RETENCION_IVA_CON_RFC', 8, '%', '2025-01-01', 'LIVA_2025', 'Art. 18-J LIVA', 'PENDIENTE_CONTADOR', 'BASE',
     'Pendiente: verificar si la tasa de retencion de IVA por plataformas con RFC inscrito es 8% del valor de la contraprestacion (Art. 18-J fr. II inciso a).'),
    ('PLAT.IVA_SIN_RFC', 'PLATAFORMAS.RETENCION_IVA_SIN_RFC', 16, '%', '2025-01-01', 'LIVA_2025', 'Art. 18-J LIVA', 'PENDIENTE_CONTADOR', 'BASE',
     'Pendiente: verificar si la tasa de retencion de IVA por plataformas sin RFC es 16% (tasa general completa). Art. 18-J fr. II inciso b.');

-- ============================================================
-- SEED DATA — Tarifas Art. 96 mensual 2025
-- ============================================================

INSERT INTO tarifa_catalogo (id, tipo, vigencia_desde, vigencia_hasta, norma_fuente_id, articulo, estado) VALUES
    ('ART96_MENSUAL_2025', 'ART96_MENSUAL', '2025-01-01', '2026-01-01', 'ANEXO8_RMF_2025', 'Art. 96 LISR + Anexo 8 RMF 2025', 'CONFIRMADO');

INSERT INTO tarifa_tramo_catalogo (tarifa_id, orden, limite_inferior, limite_superior, cuota_fija, porcentaje) VALUES
    ('ART96_MENSUAL_2025', 1,      0.01,    746.04,      0.00,  1.92),
    ('ART96_MENSUAL_2025', 2,    746.05,   6332.05,     14.32,  6.40),
    ('ART96_MENSUAL_2025', 3,   6332.06,  11128.01,    371.83, 10.88),
    ('ART96_MENSUAL_2025', 4,  11128.02,  12935.82,    893.63, 16.00),
    ('ART96_MENSUAL_2025', 5,  12935.83,  15487.71,   1182.88, 17.92),
    ('ART96_MENSUAL_2025', 6,  15487.72,  31236.49,   1640.18, 21.36),
    ('ART96_MENSUAL_2025', 7,  31236.50,  49233.00,   5004.12, 23.52),
    ('ART96_MENSUAL_2025', 8,  49233.01,  93993.90,   9236.89, 30.00),
    ('ART96_MENSUAL_2025', 9,  93993.91, 125325.20,  22665.17, 32.00),
    ('ART96_MENSUAL_2025', 10, 125325.21, 375975.61,  32691.18, 34.00),
    ('ART96_MENSUAL_2025', 11, 375975.62,      NULL, 117912.32, 35.00);

-- ============================================================
-- SEED DATA — Tarifas Art. 96 mensual 2026 (factor 1.1321)
-- ============================================================

INSERT INTO tarifa_catalogo (id, tipo, vigencia_desde, vigencia_hasta, norma_fuente_id, articulo, estado) VALUES
    ('ART96_MENSUAL_2026', 'ART96_MENSUAL', '2026-01-01', '2027-01-01', 'ANEXO8_RMF_2026', 'Art. 96 LISR + Anexo 8 RMF 2026', 'CONFIRMADO');

INSERT INTO tarifa_tramo_catalogo (tarifa_id, orden, limite_inferior, limite_superior, cuota_fija, porcentaje) VALUES
    ('ART96_MENSUAL_2026', 1,      0.01,    844.59,      0.00,  1.92),
    ('ART96_MENSUAL_2026', 2,    844.60,   7168.51,     16.22,  6.40),
    ('ART96_MENSUAL_2026', 3,   7168.52,  12598.02,    420.95, 10.88),
    ('ART96_MENSUAL_2026', 4,  12598.03,  14644.64,   1011.68, 16.00),
    ('ART96_MENSUAL_2026', 5,  14644.65,  17533.64,   1339.14, 17.92),
    ('ART96_MENSUAL_2026', 6,  17533.65,  35362.83,   1856.84, 21.36),
    ('ART96_MENSUAL_2026', 7,  35362.84,  55736.68,   5665.16, 23.52),
    ('ART96_MENSUAL_2026', 8,  55736.69, 106410.50,  10457.09, 30.00),
    ('ART96_MENSUAL_2026', 9, 106410.51, 141880.66,  25659.23, 32.00),
    ('ART96_MENSUAL_2026', 10, 141880.67, 425641.99,  37009.69, 34.00),
    ('ART96_MENSUAL_2026', 11, 425642.00,      NULL, 133488.54, 35.00);

-- ============================================================
-- SEED DATA — Tarifas RESICO PF mensual (fija en ley, 2025 y 2026)
-- ============================================================

INSERT INTO tarifa_catalogo (id, tipo, vigencia_desde, vigencia_hasta, norma_fuente_id, articulo, estado) VALUES
    ('RESICO_PF_MENSUAL_2025', 'RESICO_PF_MENSUAL', '2025-01-01', '2026-01-01', 'LISR_2025', 'Art. 113-E LISR', 'CONFIRMADO'),
    ('RESICO_PF_MENSUAL_2026', 'RESICO_PF_MENSUAL', '2026-01-01', '2027-01-01', 'LISR_2025', 'Art. 113-E LISR', 'CONFIRMADO');

INSERT INTO tarifa_tramo_catalogo (tarifa_id, orden, limite_inferior, limite_superior, cuota_fija, porcentaje, tasa) VALUES
    ('RESICO_PF_MENSUAL_2025', 1,     0.01,  25000.00, 0, 0, 1.00),
    ('RESICO_PF_MENSUAL_2025', 2, 25000.01,  50000.00, 0, 0, 1.10),
    ('RESICO_PF_MENSUAL_2025', 3, 50000.01,  83333.33, 0, 0, 1.50),
    ('RESICO_PF_MENSUAL_2025', 4, 83333.34, 208333.33, 0, 0, 2.00),
    ('RESICO_PF_MENSUAL_2025', 5, 208333.34, 291666.66, 0, 0, 2.50),
    ('RESICO_PF_MENSUAL_2026', 1,     0.01,  25000.00, 0, 0, 1.00),
    ('RESICO_PF_MENSUAL_2026', 2, 25000.01,  50000.00, 0, 0, 1.10),
    ('RESICO_PF_MENSUAL_2026', 3, 50000.01,  83333.33, 0, 0, 1.50),
    ('RESICO_PF_MENSUAL_2026', 4, 83333.34, 208333.33, 0, 0, 2.00),
    ('RESICO_PF_MENSUAL_2026', 5, 208333.34, 291666.66, 0, 0, 2.50);
