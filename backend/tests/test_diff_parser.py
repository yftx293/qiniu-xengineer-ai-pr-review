from app.services.diff_parser import DiffParser


def test_parse_patch_extracts_hunks_and_line_numbers() -> None:
    patch = """@@ -1,2 +1,3 @@
+line 1
-old line
+new line
 context
"""

    result = DiffParser.parse_patch(patch)

    assert result["added_count"] == 2
    assert result["deleted_count"] == 1
    assert result["hunks"][0]["header"] == "@@ -1,2 +1,3 @@"
    assert result["added_lines"][0] == {"line_no": 1, "content": "line 1"}
    assert result["deleted_lines"][0] == {"line_no": 1, "content": "old line"}


def test_parse_patch_returns_empty_collections_for_empty_patch() -> None:
    result = DiffParser.parse_patch("")

    assert result == {
        "added_lines": [],
        "deleted_lines": [],
        "hunks": [],
        "added_count": 0,
        "deleted_count": 0,
    }
