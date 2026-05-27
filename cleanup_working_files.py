from pathlib import Path

BASE_DIR = Path(__file__).parent

TARGET_FOLDERS = [
    "approved",
    "incoming",
    "logs",
    "processed",
    "review",
    "temp_downloads"
]

FILE_EXTENSIONS_TO_DELETE = [
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

DRY_RUN = False  #deletar arquivos.


def main():
    print("\nCleanup iniciado.")
    print(f"DRY_RUN = {DRY_RUN}")

    total_found = 0
    total_deleted = 0

    for folder_name in TARGET_FOLDERS:
        folder = BASE_DIR / folder_name

        if not folder.exists():
            print(f"Pasta não encontrada: {folder}")
            continue

        for file_path in folder.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in FILE_EXTENSIONS_TO_DELETE:
                total_found += 1
                print(f"Encontrado: {file_path}")

                if not DRY_RUN:
                    try:
                        file_path.unlink()
                        total_deleted += 1
                        print(f"Deletado: {file_path}")
                    except Exception as e:
                        print(f"Erro ao deletar {file_path}: {e}")

    print("\nCleanup finalizado.")
    print(f"Arquivos encontrados: {total_found}")
    print(f"Arquivos deletados: {total_deleted}")

    if DRY_RUN:
        print("\nNada foi deletado porque DRY_RUN = True.")
        print("Para deletar de verdade, troque DRY_RUN = False.")


if __name__ == "__main__":
    main()