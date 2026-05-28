# ================================
# CURATED COLLECTOR
# ================================

from pathlib import Path
import subprocess
import json
import time
import csv
import re

BASE_DIR = Path(__file__).parent

INCOMING = BASE_DIR / "incoming"
TEMP = BASE_DIR / "temp_downloads"
LOGS = BASE_DIR / "logs"
ARCHIVE = LOGS / "download_archive.txt"

INCOMING.mkdir(parents=True, exist_ok=True)
TEMP.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

# ================================
# FFMPEG LOCAL PATH
# ================================

FFMPEG = r"C:\ffm\bin\ffmpeg.exe"
FFPROBE = r"C:\ffm\bin\ffprobe.exe"

# ================================
# SETTINGS
# ================================

MAX_VIDEOS_PER_SOURCE = None
MAX_SEGMENTS_PER_VIDEO = 5

SEGMENT_SECONDS = 60
MIN_SEGMENT_SECONDS = 30
MAX_SEGMENT_SECONDS = 90

# ================================
# SOURCES
# ================================

CURATED_SOURCES = [
    {
        "primary": "DailyLife",

        "secondary": "InspirationRecord",

        "url": "https://www.youtube.com/playlist?list=PLsRNoUx8w3rOwHx4kVJL5ksS9vTxj5hXn",

        "required_keywords": [
            "tedx",
            "vida",
            "inspiração",
            "propósito",
            "felicidade",
            "história",
            "sucesso",
            "mudança",
            "aprendizado"
        ],

        "blocked_keywords": [
            "karaokê",
            "clipe",
            "show"
        ]
    },

    {
        "primary": "StudyEducation",

        "secondary": "LectureTrainingRecording",

        "url": "https://www.youtube.com/playlist?list=PLsRNoUx8w3rOwHx4kVJL5ksS9vTxj5hXn",

        "required_keywords": [
            "tedx",
            "educação",
            "treinamento",
            "aprendizagem",
            "conhecimento",
            "aula",
            "palestra"
        ],

        "blocked_keywords": [
            "karaokê",
            "clipe",
            "show"
        ]
    },

    {
        "primary": "ContentCreation",

        "secondary": "VoiceCreation",

        "url": "https://www.youtube.com/playlist?list=PLsRNoUx8w3rOwHx4kVJL5ksS9vTxj5hXn",

        "required_keywords": [
            "narração",
            "voz",
            "fala",
            "comunicação",
            "história",
            "conteúdo"
        ],

        "blocked_keywords": [
            "karaokê",
            "clipe",
            "show"
        ]
    }
]

# ================================
# HELPERS
# ================================

def run_command(command, capture_output=False):

    if capture_output:

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        return result.stdout

    subprocess.run(command, check=True)

    return ""


def normalize_text(text):

    if not text:
        return ""

    return text.lower().strip()


# ================================
# CATEGORY MATCH
# ================================

def metadata_matches_category(
    metadata,
    required_keywords,
    blocked_keywords
):

    title = normalize_text(
        metadata.get("title", "")
    )

    description = normalize_text(
        metadata.get("description", "")
    )

    combined_text = f"{title} {description}"

    for blocked in blocked_keywords:

        if blocked.lower() in combined_text:

            return (
                False,
                f"Blocked keyword: {blocked}"
            )

    for keyword in required_keywords:

        if keyword.lower() in combined_text:

            return (
                True,
                f"Matched keyword: {keyword}"
            )

    return (
        False,
        "No category match"
    )


# ================================
# PLAYLIST ENTRIES
# ================================

def get_playlist_entries(source_url):

    command = [
        "py", "-m", "yt_dlp",

        "--flat-playlist",

        "--dump-json",

        source_url
    ]

    output = run_command(
        command,
        capture_output=True
    )

    entries = []

    for line in output.splitlines():

        try:

            data = json.loads(line)

            video_id = data.get("id")

            if not video_id:
                continue

            video_url = (
                f"https://www.youtube.com/watch?v={video_id}"
            )

            entries.append({
                "id": video_id,
                "url": video_url,
                "title": data.get("title", "")
            })

        except Exception:
            pass

    return entries


# ================================
# VIDEO METADATA
# ================================

def get_video_metadata(video_url):

    command = [
        "py", "-m", "yt_dlp",

        "--dump-json",

        "--skip-download",

        video_url
    ]

    output = run_command(
        command,
        capture_output=True
    )

    return json.loads(output)


# ================================
# SAFE NAME
# ================================

def safe_name(text):

    text = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        text
    )

    return text[:80].strip("_")


# ================================
# DOWNLOAD AUDIO
# ================================

def download_audio(video_url, video_id):

    output_template = str(
        TEMP / f"{video_id}.%(ext)s"
    )

    command = [
        "py", "-m", "yt_dlp",

        video_url,

        "--no-playlist",

        "--download-archive",
        str(ARCHIVE),

        "--ffmpeg-location",
        r"C:\ffm\bin",

        "-f",
        "bestaudio[ext=m4a]/bestaudio/best",

        "--extract-audio",

        "--audio-format",
        "wav",

        "-o",
        output_template
    ]

    run_command(command)

    wav_file = TEMP / f"{video_id}.wav"

    if not wav_file.exists():

        wav_candidates = list(
            TEMP.glob(f"{video_id}*.wav")
        )

        if wav_candidates:
            wav_file = wav_candidates[0]

    if not wav_file.exists():

        raise FileNotFoundError(
            f"WAV file not created for {video_id}"
        )

    return wav_file


# ================================
# AUDIO DURATION
# ================================

