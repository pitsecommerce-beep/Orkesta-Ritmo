-- Fix RLS gap: perfiles_obligacion is a public catalog table
-- but was missing ENABLE ROW LEVEL SECURITY and a SELECT policy.

ALTER TABLE perfiles_obligacion ENABLE ROW LEVEL SECURITY;

CREATE POLICY perfiles_obligacion_select ON perfiles_obligacion FOR SELECT USING (true);
