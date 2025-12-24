-- =============================================================================
-- PostgreSQL Initialization Script
-- =============================================================================
-- Bu script container ilk başlatıldığında çalışır

-- Ana veritabanı (docker-compose'da oluşturuluyor, extensions ekle)
\c globalmain;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Analytics veritabanı oluştur
SELECT 'CREATE DATABASE globalmain_analytics'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'globalmain_analytics')\gexec

\c globalmain_analytics;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Logs veritabanı oluştur
SELECT 'CREATE DATABASE globalmain_logs'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'globalmain_logs')\gexec

\c globalmain_logs;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Bilgi mesajı
\echo '✅ Tüm veritabanları başarıyla oluşturuldu!'
\echo '  - globalmain'
\echo '  - globalmain_analytics'
\echo '  - globalmain_logs'