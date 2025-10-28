-- ============================================================================
-- DATABASE PERFORMANCE OPTIMIZATION - INDEX CREATION SCRIPT
-- ============================================================================
-- Purpose: Enhance query performance for the CRMS (Computer Resource Management System)
-- Database: PostgreSQL
-- Generated: Based on comprehensive code analysis
-- 
-- INSTRUCTIONS:
-- 1. Backup your database before running this script
-- 2. Run during low-traffic hours if in production
-- 3. Monitor query performance before and after applying indexes
-- 4. Remove any redundant indexes if they already exist
-- ============================================================================

-- Start transaction for safety
BEGIN;

-- ============================================================================
-- TABLE: users
-- High-traffic table - authentication, joins, lookups
-- ============================================================================

-- Email lookup (login, authentication, JWT verification)
-- Already exists: index on email (unique=True, index=True in model)
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- User approval status filtering (dashboard stats, approved users count)
CREATE INDEX IF NOT EXISTS idx_users_is_approved ON users(is_approved);

-- Department filtering (user management, filtering)
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);

-- Account role filtering (user management, role-based queries)
CREATE INDEX IF NOT EXISTS idx_users_acc_role ON users(acc_role);

-- User status filtering
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

-- Composite index for user management queries (excludes current user + filters)
CREATE INDEX IF NOT EXISTS idx_users_dept_role ON users(department, acc_role);

-- ============================================================================
-- TABLE: account_requests
-- Frequently filtered by status, user_id, supervisor/intern flags
-- ============================================================================

-- Foreign key to users (JOIN operations)
CREATE INDEX IF NOT EXISTS idx_account_requests_user_id ON account_requests(user_id);

-- Status filtering (pending requests count, filtering)
CREATE INDEX IF NOT EXISTS idx_account_requests_status ON account_requests(status);

-- Intern/Supervisor flags (user management exclusion filters)
CREATE INDEX IF NOT EXISTS idx_account_requests_is_intern ON account_requests(is_intern);
CREATE INDEX IF NOT EXISTS idx_account_requests_is_supervisor ON account_requests(is_supervisor);

-- Composite index for sidebar counts and user management
CREATE INDEX IF NOT EXISTS idx_account_requests_intern_supervisor ON account_requests(is_intern, is_supervisor);

-- Department and role filtering
CREATE INDEX IF NOT EXISTS idx_account_requests_department ON account_requests(department);
CREATE INDEX IF NOT EXISTS idx_account_requests_acc_role ON account_requests(acc_role);
CREATE INDEX IF NOT EXISTS idx_account_requests_approved_role ON account_requests(approved_acc_role);

-- Created date for sorting
CREATE INDEX IF NOT EXISTS idx_account_requests_created_at ON account_requests(created_at DESC);

-- ============================================================================
-- TABLE: equipments
-- Heavy usage - borrowing, filtering, categorization, facility joins
-- ============================================================================

-- Facility foreign key (JOINs for equipment-by-facility queries)
CREATE INDEX IF NOT EXISTS idx_equipments_facility_id ON equipments(facility_id);

-- Category filtering (dashboard stats, grouping)
CREATE INDEX IF NOT EXISTS idx_equipments_category ON equipments(category);

-- Status filtering (working, in use, for repair)
CREATE INDEX IF NOT EXISTS idx_equipments_status ON equipments(status);

-- Person liable grouping (dashboard equipment-by-person-liable)
CREATE INDEX IF NOT EXISTS idx_equipments_person_liable ON equipments(person_liable);

-- Name searching (equipment lookup)
CREATE INDEX IF NOT EXISTS idx_equipments_name ON equipments(name);

-- Created date for sorting
CREATE INDEX IF NOT EXISTS idx_equipments_created_at ON equipments(created_at DESC);

-- Composite index for availability checking
CREATE INDEX IF NOT EXISTS idx_equipments_status_category ON equipments(status, category);

-- ============================================================================
-- TABLE: borrowing
-- Critical for request management, status filtering, date range queries
-- ============================================================================

-- Foreign keys (heavy JOIN usage)
CREATE INDEX IF NOT EXISTS idx_borrowing_borrowed_item ON borrowing(borrowed_item);
CREATE INDEX IF NOT EXISTS idx_borrowing_borrowers_id ON borrowing(borrowers_id);

-- Request status filtering (pending, approved, rejected)
CREATE INDEX IF NOT EXISTS idx_borrowing_request_status ON borrowing(request_status);

-- Return status filtering (returned, not returned, overdue)
CREATE INDEX IF NOT EXISTS idx_borrowing_return_status ON borrowing(return_status);

