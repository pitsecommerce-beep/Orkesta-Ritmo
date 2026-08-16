-- RPC function for onboarding: creates tenant + membership atomically.
-- Uses SECURITY DEFINER to bypass RLS (the chicken-and-egg problem:
-- INSERT into memberships requires an existing role, but this IS the first role).

CREATE OR REPLACE FUNCTION crear_tenant_con_membership(
    p_rfc VARCHAR,
    p_nombre VARCHAR,
    p_tipo_persona tipo_persona,
    p_regimen regimen_fiscal
) RETURNS UUID AS $$
DECLARE
    v_tenant_id UUID;
    v_user_id UUID;
BEGIN
    v_user_id := auth.uid();
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Usuario no autenticado';
    END IF;

    INSERT INTO tenants (rfc, nombre, tipo_persona, regimen)
    VALUES (p_rfc, p_nombre, p_tipo_persona, p_regimen)
    RETURNING id INTO v_tenant_id;

    INSERT INTO memberships (tenant_id, user_id, rol)
    VALUES (v_tenant_id, v_user_id, 'propietario');

    RETURN v_tenant_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
