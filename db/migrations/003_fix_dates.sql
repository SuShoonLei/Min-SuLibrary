-- Point an existing library at the real dates.
-- Safe to run more than once. Chapters are matched by number.
-- A title you already changed is left alone once the dates are correct.
-- Rows you added in the app are not deleted. Only the original placeholder
-- samples are removed, and only while their text is still the sample text.

ALTER TABLE chapters DROP CONSTRAINT IF EXISTS chapters_number_positive;
ALTER TABLE chapters ADD CONSTRAINT chapters_number_positive CHECK (number >= 0);

-- Fix the two placeholder chapters only while they still look like the sample.
-- A title, subtitle, or intro you already rewrote stays as you left it.
-- A cover you replaced is kept. A leftover placeholder image is cleared.
UPDATE chapters
SET
    start_date = DATE '2023-11-01',
    end_date = DATE '2024-10-31',
    title = CASE WHEN title = 'The First Year' THEN 'Chapter 1: Year One' ELSE title END,
    subtitle = CASE
        WHEN subtitle = 'From the first day to the first anniversary' THEN 'Day one to our first anniversary'
        ELSE subtitle
    END,
    intro_text = CASE
        WHEN intro_text IN (
            'A placeholder chapter for the first year. Replace this with the real story, from the day you started dating through the first anniversary.',
            'A placeholder chapter in the Min&Su Library. Replace this with the real story, from the day you started dating through the first anniversary.'
        ) THEN 'A placeholder for our first year together. Replace this with the real story.'
        ELSE intro_text
    END,
    cover_image = CASE
        WHEN cover_image LIKE 'assets/placeholder%' THEN NULL
        ELSE cover_image
    END
WHERE number = 1
  AND (
      title = 'The First Year'
      OR start_date = DATE '2024-03-14'
  );

UPDATE chapters
SET
    start_date = DATE '2024-11-01',
    end_date = DATE '2025-10-31',
    title = CASE WHEN title = 'The Second Year' THEN 'Chapter 2: Year Two' ELSE title END,
    subtitle = CASE
        WHEN subtitle = 'Still being written' THEN 'Our second year'
        ELSE subtitle
    END,
    intro_text = CASE
        WHEN intro_text = 'A placeholder for year two. Add the days you want to keep as they happen. Leave the end date empty while the chapter is still open.'
        THEN 'A placeholder for year two. Replace this when you are ready.'
        ELSE intro_text
    END,
    cover_image = CASE
        WHEN cover_image LIKE 'assets/placeholder%' THEN NULL
        ELSE cover_image
    END
WHERE number = 2
  AND (
      title = 'The Second Year'
      OR start_date = DATE '2025-03-14'
  );

SELECT setval(
    pg_get_serial_sequence('chapters', 'id'),
    GREATEST(COALESCE((SELECT MAX(id) FROM chapters), 1), 1),
    (SELECT COUNT(*) FROM chapters) > 0
);

INSERT INTO chapters (
    number, title, subtitle, start_date, end_date, cover_image, intro_text, created_by
)
SELECT
    chapter.number,
    chapter.title,
    chapter.subtitle,
    chapter.start_date,
    chapter.end_date,
    NULL,
    chapter.intro_text,
    author.id
FROM (
    VALUES
        (
            0,
            'Prologue: Before Us',
            'College, before we were a couple',
            DATE '2023-08-31',
            DATE '2023-10-31',
            'We met at college, before we were a couple. This chapter holds the days from that first meeting until the day we started dating.'
        ),
        (
            1,
            'Chapter 1: Year One',
            'Day one to our first anniversary',
            DATE '2023-11-01',
            DATE '2024-10-31',
            'A placeholder for our first year together. Replace this with the real story.'
        ),
        (
            2,
            'Chapter 2: Year Two',
            'Our second year',
            DATE '2024-11-01',
            DATE '2025-10-31',
            'A placeholder for year two. Replace this when you are ready.'
        ),
        (
            3,
            'Chapter 3: Year Three',
            'Our third year',
            DATE '2025-11-01',
            DATE '2026-10-31',
            'A placeholder for year three. Replace this when you are ready.'
        ),
        (
            4,
            'Chapter 4: Year Four',
            'The year we are in',
            DATE '2026-11-01',
            DATE '2027-10-31',
            'A placeholder for the current year. Replace this as the year happens.'
        )
) AS chapter (number, title, subtitle, start_date, end_date, intro_text)
JOIN users AS author ON author.slug = 'min'
ON CONFLICT (number) DO NOTHING;

