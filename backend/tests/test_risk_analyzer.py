from app.services.diff_parser import DiffParser
from app.services.risk_analyzer import RiskAnalyzer


def test_risk_analyzer_detects_high_risk_patterns() -> None:
    files = [
        {
            "filename": "app/security.py",
            "status": "modified",
            "additions": 4,
            "deletions": 0,
            "changes": 4,
            "patch": """@@ -1,0 +1,4 @@
+api_key = "hardcoded-secret"
+os.system(user_input)
+query = f"select * from users where id = {user_id}"
+except: pass
""",
        }
    ]

    result = RiskAnalyzer().analyze_files(files, DiffParser.parse_files(files))
    types = {risk["type"] for risk in result["risks"]}

    assert "Hardcoded Secret" in types
    assert "Dangerous Function Usage" in types
    assert "Potential SQL Injection" in types
    assert "Swallowed Exception" in types
    assert result["risk_summary"]["high"] >= 2
    assert result["rule_hits_by_type"]["Hardcoded Secret"] == 1


def test_risk_analyzer_flags_missing_tests_for_large_changes() -> None:
    files = [
        {
            "filename": "frontend/src/App.tsx",
            "status": "modified",
            "additions": 60,
            "deletions": 10,
            "changes": 70,
            "patch": "@@ -1,0 +1,60 @@\n+" + "\n+".join(["const value = 1"] * 60),
        }
    ]

    result = RiskAnalyzer().analyze_files(files, DiffParser.parse_files(files))

    assert any(risk["type"] == "Missing Tests" for risk in result["risks"])
    assert result["rule_hits_by_type"]["Missing Tests"] == 1
