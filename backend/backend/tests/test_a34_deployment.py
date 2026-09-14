"""A34 Deployment Readiness Tests."""
import pathlib, os

BASE = pathlib.Path(r"c:/Users/HP Victus/OneDrive - Vignan University/Pictures/project/backend/backend")
FE   = pathlib.Path(r"c:/Users/HP Victus/OneDrive - Vignan University/Pictures/project/frontend/result-analysis-agent")

class TestBackendStartup:
    def test_app_imports_cleanly(self):
        from app.main import app
        assert app is not None

    def test_health_endpoint_200(self, client):
        assert client.get("/health").status_code == 200

    def test_docs_endpoint_200(self, client):
        assert client.get("/docs").status_code == 200

    def test_redoc_endpoint_200(self, client):
        assert client.get("/redoc").status_code == 200

    def test_root_endpoint_200(self, client):
        assert client.get("/").status_code == 200

    def test_openapi_json_200(self, client):
        assert client.get("/openapi.json").status_code == 200

class TestAllFilesCompile:
    def test_main_compiles(self):
        import py_compile
        py_compile.compile(str(BASE / "app/main.py"), doraise=True)

    def test_models_compile(self):
        import py_compile
        py_compile.compile(str(BASE / "app/models.py"), doraise=True)

    def test_config_compiles(self):
        import py_compile
        py_compile.compile(str(BASE / "app/config.py"), doraise=True)

    def test_auth_service_compiles(self):
        import py_compile
        py_compile.compile(str(BASE / "app/services/auth_service.py"), doraise=True)

    def test_ingestion_compiles(self):
        import py_compile
        py_compile.compile(str(BASE / "app/services/ingestion.py"), doraise=True)

    def test_metrics_compiles(self):
        import py_compile
        py_compile.compile(str(BASE / "app/services/metrics.py"), doraise=True)

    def test_narrative_compiles(self):
        import py_compile
        py_compile.compile(str(BASE / "app/services/narrative.py"), doraise=True)

    def test_report_generator_compiles(self):
        import py_compile
        py_compile.compile(str(BASE / "app/services/report_generator.py"), doraise=True)

    def test_mfa_compiles(self):
        import py_compile
        py_compile.compile(str(BASE / "app/security/mfa.py"), doraise=True)

    def test_auth_routes_compile(self):
        import py_compile
        py_compile.compile(str(BASE / "app/api/routes/auth.py"), doraise=True)

class TestEnvironmentConfiguration:
    def test_jwt_secret_configured(self):
        from app.config import get_settings
        get_settings.cache_clear()
        s = get_settings()
        assert s.JWT_SECRET_KEY
        assert len(s.JWT_SECRET_KEY) >= 32

    def test_jwt_secret_not_default_placeholder(self):
        from app.config import get_settings
        get_settings.cache_clear()
        s = get_settings()
        assert s.JWT_SECRET_KEY != "CHANGE_ME"

    def test_database_url_configured(self):
        from app.config import get_settings
        get_settings.cache_clear()
        s = get_settings()
        assert s.DATABASE_URL

    def test_upload_dir_setting(self):
        from app.config import get_settings
        get_settings.cache_clear()
        s = get_settings()
        assert s.UPLOAD_DIR

    def test_report_dir_setting(self):
        from app.config import get_settings
        get_settings.cache_clear()
        s = get_settings()
        assert s.REPORT_DIR

    def test_grade_map_parseable(self):
        from app.config import get_settings
        get_settings.cache_clear()
        s = get_settings()
        gm = s.grade_map
        assert isinstance(gm, dict)
        assert len(gm) > 0

    def test_internal_max_positive(self):
        from app.config import get_settings
        get_settings.cache_clear()
        assert get_settings().INTERNAL_MAX > 0

    def test_external_max_positive(self):
        from app.config import get_settings
        get_settings.cache_clear()
        assert get_settings().EXTERNAL_MAX > 0

    def test_total_max_positive(self):
        from app.config import get_settings
        get_settings.cache_clear()
        assert get_settings().TOTAL_MAX > 0

    def test_intervention_weights_sum_to_one(self):
        from app.config import get_settings
        get_settings.cache_clear()
        s = get_settings()
        total = (s.INTERVENTION_FAILURE_WEIGHT + s.INTERVENTION_HISTORICAL_WEIGHT +
                 s.INTERVENTION_SECTION_WEIGHT + s.INTERVENTION_CORRELATION_WEIGHT)
        assert abs(total - 1.0) < 0.01

class TestDirectoriesExist:
    def test_upload_dir_exists(self):
        from app.config import get_settings
        get_settings.cache_clear()
        s = get_settings()
        p = BASE / s.UPLOAD_DIR
        assert p.exists(), f"Upload dir missing: {p}"

    def test_reports_dir_exists(self):
        from app.config import get_settings
        get_settings.cache_clear()
        s = get_settings()
        p = BASE / s.REPORT_DIR
        assert p.exists(), f"Reports dir missing: {p}"

    def test_alembic_versions_dir_exists(self):
        assert (BASE / "alembic/versions").exists()

    def test_alembic_ini_exists(self):
        assert (BASE / "alembic.ini").exists()

class TestSecurityFiles:
    def test_env_file_exists(self):
        assert (BASE / ".env").exists()

    def test_env_example_exists(self):
        assert (BASE / ".env.example").exists()

    def test_gitignore_has_env(self):
        gi = BASE / ".gitignore"
        if gi.exists():
            content = gi.read_text()
            assert ".env" in content

class TestFrontendBuild:
    def test_frontend_dist_index_exists(self):
        dist = FE / "dist" / "index.html"
        assert dist.exists(), "Frontend dist/index.html missing. Run npm run build."

    def test_frontend_package_json_exists(self):
        assert (FE / "package.json").exists()

    def test_frontend_has_vite_config(self):
        assert (FE / "vite.config.ts").exists()
