-- Orkesta Ritmo - Row Level Security Policies
-- Every table with tenant_id gets RLS enabled and policies that isolate by tenant.

-- ============================================================
-- Enable RLS on all tenant-scoped tables
-- ============================================================

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE guest_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE periodos ENABLE ROW LEVEL SECURITY;
ALTER TABLE cfdis ENABLE ROW LEVEL SECURITY;
ALTER TABLE cfdi_impuestos ENABLE ROW LEVEL SECURITY;
ALTER TABLE complementos_pago ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctos_relacionados ENABLE ROW LEVEL SECURITY;
ALTER TABLE impuestos_dr ENABLE ROW LEVEL SECURITY;
ALTER TABLE cfdi_nomina ENABLE ROW LEVEL SECURITY;
ALTER TABLE actividades ENABLE ROW LEVEL SECURITY;
ALTER TABLE reglas_mapeo_cfdi ENABLE ROW LEVEL SECURITY;
ALTER TABLE extractos_bancarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE movimientos_bancarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE conciliaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE boveda_efirma ENABLE ROW LEVEL SECURITY;
ALTER TABLE boveda_bitacora ENABLE ROW LEVEL SECURITY;
ALTER TABLE consentimientos ENABLE ROW LEVEL SECURITY;
ALTER TABLE consumo_ia ENABLE ROW LEVEL SECURITY;
ALTER TABLE intenciones_pago ENABLE ROW LEVEL SECURITY;
ALTER TABLE bitacora_periodos ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE cookie_preferences ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Helper function: get tenant_ids for current user
-- ============================================================

CREATE OR REPLACE FUNCTION get_user_tenant_ids()
RETURNS SETOF UUID AS $$
    SELECT tenant_id FROM memberships WHERE user_id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ============================================================
-- Helper function: check user role for a tenant
-- ============================================================

CREATE OR REPLACE FUNCTION user_has_role(p_tenant_id UUID, p_rol rol_usuario)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM memberships
        WHERE user_id = auth.uid()
        AND tenant_id = p_tenant_id
        AND rol = p_rol
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

CREATE OR REPLACE FUNCTION user_has_any_role(p_tenant_id UUID, p_roles rol_usuario[])
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM memberships
        WHERE user_id = auth.uid()
        AND tenant_id = p_tenant_id
        AND rol = ANY(p_roles)
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ============================================================
-- TENANTS policies
-- ============================================================

CREATE POLICY tenants_select ON tenants FOR SELECT
    USING (id IN (SELECT get_user_tenant_ids()));

CREATE POLICY tenants_update ON tenants FOR UPDATE
    USING (user_has_any_role(id, ARRAY['propietario'::rol_usuario, 'contador'::rol_usuario]));

CREATE POLICY tenants_insert ON tenants FOR INSERT
    WITH CHECK (true);

CREATE POLICY tenants_delete ON tenants FOR DELETE
    USING (user_has_role(id, 'propietario'));

-- ============================================================
-- USER_PROFILES policies
-- ============================================================

CREATE POLICY user_profiles_select ON user_profiles FOR SELECT
    USING (id = auth.uid() OR id IN (
        SELECT m2.user_id FROM memberships m1
        JOIN memberships m2 ON m1.tenant_id = m2.tenant_id
        WHERE m1.user_id = auth.uid()
    ));

CREATE POLICY user_profiles_update ON user_profiles FOR UPDATE
    USING (id = auth.uid());

CREATE POLICY user_profiles_insert ON user_profiles FOR INSERT
    WITH CHECK (id = auth.uid());

-- ============================================================
-- MEMBERSHIPS policies
-- ============================================================

CREATE POLICY memberships_select ON memberships FOR SELECT
    USING (tenant_id IN (SELECT get_user_tenant_ids()));

CREATE POLICY memberships_insert ON memberships FOR INSERT
    WITH CHECK (user_has_any_role(tenant_id, ARRAY['propietario'::rol_usuario, 'contador'::rol_usuario]));

CREATE POLICY memberships_delete ON memberships FOR DELETE
    USING (user_has_role(tenant_id, 'propietario'));

-- ============================================================
-- Standard tenant-scoped SELECT/INSERT/UPDATE/DELETE policies
-- Applied to all data tables
-- ============================================================

