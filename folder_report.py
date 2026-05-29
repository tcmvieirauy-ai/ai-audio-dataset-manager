from pathlib import Path
import csv
from datetime import datetime

BASE_DIR = Path(__file__).parent

FOLDERS_TO_SCAN = [
    "incoming",
    "processed",
    "approved",
    "review",
    "temp_downloads",
    "logs"
]

REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

REPORT_FILE = REPORTS_DIR / "folder_report.csv"

FILE_TYPES = [
    ".mp3",
    ".mp4",
    ".m4a",
    ".wav",
    ".aac",
    ".flac",
    ".ogg",
    ".txt",
    ".csv"
]


def count_files(folder):
    files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in FILE_TYPES
    ]

    return len(files), files


def main():
    print("\nFolder report iniciado...\n")

    rows = []

    for folder_name in FOLDERS_TO_SCAN:
        root = BASE_DIR / folder_name

        if not root.exists():
            continue

        for folder in root.rglob("*"):
            if not folder.is_dir():
                continue

            total_files, files = count_files(folder)

            if total_files > 0:
                relative_path = folder.relative_to(BASE_DIR)

                print(f"{relative_path} -> {total_files} arquivos")

                rows.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "folder": str(relative_path),
                    "total_files": total_files,
                    "file_names": " | ".join([f.name for f in files])
                })

    with open(REPORT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "folder",
                "total_files",
                "file_names"
            ]
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"\nRelatório criado em: {REPORT_FILE}")


if __name__ == "__main__":
    main()
    