-- Add fecha_nacimiento to user_profiles for the intro questionnaire.

ALTER TABLE user_profiles
  ADD COLUMN fecha_nacimiento DATE;