-- Macro: for tables that have tenant_id directly
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY[
        'periodos', 'cfdis', 'cfdi_nomina',
        'actividades', 'reglas_mapeo_cfdi', 'extractos_bancarios',
        'movimientos_bancarios', 'conciliaciones', 'documentos',
        'bitacora_periodos', 'chat_messages', 'consumo_ia'
    ])
    LOOP
        EXECUTE format(
            'CREATE POLICY %I_tenant_select ON %I FOR SELECT USING (tenant_id IN (SELECT get_user_tenant_ids()))',
            tbl, tbl
        );
        EXECUTE format(
            'CREATE POLICY %I_tenant_insert ON %I FOR INSERT WITH CHECK (tenant_id IN (SELECT get_user_tenant_ids()))',
            tbl, tbl
        );
        EXECUTE format(
            'CREATE POLICY %I_tenant_update ON %I FOR UPDATE USING (tenant_id IN (SELECT get_user_tenant_ids()) AND user_has_any_role(tenant_id, ARRAY[''propietario''::rol_usuario, ''contador''::rol_usuario]))',
            tbl, tbl
        );
        EXECUTE format(
            'CREATE POLICY %I_tenant_delete ON %I FOR DELETE USING (tenant_id IN (SELECT get_user_tenant_ids()) AND user_has_any_role(tenant_id, ARRAY[''propietario''::rol_usuario, ''contador''::rol_usuario]))',
            tbl, tbl
        );
    END LOOP;
END $$;

-- ============================================================
-- Child tables without tenant_id (join through parent)
-- ============================================================

-- cfdi_impuestos → cfdis.tenant_id
CREATE POLICY cfdi_impuestos_tenant_select ON cfdi_impuestos FOR SELECT
    USING (cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())));
CREATE POLICY cfdi_impuestos_tenant_insert ON cfdi_impuestos FOR INSERT
    WITH CHECK (cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())));
CREATE POLICY cfdi_impuestos_tenant_update ON cfdi_impuestos FOR UPDATE
    USING (cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())));
CREATE POLICY cfdi_impuestos_tenant_delete ON cfdi_impuestos FOR DELETE
    USING (cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())));

-- complementos_pago → cfdis.tenant_id
CREATE POLICY complementos_pago_tenant_select ON complementos_pago FOR SELECT
    USING (cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())));
CREATE POLICY complementos_pago_tenant_insert ON complementos_pago FOR INSERT
    WITH CHECK (cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())));
CREATE POLICY complementos_pago_tenant_update ON complementos_pago FOR UPDATE
    USING (cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())));
CREATE POLICY complementos_pago_tenant_delete ON complementos_pago FOR DELETE
    USING (cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())));

-- doctos_relacionados → complementos_pago → cfdis.tenant_id
CREATE POLICY doctos_relacionados_tenant_select ON doctos_relacionados FOR SELECT
    USING (complemento_id IN (SELECT id FROM complementos_pago WHERE cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids()))));
CREATE POLICY doctos_relacionados_tenant_insert ON doctos_relacionados FOR INSERT
    WITH CHECK (complemento_id IN (SELECT id FROM complementos_pago WHERE cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids()))));
CREATE POLICY doctos_relacionados_tenant_update ON doctos_relacionados FOR UPDATE
    USING (complemento_id IN (SELECT id FROM complementos_pago WHERE cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids()))));
CREATE POLICY doctos_relacionados_tenant_delete ON doctos_relacionados FOR DELETE
    USING (complemento_id IN (SELECT id FROM complementos_pago WHERE cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids()))));

-- impuestos_dr → doctos_relacionados → complementos_pago → cfdis.tenant_id
CREATE POLICY impuestos_dr_tenant_select ON impuestos_dr FOR SELECT
    USING (docto_id IN (SELECT id FROM doctos_relacionados WHERE complemento_id IN (SELECT id FROM complementos_pago WHERE cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())))));
CREATE POLICY impuestos_dr_tenant_insert ON impuestos_dr FOR INSERT
    WITH CHECK (docto_id IN (SELECT id FROM doctos_relacionados WHERE complemento_id IN (SELECT id FROM complementos_pago WHERE cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())))));
CREATE POLICY impuestos_dr_tenant_update ON impuestos_dr FOR UPDATE
    USING (docto_id IN (SELECT id FROM doctos_relacionados WHERE complemento_id IN (SELECT id FROM complementos_pago WHERE cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())))));
