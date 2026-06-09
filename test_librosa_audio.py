from pathlib import Path
import librosa
import numpy as np

audio_path = Path("processed/StudyEducation/SelfStudyRecording/Audio 1.mp4")

print(f"Arquivo existe? {audio_path.exists()}")
print(f"Caminho: {audio_path}")

try:
    audio, sample_rate = librosa.load(str(audio_path), sr=None, mono=True)

    duration = librosa.get_duration(y=audio, sr=sample_rate)
    rms_volume = float(np.sqrt(np.mean(audio ** 2))) if len(audio) > 0 else 0.0
    active_audio_ratio = float(np.mean(np.abs(audio) > 0.01)) if len(audio) > 0 else 0.0
    clipping_ratio = float(np.mean(np.abs(audio) >= 0.98)) if len(audio) > 0 else 0.0

    print(f"Sample rate: {sample_rate}")
    print(f"Audio samples: {len(audio)}")
    print(f"Duration: {duration}")
    print(f"RMS: {rms_volume}")
    print(f"Active ratio: {active_audio_ratio}")    
    print(f"Clipping: {clipping_ratio}")

except Exception as e:
    print("ERRO NO LIBROSA:")
    print(e)