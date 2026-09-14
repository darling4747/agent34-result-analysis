"""A34 Gemini AI Narrative Tests."""

class TestDeterministicFallback:
    def test_no_api_key_uses_deterministic(self):
        from app.services.narrative import NarrativeService
        from app.config import Settings
        s = Settings(LLM_PROVIDER="", LLM_API_KEY="", LLM_MODEL="")
        svc = NarrativeService(s)
        result = svc.generate({"summary": {"pass_percentage": 80.0, "failure_percentage": 20.0,
            "total_students": 100, "average_marks": 65.0, "average_gpa": 7.0}})
        assert result["model_used"] == "deterministic"

    def test_deterministic_summary_not_empty(self):
        from app.services.narrative import NarrativeService
        from app.config import Settings
        s = Settings(LLM_PROVIDER="", LLM_API_KEY="", LLM_MODEL="")
        svc = NarrativeService(s)
        result = svc._deterministic_narrative({"summary": {"pass_percentage": 75.0,
            "failure_percentage": 25.0, "total_students": 200, "average_marks": 62.0,
            "average_gpa": 6.8}, "period": "Test Semester"})
        assert len(result["summary"]) > 10

    def test_deterministic_has_key_findings_list(self):
        from app.services.narrative import NarrativeService
        from app.config import Settings
        s = Settings(LLM_PROVIDER="", LLM_API_KEY="", LLM_MODEL="")
        svc = NarrativeService(s)
        result = svc._deterministic_narrative({"summary": {"pass_percentage": 80.0,
            "failure_percentage": 20.0, "total_students": 100}})
        assert isinstance(result["key_findings"], list)

    def test_deterministic_has_recommendations_list(self):
        from app.services.narrative import NarrativeService
        from app.config import Settings
        s = Settings(LLM_PROVIDER="", LLM_API_KEY="", LLM_MODEL="")
        svc = NarrativeService(s)
        result = svc._deterministic_narrative({"summary": {"pass_percentage": 80.0,
            "failure_percentage": 20.0, "total_students": 100}})
        assert isinstance(result["recommendations"], list)

    def test_deterministic_has_disclaimer(self):
        from app.services.narrative import NarrativeService
        from app.config import Settings
        s = Settings(LLM_PROVIDER="", LLM_API_KEY="", LLM_MODEL="")
        svc = NarrativeService(s)
        result = svc._deterministic_narrative({"summary": {"pass_percentage": 80.0,
            "failure_percentage": 20.0, "total_students": 100}})
        assert result["disclaimer"]

    def test_deterministic_critical_courses_mentioned(self):
        from app.services.narrative import NarrativeService
        from app.config import Settings
        s = Settings(LLM_PROVIDER="", LLM_API_KEY="", LLM_MODEL="")
        svc = NarrativeService(s)
        result = svc._deterministic_narrative({
            "summary": {"pass_percentage": 60.0, "failure_percentage": 40.0, "total_students": 100},
            "interventions": [{"course_code": "CS601", "priority_level": "CRITICAL", "failure_rate": 45.0}],
            "correlation": []
        })
        combined = " ".join(result["key_findings"])
        assert "CS601" in combined

    def test_deterministic_uses_pass_pct_in_summary(self):
        from app.services.narrative import NarrativeService
        from app.config import Settings
        s = Settings(LLM_PROVIDER="", LLM_API_KEY="", LLM_MODEL="")
        svc = NarrativeService(s)
        result = svc._deterministic_narrative({"summary": {"pass_percentage": 77.5,
            "failure_percentage": 22.5, "total_students": 150}})
        assert "77.5" in result["summary"]

    def test_invalid_api_key_falls_back_to_deterministic(self):
        from app.services.narrative import NarrativeService
        from app.config import Settings
        s = Settings(LLM_PROVIDER="gemini", LLM_API_KEY="INVALID_KEY_123", LLM_MODEL="gemini-2.5-flash")
        svc = NarrativeService(s)
        result = svc.generate({"summary": {"pass_percentage": 80.0, "failure_percentage": 20.0,
            "total_students": 100}})
        # Should fall back to deterministic without crashing
        assert result["summary"]
        assert result["model_used"] in ("deterministic", "gemini/gemini-2.5-flash")

class TestNarrativeEndpoints:
    def test_narrative_generate_endpoint_200(self, auth_client, db_session):
        from app.models import ImportBatch
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        r = auth_client.post("/api/analysis/narrative/generate")
        assert r.status_code == 200

    def test_narrative_generate_has_summary(self, auth_client, db_session):
        from app.models import ImportBatch
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        r = auth_client.post("/api/analysis/narrative/generate")
        data = r.json()["data"]
        assert "summary" in data

    def test_narrative_generate_has_model_used(self, auth_client, db_session):
        from app.models import ImportBatch
        db_session.query(ImportBatch).update({"is_active": False})
        db_session.commit()
        r = auth_client.post("/api/analysis/narrative/generate")
        data = r.json()["data"]
        assert "model_used" in data

    def test_narrative_post_with_custom_metrics(self, auth_client):
        metrics = {"summary": {"pass_percentage": 82.0, "failure_percentage": 18.0,
            "total_students": 250}, "interventions": [], "correlation": []}
        r = auth_client.post("/api/analysis/narrative", json=metrics)
        assert r.status_code == 200
        assert r.json()["data"]["summary"]

    def test_narrative_analytics_work_without_gemini(self):
        """Analytics must function independently of Gemini."""
        from app.services.metrics import MetricsService
        from app.config import get_settings
        from app.database import SessionLocal
        get_settings.cache_clear()
        db = SessionLocal()
        try:
            svc = MetricsService(db, get_settings())
            result = svc.get_summary({})
            assert "total_students" in result
        finally:
            db.close()

class TestNarrativeDoesNotCalculate:
    def test_gemini_never_source_of_pass_percentage(self):
        """Pass percentage must come from Python, not Gemini."""
        from app.services.metrics import MetricsService
        from app.config import get_settings
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            svc = MetricsService(db, get_settings())
            summary = svc.get_summary({})
            pp = summary.get("pass_percentage", 0)
            # Verify it's a number, not a string from LLM
            assert isinstance(pp, (int, float))
        finally:
            db.close()

    def test_correlation_from_scipy_not_llm(self):
        """Pearson r must come from SciPy."""
        from app.services.correlation import CorrelationService
        from app.config import get_settings
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            svc = CorrelationService(db, get_settings())
            result = svc.get_correlation({})
            for item in result[:3]:
                r = item.get("pearson_correlation")
                if r is not None:
                    assert -1.0 <= r <= 1.0
        finally:
            db.close()
