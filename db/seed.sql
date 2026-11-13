-- Min&Su Library sample data.
-- Anniversary and meeting dates also live in config.py (TOGETHER_SINCE, MET_ON).
-- Chapter ranges:
--   0  2023-08-31 to 2023-10-31
--   1  2023-11-01 to 2024-10-31
--   2  2024-11-01 to 2025-10-31
--   3  2025-11-01 to 2026-10-31
--   4  2026-11-01 to 2027-10-31
-- There are no passwords. Min and Su are chosen in the browser.
-- Re-running this file does not duplicate rows and does not delete anything you added.

INSERT INTO users (id, display_name, slug, accent_color)
VALUES
    (1, 'Min', 'min', '#C2E0EA'),
    (2, 'Su', 'su', '#F8BDB2')
ON CONFLICT (id) DO NOTHING;

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

-- Explicit ids above do not move identity sequences on their own.
-- is_called is true only when the table already has rows, so the next insert is max(id)+1.
SELECT setval(
    pg_get_serial_sequence('users', 'id'),
    GREATEST(COALESCE((SELECT MAX(id) FROM users), 1), 1),
    (SELECT COUNT(*) FROM users) > 0
);

SELECT setval(
    pg_get_serial_sequence('chapters', 'id'),
    GREATEST(COALESCE((SELECT MAX(id) FROM chapters), 1), 1),
    (SELECT COUNT(*) FROM chapters) > 0
);

SELECT setval(
    pg_get_serial_sequence('photos', 'id'),
    GREATEST(COALESCE((SELECT MAX(id) FROM photos), 1), 1),
    (SELECT COUNT(*) FROM photos) > 0
);

SELECT setval(
    pg_get_serial_sequence('trips', 'id'),
    GREATEST(COALESCE((SELECT MAX(id) FROM trips), 1), 1),
    (SELECT COUNT(*) FROM trips) > 0
);

SELECT setval(
    pg_get_serial_sequence('dates', 'id'),
    GREATEST(COALESCE((SELECT MAX(id) FROM dates), 1), 1),
    (SELECT COUNT(*) FROM dates) > 0
);

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