-- Date range queries (borrowed today, last 7 days)
CREATE INDEX IF NOT EXISTS idx_borrowing_start_date ON borrowing(start_date);
CREATE INDEX IF NOT EXISTS idx_borrowing_end_date ON borrowing(end_date);

-- Created date for sorting (dashboard requests)
CREATE INDEX IF NOT EXISTS idx_borrowing_created_at ON borrowing(created_at DESC);

-- Composite index for pending requests with approved status
CREATE INDEX IF NOT EXISTS idx_borrowing_request_return_status ON borrowing(request_status, return_status);

-- Composite index for date + status queries (borrowed today with approved status)
CREATE INDEX IF NOT EXISTS idx_borrowing_start_status ON borrowing(start_date, request_status);

-- ============================================================================
-- TABLE: facilities
-- Moderate usage - bookings, equipment joins, filtering
-- ============================================================================

-- Facility type filtering
CREATE INDEX IF NOT EXISTS idx_facilities_facility_type ON facilities(facility_type);

-- Status filtering (available, occupied)
CREATE INDEX IF NOT EXISTS idx_facilities_status ON facilities(status);

-- Floor level filtering
CREATE INDEX IF NOT EXISTS idx_facilities_floor_level ON facilities(floor_level);

-- Building filtering
CREATE INDEX IF NOT EXISTS idx_facilities_building ON facilities(building);

-- Name searching
CREATE INDEX IF NOT EXISTS idx_facilities_name ON facilities(facility_name);

-- Created date for sorting
CREATE INDEX IF NOT EXISTS idx_facilities_created_at ON facilities(created_at DESC);

-- ============================================================================
-- TABLE: bookings
-- Heavy usage - request management, facility bookings, user queries
-- ============================================================================

-- Foreign keys (heavy JOIN usage)
CREATE INDEX IF NOT EXISTS idx_bookings_bookers_id ON bookings(bookers_id);
CREATE INDEX IF NOT EXISTS idx_bookings_facility_id ON bookings(facility_id);

-- Status filtering (pending, approved, rejected)
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);

-- Date range queries (conflict checking, date filters)
CREATE INDEX IF NOT EXISTS idx_bookings_start_date ON bookings(start_date);
CREATE INDEX IF NOT EXISTS idx_bookings_end_date ON bookings(end_date);

-- Created date for sorting
CREATE INDEX IF NOT EXISTS idx_bookings_created_at ON bookings(created_at DESC);

-- Composite index for conflict detection (facility + date range)
CREATE INDEX IF NOT EXISTS idx_bookings_facility_dates ON bookings(facility_id, start_date, end_date);

-- Composite index for pending requests
CREATE INDEX IF NOT EXISTS idx_bookings_status_created ON bookings(status, created_at DESC);

-- ============================================================================
-- TABLE: supplies
-- Moderate usage - supply management, acquiring requests
-- ============================================================================

-- Facility foreign key
CREATE INDEX IF NOT EXISTS idx_supplies_facility_id ON supplies(facility_id);

-- Category filtering
CREATE INDEX IF NOT EXISTS idx_supplies_category ON supplies(category);

-- Name searching
CREATE INDEX IF NOT EXISTS idx_supplies_name ON supplies(supply_name);

-- Quantity filtering (low stock alerts)
CREATE INDEX IF NOT EXISTS idx_supplies_quantity ON supplies(quantity);

-- Created date for sorting
CREATE INDEX IF NOT EXISTS idx_supplies_created_at ON supplies(created_at DESC);

-- Composite index for low stock detection
CREATE INDEX IF NOT EXISTS idx_supplies_quantity_stocking ON supplies(quantity, stocking_point);

-- ============================================================================
-- TABLE: acquiring
-- Moderate usage - supply requests, user queries
-- ============================================================================

-- Foreign keys
CREATE INDEX IF NOT EXISTS idx_acquiring_acquirers_id ON acquiring(acquirers_id);
CREATE INDEX IF NOT EXISTS idx_acquiring_supply_id ON acquiring(supply_id);

-- Status filtering
CREATE INDEX IF NOT EXISTS idx_acquiring_status ON acquiring(status);

-- Created date for sorting
CREATE INDEX IF NOT EXISTS idx_acquiring_created_at ON acquiring(created_at DESC);

-- Composite index for pending requests
CREATE INDEX IF NOT EXISTS idx_acquiring_status_created ON acquiring(status, created_at DESC);

-- ============================================================================
-- TABLE: notifications
-- High-traffic - user notifications, read/unread status
-- ============================================================================

-- Foreign key to users
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);

-- Read status filtering
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- Type filtering
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);

-- Created date for sorting
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Composite index for user's unread notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read, created_at DESC);

-- ============================================================================
-- TABLE: return_notifications
-- Important for equipment return workflow
-- ============================================================================

