-- Keyword search next to the vectors (Module 5, the evidence-based improvement).
-- 'simple' splits words and lowercases them without stemming, so it works the same for French
-- words and for product codes such as PW-2200.
ALTER TABLE chunks ADD COLUMN words tsvector GENERATED ALWAYS AS (to_tsvector('simple', text)) STORED;
CREATE INDEX chunks_words ON chunks USING gin (words);
