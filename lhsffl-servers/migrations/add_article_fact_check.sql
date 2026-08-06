-- Adds the fact_check column: an automated post-generation pass that lists
-- contradictions between the article and the data it was generated from.
-- Shown to admins during review; never blocks publishing.
ALTER TABLE Articles ADD COLUMN fact_check TEXT DEFAULT NULL;
