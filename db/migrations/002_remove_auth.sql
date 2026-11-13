-- Drop logins. Users become Min and Su, named by a slug.
-- Safe to run more than once, including on a database created from the
-- current schema.sql (the columns may already be gone, or already present).

ALTER TABLE users ADD COLUMN IF NOT EXISTS slug TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS accent_color TEXT;

UPDATE users
SET slug = 'min'
WHERE id = 1 AND (slug IS NULL OR btrim(slug) = '');

UPDATE users
SET slug = 'su'
WHERE id = 2 AND (slug IS NULL OR btrim(slug) = '');

UPDATE users
SET slug = 'person-' || id::text
WHERE slug IS NULL OR btrim(slug) = '';

UPDATE users
SET accent_color = '#C2E0EA'
WHERE id = 1 AND (accent_color IS NULL OR btrim(accent_color) = '');

UPDATE users
SET accent_color = '#F8BDB2'
WHERE id = 2 AND (accent_color IS NULL OR btrim(accent_color) = '');

UPDATE users
SET accent_color = '#232C4B'
WHERE accent_color IS NULL OR btrim(accent_color) = '';

DROP INDEX IF EXISTS users_email_lower_idx;

ALTER TABLE users DROP COLUMN IF EXISTS email;
ALTER TABLE users DROP COLUMN IF EXISTS password_hash;

ALTER TABLE users ALTER COLUMN slug SET NOT NULL;
ALTER TABLE users ALTER COLUMN accent_color SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS users_slug_unique ON users (slug);
