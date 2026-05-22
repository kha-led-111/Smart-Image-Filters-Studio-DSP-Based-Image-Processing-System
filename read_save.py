import librosa
import soundfile as sf
import numpy as np

def load_audio(path):
    audio, sr = librosa.load(path,sr=None)
    return audio, sr

def save_audio(path, audio, sr):
    audio = np.clip(audio, -1.0, 1.0) 
    sf.write(path, audio, sr, subtype='PCM_16')