CREATE POLICY impuestos_dr_tenant_delete ON impuestos_dr FOR DELETE
    USING (docto_id IN (SELECT id FROM doctos_relacionados WHERE complemento_id IN (SELECT id FROM complementos_pago WHERE cfdi_id IN (SELECT id FROM cfdis WHERE tenant_id IN (SELECT get_user_tenant_ids())))));

-- ============================================================
-- BOVEDA: only propietario can access
-- ============================================================

CREATE POLICY boveda_efirma_select ON boveda_efirma FOR SELECT
    USING (user_has_role(tenant_id, 'propietario'));

CREATE POLICY boveda_efirma_insert ON boveda_efirma FOR INSERT
    WITH CHECK (user_has_role(tenant_id, 'propietario'));

CREATE POLICY boveda_efirma_update ON boveda_efirma FOR UPDATE
    USING (user_has_role(tenant_id, 'propietario'));

CREATE POLICY boveda_efirma_delete ON boveda_efirma FOR DELETE
    USING (user_has_role(tenant_id, 'propietario'));

CREATE POLICY boveda_bitacora_select ON boveda_bitacora FOR SELECT
    USING (user_has_role(tenant_id, 'propietario'));

CREATE POLICY boveda_bitacora_insert ON boveda_bitacora FOR INSERT
    WITH CHECK (tenant_id IN (SELECT get_user_tenant_ids()));

-- ============================================================
-- CONSENTIMIENTOS
-- ============================================================

CREATE POLICY consentimientos_select ON consentimientos FOR SELECT
    USING (tenant_id IN (SELECT get_user_tenant_ids()));

CREATE POLICY consentimientos_insert ON consentimientos FOR INSERT
    WITH CHECK (user_id = auth.uid() AND tenant_id IN (SELECT get_user_tenant_ids()));

-- ============================================================
-- INTENCIONES_PAGO: public insert, tenant-scoped read
-- ============================================================

CREATE POLICY intenciones_pago_insert ON intenciones_pago FOR INSERT
    WITH CHECK (true);

CREATE POLICY intenciones_pago_select ON intenciones_pago FOR SELECT
    USING (tenant_id IN (SELECT get_user_tenant_ids()));

-- ============================================================
-- GUEST SESSIONS
-- ============================================================

CREATE POLICY guest_sessions_select ON guest_sessions FOR SELECT
    USING (true);

CREATE POLICY guest_sessions_insert ON guest_sessions FOR INSERT
    WITH CHECK (true);

CREATE POLICY guest_sessions_update ON guest_sessions FOR UPDATE
    USING (true);

-- ============================================================
-- COOKIE PREFERENCES
-- ============================================================

CREATE POLICY cookie_preferences_select ON cookie_preferences FOR SELECT
    USING (user_id = auth.uid() OR guest_session_id IS NOT NULL);

CREATE POLICY cookie_preferences_insert ON cookie_preferences FOR INSERT
    WITH CHECK (true);

CREATE POLICY cookie_preferences_update ON cookie_preferences FOR UPDATE
    USING (user_id = auth.uid() OR guest_session_id IS NOT NULL);

-- ============================================================
-- Public tables (no tenant scope)
-- ============================================================

-- ejercicios, tarifas_resico, tarifas_art96, cuestionario_* are public read
ALTER TABLE ejercicios ENABLE ROW LEVEL SECURITY;
ALTER TABLE tarifas_resico ENABLE ROW LEVEL SECURITY;
ALTER TABLE tarifas_art96 ENABLE ROW LEVEL SECURITY;
ALTER TABLE cuestionario_nodos ENABLE ROW LEVEL SECURITY;
ALTER TABLE cuestionario_opciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE cuestionario_transiciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE lista_espera ENABLE ROW LEVEL SECURITY;

CREATE POLICY ejercicios_select ON ejercicios FOR SELECT USING (true);
CREATE POLICY tarifas_resico_select ON tarifas_resico FOR SELECT USING (true);
CREATE POLICY tarifas_art96_select ON tarifas_art96 FOR SELECT USING (true);
CREATE POLICY cuestionario_nodos_select ON cuestionario_nodos FOR SELECT USING (true);
CREATE POLICY cuestionario_opciones_select ON cuestionario_opciones FOR SELECT USING (true);
CREATE POLICY cuestionario_transiciones_select ON cuestionario_transiciones FOR SELECT USING (true);
CREATE POLICY lista_espera_insert ON lista_espera FOR INSERT WITH CHECK (true);
