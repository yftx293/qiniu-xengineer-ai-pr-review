from app.services.diff_parser import DiffParser
from app.services.risk_analyzer import RiskAnalyzer


def test_risk_analyzer_detects_high_risk_patterns() -> None:
    files = [
        {
            "filename": "app/security.py",
            "status": "modified",
            "additions": 5,
            "deletions": 0,
            "changes": 5,
            "patch": """@@ -1,0 +1,5 @@
+api_key = "prod-secret-value"
+os.system(user_input)
+query = f"select * from users where id = {user_id}"
+except: pass
+logger.info("token=%s", token)
""",
        }
    ]

    result = RiskAnalyzer().analyze_files(files, DiffParser.parse_files(files))
    types = {risk["type"] for risk in result["risks"]}

    assert "Hardcoded Secret" in types
    assert "Dangerous Function Usage" in types
    assert "Potential SQL Injection" in types
    assert "Swallowed Exception" in types
    assert "Sensitive Data Logging" in types
    assert result["risk_summary"]["high"] >= 2
    assert result["rule_hits_by_type"]["Hardcoded Secret"] == 1


def test_risk_analyzer_reduces_secret_false_positives_in_docs_and_tests() -> None:
    files = [
        {
            "filename": "README.md",
            "status": "modified",
            "additions": 2,
            "deletions": 0,
            "changes": 2,
            "patch": """@@ -1,0 +1,2 @@
+# example token setup
+Use token=example-token when documenting local setup.
""",
        },
        {
            "filename": "tests/test_auth.py",
            "status": "modified",
            "additions": 1,
            "deletions": 0,
            "changes": 1,
            "patch": """@@ -1,0 +1 @@
+api_key = "demo-token"
""",
        },
    ]

    result = RiskAnalyzer().analyze_files(files, DiffParser.parse_files(files))

    assert not any(risk["type"] == "Hardcoded Secret" for risk in result["risks"])


def test_risk_analyzer_flags_test_regression_and_infra_changes() -> None:
    files = [
        {
            "filename": "tests/test_checkout.py",
            "status": "modified",
            "additions": 0,
            "deletions": 4,
            "changes": 4,
            "patch": """@@ -10,4 +10,0 @@
-def test_checkout_requires_login():
-    assert checkout(user=None) == 401
-    assert checkout(user="guest") == 403
-    assert checkout(user="admin") == 200
""",
        },
        {
            "filename": ".github/workflows/deploy.yml",
            "status": "modified",
            "additions": 6,
            "deletions": 0,
            "changes": 6,
            "patch": """@@ -1,0 +1,6 @@
+name: deploy
+jobs:
+  deploy:
+    steps:
+      - run: ./deploy.sh
+      - run: echo done
""",
        },
    ]

    result = RiskAnalyzer().analyze_files(files, DiffParser.parse_files(files))
    types = {risk["type"] for risk in result["risks"]}

    assert "Test Coverage Regression" in types
    assert "CI/Deploy Sensitive Change" in types


def test_risk_analyzer_does_not_flag_missing_tests_for_docs_only_changes() -> None:
    files = [
        {
            "filename": "README.md",
            "status": "modified",
            "additions": 60,
            "deletions": 10,
            "changes": 70,
            "patch": "@@ -1,0 +1,60 @@\n+" + "\n+".join(["Documented the new review flow."] * 60),
        }
    ]

    result = RiskAnalyzer().analyze_files(files, DiffParser.parse_files(files))

    assert not any(risk["type"] == "Missing Tests" for risk in result["risks"])


def test_risk_analyzer_flags_missing_tests_for_runtime_sensitive_changes() -> None:
    files = [
        {
            "filename": "backend/app/auth_service.py",
            "status": "modified",
            "additions": 60,
            "deletions": 25,
            "changes": 85,
            "patch": "@@ -1,0 +1,60 @@\n+" + "\n+".join(["if token: return validate(token)"] * 60),
        }
    ]

    result = RiskAnalyzer().analyze_files(files, DiffParser.parse_files(files))

    assert any(risk["type"] == "Missing Tests" for risk in result["risks"])
    missing_tests = next(risk for risk in result["risks"] if risk["type"] == "Missing Tests")
    assert missing_tests["severity"] == "High"
