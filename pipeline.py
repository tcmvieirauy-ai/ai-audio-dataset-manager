import os
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

from faster_whisper import WhisperModel
from pathlib import Path
import shutil
import time
import librosa
import numpy as np

LANGUAGE_FOLDER = "Portuguese"

BASE_DIR = Path(__file__).parent

INCOMING = BASE_DIR / "incoming"
PROCESSED = BASE_DIR / "processed"
REVIEW = BASE_DIR / "review" / LANGUAGE_FOLDER
APPROVED = BASE_DIR / "approved" / LANGUAGE_FOLDER
LOGS = BASE_DIR / "logs"

#transcription quality rules
MIN_WORDS = 8
MAX_NO_SPEECH_PROB = 0.90
MIN_AVG_LOGPROB = -1.50

#audio quality rules
MIN_DURATION_SECONDS = 10
MAX_DURATION_SECONDS = 90
MIN_RMS_VOLUME = 0.002
MIN_ACTIVE_AUDIO_RATIO = 0.20
MAX_CLIPPING_RATIO = 0.03
SILENCE_THRESHOLD = 0.01

AUTO_APPROVE = True

for folder in [INCOMING, PROCESSED, REVIEW, APPROVED, LOGS]:
    folder.mkdir(parents=True, exist_ok=True)

print("Carregando Whisper...")
model = WhisperModel("small", device="cpu", compute_type="int8")
print("Whisper carregado.")


def get_next_id(primary, secondary, output_folder):
    existing = list(output_folder.glob(f"{primary}_{secondary}_*.mp4"))
    nums = []

    for file in existing:
        try:
            nums.append(int(file.stem.split("_")[-1]))
        except Exception:
            pass

    return max(nums) + 1 if nums else 1


def analyze_audio_quality(audio_path):
    try:
        audio, sample_rate = librosa.load(str(audio_path), sr=None, mono=True)

        duration = librosa.get_duration(y=audio, sr=sample_rate)

        rms_volume = (
            float(np.sqrt(np.mean(audio ** 2)))
            if len(audio) > 0
            else 0.0
        )

        active_audio_ratio = (
            float(np.mean(np.abs(audio) > SILENCE_THRESHOLD))
            if len(audio) > 0
            else 0.0
        )

        clipping_ratio = (
            float(np.mean(np.abs(audio) >= 0.98))
            if len(audio) > 0
            else 0.0
        )

        return {
            "duration": duration,
            "rms_volume": rms_volume,
            "active_audio_ratio": active_audio_ratio,
            "clipping_ratio": clipping_ratio,
            "audio_error": None
        }

    except Exception as e:
        return {
            "duration": 0,
            "rms_volume": 0,
            "active_audio_ratio": 0,
            "clipping_ratio": 1,
            "audio_error": str(e)
        }


def audio_quality_check(audio_metrics):
    if audio_metrics["audio_error"]:
        return "REVIEW", f"Audio analysis error: {audio_metrics['audio_error']}"

    if audio_metrics["duration"] < MIN_DURATION_SECONDS:
        return "REVIEW", "Audio too short"

    if audio_metrics["duration"] > MAX_DURATION_SECONDS:
        return "REVIEW", "Audio too long"

    if audio_metrics["rms_volume"] < MIN_RMS_VOLUME:
        return "REVIEW", "Volume too low"

    if audio_metrics["active_audio_ratio"] < MIN_ACTIVE_AUDIO_RATIO:
        return "REVIEW", "Too much silence"

    if audio_metrics["clipping_ratio"] > MAX_CLIPPING_RATIO:
        return "REVIEW", "Audio clipping detected"

    return "APPROVED", "Passed audio quality rules"


def transcribe_audio(audio_path):
    segments, info = model.transcribe(
        str(audio_path),
        language="pt",
        beam_size=5
    )

    text_parts = []
    no_speech_probs = []
    avg_logprobs = []

    for segment in segments:
        text_parts.append(segment.text.strip())
        no_speech_probs.append(segment.no_speech_prob)
        avg_logprobs.append(segment.avg_logprob)

    transcript = "\n".join(text_parts).strip()

    avg_no_speech = (
        sum(no_speech_probs) / len(no_speech_probs)
        if no_speech_probs
        else 1
    )

    avg_logprob = (
        sum(avg_logprobs) / len(avg_logprobs)
        if avg_logprobs
        else -99
    )

    return transcript, avg_no_speech, avg_logprob


def transcription_quality_check(transcript, avg_no_speech, avg_logprob):
    word_count = len(transcript.split())

    if word_count < MIN_WORDS:
        return "REVIEW", "Too few words"

    if avg_no_speech > MAX_NO_SPEECH_PROB:
        return "REVIEW", "High no speech probability"

    if avg_logprob < MIN_AVG_LOGPROB:
        return "REVIEW", "Low transcription confidence"

    return "APPROVED", "Passed transcription quality rules"

#transcripition quality rules
MIN_WORDS = 8
MAX_NO_SPEECH_PROB = 0.90
MIN_AVG_LOGPROB = -1.50

