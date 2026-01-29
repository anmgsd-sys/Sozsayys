import google.generativeai as genai

# Өзіңіздің API кілтіңізді осында қойыңыз
GOOG_API_KEY = "AIzaSyDfHYVL47svlxFe290-J93qwXMa3lREc4U"

genai.configure(api_key=GOOG_API_KEY)

print("--- ҚОЛЖЕТІМДІ МОДЕЛЬДЕР ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Қате шықты: {e}")
print("----------------------------")