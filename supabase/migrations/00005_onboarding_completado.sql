-- Track whether the user has completed or skipped the dashboard onboarding tour.

ALTER TABLE user_profiles
  ADD COLUMN onboarding_completado BOOLEAN NOT NULL DEFAULT false;

-- Update the trigger to include the new column default.
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_profiles (id, email, email_verificado, onboarding_completado)
  VALUES (NEW.id, NEW.email, false, false)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