DELETE FROM photos
WHERE id IN (1, 2, 3, 4, 5, 6)
  AND caption IN (
      'The day it became official',
      'A Tuesday that felt like a holiday',
      'Kitchen light, late',
      'One year in',
      'First morning of year two',
      'A walk with nowhere to be'
  );

DELETE FROM trips
WHERE id IN (1, 2, 3)
  AND title IN ('Coast road', 'Train weekend', 'Long weekend');

DELETE FROM dates
WHERE id IN (1, 2, 3, 4)
  AND title IN (
      'First dinner',
      'Rainy museum afternoon',
      'Breakfast for dinner',
      'Sunday market'
  );

DELETE FROM notes
WHERE id IN (1, 2, 3, 4)
  AND body IN (
      'Placeholder note. This is where a letter from Min to Su will live.',
      'Placeholder note. This one is from Su, so you can see both names on the page.',
      'Year two, still a placeholder. Replace this with something true.',
      'And the reply can live right beside it.'
  );

DELETE FROM achievements
WHERE id IN (1, 2, 3)
  AND title IN ('Said it out loud', 'First shared key', 'A year of Tuesdays');

SELECT setval(
    pg_get_serial_sequence('notes', 'id'),
    GREATEST(COALESCE((SELECT MAX(id) FROM notes), 1), 1),
    (SELECT COUNT(*) FROM notes) > 0
);

SELECT setval(
    pg_get_serial_sequence('achievements', 'id'),
    GREATEST(COALESCE((SELECT MAX(id) FROM achievements), 1), 1),
    (SELECT COUNT(*) FROM achievements) > 0
);

INSERT INTO notes (chapter_id, created_by, body, written_on)
SELECT c.id, u.id,
    'Su, this is a placeholder for the letter I want to write about meeting you. I will replace it with the real one.',
    DATE '2023-08-31'
FROM chapters c
JOIN users u ON u.slug = 'min'
WHERE c.number = 0
AND NOT EXISTS (
    SELECT 1 FROM notes n
    WHERE n.chapter_id = c.id AND n.created_by = u.id AND n.written_on = DATE '2023-08-31'
);

INSERT INTO notes (chapter_id, created_by, body, written_on)
SELECT c.id, u.id,
    'Min, this is a placeholder for my letter back. I will fill in what I actually remember.',
    DATE '2023-09-16'
FROM chapters c
JOIN users u ON u.slug = 'su'
WHERE c.number = 0
AND NOT EXISTS (
    SELECT 1 FROM notes n
    WHERE n.chapter_id = c.id AND n.created_by = u.id AND n.written_on = DATE '2023-09-16'
);

INSERT INTO achievements (chapter_id, created_by, title, achieved_on, description, photo, kind)
SELECT c.id, u.id, milestone.title, milestone.achieved_on, milestone.description, NULL, milestone.kind
FROM (
    VALUES
        (
            0, 'min', 'We met', DATE '2023-08-31',
            'The day we met at college. Replace this with what you actually remember.',
            'shared'
        ),
        (
            0, 'su', 'Min bought me my first drink', DATE '2023-09-05',
            'Min bought Su the first drink. Replace this with the real story.',
            'personal'
        ),
        (
            0, 'min', 'Our first hangout', DATE '2023-09-16',
            'The first time we hung out. Replace this with what we did.',
            'shared'
        ),
        (
            1, 'min', 'We became a couple', DATE '2023-11-01',
            'The day we started dating. Replace this with how it happened.',
            'shared'
        )
) AS milestone (chapter_number, author_slug, title, achieved_on, description, kind)
JOIN chapters c ON c.number = milestone.chapter_number
JOIN users u ON u.slug = milestone.author_slug
WHERE NOT EXISTS (
    SELECT 1 FROM achievements a
    WHERE a.chapter_id = c.id
      AND a.title = milestone.title
      AND a.achieved_on = milestone.achieved_on
);
