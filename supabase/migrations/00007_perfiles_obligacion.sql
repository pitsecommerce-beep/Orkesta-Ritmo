-- Orkesta Ritmo — Migration 00007
-- Perfiles de obligación por régimen y corrección tipo_deduccion.
--
-- Reemplaza la lógica condicional en código por configuración en BD.
-- Cada régimen tiene N filas indicando qué impuestos debe declarar,
-- con qué periodicidad y en qué día del mes vence.

-- ============================================================
-- FIX: renombrar valor 'ciega' → 'opcional' en tipo_deduccion
-- El término legal correcto es "deducción opcional" (Art. 115 LISR).
-- ============================================================

ALTER TYPE tipo_deduccion RENAME VALUE 'ciega' TO 'opcional';

UPDATE tenants SET tipo_deduccion = 'opcional' WHERE tipo_deduccion = 'opcional';
-- (No-op: el RENAME VALUE ya cambió el valor almacenado.)

-- ============================================================
-- TABLA: perfiles_obligacion
-- ============================================================

CREATE TABLE perfiles_obligacion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    regimen regimen_fiscal NOT NULL,
    impuesto tipo_impuesto NOT NULL,
    tipo_periodo tipo_periodo NOT NULL,
    dia_limite INTEGER NOT NULL DEFAULT 17,
    admite_trimestral BOOLEAN NOT NULL DEFAULT false,
    presenta_anual BOOLEAN NOT NULL DEFAULT false,
    es_pago_definitivo BOOLEAN NOT NULL DEFAULT false,
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(regimen, impuesto)
);

CREATE INDEX idx_perfiles_obligacion_regimen ON perfiles_obligacion(regimen);

-- ============================================================
-- SEED DATA: obligaciones por régimen
-- ============================================================

-- RESICO PF: ISR mensual definitivo + IVA mensual
INSERT INTO perfiles_obligacion (regimen, impuesto, tipo_periodo, dia_limite, admite_trimestral, presenta_anual, es_pago_definitivo) VALUES
    ('RESICO_PF', 'ISR', 'mensual', 17, false, false, true),
    ('RESICO_PF', 'IVA', 'mensual', 17, false, false, false);

-- RESICO PF con sueldos: mismas obligaciones
INSERT INTO perfiles_obligacion (regimen, impuesto, tipo_periodo, dia_limite, admite_trimestral, presenta_anual, es_pago_definitivo) VALUES
    ('RESICO_PF_SUELDOS', 'ISR', 'mensual', 17, false, false, true),
    ('RESICO_PF_SUELDOS', 'IVA', 'mensual', 17, false, false, false);

-- Arrendamiento: ISR provisional mensual + IVA mensual, admite trimestral, presenta anual
INSERT INTO perfiles_obligacion (regimen, impuesto, tipo_periodo, dia_limite, admite_trimestral, presenta_anual, es_pago_definitivo) VALUES
    ('ARRENDAMIENTO', 'ISR', 'mensual', 17, true, true, false),
    ('ARRENDAMIENTO', 'IVA', 'mensual', 17, true, false, false);

-- Arrendamiento con sueldos: mismas obligaciones
INSERT INTO perfiles_obligacion (regimen, impuesto, tipo_periodo, dia_limite, admite_trimestral, presenta_anual, es_pago_definitivo) VALUES
    ('ARRENDAMIENTO_SUELDOS', 'ISR', 'mensual', 17, true, true, false),
    ('ARRENDAMIENTO_SUELDOS', 'IVA', 'mensual', 17, true, false, false);

-- RESICO PM: deshabilitado pero se registra para completitud.
-- No se generan periodos porque el motor lanza RegimenEnValidacionError.
INSERT INTO perfiles_obligacion (regimen, impuesto, tipo_periodo, dia_limite, admite_trimestral, presenta_anual, es_pago_definitivo, activo) VALUES
    ('RESICO_PM', 'ISR', 'mensual', 17, false, true, false, false),
    ('RESICO_PM', 'IVA', 'mensual', 17, false, false, false, false);
