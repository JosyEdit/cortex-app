#!/usr/bin/env python3
"""Inventorie les fichiers sous C:\\Users\\JOSY EI, sans AppData ni Windows."""

from collections import Counter, defaultdict
from datetime import datetime
import os
from pathlib import Path
import stat


ROOT = Path(r"C:\Users\JOSY EI")
OUTPUT = Path(__file__).resolve().parent / "inventaire_pc.txt"
EXCLUDED_DIR_NAMES = {"appdata", "windows"}
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def is_reparse_point(path):
    """Évite de suivre les liens et jonctions susceptibles de sortir du dossier ciblé."""
    info = os.stat(path, follow_symlinks=False)
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & REPARSE_POINT
    )


def human_size(size):
    value = float(size)
    for unit in ("o", "Kio", "Mio", "Gio", "Tio"):
        if value < 1024 or unit == "Tio":
            return f"{value:.1f} {unit}"
        value /= 1024


def main():
    if not ROOT.is_dir():
        raise FileNotFoundError(f"Dossier à inventorier introuvable : {ROOT}")

    extension_counts = Counter()
    folder_sizes = defaultdict(int)
    errors = []
    skipped_directories = 0
    total_files = 0
    total_size = 0

    for item in ROOT.iterdir():
        if item.is_dir() and item.name.casefold() not in EXCLUDED_DIR_NAMES:
            try:
                if not is_reparse_point(item):
                    folder_sizes[item.name] += 0
            except OSError as exc:
                errors.append(f"{item}: {exc}")

    def on_walk_error(exc):
        errors.append(f"{getattr(exc, 'filename', ROOT)}: {exc}")

    for current, directory_names, file_names in os.walk(
        ROOT, topdown=True, onerror=on_walk_error, followlinks=False
    ):
        current_path = Path(current)
        kept_directories = []
        for name in directory_names:
            directory = current_path / name
            if name.casefold() in EXCLUDED_DIR_NAMES:
                skipped_directories += 1
                continue
            try:
                if is_reparse_point(directory):
                    skipped_directories += 1
                    continue
            except OSError as exc:
                errors.append(f"{directory}: {exc}")
                skipped_directories += 1
                continue
            kept_directories.append(name)
        directory_names[:] = kept_directories

        for name in file_names:
            path = current_path / name
            if path == OUTPUT:
                continue
            try:
                if is_reparse_point(path):
                    continue
                size = path.stat().st_size
            except OSError as exc:
                errors.append(f"{path}: {exc}")
                continue

            extension = path.suffix.casefold() or "(sans extension)"
            extension_counts[extension] += 1
            relative = path.relative_to(ROOT)
            folder = relative.parts[0] if len(relative.parts) > 1 else "(fichiers à la racine)"
            folder_sizes[folder] += size
            total_files += 1
            total_size += size

    lines = [
        "INVENTAIRE DU PC",
        f"Date : {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Périmètre : {ROOT}",
        "Exclusions : dossiers nommés AppData ou Windows ; liens et jonctions.",
        f"Dossiers exclus ou non suivis : {skipped_directories}",
        f"Fichiers inventoriés : {total_files}",
        f"Taille totale : {human_size(total_size)} ({total_size:,} octets)",
        "",
        "NOMBRE DE FICHIERS PAR EXTENSION",
        "--------------------------------",
    ]
    if extension_counts:
        lines.extend(
            f"{extension:24} {count:>10,}"
            for extension, count in sorted(extension_counts.items())
        )
    else:
        lines.append("(aucun fichier)")

    lines.extend(
        [
            "",
            "TAILLE PAR GRAND DOSSIER",
            "------------------------",
        ]
    )
    if folder_sizes:
        lines.extend(
            f"{folder:40} {human_size(size):>12} ({size:,} octets)"
            for folder, size in sorted(folder_sizes.items(), key=lambda item: item[0].casefold())
        )
    else:
        lines.append("(aucun dossier)")

    lines.extend(["", f"Erreurs de lecture : {len(errors)}"])
    if errors:
        lines.extend(f"- {error}" for error in errors)
    lines.append("")
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rapport écrit : {OUTPUT}")
    print(f"Fichiers : {total_files}; erreurs : {len(errors)}")


if __name__ == "__main__":
    main()
