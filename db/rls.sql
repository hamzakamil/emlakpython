-- ============================================================================
-- RLS (Row Level Security) — tenant_id garantisi DB katmanında
-- Plan: docs/rls-plani.md
-- Uygulama (geliştirme):
--   Get-Content db\rls.sql -Raw | docker exec -i emlak_erp_db psql -U emlak -d emlak_erp
--
-- Notlar:
--   * Idempotent: tekrar çalıştırılabilir (DROP/CREATE POLICY IF EXISTS desenli).
--   * Geliştirmede FORCE uygulanmaz: tablo sahibi (emlak) RLS'den muaftır →
--     Django ve management komutları etkilenmez (plan §4).
--   * Üretimde ayrı uygulama rolü + FORCE ROW LEVEL SECURITY (plan §5).
-- ============================================================================

BEGIN;

-- 1) Bağlam yardımcı fonksiyonu: ayarlanmamış/boşsa NULL döner (güvenli varsayılan).
CREATE OR REPLACE FUNCTION app_mevcut_tenant() RETURNS bigint
LANGUAGE sql STABLE
AS $$
    SELECT NULLIF(current_setting('app.current_tenant', true), '')::bigint;
$$;

-- 2) tenant_id kolonlu tablolar — okuma + yazma korumalı policy'ler.
DO $do$
DECLARE
    tablo text;
BEGIN
    FOREACH tablo IN ARRAY ARRAY[
            'construction_pozgrubu',
            'construction_poz',
            'construction_malzeme',
            'construction_pozmalzemeiliskisi',
            'construction_pozfiyat',
            'construction_yapisinifibirimmaliyet',
            'construction_proje',
            'construction_pozplan',
            'construction_yfkpozversiyon',
            'construction_yfkfiyat',
            'construction_yfkrayic',
            'construction_yfkanaliz',
            'construction_yfkguncellemegecmisi',
            'real_estate_realestate',
            'users_user'
    ]
    LOOP
        BEGIN
            EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tablo);
            EXECUTE format('DROP POLICY IF EXISTS rls_tenant_izolasyon ON %I', tablo);
            EXECUTE format(
                'CREATE POLICY rls_tenant_izolasyon ON %I '
                || 'USING (tenant_id = app_mevcut_tenant()) '
                || 'WITH CHECK (tenant_id = app_mevcut_tenant())',
                tablo
            );
        EXCEPTION WHEN undefined_table THEN
            RAISE NOTICE 'Table % does not exist, skipping', tablo;
        END;
    END LOOP;
END
$do$;

-- 2b) tenant kolonsuz satır tabloları — üst kaydın tenant'ı üzerinden izole.
--     (FisSatiri → MuhasebeFisi, HakedisSatiri → Hakedis; uygulama katmanında
--     yalnızca üst kayıt üzerinden erişilir, DB katmanında da eşleşme zorunlu.)
DO $do$
BEGIN
    BEGIN
        ALTER TABLE accounting_fissatiri ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS rls_tenant_izolasyon ON accounting_fissatiri;
        CREATE POLICY rls_tenant_izolasyon ON accounting_fissatiri
            USING (
                EXISTS (
                    SELECT 1 FROM accounting_muhasebefisi f
                    WHERE f.id = fis_id AND f.tenant_id = app_mevcut_tenant()
                )
            )
            WITH CHECK (
                EXISTS (
                    SELECT 1 FROM accounting_muhasebefisi f
                    WHERE f.id = fis_id AND f.tenant_id = app_mevcut_tenant()
                )
            );
    EXCEPTION WHEN undefined_table THEN
        RAISE NOTICE 'Table accounting_fissatiri does not exist, skipping';
    END;
END
$do$;

DO $do$
BEGIN
    BEGIN
        ALTER TABLE construction_hakedissatiri ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS rls_tenant_izolasyon ON construction_hakedissatiri;
        CREATE POLICY rls_tenant_izolasyon ON construction_hakedissatiri
            USING (
                EXISTS (
                    SELECT 1 FROM construction_hakedis h
                    WHERE h.id = hakedis_id AND h.tenant_id = app_mevcut_tenant()
                )
            )
            WITH CHECK (
                EXISTS (
                    SELECT 1 FROM construction_hakedis h
                    WHERE h.id = hakedis_id AND h.tenant_id = app_mevcut_tenant()
                )
            );
    EXCEPTION WHEN undefined_table THEN
        RAISE NOTICE 'Table construction_hakedissatiri does not exist, skipping';
    END;
END
$do$;

COMMIT;

-- 4) ÜRETİM AŞAMASI (şimdilik kapalı — plan §5 kontrol listesiyle birlikte):
--    ALTER TABLE construction_poz FORCE ROW LEVEL SECURITY;  -- (her tablo için)
--    Uygulama rolü emlak_app (sahibi değil) + DATABASE_URL geçişi.

-- 5) Senaryo doğrulama rolü (yalnız geliştirme; prod'da gerçek uygulama rolü kullanılır).
DO $do$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rls_deneme') THEN
        CREATE ROLE rls_deneme LOGIN PASSWORD 'rls_deneme_dev';
    END IF;
END
$do$;

GRANT USAGE ON SCHEMA public TO rls_deneme;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO rls_deneme;
REVOKE SELECT ON users_user FROM rls_deneme;  -- kimlik/parola verisini koru

-- ============================================================================
-- SENARYO (elle doğrulama — psql; beklenen sonuçlar docs/rls-plani.md §6):
--   docker exec -it emlak_erp_db psql -U emlak -d emlak_erp
--
--   SET ROLE rls_deneme;
--   SELECT set_config('app.current_tenant', '1', false);
--   SELECT count(*) FROM construction_poz;              -- tenant 1 satırları
--   SELECT set_config('app.current_tenant', '2', false);
--   SELECT count(*) FROM construction_poz;              -- 0 (başka tenant)
--   SELECT set_config('app.current_tenant', '', false);
--   SELECT count(*) FROM construction_poz;              -- 0 (bağlam yok)
--   RESET ROLE;
--   SELECT count(*) FROM construction_poz;              -- sahibi bypass: tümü
-- ============================================================================