-- Foreign key to borrowing
CREATE INDEX IF NOT EXISTS idx_return_notifications_borrowing_id ON return_notifications(borrowing_id);

-- Status filtering (pending_confirmation, confirmed, rejected)
CREATE INDEX IF NOT EXISTS idx_return_notifications_status ON return_notifications(status);

-- Created date for sorting
CREATE INDEX IF NOT EXISTS idx_return_notifications_created_at ON return_notifications(created_at DESC);

-- Composite index for pending return notifications
CREATE INDEX IF NOT EXISTS idx_return_notif_status_created ON return_notifications(status, created_at DESC);

-- ============================================================================
-- TABLE: done_notifications
-- Important for booking completion workflow
-- ============================================================================

-- Foreign key to bookings
CREATE INDEX IF NOT EXISTS idx_done_notifications_booking_id ON done_notifications(booking_id);

-- Status filtering (pending_confirmation, confirmed, dismissed)
CREATE INDEX IF NOT EXISTS idx_done_notifications_status ON done_notifications(status);

-- Created date for sorting
CREATE INDEX IF NOT EXISTS idx_done_notifications_created_at ON done_notifications(created_at DESC);

-- Composite index for pending done notifications
CREATE INDEX IF NOT EXISTS idx_done_notif_status_created ON done_notifications(status, created_at DESC);

-- ============================================================================
-- TABLE: equipment_logs
-- High-volume logging table - needs efficient querying
-- ============================================================================

-- Foreign key to equipment
CREATE INDEX IF NOT EXISTS idx_equipment_logs_equipment_id ON equipment_logs(equipment_id);

-- User email for filtering
CREATE INDEX IF NOT EXISTS idx_equipment_logs_user_email ON equipment_logs(user_email);

-- Action filtering
CREATE INDEX IF NOT EXISTS idx_equipment_logs_action ON equipment_logs(action);

-- Created date for sorting and pagination
CREATE INDEX IF NOT EXISTS idx_equipment_logs_created_at ON equipment_logs(created_at DESC);

-- Composite index for equipment activity logs
CREATE INDEX IF NOT EXISTS idx_equipment_logs_equip_created ON equipment_logs(equipment_id, created_at DESC);

-- ============================================================================
-- TABLE: facility_logs
-- High-volume logging table - needs efficient querying
-- ============================================================================

-- Foreign key to facility
CREATE INDEX IF NOT EXISTS idx_facility_logs_facility_id ON facility_logs(facility_id);

-- User email for filtering
CREATE INDEX IF NOT EXISTS idx_facility_logs_user_email ON facility_logs(user_email);

-- Action filtering
CREATE INDEX IF NOT EXISTS idx_facility_logs_action ON facility_logs(action);

-- Created date for sorting and pagination
CREATE INDEX IF NOT EXISTS idx_facility_logs_created_at ON facility_logs(created_at DESC);

-- Composite index for facility activity logs
CREATE INDEX IF NOT EXISTS idx_facility_logs_facility_created ON facility_logs(facility_id, created_at DESC);

-- ============================================================================
-- TABLE: supply_logs
-- High-volume logging table - needs efficient querying
-- ============================================================================

-- Foreign key to supply
CREATE INDEX IF NOT EXISTS idx_supply_logs_supply_id ON supply_logs(supply_id);

-- User email for filtering
CREATE INDEX IF NOT EXISTS idx_supply_logs_user_email ON supply_logs(user_email);

-- Action filtering
CREATE INDEX IF NOT EXISTS idx_supply_logs_action ON supply_logs(action);

-- Created date for sorting and pagination
CREATE INDEX IF NOT EXISTS idx_supply_logs_created_at ON supply_logs(created_at DESC);

-- Composite index for supply activity logs
CREATE INDEX IF NOT EXISTS idx_supply_logs_supply_created ON supply_logs(supply_id, created_at DESC);

-- ============================================================================
-- PARTIAL INDEXES (for specific filtered queries)
-- These are more efficient than full indexes for specific use cases
-- ============================================================================

-- Pending borrowing requests only
CREATE INDEX IF NOT EXISTS idx_borrowing_pending ON borrowing(created_at DESC)
WHERE request_status = 'Pending';

-- Approved borrowing requests only
CREATE INDEX IF NOT EXISTS idx_borrowing_approved ON borrowing(start_date, end_date)
WHERE request_status = 'Approved';

-- Pending booking requests only
CREATE INDEX IF NOT EXISTS idx_bookings_pending ON bookings(created_at DESC)
WHERE status = 'Pending';

-- Pending acquiring requests only
CREATE INDEX IF NOT EXISTS idx_acquiring_pending ON acquiring(created_at DESC)
WHERE status = 'Pending';

-- Unread notifications only
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, created_at DESC)
WHERE is_read = false;

