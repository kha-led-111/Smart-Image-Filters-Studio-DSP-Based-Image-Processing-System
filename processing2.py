import numpy as np
import noisereduce as nr
import speech_recognition as sr

def clean_audio_signal(signal, sr_rate):
    signal = signal.astype('float32')
    
    reduced_noise = nr.reduce_noise(
        y=signal, 
        sr=sr_rate, 
        prop_decrease=0.6,  
        stationary=True  # DEGREE OF FREEDOM!!!
    )
    
    if np.max(np.abs(reduced_noise)) > 0:
        reduced_noise = reduced_noise / np.max(np.abs(reduced_noise))
        
    return reduced_noise.astype('float32')

""" def clean_audio_signal(signal, sr_rate):
    signal = signal.astype('float32')
    
    # 1. تنظيف الضوضاء
    reduced_noise = nr.reduce_noise(y=signal, sr=sr_rate, prop_decrease=0.8) # قللنا النسبة لعدم كتم الصوت تماماً
    
    # 2. عملية التطبيع (Normalization) - مهمة جداً للتعرف على الكلام
    # نرفع أعلى قمة في الصوت لتصل إلى 1.0 ليكون الكلام واضحاً للمحرك
    if np.max(np.abs(reduced_noise)) > 0:
        reduced_noise = reduced_noise / np.max(np.abs(reduced_noise))
        
    return reduced_noise.astype('float32') """

def speech_to_text(file_path, selected_lang="en-US"):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language=selected_lang)
            return text
        except:
            return