#audio quality rules
MIN_DURATION_SECONDS = 8
MAX_DURATION_SECONDS = 90
MIN_RMS_VOLUME = 0.001
MIN_ACTIVE_AUDIO_RATIO = 0.15
MAX_CLIPPING_RATIO = 0.05
SILENCE_THRESHOLD = 0.01

def final_quality_decision(
    audio_status,
    audio_reason,
    transcription_status,
    transcription_reason
):
    # If the transcription failed, send to review
    if transcription_status == "REVIEW":
        return "REVIEW", transcription_reason

    # If the transcription is good enough send to approved
    if audio_status == "REVIEW":
        light_audio_issues = [
            "Volume too low",
            "Too much silence"
        ]

        if audio_reason in light_audio_issues:
            return "APPROVED", f"Transcription passed; light audio issue: {audio_reason}"

        return "REVIEW", audio_reason

    return "APPROVED", "Passed transcription and usable audio rules"


def write_log(
    base_name,
    status,
    reason,
    audio_status,
    audio_reason,
    transcription_status,
    transcription_reason,
    transcript,
    avg_no_speech,
    avg_logprob,
    audio_metrics,
    original_name
):
    with open(LOGS / "processed_log.txt", "a", encoding="utf-8") as log:
        log.write(
            f"{base_name} | {status} | {reason} | "
            f"audio_status={audio_status} | "
            f"audio_reason={audio_reason} | "
            f"transcription_status={transcription_status} | "
            f"transcription_reason={transcription_reason} | "
            f"words={len(transcript.split())} | "
            f"no_speech={avg_no_speech:.2f} | "
            f"logprob={avg_logprob:.2f} | "
            f"duration={audio_metrics['duration']:.2f}s | "
            f"rms={audio_metrics['rms_volume']:.4f} | "
            f"active_ratio={audio_metrics['active_audio_ratio']:.2f} | "
            f"clipping={audio_metrics['clipping_ratio']:.4f} | "
            f"original={original_name}\n"
        )


def process_file(audio_path, primary, secondary):
    audio_metrics = analyze_audio_quality(audio_path)

    audio_status, audio_reason = audio_quality_check(audio_metrics)

    transcript, avg_no_speech, avg_logprob = transcribe_audio(audio_path)

    transcription_status, transcription_reason = transcription_quality_check(
        transcript,
        avg_no_speech,
        avg_logprob
    )

    status, reason = final_quality_decision(
        audio_status,
        audio_reason,
        transcription_status,
        transcription_reason
    )

    if status == "APPROVED" and AUTO_APPROVE:
        output_folder = APPROVED / primary / secondary
    else:
        output_folder = REVIEW / primary / secondary

    processed_folder = PROCESSED / primary / secondary

    output_folder.mkdir(parents=True, exist_ok=True)
    processed_folder.mkdir(parents=True, exist_ok=True)

    next_id = get_next_id(primary, secondary, output_folder)

    base_name = f"{primary}_{secondary}_{next_id:04d}"

    output_audio = output_folder / f"{base_name}.mp4"
    output_txt = output_folder / f"{base_name}.txt"

    print(f"\nProcessando: {audio_path.name}")
    print(f"Categoria: {primary} / {secondary}")
    print(f"Audio QA: {audio_status} | {audio_reason}")
    print(f"Transcription QA: {transcription_status} | {transcription_reason}")
    print(f"Final Status: {status} | {reason}")
    print(f"Words: {len(transcript.split())}")
    print(f"No speech: {avg_no_speech:.2f}")
    print(f"Logprob: {avg_logprob:.2f}")
    print(f"Duration: {audio_metrics['duration']:.2f}s")
    print(f"RMS: {audio_metrics['rms_volume']:.4f}")
    print(f"Active ratio: {audio_metrics['active_audio_ratio']:.2f}")
    print(f"Clipping: {audio_metrics['clipping_ratio']:.4f}")

    shutil.copy2(audio_path, output_audio)

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(transcript)

    write_log(
        base_name=base_name,
        status=status,
        reason=reason,
        audio_status=audio_status,
        audio_reason=audio_reason,
        transcription_status=transcription_status,
        transcription_reason=transcription_reason,
        transcript=transcript,
        avg_no_speech=avg_no_speech,
        avg_logprob=avg_logprob,
        audio_metrics=audio_metrics,
        original_name=audio_path.name
    )

    shutil.move(str(audio_path), processed_folder / audio_path.name)

    print(f"Concluído: {base_name}")


def main():
    print("\nPipeline iniciado.")
    print("Aguardando arquivos em incoming/PrimaryCategory/SecondaryCategory/\n")

    while True:
        primary_folders = [f for f in INCOMING.iterdir() if f.is_dir()]

        for primary_folder in primary_folders:
            primary = primary_folder.name

            secondary_folders = [
                f for f in primary_folder.iterdir()
                if f.is_dir()
            ]

            for secondary_folder in secondary_folders:
                secondary = secondary_folder.name

                files = list(secondary_folder.glob("*.mp4"))

                for file in files:
                    try:
                        process_file(file, primary, secondary)

                    except Exception as e:
                        print(f"Erro ao processar {file.name}: {e}")

        time.sleep(5)


if __name__ == "__main__":
    main()