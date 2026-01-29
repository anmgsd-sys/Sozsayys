# -*- coding: utf-8 -*-
import os
import asyncio
import uuid
import random
import nest_asyncio
import certifi
import sys
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from groq import Groq
import edge_tts

# Windows-тағы қазақша әріптердің консольдегі қатесін түзету
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

nest_asyncio.apply()
os.environ['SSL_CERT_FILE'] = certifi.where()

# --- БАПТАУЛАР ---
# API кілтін сақтау (Қауіпсіздік үшін айнымалыға шығарылған)
GROQ_API_KEY = "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" 
client = Groq(api_key=GROQ_API_KEY)
SELECTED_MODEL = "llama-3.3-70b-versatile"

app = Flask(__name__)
CORS(app)

FALLBACK_TOPICS = [
    "Бұл палата мектептегі үй тапсырмасын толығымен жоюды ұсынады",
    "Бұл палата жасанды интеллекттің дамуы адамзатқа қауіп төндіреді деп есептейді",
    "Бұл палата әлеуметтік желілерді 16 жасқа дейін пайдалануға тыйым салуды қолдайды"
]

SPEAKER_PROMPTS = {
    "Үкімет 1 (Лидер)": "Сен - Үкімет Лидерісің. Резолюцияны түсіндір, терминдерге анықтама бер және 2-3 негізгі аргумент ұсын.",
    "Оппозиция 1 (Лидер)": "Сен - Оппозиция Лидерісің. Үкіметтің терминдерімен келісу/келіспеу және алғашқы қарсы аргументтерді айт.",
    "Үкімет 2 (Спикер)": "Сен - Үкіметтің 2-спикерісің. Аргументтерді тереңдет және Оппозицияның сөзін терісте.",
    "Оппозиция 2 (Спикер)": "Сен - Оппозицияның 2-спикерісің. Өз аргументтеріңді дамыт және Үкіметтің қатесін көрсет.",
    "Үкімет 3 (Қорытынды)": "Сен - Үкіметтің қорытынды спикерісің. Негізгі қақтығыс нүктелерін талда және Үкіметтің неге жеңгенін дәлелде. ЖАҢА АРГУМЕНТ ҚОСПА.",
    "Оппозиция 3 (Қорытынды)": "Сен - Оппозицияның қорытынды спикерісің. Бүкіл дебатты қорытындыла және салыстырмалы талдау жаса. ЖАҢА АРГУМЕНТ ҚОСПА."
}

JUDGE_CRITERIA = "Сен - бейтарап Төрешісің. Дебатты Аргументация (40%), Терістеу (25%), Құрылым (15%), Мәдениет (10%) және Командалық жұмыс (10%) бойынша бағалап, жеңімпазды анықта. Қорытындыны толық жаз."

def get_groq_response(system_prompt, user_prompt):
    full_system_prompt = system_prompt + " Маңызды: Сөзіңді соңына дейін аяқта, логикалық нүкте қой. Жарты жолда үзіліп қалмасын."
    
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model=SELECTED_MODEL,
        temperature=0.7,
        max_tokens=2500, 
    )
    return chat_completion.choices[0].message.content.strip()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_topic', methods=['GET'])
def get_topic():
    try:
        prompt = "Парламенттік дебатқа арналған қызықты резолюция ұсын. 1 сөйлем. 'Бұл палата...' деп басталсын."
        ai_topic = get_groq_response("Сен дебат сарапшысысың.", prompt)
        return jsonify({"topic": ai_topic.replace("*", "")})
    except:
        return jsonify({"topic": random.choice(FALLBACK_TOPICS)})

@app.route('/process_text', methods=['POST'])
def process_text():
    try:
        data = request.json
        user_text = data.get('text', '')
        topic = data.get('topic', '')
        turn_index = data.get('turn_index', 0)
        history = data.get('history', '')

        if turn_index >= 5 or "Дебатты қорытындыла" in user_text:
            current_role = "Төреші"
            system_p = JUDGE_CRITERIA
            user_p = f"Дебат тарихы: {history}\nСоңғы сөз: {user_text}\nЖеңімпазды анықта."
        else:
            roles_list = [
                "Үкімет 1 (Лидер)", "Оппозиция 1 (Лидер)", 
                "Үкімет 2 (Спикер)", "Оппозиция 2 (Спикер)", 
                "Үкімет 3 (Қорытынды)", "Оппозиция 3 (Қорытынды)"
            ]
            idx = min(turn_index + 1, 5)
            current_role = roles_list[idx]
            system_p = SPEAKER_PROMPTS.get(current_role, "Сен дебатшысың.")
            user_p = f"Тақырып: {topic}. Тарих: {history}. Қарсыластың сөзі: {user_text}."

        ai_text = get_groq_response(system_p, user_p).replace("*", "")
        
        # Аудио файлды жасау
        unique_filename = f"audio_{uuid.uuid4().hex[:8]}.mp3"
        output_path = os.path.join("static", unique_filename)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        communicate = edge_tts.Communicate(ai_text, "kk-KZ-DauletNeural")
        loop.run_until_complete(communicate.save(output_path))
        loop.close()

        return jsonify({
            "ai_text": ai_text,
            "role": current_role,
            "audio_url": f"/static/{unique_filename}",
            "is_final": (current_role == "Төреші")
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"ai_text": "Қате орын алды. Жүйені қайта қосыңыз.", "role": "Жүйе"}), 500

if __name__ == '__main__':
    if not os.path.exists("static"):
        os.makedirs("static")
    app.run(debug=True, port=5000)