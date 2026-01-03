#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FOOTNOTE_RE = re.compile(r"^\[\^[^\]]+\]:\s*(.*)$")


def count_braces(text: str) -> int:
    count = 0
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            count += 1
        elif ch == "}":
            count -= 1
    return count


def iter_json_blocks(lines: list[str]):
    i = 0
    while i < len(lines):
        line = lines[i]
        match = FOOTNOTE_RE.match(line)
        if match:
            rest = match.group(1)
            if "{" in rest:
                start_line = i + 1
                json_start = rest.index("{")
                buffer = rest[json_start:]
                brace_count = count_braces(buffer)
                j = i
                while brace_count > 0 and j + 1 < len(lines):
                    j += 1
                    buffer += "\n" + lines[j]
                    brace_count += count_braces(lines[j])
                yield start_line, buffer, brace_count == 0
                i = j
        i += 1


def validate_value(value, schema, path: str) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{path} must be a string")
            return errors
        min_len = schema.get("minLength")
        if min_len is not None and len(value) < min_len:
            errors.append(f"{path} must be at least {min_len} characters")
        max_len = schema.get("maxLength")
        if max_len is not None and len(value) > max_len:
            errors.append(f"{path} must be at most {max_len} characters")
        pattern = schema.get("pattern")
        if pattern and not re.search(pattern, value):
            errors.append(f"{path} does not match pattern {pattern}")
    elif expected_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{path} must be a number")
            return errors
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            errors.append(f"{path} must be >= {minimum}")
        maximum = schema.get("maximum")
        if maximum is not None and value > maximum:
            errors.append(f"{path} must be <= {maximum}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path} must be one of {schema['enum']}")
    return errors


def validate_instance(instance, schema) -> list[str]:
    errors: list[str] = []
    if schema.get("type") == "object":
        if not isinstance(instance, dict):
            return ["value must be an object"]
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"missing required field '{key}'")
        properties = schema.get("properties", {})
        additional_allowed = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in properties:
                errors.extend(validate_value(value, properties[key], key))
            elif additional_allowed is False:
                errors.append(f"unexpected field '{key}'")
    else:
        errors.append("schema type is not supported")
    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = repo_root / ".digital-brain" / "relations.schema.json"
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}", file=sys.stderr)
        return 1
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    error_count = 0
    for path in sorted(repo_root.rglob("*.md")):
        # Skip the .digital-brain infrastructure directory
        if ".digital-brain" in path.parts:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for start_line, json_text, balanced in iter_json_blocks(lines):
            if not balanced:
                print(f"{path}:{start_line}: unterminated JSON block", file=sys.stderr)
                error_count += 1
                continue
            try:
                payload = json.loads(json_text)
            except json.JSONDecodeError as exc:
                print(
                    f"{path}:{start_line}: invalid JSON ({exc.msg})",
                    file=sys.stderr,
                )
                error_count += 1
                continue
            errors = validate_instance(payload, schema)
            for message in errors:
                print(f"{path}:{start_line}: {message}", file=sys.stderr)
                error_count += 1

    if error_count:
        print(f"{error_count} error(s) found.", file=sys.stderr)
        return 1
    print("No relation errors found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
