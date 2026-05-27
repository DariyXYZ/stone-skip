#!/usr/bin/env python3
"""Bake Stone Skipping browser asset edits into the repository.

The asset editor is allowed to use browser localStorage as a fast preview
draft. This script turns that draft into the linear source of truth:

1. read the latest stone-skipping-game-asset-patch-v1 value from Chrome/Edge,
2. write assets/stone-skipping-assets.json,
3. replace the embedded ASSET_PACK in stone-skipping-game.html.

No commit or push is performed here.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GAME_HTML = ROOT / "stone-skipping-game.html"
CANONICAL_ASSETS = ROOT / "assets" / "stone-skipping-assets.json"
STORAGE_KEY = "stone-skipping-game-asset-patch-v1"
DEFAULT_ORIGIN = "http://localhost:8027"
DEFAULT_META = {
  "version": 6,
  "name": "stone-skipping-game-core",
  "splashCoverVersion": 5,
  "splashTitleVersion": 1,
  "shopFrameVersion": 3,
}


def read_varint(buf: bytes, index: int) -> tuple[int, int]:
  value = 0
  shift = 0
  while True:
    byte = buf[index]
    index += 1
    value |= (byte & 0x7F) << shift
    if not byte & 0x80:
      return value, index
    shift += 7


def iter_leveldb_log_records(path: Path) -> list[bytes]:
  data = path.read_bytes()
  block_size = 32768
  records: list[bytes] = []
  fragment = b""
  pos = 0
  while pos + 7 <= len(data):
    block_remaining = block_size - (pos % block_size)
    if block_remaining < 7:
      pos += block_remaining
      continue
    length = int.from_bytes(data[pos + 4:pos + 6], "little")
    record_type = data[pos + 6]
    pos += 7
    if length == 0 and record_type == 0:
      if pos % block_size:
        pos += block_size - (pos % block_size)
      continue
    payload = data[pos:pos + length]
    pos += length
    if record_type == 1:
      records.append(payload)
    elif record_type == 2:
      fragment = payload
    elif record_type == 3:
      fragment += payload
    elif record_type == 4:
      records.append(fragment + payload)
      fragment = b""
  return records


def iter_leveldb_batch_entries(record: bytes) -> list[tuple[bytes, bytes]]:
  if len(record) < 12:
    return []
  count = int.from_bytes(record[8:12], "little")
  entries: list[tuple[bytes, bytes]] = []
  pos = 12
  for _ in range(count):
    if pos >= len(record):
      break
    tag = record[pos]
    pos += 1
    key_len, pos = read_varint(record, pos)
    key = record[pos:pos + key_len]
    pos += key_len
    if tag == 1:
      value_len, pos = read_varint(record, pos)
      value = record[pos:pos + value_len]
      pos += value_len
      entries.append((key, value))
  return entries


def decode_local_storage_value(raw: bytes) -> Any | None:
  # Chrome stores DOMStorage values as a one-byte UTF-16 marker plus UTF-16LE.
  for offset in (1, 0, 2):
    value = raw[offset:]
    if len(value) % 2:
      value = value[:-1]
    try:
      text = value.decode("utf-16le")
    except UnicodeDecodeError:
      continue
    if not text.startswith("{"):
      continue
    try:
      return json.loads(text)
    except json.JSONDecodeError:
      continue
  return None


def browser_leveldb_dirs() -> list[Path]:
  local = Path(os.environ.get("LOCALAPPDATA", ""))
  candidates = [
    local / "Google" / "Chrome" / "User Data" / "Default" / "Local Storage" / "leveldb",
    local / "Microsoft" / "Edge" / "User Data" / "Default" / "Local Storage" / "leveldb",
  ]
  return [path for path in candidates if path.exists()]


def latest_browser_patch(origin: str) -> dict[str, Any]:
  wanted = f"_{origin}\x00\x01{STORAGE_KEY}".encode()
  found: list[tuple[float, Path, dict[str, Any]]] = []
  for folder in browser_leveldb_dirs():
    for path in folder.glob("*"):
      if path.suffix not in {".log", ".ldb"}:
        continue
      try:
        haystack = path.read_bytes()
      except OSError:
        continue
      if STORAGE_KEY.encode() not in haystack:
        continue
      records = iter_leveldb_log_records(path) if path.suffix == ".log" else [haystack]
      for record in records:
        for key, value in iter_leveldb_batch_entries(record):
          if key != wanted:
            continue
          patch = decode_local_storage_value(value)
          if isinstance(patch, dict):
            found.append((path.stat().st_mtime, path, patch))
  if not found:
    raise SystemExit(f"No {STORAGE_KEY} patch found for {origin}. Open the editor, save to game, then rerun.")
  found.sort(key=lambda item: item[0])
  return found[-1][2]


def js_string(value: str) -> str:
  if "\n" in value:
    safe = value.replace("`", "\\`").replace("${", "\\${")
    return f"String.raw`{safe}`"
  return json.dumps(value, ensure_ascii=False)


def js_value(value: Any, indent: int = 0) -> str:
  pad = " " * indent
  next_pad = " " * (indent + 2)
  if isinstance(value, dict):
    if not value:
      return "{}"
    parts = []
    for key, item in value.items():
      js_key = key if re.match(r"^[A-Za-z_$][\w$]*$", key) else json.dumps(key, ensure_ascii=False)
      parts.append(f"{next_pad}{js_key}: {js_value(item, indent + 2)}")
    return "{\n" + ",\n".join(parts) + "\n" + pad + "}"
  if isinstance(value, list):
    if not value:
      return "[]"
    if all(not isinstance(item, (dict, list)) and not (isinstance(item, str) and "\n" in item) for item in value):
      return "[" + ", ".join(js_value(item) for item in value) + "]"
    return "[\n" + ",\n".join(f"{next_pad}{js_value(item, indent + 2)}" for item in value) + "\n" + pad + "]"
  if isinstance(value, str):
    return js_string(value)
  if value is True:
    return "true"
  if value is False:
    return "false"
  if value is None:
    return "null"
  return json.dumps(value, ensure_ascii=False)


def bake_game_html(assets: dict[str, Any]) -> None:
  source = GAME_HTML.read_text(encoding="utf-8")
  start = source.index("const ASSET_PACK = {")
  end = source.index("\n};\n\nfunction cloneAsset", start) + len("\n};")
  packed = "const ASSET_PACK = " + js_value(assets) + ";"
  GAME_HTML.write_text(source[:start] + packed + source[end:], encoding="utf-8", newline="\n")


def normalize_assets(assets: dict[str, Any]) -> dict[str, Any]:
  normalized = dict(assets)
  meta = dict(normalized.get("meta") or {})
  for key, value in DEFAULT_META.items():
    meta.setdefault(key, value)
  meta["version"] = max(int(meta.get("version") or 0), DEFAULT_META["version"])
  normalized["meta"] = meta
  return normalized


def main() -> None:
  parser = argparse.ArgumentParser(description="Bake Stone Skipping asset edits into source files.")
  parser.add_argument("--origin", default=DEFAULT_ORIGIN, help="Browser origin used by the asset editor.")
  parser.add_argument("--input", type=Path, help="Use a JSON patch file instead of browser localStorage.")
  args = parser.parse_args()

  if args.input:
    assets = json.loads(args.input.read_text(encoding="utf-8"))
  else:
    assets = latest_browser_patch(args.origin)
  assets = normalize_assets(assets)

  CANONICAL_ASSETS.parent.mkdir(exist_ok=True)
  CANONICAL_ASSETS.write_text(json.dumps(assets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
  bake_game_html(assets)

  title = assets.get("raster", {}).get("splashTitle", "")
  title_lines = title.split("\n") if title else []
  print(f"Baked {CANONICAL_ASSETS.relative_to(ROOT)}")
  if title_lines:
    print(f"splashTitle: {len(title_lines)} rows x {max(len(line) for line in title_lines)} cols")
  print(f"Updated {GAME_HTML.relative_to(ROOT)}")


if __name__ == "__main__":
  main()