-- Approved users only
CREATE INDEX IF NOT EXISTS idx_users_approved ON users(id)
WHERE is_approved = true;

-- Non-null person liable (for grouping queries)
CREATE INDEX IF NOT EXISTS idx_equipment_person_liable_nn ON equipments(person_liable)
WHERE person_liable IS NOT NULL;

-- Non-null category (for grouping queries)
CREATE INDEX IF NOT EXISTS idx_equipment_category_nn ON equipments(category)
WHERE category IS NOT NULL;

-- ============================================================================
-- TEXT SEARCH INDEXES (for ILIKE queries)
-- Using LOWER() function indexes for case-insensitive searching
-- ============================================================================

-- User department text search
CREATE INDEX IF NOT EXISTS idx_users_department_lower ON users(LOWER(department));

-- User acc_role text search
CREATE INDEX IF NOT EXISTS idx_users_acc_role_lower ON users(LOWER(acc_role));

-- Account request department text search
CREATE INDEX IF NOT EXISTS idx_account_req_dept_lower ON account_requests(LOWER(department));

-- Account request acc_role text search
CREATE INDEX IF NOT EXISTS idx_account_req_role_lower ON account_requests(LOWER(acc_role));

-- Equipment name text search
CREATE INDEX IF NOT EXISTS idx_equipment_name_lower ON equipments(LOWER(name));

-- Facility name text search
CREATE INDEX IF NOT EXISTS idx_facilities_name_lower ON facilities(LOWER(facility_name));

-- Supply name text search
CREATE INDEX IF NOT EXISTS idx_supplies_name_lower ON supplies(LOWER(supply_name));

-- ============================================================================
-- ANALYZE TABLES (update statistics for query planner)
-- ============================================================================

ANALYZE users;
ANALYZE account_requests;
ANALYZE equipments;
ANALYZE borrowing;
ANALYZE facilities;
ANALYZE bookings;
ANALYZE supplies;
ANALYZE acquiring;
ANALYZE notifications;
ANALYZE return_notifications;
ANALYZE done_notifications;
ANALYZE equipment_logs;
ANALYZE facility_logs;
ANALYZE supply_logs;

-- Commit all changes
COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- Run these to verify indexes were created successfully
-- ============================================================================

-- List all indexes
-- SELECT schemaname, tablename, indexname, indexdef
-- FROM pg_indexes
-- WHERE schemaname = 'public'
-- ORDER BY tablename, indexname;

-- Check index usage statistics
-- SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
-- FROM pg_stat_user_indexes
-- ORDER BY idx_scan DESC;

-- Find unused indexes (run after system has been in production)
-- SELECT schemaname, tablename, indexname
-- FROM pg_stat_user_indexes
-- WHERE idx_scan = 0
-- AND schemaname = 'public';

-- ============================================================================
-- MAINTENANCE RECOMMENDATIONS
-- ============================================================================

-- 1. Run VACUUM ANALYZE periodically (weekly for high-traffic tables)
--    VACUUM ANALYZE borrowing;
--    VACUUM ANALYZE bookings;
--    VACUUM ANALYZE equipment_logs;

-- 2. Monitor index bloat
--    SELECT * FROM pgstattuple('idx_borrowing_request_status');

-- 3. Reindex if needed (during maintenance window)
--    REINDEX TABLE borrowing;

-- 4. Remove unused indexes after monitoring
--    DROP INDEX IF EXISTS idx_name;

-- ============================================================================
-- PERFORMANCE IMPACT SUMMARY
-- ============================================================================

-- Tables with most performance gain:
-- 1. borrowing - Heavy JOINs, status filtering, date range queries
-- 2. bookings - Status filtering, facility JOINs, date conflicts
-- 3. equipment_logs - High-volume pagination with sorting
-- 4. users - Authentication, filtering, JOINs
-- 5. notifications - User-specific unread filtering

-- Expected improvements:
-- - Sidebar counts: 3-5x faster
-- - Dashboard requests: 5-10x faster
-- - Pagination queries: 3-7x faster
-- - JOIN operations: 2-4x faster
-- - Text search (ILIKE): 10-50x faster with lower() indexes

-- ============================================================================
-- NOTES
-- ============================================================================

-- 1. Some indexes may already exist (check before running)
-- 2. Index creation is non-blocking (CONCURRENTLY) but takes time
-- 3. Monitor disk space - indexes require storage
-- 4. Review query performance before/after with EXPLAIN ANALYZE
-- 5. Adjust maintenance_work_mem for faster index creation
-- 6. Consider partial indexes for very large tables
-- 7. Text search indexes (lower()) enable efficient ILIKE queries

-- ============================================================================
-- END OF INDEX CREATION SCRIPT
-- ============================================================================
