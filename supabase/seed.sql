-- ============================================================
-- Centaurus - Supabase Seed Data
-- Execute this AFTER schema.sql
-- ============================================================

insert into authors (email, phone, dashboard_name, instagram_handle) values
('sara.johnson@xyz.com',    '+919876543210', 'Sara J.',        '@sarapoetry23'),
('arjun.mehta@gmail.com',   '+919988776655', 'Arjun Mehta',    '@arjunwrites'),
('priya.sharma@yahoo.com',  '+918877665544', 'Priya S.',       '@priyabooks'),
('rahul.das@outlook.com',   '+917766554433', 'Rahul Das',      '@rahul_author'),
('nisha.patel@hotmail.com', '+916655443322', 'Nisha P.',       '@nishapoems'),
('vikram.nair@gmail.com',   '+915544332211', 'Vikram Nair',    '@vikramstories');

insert into books (
    author_id,
    book_title,
    isbn,
    final_submission_date,
    book_live_date,
    royalty_status,
    add_on_services,
    sales_count,
    author_copy_dispatched,
    author_copy_dispatch_date
) values
(
    (select id from authors where email = 'sara.johnson@xyz.com'),
    'Echoes of Srinagar', '978-81-000001-1', '2025-10-15', '2025-11-20',
    'processing', '["Launch Sprint", "Media Relay"]', 1240, true, '2025-11-25'
),
(
    (select id from authors where email = 'arjun.mehta@gmail.com'),
    'The Algorithm of Stars', '978-81-000002-2', '2025-12-01', null,
    'pending', '[]', 0, false, null
),
(
    (select id from authors where email = 'priya.sharma@yahoo.com'),
    'Letters to Nobody', '978-81-000003-3', '2025-09-01', '2025-10-05',
    'paid', '["Awards Circuit"]', 340, false, null
),
(
    (select id from authors where email = 'rahul.das@outlook.com'),
    'Monsoon Diaries', '978-81-000004-4', '2025-08-10', '2025-09-15',
    'on_hold', '["Launch Sprint"]', 876, true, '2025-09-20'
),
(
    (select id from authors where email = 'nisha.patel@hotmail.com'),
    'Crimson Petals', '978-81-000005-5', '2025-11-01', '2025-12-10',
    'processing', '[]', 90, false, null
),
(
    (select id from authors where email = 'nisha.patel@hotmail.com'),
    'Violet Hours', '978-81-000006-6', '2025-07-15', '2025-08-20',
    'paid', '["Media Relay"]', 520, true, '2025-08-25'
),
(
    (select id from authors where email = 'vikram.nair@gmail.com'),
    'Tides of Coromandel', '978-81-000007-7', '2026-01-10', null,
    'pending', '["Launch Sprint", "Awards Circuit"]', 0, false, null
);

insert into knowledge_base (category, question, answer) values
('timeline', 'How long does publishing take?',
 'After final manuscript submission, the standard publishing timeline is 45 to 60 days. This includes editorial review, formatting, cover approval, metadata setup, ISBN registration, and distribution preparation.'),

('royalty', 'When do I get my royalty?',
 'Royalties are calculated quarterly in January, April, July, and October. Payments are typically processed within 60 days of quarter close. Status values include pending, processing, paid, and on_hold.'),

('dashboard', 'How do I access my dashboard?',
 'Use the Centaurus workspace link sent during onboarding and sign in with your registered email. If you cannot log in, reset your password first and then contact ops@centaurus.dev if the issue continues.'),

('addons', 'What is Launch Sprint?',
 'Launch Sprint is a release support program focused on launch coordination, category positioning, and marketplace visibility during the early release window.'),

('author_copy', 'When will I get my author copy?',
 'Physical author copies are typically dispatched within 7 to 10 business days of the book going live. Tracking details are sent after shipment is booked.'),

('sales', 'How do I check my book sales?',
 'Sales data refreshes on a rolling basis in the workspace and monthly consolidated reporting is usually sent during the first week of the month.');
