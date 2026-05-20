-- ============================================================
-- BookLeaf AI Automation — Supabase Seed Data
-- Execute this AFTER schema.sql
-- Spec Reference: Section 5.2
-- ============================================================

-- ============================================================
-- SEED: Authors (6 profiles covering all test scenarios)
-- ============================================================
insert into authors (email, phone, dashboard_name, instagram_handle) values
('sara.johnson@xyz.com',    '+919876543210', 'Sara J.',        '@sarapoetry23'),
('arjun.mehta@gmail.com',   '+919988776655', 'Arjun Mehta',    '@arjunwrites'),
('priya.sharma@yahoo.com',  '+918877665544', 'Priya S.',       '@priyabooks'),
('rahul.das@outlook.com',   '+917766554433', 'Rahul Das',      '@rahul_author'),
('nisha.patel@hotmail.com', '+916655443322', 'Nisha P.',       '@nishapoems'),
('vikram.nair@gmail.com',   '+915544332211', 'Vikram Nair',    '@vikramstories');

-- ============================================================
-- SEED: Books (7 rows covering every intent type and edge case)
-- ============================================================
insert into books (author_id, book_title, isbn, final_submission_date, book_live_date,
    royalty_status, add_on_services, sales_count, author_copy_dispatched, author_copy_dispatch_date)
values

-- Author 1: Sara J. — Book LIVE, royalty processing, has add-ons, author copy dispatched
(
    (select id from authors where email = 'sara.johnson@xyz.com'),
    'Echoes of Srinagar', '978-81-000001-1', '2025-10-15', '2025-11-20',
    'processing', '["Bestseller Package", "PR Push"]', 1240, true, '2025-11-25'
),

-- Author 2: Arjun Mehta — Book NOT live (pending), no live date
(
    (select id from authors where email = 'arjun.mehta@gmail.com'),
    'The Algorithm of Stars', '978-81-000002-2', '2025-12-01', null,
    'pending', '[]', 0, false, null
),

-- Author 3: Priya Sharma — Royalty PAID, author copy NOT dispatched
(
    (select id from authors where email = 'priya.sharma@yahoo.com'),
    'Letters to Nobody', '978-81-000003-3', '2025-09-01', '2025-10-05',
    'paid', '["Award Submission"]', 340, false, null
),

-- Author 4: Rahul Das — Royalty ON HOLD, author copy dispatched
(
    (select id from authors where email = 'rahul.das@outlook.com'),
    'Monsoon Diaries', '978-81-000004-4', '2025-08-10', '2025-09-15',
    'on_hold', '["Bestseller Package"]', 876, true, '2025-09-20'
),

-- Author 5: Nisha Patel — MULTIPLE BOOKS (tests disambiguation)
(
    (select id from authors where email = 'nisha.patel@hotmail.com'),
    'Crimson Petals', '978-81-000005-5', '2025-11-01', '2025-12-10',
    'processing', '[]', 90, false, null
),
(
    (select id from authors where email = 'nisha.patel@hotmail.com'),
    'Violet Hours', '978-81-000006-6', '2025-07-15', '2025-08-20',
    'paid', '["PR Push"]', 520, true, '2025-08-25'
),

-- Author 6: Vikram Nair — Recently submitted, no live date, multiple add-ons
(
    (select id from authors where email = 'vikram.nair@gmail.com'),
    'Tides of Coromandel', '978-81-000007-7', '2026-01-10', null,
    'pending', '["Bestseller Package", "Award Submission"]', 0, false, null
);

-- ============================================================
-- SEED: Knowledge Base (6 structured FAQ entries)
-- ============================================================
insert into knowledge_base (category, question, answer) values
('timeline', 'How long does publishing take?',
 'After final manuscript submission, the standard publishing timeline is 45 to 60 days. This includes editorial review (7-10 days), formatting and layout (10-15 days), cover design approval (5-7 days), ISBN registration (3-5 days), and distribution setup across platforms (7-10 days).'),

('royalty', 'When do I get my royalty?',
 'Royalties are calculated quarterly: January, April, July, and October. Payments are processed within 60 days of the quarter close. Status values: pending (not yet calculated), processing (payment initiated), paid (funds transferred), on_hold (bank details issue or disputed sales).'),

('dashboard', 'How do I access my dashboard?',
 'The author dashboard is at dashboard.bookleafpub.com. Login uses your registered email. If you cannot log in, use "Forgot Password" or email support@bookleafpub.in.'),

('addons', 'What is the Bestseller Package?',
 'The Bestseller Package includes Amazon category targeting, 50 review outreach emails, and 30 days of social media graphics. Active for 90 days from book live date.'),

('author_copy', 'When will I get my author copy?',
 'Physical author copies are dispatched within 7-10 business days of the book going live. Tracking details are sent to the registered email. Standard delivery: 5-7 business days. International: 15-21 business days.'),

('sales', 'How do I check my book sales?',
 'Sales data updates every 48 hours on the dashboard. Monthly consolidated reports are emailed on the 5th of every month. Includes Amazon India, Amazon Global, Flipkart, BookLeaf Store.');

-- ============================================================
-- VERIFICATION QUERIES (run these to confirm seed success)
-- ============================================================
-- select count(*) from authors;         -- expected: 6
-- select count(*) from books;           -- expected: 7
-- select count(*) from knowledge_base;  -- expected: 6
-- select b.book_title, a.email, b.royalty_status, b.book_live_date
--   from books b join authors a on b.author_id = a.id;
