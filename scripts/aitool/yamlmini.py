"""Minimal YAML subset parser plus file helpers.

Deliberately dependency-free so the template works after a bare `git pull` with nothing
but a Python interpreter. Supports what this template's own files use: nested maps, lists
of scalars, lists of maps, inline [a, b] lists, comments, quoted strings, and
int / bool / null scalars, with two-space indentation.

Not supported: block scalars (| and >), anchors, multiple documents, flow maps. Those
raise ConfigError with a line number rather than being silently mis-parsed.
"""

from __future__ import annotations

import hashlib
import re


class ConfigError(Exception):
    """Raised for a malformed or inconsistent configuration."""


def quote_scalar(value):
    """Render a value as a double-quoted YAML scalar, escaping what would break it.

    Inverse of the quoted-string branch of _parse_scalar, so a value written by this
    function reads back unchanged.
    """
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    for broken, replacement in (("\r\n", " "), ("\n", " "), ("\r", " ")):
        text = text.replace(broken, replacement)
    return f'"{text}"'


def parse_yaml(text, origin="<yaml>"):
    lines = []
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if "\t" in raw[:indent]:
            raise ConfigError(f"{origin}:{number}: tab indentation, use two spaces")
        lines.append((number, indent, raw.strip()))
    if not lines:
        return None
    value, index = _parse_block(lines, 0, lines[0][1], origin)
    if index != len(lines):
        raise ConfigError(f"{origin}:{lines[index][0]}: unexpected indentation")
    return value


def _parse_block(lines, index, indent, origin):
    if index >= len(lines):
        return None, index
    if lines[index][2].startswith("- "):
        return _parse_list(lines, index, indent, origin)
    return _parse_map(lines, index, indent, origin)


def _parse_map(lines, index, indent, origin):
    result = {}
    while index < len(lines):
        number, line_indent, content = lines[index]
        if line_indent < indent or content.startswith("- "):
            break
        if line_indent > indent:
            raise ConfigError(f"{origin}:{number}: unexpected indentation")
        if content.startswith(("|", ">")):
            raise ConfigError(f"{origin}:{number}: block scalars are not supported")
        if ":" not in content:
            raise ConfigError(f"{origin}:{number}: expected 'key: value'")
        key, _, rest = content.partition(":")
        key, rest = key.strip(), rest.strip()
        index += 1
        if rest:
            result[key] = _parse_scalar(rest, origin, number)
            continue
        if index < len(lines) and lines[index][1] > indent:
            result[key], index = _parse_block(lines, index, lines[index][1], origin)
        elif (index < len(lines) and lines[index][1] == indent
              and lines[index][2].startswith("- ")):
            result[key], index = _parse_list(lines, index, indent, origin)
        else:
            result[key] = None
    return result, index


def _parse_list(lines, index, indent, origin):
    result = []
    while index < len(lines):
        number, line_indent, content = lines[index]
        if line_indent < indent or not content.startswith("- "):
            break
        if line_indent > indent:
            raise ConfigError(f"{origin}:{number}: unexpected indentation")
        item = content[2:].strip()
        index += 1
        if ":" in item and not item.startswith(("'", '"', "[")):
            # "- key: value" opens a map whose remaining keys sit two spaces deeper.
            key, _, rest = item.partition(":")
            entry = {}
            entry_indent = line_indent + 2
            if rest.strip():
                entry[key.strip()] = _parse_scalar(rest.strip(), origin, number)
            elif index < len(lines) and lines[index][1] > entry_indent:
                entry[key.strip()], index = _parse_block(
                    lines, index, lines[index][1], origin)
            else:
                entry[key.strip()] = None
            tail, index = _parse_map(lines, index, entry_indent, origin)
            entry.update(tail or {})
            result.append(entry)
        else:
            result.append(_parse_scalar(item, origin, number))
    return result, index


def _split_comment(raw):
    """Strip a trailing ' #...' comment, ignoring any # that sits inside quotes.

    A blind '\\s+#' search truncates values like "path to #1 rule" at the hash. Walking
    the string keeps quoted runs intact so only a genuine trailing comment is removed.
    """
    quote = None
    for index, char in enumerate(raw):
        if quote:
            if char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "#" and index and raw[index - 1] in " \t":
            return raw[:index].rstrip()
    return raw.rstrip()


def _parse_scalar(raw, origin="<yaml>", number=0):
    if raw.startswith(('"', "'")):
        quote = raw[0]
        out, index = [], 1
        while index < len(raw):
            char = raw[index]
            if quote == '"' and char == "\\" and index + 1 < len(raw):
                out.append(raw[index + 1])
                index += 2
                continue
            if char == quote:
                break
            out.append(char)
            index += 1
        else:
            raise ConfigError(f"{origin}:{number}: unterminated string")
        return "".join(out)
    if raw.startswith("["):
        if "]" not in raw:
            raise ConfigError(f"{origin}:{number}: unterminated inline list")
        inner = raw[1:raw.rindex("]")]
        return [_parse_scalar(part.strip(), origin, number)
                for part in inner.split(",") if part.strip()]
    raw = _split_comment(raw)
    lowered = raw.lower()
    if lowered in ("true", "yes"):
        return True
    if lowered in ("false", "no"):
        return False
    if lowered in ("null", "~", ""):
        return None
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return raw


def split_front_matter(text, origin):
    """Return (metadata, body). No front matter yields ({}, text)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        raise ConfigError(f"{origin}: unterminated front matter")
    head = text[text.index("\n", 3) + 1:end]
    return parse_yaml(head, origin) or {}, text[end + 4:].lstrip("\n")


def read_text(path):
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ConfigError(f"{path}: UTF-8 BOM found, files must be UTF-8 without BOM")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError(f"{path}: not valid UTF-8 ({exc})") from exc


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def normalize(text):
    """Collapse line endings so a CRLF checkout is not mistaken for drift.

    git with core.autocrlf=true rewrites line endings on checkout, so comparing raw text
    would report every generated file as stale on a fresh clone under Windows.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def digest(text):
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()[:16]
