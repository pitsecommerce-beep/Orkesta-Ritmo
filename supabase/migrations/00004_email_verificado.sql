-- Add email verification tracking to user_profiles.
-- Users can register and use the app without verifying,
-- but must verify before running tax calculations.

ALTER TABLE user_profiles
  ADD COLUMN email_verificado BOOLEAN NOT NULL DEFAULT false;

-- Auto-create a user_profiles row when a new auth user is created.
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_profiles (id, email, email_verificado)
  VALUES (NEW.id, NEW.email, false)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();
