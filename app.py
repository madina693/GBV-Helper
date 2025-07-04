from flask import Flask, request, render_template_string, url_for, send_from_directory, redirect, session, send_file, jsonify
import os
import sqlite3
from datetime import datetime
import pandas as pd
import io
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def init_db():
    db_path = 'gbv_assessments.db'
    # Comment out os.remove to persist data; uncomment only for testing
    # if os.path.exists(db_path):
    #     os.remove(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age INTEGER,
                gender TEXT,
                language TEXT,
                responses TEXT,
                yes_count INTEGER,
                no_count INTEGER,
                level TEXT,
                support TEXT,
                timestamp DATETIME
            )
        ''')
        conn.commit()

init_db()

QUESTIONS = {
    'en': [
        "Has someone ever touched you in a way that made you uncomfortable or you didn’t agree to?",
        "Have you ever been called hurtful names or insulted often by someone close to you?",
        "Has anyone ever tried to control who you talk to, where you go, or what you wear?",
        "Have you ever felt scared of someone you’re in a relationship with (past or present)?",
        "Has anyone ever forced you to do something you didn’t want to do by using pressure or threats?",
        "Has someone close to you ever hurt you physically, even if it happened only once?",
        "Have you ever been made to feel ashamed or blamed for something someone else did to you?",
        "Has anyone ever taken something important from you (like money, phone, or school supplies) without your permission to punish or control you?",
        "Do you sometimes feel trapped, unsafe, or very stressed in your home or relationship?",
        "Have you ever been forced or pressured to stay in a relationship or situation you wanted to leave?"
    ],
    'sw': [
        "Je, mtu amewahi kukugusa kwa njia ambayo haikukufanya ujisikie vizuri au haukubali?",
        "Je, umewahi kuitwa majina ya kuumiza au kuudhi mara nyingi na mtu wa karibu nawe?",
        "Je, mtu amewahi kujaribu kudhibiti unayemzungumza naye, unakokwenda, au unavyovaa?",
        "Je, umewahi kuhisi woga kwa mtu unayehusiana naye (zamani au sasa)?",
        "Je, mtu amewahi kukulazimisha kufanya jambo usilotaka kwa kutumia shinikizo au vitisho?",
        "Je, mtu wa karibu amewahi kukuumiza kimwili, hata tukio likitokea mara moja tu?",
        "Je, umewahi kuhisi aibu au kuliwaumuwa kwa jambo ambalo mtu mwingine alimfanyia?",
        "Je, mtu amewahi kuchukua kitu muhimu kutoka kwako (kama pesa, simu, au vifaa vya shule) bila idhini yako ili kukudhibiti au kukandamiza?",
        "Je, wakati mwingine unahisi umefungwa, huna usalama, au unahisi msongo mkubwa nyumbani au katika uhusiano wako?",
        "Je, umewahi kulazimishwa au kushinikizwa kubaki katika uhusiano au hali ambayo ulikuwa unataka kuondoka?"
    ]
}

NAVBAR_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GBV Helper</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100 font-sans flex flex-col min-h-screen">
    <nav class="bg-blue-600 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/about" class="text-2xl font-bold">GBV Helper</a>
            <div class="flex items-center space-x-4">
                <div class="relative">
                    <form method="POST" action="/set_language">
                        <select name="language" onchange="this.form.submit()" class="bg-blue-500 text-white border border-white rounded-md px-2 py-1 focus:outline-none">
                            <option value="en" {{ 'selected' if language == 'en' else '' }}>English</option>
                            <option value="sw" {{ 'selected' if language == 'sw' else '' }}>Kiswahili</option>
                        </select>
                        <input type="hidden" name="redirect_url" value="{{ request_path }}">
                    </form>
                </div>
                <a href="/about" class="hover:underline">{{ 'About Us' if language == 'en' else 'Kuhusu Sisi' }}</a>
                <a href="/admin" class="hover:underline">{{ 'Admin' if language == 'en' else 'Msimamizi' }}</a>
            </div>
        </div>
    </nav>
"""

FOOTER_TEMPLATE = """
    <footer class="bg-gray-800 text-white p-4 mt-auto">
        <div class="container mx-auto text-center">
            <p>Contact us: <a href="mailto:info@healthtotech.org" class="underline">info@healthtotech.org</a></p>
            <p>Copyright © Health to Tech</p>
            <p class="mt-2 text-red-400">
                🚫 {{ 'This service does not replace healthcare providers or counselors'}}
            </p>
        </div>
    </footer>
</body>
</html>
"""

ABOUT_TEMPLATE = """
{{ navbar | safe }}
<main class="flex-grow">
    <div class="container mx-auto p-6">
        <div class="bg-white shadow-md rounded-lg p-8 max-w-2xl mx-auto">
            <h1 class="text-3xl font-bold mb-4">{{ 'About Us' if language == 'en' else 'Kuhusu Sisi' }}</h1>
            <p class="mb-4">
                {{ 
                    'At Health to Tech, we are committed to eradicating Gender-Based Violence (GBV) by leveraging cutting-edge technology. Our mission is to empower youth aged 13–35 in Tanzania with anonymous, accessible tools to assess their GBV risk and connect with vital support services. Through online direct link with local organizations, for legal aid, counseling, and psychosocial support to survivors, fostering safer communities.'
                    if language == 'en' else 
                    'Kwa Health to Tech, Katika Health to Tech, tumejikita katika kutokomeza ukatili wa kijinsia (GBV) kwa kutumia teknolojia ya kisasa. Lengo letu ni kuwawezesha vijana wenye umri wa miaka 13 hadi 35 hapa Tanzania kutumia zana rafiki na za faragha kutathmini hatari ya ukatili wa kijinsia na kuunganishwa moja kwa moja na huduma muhimu za msaada. Kupitia mtandao, tunawaunganisha na mashirika ya ndani yanayotoa msaada wa kisheria, ushauri wa kisaikolojia, na huduma za afya ya akili kwa waathirika, ili kujenga jamii salama zaidi.'
                }}
            </p>
            <h2 class="text-2xl font-semibold mb-4">{{ 'What We Do' if language == 'en' else 'Tunachofanya' }}</h2>
            <div class="flex flex-row space-x-4 mb-6">
                <div class="bg-white text-blue-600 p-4 rounded-md shadow-md flex-1 text-center border border-gray-200">
                    <h3 class="font-semibold">{{ 'Assess Participants' if language == 'en' else 'Tathmini Washiriki' }}</h3>
                    <p>{{ 
                        'Our assessment tool helps identify GBV risks through a confidential questionnaire tailored for youth aged 13–35, enabling targeted interventions.' 
                        if language == 'en' else 
                        'Zana yetu ya tathmini husaidia kubainisha hatari za GBV kupitia dodoso la siri lililobuniwa kwa vijana wa miaka 13–35, likiwezesha afua za kulengwa.'
                    }}</p>
                </div>
                <div class="bg-white text-blue-600 p-4 rounded-md shadow-md flex-1 text-center border border-gray-200">
                    <h3 class="font-semibold">{{ 'Provide Support' if language == 'en' else 'Toa Msaada' }}</h3>
                    <p>{{ 
                        'We connect survivors to trusted local organizations offering legal aid and counseling to address GBV effectively.' 
                        if language == 'en' else 
                        'Tunawaunganisha waathirika na mashirika ya ndani ya kuaminika yanayotoa msaada wa kisheria na ushauri nasaha ili kushughulikia GBV kwa ufanisi.'
                    }}</p>
                </div>
                <div class="bg-white text-blue-600 p-4 rounded-md shadow-md flex-1 text-center border border-gray-200">
                    <h3 class="font-semibold">{{ 'Anonymous Chatbot' if language == 'en' else 'Chatbot Isiyojulikana' }}</h3>
                    <p>{{ 
                        'Our anonymous chatbot provides a safe space to learn about GBV, offering guidance and raising awareness.' 
                        if language == 'en' else 
                        'Chatbot yetu isiyojulikana hutoa nafasi salama ya kujifunza kuhusu GBV, ikitoa mwongozo na kuongeza uelewa.'
                    }}</p>
                </div>
            </div>
            <a href="/assessment" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 inline-flex items-center">
                {{ 'Take the Assessment' if language == 'en' else 'Fanya Tathmini' }}
                <svg class="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
            </a>
        </div>
    </div>
</main>
{{ footer | safe }}
"""

FORM_TEMPLATE = """
{{ navbar | safe }}
<main class="flex-grow">
    <div class="container mx-auto p-20">
        <div class="bg-white shadow-md rounded-lg p-8 max-w-2xl mx-auto">
            <h1 class="text-3xl font-bold mb-4">{{ 'GBV Risk Assessment Form' if language == 'en' else 'Fomu ya Tathmini ya Hatari ya GBV' }}</h1>
            <form method="POST" class="space-y-4">
                {% if not show_questions %}
                <div>
                    <label for="age" class="block text-sm font-medium text-gray-700">{{ 'Age' if language == 'en' else 'Umri' }}</label>
                    <input type="number" name="age" id="age" value="{{ age }}" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" required>
                </div>
                <div>
                    <label for="gender" class="block text-sm font-medium text-gray-700">{{ 'Gender' if language == 'en' else 'Jinsia' }}</label>
                    <select name="gender" id="gender" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" required>
                        <option value="" {{ 'selected' if not gender else '' }}>{{ 'Select Gender' if language == 'en' else 'Chagua Jinsia' }}</option>
                        <option value="Male" {{ 'selected' if gender == 'Male' else '' }}>{{ 'Male' if language == 'en' else 'Mwanaume' }}</option>
                        <option value="Female" {{ 'selected' if gender == 'Female' else '' }}>{{ 'Female' if language == 'en' else 'Mwanamke' }}</option>
                    </select>
                </div>
                {% if error %}
                <p class="text-red-500">{{ error }}</p>
                {% endif %}
                <button type="submit" name="submit_initial" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">{{ 'Continue' if language == 'en' else 'Endelea' }}</button>
                {% else %}
                {% for i, question in questions %}
                <div class="border-b pb-4">
                    <p class="font-medium">{{ i + 1 }}. {{ question }}</p>
                    <div class="mt-2 space-x-4">
                        <label><input type="radio" name="q{{ i }}" value="yes" required> {{ 'Yes' if language == 'en' else 'Ndiyo' }}</label>
                        <label><input type="radio" name="q{{ i }}" value="no" required> {{ 'No' if language == 'en' else 'Hapana' }}</label>
                    </div>
                </div>
                {% endfor %}
                <input type="hidden" name="current_language" value="{{ language }}">
                {% if error %}
                <p class="text-red-500">{{ error }}</p>
                {% endif %}
                <button type="submit" name="submit_questions" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">{{ 'Submit' if language == 'en' else 'Wasilisha' }}</button>
                {% endif %}
            </form>
        </div>
    </div>
</main>
{{ footer | safe }}
"""

ADMIN_TEMPLATE = """
{{ navbar | safe }}
<main class="flex-grow">
    <div class="container mx-auto p-6">
        <div class="bg-white shadow-md rounded-lg p-8">
            <h1 class="text-3xl font-bold mb-4">{{ 'GBV Assessment Admin Dashboard' if language == 'en' else 'Dashibodi ya Msimamizi wa Tathmini ya GBV' }}</h1>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                    <h2 class="text-xl font-semibold mb-4">{{ 'Assessments by Age Range and Gender' if language == 'en' else 'Tathmini kwa Rangi ya Umri na Jinsia' }}</h2>
                    <canvas id="ageGenderChart" class="w-full h-[52px]"></canvas>
                </div>
                <div>
                    <h2 class="text-xl font-semibold mb-4">{{ 'GBV Risk vs No Risk (Percentage)' if language == 'en' else 'Hatari ya GBV dhidi ya Hakuna Hatari (Asilimia)' }}</h2>
                    <canvas id="riskChart" class="w-full h-64"></canvas>
                </div>
            </div>
            <a href="/download_csv" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 inline-block mb-4">{{ 'Download CSV Report' if language == 'en' else 'Pakua Ripoti ya CSV' }}</a>
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white border">
                    <thead>
                        <tr class="bg-gray-200">
                            <th class="py-2 px-4 border">{{ 'ID' if language == 'en' else 'Kitambulisho' }}</th>
                            <th class="py-2 px-4 border">{{ 'Age' if language == 'en' else 'Umri' }}</th>
                            <th class="py-2 px-4 border">{{ 'Gender' if language == 'en' else 'Jinsia' }}</th>
                            <th class="py-2 px-4 border">{{ 'Language' if language == 'en' else 'Lugha' }}</th>
                            <th class="py-2 px-4 border">{{ 'Responses' if language == 'en' else 'Majibu' }}</th>
                            <th class="py-2 px-4 border">{{ 'Yes Count' if language == 'en' else 'Idadi ya Ndiyo' }}</th>
                            <th class="py-2 px-4 border">{{ 'No Count' if language == 'en' else 'Idadi ya Hapana' }}</th>
                            <th class="py-2 px-4 border">{{ 'Level' if language == 'en' else 'Kiwango' }}</th>
                            <th class="py-2 px-4 border">{{ 'Support' if language == 'en' else 'Msaada' }}</th>
                            <th class="py-2 px-4 border">{{ 'Timestamp' if language == 'en' else 'Muhuri wa Wakati' }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for assessment in assessments %}
                        <tr>
                            <td class="py-2 px-4 border">{{ assessment[0] }}</td>
                            <td class="py-2 px-4 border">{{ assessment[1] }}</td>
                            <td class="py-2 px-4 border">{{ assessment[2] }}</td>
                            <td class="py-2 px-4 border">{{ assessment[3] }}</td>
                            <td class="py-2 px-4 border">{{ assessment[4] }}</td>
                            <td class="py-2 px-4 border">{{ assessment[5] }}</td>
                            <td class="py-2 px-4 border">{{ assessment[6] }}</td>
                            <td class="py-2 px-4 border">{{ assessment[7] }}</td>
                            <td class="py-2 px-4 border">{{ assessment[8] or ('Not Selected' if language == 'en' else 'Haikuchaguliwa') }}</td>
                            <td class="py-2 px-4 border">{{ assessment[9] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</main>
<script>
    const ageGenderData = {{ age_gender_data | tojson }};
    const riskData = {{ risk_data | tojson }};

    const ageGenderCtx = document.getElementById('ageGenderChart').getContext('2d');
    new Chart(ageGenderCtx, {
        type: 'bar',
        data: {
            labels: ['13-18', '19-25', '26-35'],
            datasets: [
                {
                    label: '{{ 'Male' if language == 'en' else 'Mwanaume' }}',
                    data: [ageGenderData['13-18'].Male, ageGenderData['19-25'].Male, ageGenderData['26-35'].Male],
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: '{{ 'Female' if language == 'en' else 'Mwanamke' }}',
                    data: [ageGenderData['13-18'].Female, ageGenderData['19-25'].Female, ageGenderData['26-35'].Female],
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            scales: {
                y: { beginAtZero: true, title: { display: true, text: '{{ 'Number of Assessments' if language == 'en' else 'Idadi ya Tathmini' }}' } },
                x: { title: { display: true, text: '{{ 'Age Range' if language == 'en' else 'Rangi ya Umri' }}' } }
            },
            plugins: { legend: { display: true } }
        }
    });

    const riskCtx = document.getElementById('riskChart').getContext('2d');
    new Chart(riskCtx, {
        type: 'pie',
        data: {
            labels: ['{{ 'GBV Risk' if language == 'en' else 'Hatari ya GBV' }}', '{{ 'No Risk' if language == 'en' else 'Hakuna Hatari' }}'],
            datasets: [{
                data: [riskData.risk, riskData.no_risk],
                backgroundColor: ['rgba(255, 99, 132, 0.5)', 'rgba(75, 192, 192, 0.5)'],
                borderColor: ['rgba(255, 99, 132, 1)', 'rgba(75, 192, 192, 1)'],
                borderWidth: 1
            }]
        },
        options: {
            plugins: { legend: { display: true } }
        }
    });
</script>
{{ footer | safe }}
"""

SUPPORT_TEMPLATE = """
{{ navbar | safe }}
<main class="flex-grow">
    <div class="container mx-auto p-6">
        <div class="bg-white shadow-md rounded-lg p-8 max-w-2xl mx-auto">
            <h1 class="text-3xl font-bold mb-4">{{ 'Support for GBV Survivors' if language == 'en' else 'Msaada kwa Waathirika wa GBV' }}</h1>
            <div class="mb-6">
                <h2 class="text-xl font-semibold mb-2">{{ 'Legal Support for GBV Survivors' if language == 'en' else 'Msaada wa Kisheria kwa Waathirika wa GBV' }}</h2>
                <ul class="list-disc pl-5">
                    <li><a href="https://tawla.or.tz" target="_blank" class="underline">{{ 'Tanzania Women Lawyers Association (TAWLA)' if language == 'en' else 'Chama cha Wanasheria Wanawake Tanzania (TAWLA)' }}</a> - {{ 'Legal aid for women' if language == 'en' else 'Msaada wa kisheria kwa wanawake' }}</li>
                    <li><a href="https://www.lhrc.or.tz" target="_blank" class="underline">{{ 'Legal and Human Rights Centre (LHRC)' if language == 'en' else 'Kituo cha Sheria na Haki za Binadamu (LHRC)' }}</a> - {{ 'Legal assistance and advocacy' if language == 'en' else 'Msaada wa kisheria na utetezi' }}</li>
                </ul>
            </div>
            <div class="mb-6">
                <h2 class="text-xl font-semibold mb-2">{{ 'Counselling Support for GBV Survivors' if language == 'en' else 'Msaada wa Ushauri Nasaha kwa Waathirika wa GBV' }}</h2>
                <ul class="list-disc pl-5">
                    <li><a href="https://www.tanzania.go.tz" target="_blank" class="underline">{{ 'National Child Helpline Tanzania' if language == 'en' else 'Simu ya Msaada ya Watoto Tanzania' }}</a> - {{ 'Support for GBV concerns' if language == 'en' else 'Msaada kwa masuala ya GBV' }}</li>
                    <li><a href="https://tamwa.org" target="_blank" class="underline">{{ 'Tanzania Media Women’s Association (TAMWA)' if language == 'en' else 'Chama cha Wanawake wa Vyombo vya Habari Tanzania (TAMWA)' }}</a> - {{ 'Psychosocial support' if language == 'en' else 'Msaada wa kisaikolojia' }}</li>
                    <li><a href="https://wildaftz.or.tz" target="_blank" class="underline">{{ 'Women in Law and Development in Africa (WiLDAF Tanzania)' if language == 'en' else 'Wanawake katika Sheria na Maendeleo Afrika (WiLDAF Tanzania)' }}</a> - {{ 'Legal support and GBV case referrals' if language == 'en' else 'Msaada wa kisheria na rufaa za kesi za GBV' }}</li>
                </ul>
            </div>
            <a href="/assessment" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">{{ 'Back to Assessment' if language == 'en' else 'Rudi kwenye Tathmini' }}</a>
        </div>
    </div>
    <script src="https://cdn.botpress.cloud/webchat/v3.0/inject.js"></script>
    <script src="https://files.bpcontent.cloud/2025/06/01/14/20250601145948-QV2AEO5Z.js"></script>
</main>
{{ footer | safe }}
"""

@app.route("/set_language", methods=["POST"])
def set_language():
    language = request.form.get('language', 'en')
    if language in ['en', 'sw']:
        session['language'] = language
    redirect_url = request.form.get('redirect_url', url_for('index'))
    return redirect(redirect_url)

@app.route("/static/<path:filename>")
def static_files(filename):
    static_dir = os.path.join(app.root_path, 'static')
    if not os.path.exists(os.path.join(static_dir, filename)):
        print(f"Error: File not found - static/{filename}")
    return send_from_directory(static_dir, filename)

@app.route("/", methods=["GET", "POST"])
def index():
    return redirect(url_for('about'))

@app.route("/assessment", methods=["GET", "POST"])
def assessment():
    language = session.get('language', 'en')
    questions = QUESTIONS.get(language, QUESTIONS['en'])
    error = None
    show_questions = False
    gender = ""
    age = ""

    navbar = render_template_string(NAVBAR_TEMPLATE, language=language, request_path=request.path)
    footer = render_template_string(FOOTER_TEMPLATE)

    if request.method == "POST":
        if 'submit_initial' in request.form:
            age = request.form.get("age", "").strip()
            gender = request.form.get("gender", "").strip()

            if not age or not age.isdigit():
                error = "Please enter a valid age." if language == 'en' else "Tafadhali weka umri sahihi."
            elif not gender:
                error = "Please select your gender." if language == 'en' else "Tafadhali chagua jinsia yako."
            else:
                try:
                    age = int(age)
                    if age < 13 or age > 35:
                        error = "Only participants aged 13 to 35 are allowed." if language == 'en' else "Ni washiriki wa miaka 13 hadi 35 tu wanaoruhusiwa."
                    else:
                        show_questions = True
                        session['age'] = age
                        session['gender'] = gender
                        session['language'] = language
                except ValueError:
                    error = "Invalid age format." if language == 'en' else "Umri si wa sahihi."
        elif 'submit_questions' in request.form:
            language = request.form.get('current_language', 'en')
            questions = QUESTIONS.get(language, QUESTIONS['en'])
            responses = [request.form.get(f'q{i}', 'no') for i in range(len(questions))]
            yes_count = sum(1 for r in responses if r == 'yes')
            no_count = sum(1 for r in responses if r == 'no')

            if yes_count + no_count != 10:
                error = "Please answer all 10 questions." if language == 'en' else "Tafadhali jibu maswali yote 10."
            else:
                if yes_count >= 1:
                    level = "GBV Risk" if language == 'en' else "Hatari ya GBV"
                else:
                    level = "No Risk" if language == 'en' else "Hakuna Hatari"

                try:
                    with sqlite3.connect('gbv_assessments.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO assessments (age, gender, language, responses, yes_count, no_count, level, support, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (session.get('age'), session.get('gender'), language, json.dumps(responses), yes_count, no_count, level, None, datetime.now()))
                        conn.commit()
                        assessment_id = cursor.lastrowid
                except sqlite3.Error as e:
                    print(f"Database error: {e}")
                    return "Database error occurred.", 500

                session['assessment_id'] = assessment_id
                session['support'] = None

                result_template = """
                {{ navbar | safe }}
                <main class="flex-grow">
                    <div class="container mx-auto p-20">
                        <div class="bg-white shadow-md rounded-lg p-8 max-w-2xl mx-auto">
                            <h1 class="text-3xl font-bold mb-4">{{ 'Assessment Result' if language == 'en' else 'Matokeo ya Tathmini' }}</h1>
                            <p class="text-xl mb-4">{{ level }}</p>
                            <div class="mb-6">
                                <p class="font-medium">{{ 'Do you agree to get legal and support organizations for GBV support?' if language == 'en' else 'Je, unakubali kupata mashirika ya kisheria na msaada kwa msaada wa GBV?' }}</p>
                                <div class="space-x-4 mt-2">
                                    <a href="/update_support/yes/{{ language }}" class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">{{ ' Agree to Support' if language == 'en' else 'Kubali Msaada' }}</a>
                                    <a href="/update_support/no/{{ language }}" class="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700">{{ 'Do Not Agree to Support' if language == 'en' else 'Sikubali Msaada' }}</a>
                                </div>
                            </div>
                            {% if support == 'yes' %}
                            <div class="mb-6">
                                <p class="font-medium">{{ 'Support Options' if language == 'en' else 'Chaguzi za Msaada' }}</p>
                                <ul class="list-disc pl-5">
                                    <li><a href="/support/{{ language }}" class="underline">{{ 'Legal Support for GBV Survivors' if language == 'en' else 'Msaada wa Kisheria kwa Waathirika wa GBV' }}</a></li>
                                    <li><a href="/support/{{ language }}" class="underline">{{ 'Counselling Support for GBV Survivors' if language == 'en' else 'Msaada wa Ushauri Nasaha kwa Waathirika wa GBV' }}</a></li>
                                </ul>
                            </div>
                            {% endif %}
                            <p class="mb-4">{{ 'Chat with our chatbot to learn more about GBV anonymously.' if language == 'en' else 'Ongea na chatbot yetu kujifunza zaidi kuhusu GBV bila kujulikana.' }}</p>
                            <a href="/assessment" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">{{ 'Start Over' if language == 'en' else 'Anza Tena' }}</a>
                        </div>
                    </div>
                    <script src="https://cdn.botpress.cloud/webchat/v3.0/inject.js"></script>
                <script src="https://files.bpcontent.cloud/2025/06/01/14/20250601145948-QV2AEO5Z.js"></script>
                </main>
                
                {{ footer | safe }}
                """
                return render_template_string(result_template, language=language, level=level, navbar=navbar, footer=footer, support=session.get('support'))

    return render_template_string(FORM_TEMPLATE, language=language, questions=enumerate(questions), show_questions=show_questions, age=age, gender=gender, error=error, navbar=navbar, footer=footer)

@app.route("/about")
def about():
    language = session.get('language', 'en')
    navbar = render_template_string(NAVBAR_TEMPLATE, language=language, request_path=request.path)
    footer = render_template_string(FOOTER_TEMPLATE)
    return render_template_string(ABOUT_TEMPLATE, language=language, navbar=navbar, footer=footer)

@app.route("/support/<lang>")
def support(lang):
    language = lang if lang in ['en', 'sw'] else 'en'
    navbar = render_template_string(NAVBAR_TEMPLATE, language=language, request_path=request.path)
    footer = render_template_string(FOOTER_TEMPLATE)
    return render_template_string(SUPPORT_TEMPLATE, language=language, navbar=navbar, footer=footer)

@app.route("/update_support/<support>/<lang>")
def update_support(support, lang):
    language = lang if lang in ['en', 'sw'] else 'en'
    assessment_id = session.get('assessment_id')

    if support in ['yes', 'no'] and assessment_id:
        try:
            with sqlite3.connect('gbv_assessments.db') as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE assessments SET support = ? WHERE id = ?', (support, assessment_id))
                conn.commit()
            session['support'] = support
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return "Database error occurred.", 500

    if support == 'yes':
        return redirect(url_for('support', lang=language))
    else:
        return redirect(url_for('assessment'))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    language = session.get('language', 'en')
    navbar = render_template_string(NAVBAR_TEMPLATE, language=language, request_path=request.path)
    footer = render_template_string(FOOTER_TEMPLATE)

    if request.method == "POST":
        password = request.form.get("password")
        if password == "admin123":
            session['admin'] = True
        else:
            return render_template_string("""
            {{ navbar | safe }}
            <main class="flex-grow">
                <div class="container mx-auto p-6">
                    <div class="bg-white shadow-md rounded-lg p-8 max-w-md mx-auto">
                        <h1 class="text-3xl font-bold mb-4">{{ 'Admin Login' if language == 'en' else 'Ingia kama Msimamizi' }}</h1>
                        <p class="text-red-500 mb-4">{{ 'Invalid password' if language == 'en' else 'Nenosiri si Sahihi' }}</p>
                        <form method="POST" class="space-y-4">
                            <div>
                                <label for="password" class="block text-sm font-medium text-gray-700">{{ 'Password' if language == 'en' else 'Nenosiri' }}:</label>
                                <input type="password" name="password" id="password" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" required>
                            </div>
                            <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">{{ 'Login' if language == 'en' else 'Ingia' }}</button>
                        </form>
                    </div>
                </div>
            </main>
            {{ footer | safe }}
            """, navbar=navbar, footer=footer)

    if session.get('admin'):
        try:
            with sqlite3.connect('gbv_assessments.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM assessments')
                assessments = cursor.fetchall()

            age_ranges = {'13-18': {'Male': 0, 'Female': 0}, '19-25': {'Male': 0, 'Female': 0}, '26-35': {'Male': 0, 'Female': 0}}
            risk_count = 0
            no_risk_count = 0

            for assessment in assessments:
                age = assessment[1]
                gender = assessment[2]
                level = assessment[7]
                if 13 <= age <= 18:
                    age_ranges['13-18'][gender] += 1
                elif 19 <= age <= 25:
                    age_ranges['19-25'][gender] += 1
                elif 26 <= age <= 35:
                    age_ranges['26-35'][gender] += 1
                if level in ['GBV Risk', 'Hatari ya GBV']:
                    risk_count += 1
                else:
                    no_risk_count += 1

            total = risk_count + no_risk_count
            risk_data = {
                'risk': risk_count / total * 100 if total > 0 else 0,
                'no_risk': no_risk_count / total * 100 if total > 0 else 0
            }

            return render_template_string(ADMIN_TEMPLATE, language=language, navbar=navbar, footer=footer, assessments=assessments, age_gender_data=age_ranges, risk_data=risk_data)
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return "Database error occurred.", 500

    return render_template_string("""
    {{ navbar | safe }}
    <main class="flex-grow">
        <div class="container mx-auto p-6">
            <div class="bg-white shadow-md rounded-lg p-8 max-w-md mx-auto">
                <h1 class="text-3xl font-bold mb-4">{{ 'Admin Login' if language == 'en' else 'Ingia kama Msimamizi' }}</h1>
                <form method="POST" class="space-y-4">
                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-700">{{ 'Password' if language == 'en' else 'Nenosiri' }}:</label>
                        <input type="password" name="password" id="password" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm" required>
                    </div>
                    <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">{{ 'Login' if language == 'en' else 'Ingia' }}</button>
                </form>
            </div>
        </div>
    </main>
    {{ footer | safe }}
    """, navbar=navbar, footer=footer)

@app.route("/download_csv")
def download_csv():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    try:
        with sqlite3.connect('gbv_assessments.db') as conn:
            df = pd.read_sql_query('SELECT * FROM assessments', conn)

        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='gbv_assessments.csv'
        )
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Database error occurred.", 500

if __name__ == '__main__':
    app.run(debug=True)