def get_audio_duration_seconds(audio_path):

    command = [
        FFPROBE,

        "-v", "error",

        "-show_entries",
        "format=duration",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        str(audio_path)
    ]

    output = run_command(
        command,
        capture_output=True
    ).strip()

    return float(output)


# ================================
# CUT SEGMENT
# ================================

def cut_audio_segment(
    input_audio,
    output_mp4,
    start_seconds,
    duration_seconds
):

    command = [
        FFMPEG,

        "-y",

        "-i",
        str(input_audio),

        "-ss",
        str(start_seconds),

        "-t",
        str(duration_seconds),

        "-vn",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        str(output_mp4)
    ]

    run_command(command)


# ================================
# CREATE SEGMENTS
# ================================

def create_segments(
    input_audio,
    primary,
    secondary,
    video_id
):

    target_folder = (
        INCOMING /
        primary /
        secondary
    )

    if not target_folder.exists():
        print(f"ERRO: pasta não existe: {target_folder}")
        return 0
    

    duration = get_audio_duration_seconds(
        input_audio
    )

    if duration < MIN_SEGMENT_SECONDS:

        print(
            f"SKIPPED:"
            f" audio too short"
            f" ({duration:.2f}s)"
        )

        return 0

    if (
        duration >= MIN_SEGMENT_SECONDS
        and
        duration <= MAX_SEGMENT_SECONDS
    ):

        output_name = (
            f"collected_{safe_name(video_id)}_001.mp4"
        )

        output_file = (
            target_folder / output_name
        )

        cut_audio_segment(
            input_audio=input_audio,
            output_mp4=output_file,
            start_seconds=0,
            duration_seconds=duration
        )

        print(
            f"FULL AUDIO SAVED:"
            f" {output_file}"
        )

        return 1

    segment_count = 0
    start = 0

    while (
        start + MIN_SEGMENT_SECONDS <= duration
        and
        segment_count < MAX_SEGMENTS_PER_VIDEO
    ):

        remaining = duration - start

        segment_duration = min(
            SEGMENT_SECONDS,
            remaining
        )

        if segment_duration < MIN_SEGMENT_SECONDS:
            break

        if segment_duration > MAX_SEGMENT_SECONDS:
            segment_duration = MAX_SEGMENT_SECONDS

        output_name = (
            f"collected_{safe_name(video_id)}_"
            f"{segment_count + 1:03d}.mp4"
        )

        output_file = (
            target_folder / output_name
        )

        cut_audio_segment(
            input_audio=input_audio,
            output_mp4=output_file,
            start_seconds=start,
            duration_seconds=segment_duration
        )

        print(
            f"SEGMENT CREATED:"
            f" {output_file}"
        )

        segment_count += 1

        start += segment_duration

    return segment_count


# ================================
# LOG
# ================================

def append_log(row):

    log_file = (
        LOGS /
        "collector_curated_log.csv"
    )

    file_exists = log_file.exists()

    with open(
        log_file,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        if not file_exists:

            writer.writerow([
                "timestamp",
                "primary",
                "secondary",
                "video_id",
                "video_title",
                "video_url",
                "decision",
                "reason",
                "segments_created"
            ])

        writer.writerow(row)


# ================================
# PROCESS SOURCE
# ================================

def process_source(source):

    primary = source["primary"]

    secondary = source["secondary"]

    url = source["url"]

    required_keywords = source.get(
        "required_keywords",
        []
    )

    blocked_keywords = source.get(
        "blocked_keywords",
        []
    )

    print(
        f"\nProcessing source:"
        f" {primary} / {secondary}"
    )

    print(f"URL: {url}")

    entries = get_playlist_entries(url)

    selected_entries = (
        entries
        if MAX_VIDEOS_PER_SOURCE is None
        else entries[:MAX_VIDEOS_PER_SOURCE]
    )

    for entry in selected_entries:

        video_url = entry["url"]

        video_id = entry["id"]

        try:

            metadata = get_video_metadata(
                video_url
            )

            title = metadata.get("title", "")

            matches, reason = (
                metadata_matches_category(
                    metadata=metadata,
                    required_keywords=required_keywords,
                    blocked_keywords=blocked_keywords
                )
            )

            if not matches:

                print(
                    f"SKIPPED:"
                    f" {title}"
                    f" | {reason}"
                )

                continue

            print(
                f"ACCEPTED:"
                f" {title}"
                f" | {reason}"
            )

            audio_file = download_audio(
                video_url,
                video_id
            )

            segments_created = create_segments(
                input_audio=audio_file,
                primary=primary,
                secondary=secondary,
                video_id=video_id
            )

            append_log([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                primary,
                secondary,
                video_id,
                title,
                video_url,
                "DOWNLOADED_SEGMENTED",
                reason,
                segments_created
            ])

            try:
                audio_file.unlink()

            except Exception:
                pass

        except Exception as e:

            print(
                f"ERROR:"
                f" {video_url}"
                f" | {e}"
            )


# ================================
# MAIN
# ================================

def main():

    print("\nCurated collector iniciado.")

    print(
        "Analisa metadata,"
        " baixa áudio,"
        " corta em segmentos"
        " de 30s a 90s.\n"
    )

    if not Path(FFMPEG).exists():

        print(
            f"ERRO:"
            f" ffmpeg não encontrado:"
            f" {FFMPEG}"
        )

        return

    if not Path(FFPROBE).exists():

        print(
            f"ERRO:"
            f" ffprobe não encontrado:"
            f" {FFPROBE}"
        )

        return

    for source in CURATED_SOURCES:

        process_source(source)

    print("\nColeta curada finalizada.")

    print("Agora rode:")

    print("py pipeline.py")


if __name__ == "__main__":
    main()