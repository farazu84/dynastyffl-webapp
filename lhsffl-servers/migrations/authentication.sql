-- =============================================================================
-- Authentication Migrations
-- =============================================================================
-- All schema changes related to the authentication system live here.
-- Migrations are written to be idempotent where possible (safe to re-run).
--
-- Tracked by: migrations/migrate.py (_schema_migrations table)
-- To apply:   python migrations/migrate.py
-- To check:   python migrations/migrate.py --status
-- =============================================================================


-- -----------------------------------------------------------------------------
-- [auth-002] Add email and google_id columns to Users
-- Date: 2026-02-19
--
-- email:     used as the human-readable identity from Google OAuth and as a
--            future login identifier alongside user_name.
-- google_id: the stable unique ID Google returns for a user (the 'sub' claim
--            in their ID token). Used to look up or create a User record on
--            Google OAuth callback without relying on email, which can change.
-- -----------------------------------------------------------------------------
ALTER TABLE Users
    ADD COLUMN email     VARCHAR(255) UNIQUE DEFAULT NULL,
    ADD COLUMN google_id VARCHAR(255) UNIQUE DEFAULT NULL;


-- -----------------------------------------------------------------------------
-- [auth-003] Make Users.password nullable — Google-only auth
-- Date: 2026-02-21
--
-- Since the app uses Google OAuth exclusively, passwords are no longer set
-- on user records. The column is kept for potential future use but is now
-- nullable with no default.
-- -----------------------------------------------------------------------------
ALTER TABLE Users MODIFY COLUMN password VARCHAR(256) NULL DEFAULT NULL;


-- -----------------------------------------------------------------------------
-- [auth-001] Widen Users.password column to support hashed passwords
-- Date: 2026-02-19
--
-- The password column was VARCHAR(64), which is too narrow for any standard
-- password hash. Werkzeug's PBKDF2-SHA256 (used via set_password/check_password
-- on the Users model) produces ~93-character hashes. VARCHAR(256) comfortably
-- accommodates all common hashing algorithms including future ones.
-- -----------------------------------------------------------------------------
ALTER TABLE Users MODIFY COLUMN password VARCHAR(256) NOT NULL DEFAULT '';
