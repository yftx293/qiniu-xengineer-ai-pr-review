from __future__ import annotations

import re
from typing import Any


HUNK_HEADER_PATTERN = re.compile(r"^@@\s*-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s*@@")


class DiffParser:
    @staticmethod
    def parse_patch(patch: str) -> dict[str, Any]:
        if not patch:
            return {
                "added_lines": [],
                "deleted_lines": [],
                "hunks": [],
                "added_count": 0,
                "deleted_count": 0,
            }

        added_lines: list[dict[str, Any]] = []
        deleted_lines: list[dict[str, Any]] = []
        hunks: list[dict[str, Any]] = []

        current_hunk: dict[str, Any] | None = None
        old_line_no: int | None = None
        new_line_no: int | None = None

        for raw_line in patch.splitlines():
            if raw_line.startswith("@@"):
                match = HUNK_HEADER_PATTERN.match(raw_line)
                old_line_no = int(match.group(1)) if match else None
                new_line_no = int(match.group(2)) if match else None
                current_hunk = {"header": raw_line, "added_count": 0, "deleted_count": 0}
                hunks.append(current_hunk)
                continue

            if raw_line.startswith("+++"):
                continue
            if raw_line.startswith("---"):
                continue

            if raw_line.startswith("+"):
                content = raw_line[1:]
                added_lines.append({"line_no": new_line_no, "content": content})
                if current_hunk is not None:
                    current_hunk["added_count"] += 1
                if new_line_no is not None:
                    new_line_no += 1
                continue

            if raw_line.startswith("-"):
                content = raw_line[1:]
                deleted_lines.append({"line_no": old_line_no, "content": content})
                if current_hunk is not None:
                    current_hunk["deleted_count"] += 1
                if old_line_no is not None:
                    old_line_no += 1
                continue

            # Context lines advance both counters when known.
            if raw_line.startswith("\\"):
                continue
            if old_line_no is not None:
                old_line_no += 1
            if new_line_no is not None:
                new_line_no += 1

        return {
            "added_lines": added_lines,
            "deleted_lines": deleted_lines,
            "hunks": hunks,
            "added_count": len(added_lines),
            "deleted_count": len(deleted_lines),
        }

    @classmethod
    def parse_file_patch(cls, file_item: dict[str, Any]) -> dict[str, Any]:
        parsed = cls.parse_patch((file_item.get("patch") or ""))
        return {
            "filename": file_item.get("filename", ""),
            "status": file_item.get("status", "unknown"),
            "added_lines": parsed["added_lines"],
            "deleted_lines": parsed["deleted_lines"],
            "hunks": parsed["hunks"],
            "added_count": parsed["added_count"],
            "deleted_count": parsed["deleted_count"],
        }

    @classmethod
    def parse_files(cls, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not files:
            return []
        return [cls.parse_file_patch(file_item) for file_item in files]
