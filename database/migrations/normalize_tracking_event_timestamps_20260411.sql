-- Normalize platform tracking timestamps from JavaScript milliseconds to Unix seconds.
-- Safe to re-run: rows already stored in seconds are not modified.

UPDATE tracking_events
SET created_at = FLOOR(created_at / 1000)
WHERE created_at > 9999999999;
