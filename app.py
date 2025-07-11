from flask import Flask, request, render_template_string, url_for, send_from_directory, redirect, session, send_file
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>GBV Helper</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: #1d4ed8;
            --secondary: #3b82f6;
            --accent: #f43f5e;
            --bg-light: #f3f4f6;
            --text-dark: #1f2937;
        }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(to bottom, var(--bg-light), #ffffff);
        }
        .container {
            max-width: 1200px;
            padding: 0.5rem;
            margin: 0 auto;
        }
        .navbar {
            position: sticky;
            top: 0;
            z-index: 50;
            background: linear-gradient(to right, var(--primary), var(--secondary));
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            padding: 0.5rem 0;
        }
        .navbar-brand {
            font-size: 1.25rem;
            font-weight: 700;
            color: white;
            transition: color 0.2s ease;
        }
        .navbar-brand:hover {
            color: #dbeafe;
        }
        .navbar-menu {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        .nav-link {
            color: white;
            font-size: 0.875rem;
            padding: 0.25rem 0.75rem;
            border-radius: 0.25rem;
            transition: background-color 0.2s ease, transform 0.2s ease;
        }
        .nav-link:hover {
            background-color: rgba(255, 255, 255, 0.1);
            transform: translateY(-2px);
        }
        @media (min-width: 640px) {
            .navbar-menu {
                flex-direction: row;
                gap: 1rem;
            }
            .navbar-brand {
                font-size: 1.5rem;
            }
        }
        @media (min-width: 1024px) {
            .navbar-brand {
                font-size: 1.75rem;
            }
        }
        .form-input {
            padding: 0.75rem;
            font-size: 1rem;
            border: 2px solid #d1d5db;
            border-radius: 0.5rem;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
            width: 100%;
        }
        .form-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.2);
            outline: none;
        }
        .form-button {
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 0.5rem;
            background: var(--primary);
            color: white;
            transition: background-color 0.2s ease, transform 0.2s ease;
        }
        .form-button:hover {
            background: var(--secondary);
            transform: translateY(-2px);
        }
        .form-button:active {
            transform: translateY(0);
        }
        .chart-container {
            max-width: 100%;
            height: auto;
            margin: 0 auto;
            background: white;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        canvas {
            max-height: 350px !important;
            width: 100% !important;
        }
        .card {
            background: white;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        .text-sm { font-size: 0.875rem; }
        .text-base { font-size: 1rem; }
        .text-lg { font-size: 1.125rem; }
        .text-xl { font-size: 1.25rem; }
        .text-2xl { font-size: 1.5rem; }
        .text-3xl { font-size: 1.875rem; }
        @media (min-width: 640px) {
            .text-sm { font-size: 0.9375rem; }
            .text-base { font-size: 1.125rem; }
            .text-lg { font-size: 1.25rem; }
            .text-xl { font-size: 1.5rem; }
            .text-2xl { font-size: 1.75rem; }
            .text-3xl { font-size: 2.25rem; }
        }
        @media (min-width: 1024px) {
            .text-sm { font-size: 1rem; }
            .text-base { font-size: 1.25rem; }
            .text-lg { font-size: 1.5rem; }
            .text-xl { font-size: 1.75rem; }
            .text-2xl { font-size: 2rem; }
            .text-3xl { font-size: 2.5rem; }
        }
        @media (max-width: 640px) {
            .p-8 { padding: 1rem; }
            .p-6 { padding: 0.75rem; }
            .max-w-4xl { max-width: 100%; }
            .grid-cols-3 { grid-template-columns: 1fr; }
            .grid-cols-2 { grid-template-columns: 1fr; }
            .space-x-4 > * + * { margin-left: 0; margin-top: 0.75rem; }
            .flex-row { flex-direction: column; }
            .table { font-size: 0.75rem; }
            .table th, .table td { padding: 0.5rem; }
        }
        .radio-group {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        .radio-label {
            display: flex;
            align-items: center;
            padding: 0.5rem 1rem;
            border: 2px solid #d1d5db;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .radio-label:hover {
            background: #f3f4f6;
        }
        .radio-label input:checked + span {
            color: var(--primary);
            font-weight: 600;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body class="bg-gray-100 flex flex-col min-h-screen">
    <nav class="navbar text-white">
        <div class="container flex flex-col sm:flex-row justify-between items-center">
            <a href="/about" class="navbar-brand mb-1 sm:mb-0">GBV Helper</a>
            <div class="navbar-menu sm:flex-row items-center">
                <div class="relative">
                    <form method="POST" action="/set_language">
                        <select name="language" onchange="this.form.submit()" class="bg-transparent text-white border-2 border-white rounded-md px-2 py-1 text-sm w-full sm:w-auto transition-all duration-200">
                            <option value="en" {{ 'selected' if language == 'en' else '' }} class="bg-white text-gray-800">English</option>
                            <option value="sw" {{ 'selected' if language == 'sw' else '' }} class="bg-white text-gray-800">Kiswahili</option>
                        </select>
                        <input type="hidden" name="redirect_url" value="{{ request_path }}">
                    </form>
                </div>
                <a href="/about" class="nav-link">{{ 'About Us' if language == 'en' else 'Kuhusu Sisi' }}</a>
            </div>
        </div>
    </nav>
    <div class="pt-8"></div>
"""

FOOTER_TEMPLATE = """
    <footer class="bg-gray-900 text-white mt-auto">
        <div class="container text-center space-y-1 py-3">
            <p class="text-sm">Contact us: <a href="mailto:info@healthtotech.org" class="underline hover:text-blue-300 transition-colors">info@healthtotech.org</a></p>
            <p class="text-xs">Copyright © {{ '2025' }} Health to Tech</p>
            <p class="text-red-400 text-xs font-medium">
                🚫 {{ 'This service does not replace healthcare providers' if language == 'en' else 'Huduma hii haichukui nafasi ya watoa huduma za afya' }}
            </p>
        </div>
    </footer>
</body>
</html>
"""

ABOUT_TEMPLATE = """
{{ navbar | safe }}
<main class="flex-grow">
    <div class="container p-6">
        <div class="card p-8 max-w-4xl mx-auto">
            <h1 class="text-3xl font-bold mb-6 text-center text-gray-800">{{ 'About Us' if language == 'en' else 'Kuhusu Sisi' }}</h1>
            <p class="mb-6 text-base text-gray-600 leading-relaxed">
                {{ 
                    'At Health to Tech, we are committed to eradicating Gender-Based Violence (GBV) by leveraging cutting-edge technology. Our mission is to empower youth aged 13–35 in Tanzania with anonymous, accessible tools to assess their GBV risk and connect with vital support services. Through online direct links with local organizations, we provide legal aid, counseling, and psychosocial support to survivors, fostering safer communities.'
                    if language == 'en' else 
                    'Kwa Health to Tech, tumejikita katika kutokomeza ukatili wa kijinsia (GBV) kwa kutumia teknolojia ya kisasa. Lengo letu ni kuwawezesha vijana wenye umri wa miaka 13 hadi 35 hapa Tanzania kutumia zana rafiki na za faragha kutathmini hatari ya ukatili wa kijinsia na kuunganishwa moja kwa moja na huduma muhimu za msaada. Kupitia mtandao, tunawaunganisha na mashirika ya ndani yanayotoa msaada wa kisheria, ushauri wa kisaikolojia, na huduma za afya ya akili kwa waathirika, ili kujenga jamii salama zaidi.'
                }}
            </p>
            <h2 class="text-2xl font-semibold mb-6 text-center text-gray-800">{{ 'What We Do' if language == 'en' else 'Tunachofanya' }}</h2>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
                <div class="card p-6 text-center">
                    <div class="mb-4">
                        <svg class="w-12 h-12 mx-auto text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <h3 class="font-semibold text-lg mb-2">{{ 'Assess Participants' if language == 'en' else 'Tathmini Washiriki' }}</h3>
                    <p class="text-sm text-gray-600">
                        {{ 
                            'Our assessment tool helps identify GBV risks through a confidential questionnaire tailored for youth aged 13–35, enabling targeted interventions.' 
                            if language == 'en' else 
                            'Zana yetu ya tathmini husaidia kubainisha hatari za GBV kupitia dodoso la siri lililobuniwa kwa vijana wa miaka 13–35, likiwezesha afua za kulengwa.'
                        }}
                    </p>
                </div>
                <div class="card p-6 text-center">
                    <div class="mb-4">
                        <svg class="w-12 h-12 mx-auto text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.747 0-3.332.477-4.5 1.253"></path>
                        </svg>
                    </div>
                    <h3 class="font-semibold text-lg mb-2">{{ 'Provide Support' if language == 'en' else 'Toa Msaada' }}</h3>
                    <p class="text-sm text-gray-600">
                        {{ 
                            'We connect survivors to trusted local organizations offering legal aid and counseling to address GBV effectively.' 
                            if language == 'en' else 
                            'Tunawaunganisha waathirika na mashirika ya ndani ya kuaminika yanayotoa msaada wa kisheria na ushauri nasaha ili kushughulikia GBV kwa ufanisi.'
                        }}
                    </p>
                </div>
                <div class="card p-6 text-center">
                    <div class="mb-4">
                        <svg class="w-12 h-12 mx-auto text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5v-4a2 2 0 012-2h10a2 2 0 012 2v4h-4m-6 0h6"></path>
                        </svg>
                    </div>
                    <h3 class="font-semibold text-lg mb-2">{{ 'Anonymous Chatbot' if language == 'en' else 'Chatbot Isiyojulikana' }}</h3>
                    <p class="text-sm text-gray-600">
                        {{ 
                            'Our anonymous chatbot provides a safe space to learn about GBV, offering guidance and raising awareness.' 
                            if language == 'en' else 
                            'Chatbot yetu isiyojulikana hutoa nafasi salama ya kujifunza kuhusu GBV, ikitoa mwongozo na kuongeza uelewa.'
                        }}
                    </p>
                </div>
            </div>
            <div class="text-center">
                <a href="/assessment" class="form-button inline-flex items-center">
                    {{ 'Take the Assessment' if language == 'en' else 'Fanya Tathmini' }}
                    <svg class="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                    </svg>
                </a>
            </div>
        </div>
    </div>
</main>
{{ footer | safe }}
"""

FORM_TEMPLATE = """
{{ navbar | safe }}
<main class="flex-grow">
    <div class="container p-6">
        <div class="card p-8 max-w-4xl mx-auto">
            <h1 class="text-3xl font-bold mb-6 text-center text-gray-800">{{ 'GBV Risk Assessment Form' if language == 'en' else 'Fomu ya Tathmini ya Hatari ya GBV' }}</h1>
            <form method="POST" class="space-y-6">
                {% if not agreed %}
                <div>
                    <p class="text-base text-gray-600 mb-4">
                        {{ 
                            'By proceeding with this assessment, you agree to answer the questions honestly and understand that this tool is designed to help identify potential GBV risks. Your responses are anonymous and will be used to provide tailored support options. This service does not replace professional healthcare advice.'
                            if language == 'en' else 
                            'Kwa kuendelea na tathmini hii, unakubali kujibu maswali kwa uaminifu na kuelewa kuwa zana hii imeundwa kusaidia kubainisha hatari zinazowezekana za GBV. Majibu yako ni ya siri na yatatumika kutoa chaguzi za msaada zinazolengwa. Huduma hii haichukui nafasi ya ushauri wa kitaalamu wa afya.'
                        }}
                    </p>
                    <div class="text-center">
                        <button type="submit" name="agree" class="form-button">{{ 'I Agree' if language == 'en' else 'Nakubali' }}</button>
                    </div>
                </div>
                {% elif not show_questions %}
                <div>
                    <label for="age" class="block text-lg font-medium text-gray-700 mb-2">{{ 'Age' if language == 'en' else 'Umri' }}</label>
                    <input type="number" name="age" id="age" value="{{ age }}" class="form-input" required aria-describedby="age-error">
                    {% if error and 'age' in error.lower() %}
                    <p id="age-error" class="text-red-500 text-sm mt-2">{{ error }}</p>
                    {% endif %}
                </div>
                <div>
                    <label for="gender" class="block text-lg font-medium text-gray-700 mb-2">{{ 'Gender' if language == 'en' else 'Jinsia' }}</label>
                    <select name="gender" id="gender" class="form-input" required aria-describedby="gender-error">
                        <option value="" {{ 'selected' if not gender else '' }}>{{ 'Select Gender' if language == 'en' else 'Chagua Jinsia' }}</option>
                        <option value="Male" {{ 'selected' if gender == 'Male' else '' }}>{{ 'Male' if language == 'en' else 'Mwanaume' }}</option>
                        <option value="Female" {{ 'selected' if gender == 'Female' else '' }}>{{ 'Female' if language == 'en' else 'Mwanamke' }}</option>
                    </select>
                    {% if error and 'gender' in error.lower() %}
                    <p id="gender-error" class="text-red-500 text-sm mt-2">{{ error }}</p>
                    {% endif %}
                </div>
                <div class="text-center">
                    <button type="submit" name="submit_initial" class="form-button">{{ 'Continue' if language == 'en' else 'Endelea' }}</button>
                </div>
                {% else %}
                {% for i, question in questions %}
                <div class="border-b border-gray-200 pb-6">
                    <p class="font-medium text-lg text-gray-800">{{ i + 1 }}. {{ question }}</p>
                    <div class="radio-group mt-3">
                        <label class="radio-label">
                            <input type="radio" name="q{{ i }}" value="yes" required class="mr-2">
                            <span>{{ 'Yes' if language == 'en' else 'Ndiyo' }}</span>
                        </label>
                        <label class="radio-label">
                            <input type="radio" name="q{{ i }}" value="no" required class="mr-2">
                            <span>{{ 'No' if language == 'en' else 'Hapana' }}</span>
                        </label>
                    </div>
                </div>
                {% endfor %}
                <input type="hidden" name="current_language" value="{{ language }}">
                {% if error %}
                <p class="text-red-500 text-sm text-center">{{ error }}</p>
                {% endif %}
                <div class="text-center">
                    <button type="submit" name="submit_questions" class="form-button">{{ 'Submit' if language == 'en' else 'Wasilisha' }}</button>
                </div>
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
    <div class="container p-6">
        <div class="card p-8">
            <h1 class="text-3xl font-bold mb-8 text-center text-gray-800">{{ 'GBV Assessment Admin Dashboard' if language == 'en' else 'Dashibodi ya Msimamizi wa Tathmini ya GBV' }}</h1>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                <div class="chart-container">
                    <h2 class="text-xl font-semibold mb-4 text-center text-gray-800">{{ 'Assessments by Age Range and Gender' if language == 'en' else 'Tathmini kwa Rangi ya Umri na Jinsia' }}</h2>
                    <canvas id="ageGenderChart"></canvas>
                    {% if not assessments %}
                    <p class="text-center text-gray-500 text-sm mt-4">{{ 'No data available for charts.' if language == 'en' else 'Hakuna data inapatikana kwa chati.' }}</p>
                    {% endif %}
                </div>
                <div class="chart-container">
                    <h2 class="text-xl font-semibold mb-4 text-center text-gray-800">{{ 'GBV Risk vs No Risk (Percentage)' if language == 'en' else 'Hatari ya GBV dhidi ya Hakuna Hatari (Asilimia)' }}</h2>
                    <canvas id="riskChart"></canvas>
                    {% if not assessments %}
                    <p class="text-center text-gray-500 text-sm mt-4">{{ 'No data available for charts.' if language == 'en' else 'Hakuna data inapatikana kwa chati.' }}</p>
                    {% endif %}
                </div>
            </div>
            <div class="text-center mb-8">
                <a href="/download_csv" class="form-button">{{ 'Download CSV Report' if language == 'en' else 'Pakua Ripoti ya CSV' }}</a>
            </div>
            <div class="overflow-x-auto">
                <table class="table min-w-full bg-white border text-sm">
                    <thead>
                        <tr class="bg-gray-100">
                            <th class="py-3 px-4 border">{{ 'ID' if language == 'en' else 'Kitambulisho' }}</th>
                            <th class="py-3 px-4 border">{{ 'Age' if language == 'en' else 'Umri' }}</th>
                            <th class="py-3 px-4 border">{{ 'Gender' if language == 'en' else 'Jinsia' }}</th>
                            <th class="py-3 px-4 border">{{ 'Language' if language == 'en' else 'Lugha' }}</th>
                            <th class="py-3 px-4 border">{{ 'Responses' if language == 'en' else 'Majibu' }}</th>
                            <th class="py-3 px-4 border">{{ 'Yes Count' if language == 'en' else 'Idadi ya Ndiyo' }}</th>
                            <th class="py-3 px-4 border">{{ 'No Count' if language == 'en' else 'Idadi ya Hapana' }}</th>
                            <th class="py-3 px-4 border">{{ 'Level' if language == 'en' else 'Kiwango' }}</th>
                            <th class="py-3 px-4 border">{{ 'Support' if language == 'en' else 'Msaada' }}</th>
                            <th class="py-3 px-4 border">{{ 'Timestamp' if language == 'en' else 'Muhuri wa Wakati' }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for assessment in assessments %}
                        <tr class="hover:bg-gray-50">
                            <td class="py-3 px-4 border">{{ assessment[0] }}</td>
                            <td class="py-3 px-4 border">{{ assessment[1] }}</td>
                            <td class="py-3 px-4 border">{{ assessment[2] }}</td>
                            <td class="py-3 px-4 border">{{ assessment[3] }}</td>
                            <td class="py-3 px-4 border">{{ assessment[4] }}</td>
                            <td class="py-3 px-4 border">{{ assessment[5] }}</td>
                            <td class="py-3 px-4 border">{{ assessment[6] }}</td>
                            <td class="py-3 px-4 border">{{ assessment[7] }}</td>
                            <td class="py-3 px-4 border">{{ assessment[8] or ('Not Selected' if language == 'en' else 'Haikuchaguliwa') }}</td>
                            <td class="py-3 px-4 border">{{ assessment[9] }}</td>
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
                    backgroundColor: 'rgba(29, 78, 216, 0.6)',
                    borderColor: 'rgba(29, 78, 216, 1)',
                    borderWidth: 1
                },
                {
                    label: '{{ 'Female' if language == 'en' else 'Mwanamke' }}',
                    data: [ageGenderData['13-18'].Female, ageGenderData['19-25'].Female, ageGenderData['26-35'].Female],
                    backgroundColor: 'rgba(244, 63, 94, 0.6)',
                    borderColor: 'rgba(244, 63, 94, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: '{{ 'Number of Assessments' if language == 'en' else 'Idadi ya Tathmini' }}', font: { size: 14 } },
                    ticks: { font: { size: 12 } },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                },
                x: {
                    title: { display: true, text: '{{ 'Age Range' if language == 'en' else 'Rangi ya Umri' }}', font: { size: 14 } },
                    ticks: { font: { size: 12 } }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: { font: { size: 12 }, padding: 15 }
                }
            }
        }
    });

    const riskCtx = document.getElementById('riskChart').getContext('2d');
    new Chart(riskCtx, {
        type: 'pie',
        data: {
            labels: ['{{ 'GBV Risk' if language == 'en' else 'Hatari ya GBV' }}', '{{ 'No Risk' if language == 'en' else 'Hakuna Hatari' }}'],
            datasets: [{
                data: [riskData.risk, riskData.no_risk],
                backgroundColor: ['rgba(244, 63, 94, 0.6)', 'rgba(74, 222, 128, 0.6)'],
                borderColor: ['rgba(244, 63, 94, 1)', 'rgba(74, 222, 128, 1)'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: { font: { size: 12 }, padding: 15 }
                },
                tooltip: {
                    bodyFont: { size: 12 },
                    titleFont: { size: 14 }
                }
            }
        }
    });
</script>
{{ footer | safe }}
"""

SUPPORT_TEMPLATE = """
{{ navbar | safe }}
<main class="flex-grow">
    <div class="container p-6">
        <div class="card p-8 max-w-4xl mx-auto">
            <h1 class="text-3xl font-bold mb-6 text-center text-gray-800">{{ 'Support for GBV Survivors' if language == 'en' else 'Msaada kwa Waathirika wa GBV' }}</h1>
            <div class="mb-8">
                <h2 class="text-xl font-semibold mb-4 text-gray-800">{{ 'Legal Support for GBV Survivors' if language == 'en' else 'Msaada wa Kisheria kwa Waathirika wa GBV' }}</h2>
                <ul class="list-disc pl-6 text-base text-gray-600 space-y-3">
                    <li><a href="https://tawla.or.tz" target="_blank" class="underline hover:text-blue-600 transition-colors">{{ 'Tanzania Women Lawyers Association (TAWLA)' if language == 'en' else 'Chama cha Wanasheria Wanawake Tanzania (TAWLA)' }}</a> - {{ 'Legal aid for women' if language == 'en' else 'Msaada wa kisheria kwa wanawake' }}</li>
                    <li><a href="https://www.lhrc.or.tz" target="_blank" class="underline hover:text-blue-600 transition-colors">{{ 'Legal and Human Rights Centre (LHRC)' if language == 'en' else 'Kituo cha Sheria na Haki za Binadamu (LHRC)' }}</a> - {{ 'Legal assistance and advocacy' if language == 'en' else 'Msaada wa kisheria na utetezi' }}</li>
                </ul>
            </div>
            <div class="mb-8">
                <h2 class="text-xl font-semibold mb-4 text-gray-800">{{ 'Counselling Support for GBV Survivors' if language == 'en' else 'Msaada wa Ushauri Nasaha kwa Waathirika wa GBV' }}</h2>
                <ul class="list-disc pl-6 text-base text-gray-600 space-y-3">
                    <li><a href="https://www.tanzania.go.tz" target="_blank" class="underline hover:text-blue-600 transition-colors">{{ 'National Child Helpline Tanzania' if language == 'en' else 'Simu ya Msaada ya Watoto Tanzania' }}</a> - {{ 'Support for GBV concerns' if language == 'en' else 'Msaada kwa masuala ya GBV' }}</li>
                    <li><a href="https://tamwa.org" target="_blank" class="underline hover:text-blue-600 transition-colors">{{ 'Tanzania Media Women’s Association (TAMWA)' if language == 'en' else 'Chama cha Wanawake wa Vyombo vya Habari Tanzania (TAMWA)' }}</a> - {{ 'Psychosocial support' if language == 'en' else 'Msaada wa kisaikolojia' }}</li>
                    <li><a href="https://wildaftz.or.tz" target="_blank" class="underline hover:text-blue-600 transition-colors">{{ 'Women in Law and Development in Africa (WiLDAF Tanzania)' if language == 'en' else 'Wanawake katika Sheria na Maendeleo Afrika (WiLDAF Tanzania)' }}</a> - {{ 'Legal support and GBV case referrals' if language == 'en' else 'Msaada wa kisheria na rufaa za kesi za GBV' }}</li>
                </ul>
            </div>
            <div class="text-center">
                <a href="/assessment" class="form-button">{{ 'Back to Assessment' if language == 'en' else 'Rudi kwenye Tathmini' }}</a>
            </div>
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
    agreed = session.get('agreed', False)

    navbar = render_template_string(NAVBAR_TEMPLATE, language=language, request_path=request.path)
    footer = render_template_string(FOOTER_TEMPLATE, language=language)

    if request.method == "POST":
        if 'agree' in request.form:
            session['agreed'] = True
            agreed = True
        elif 'submit_initial' in request.form and agreed:
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
        elif 'submit_questions' in request.form and agreed:
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
                session['agreed'] = False  # Reset agreement after submission

                result_template = """
                {{ navbar | safe }}
                <main class="flex-grow">
                    <div class="container p-6">
                        <div class="card p-8 max-w-4xl mx-auto">
                            <h1 class="text-3xl font-bold mb-6 text-center text-gray-800">{{ 'Assessment Result' if language == 'en' else 'Matokeo ya Tathmini' }}</h1>
                            <p class="text-xl mb-6 text-center {{ 'text-red-600' if level in ['GBV Risk', 'Hatari ya GBV'] else 'text-green-600' }}">{{ level }}</p>
                            <div class="mb-8 text-center">
                                <p class="font-medium text-lg text-gray-800">{{ 'Do you agree to get legal and support organizations for GBV support?' if language == 'en' else 'Je, unakubali kupata mashirika ya kisheria na msaada kwa msaada wa GBV?' }}</p>
                                <div class="mt-4 flex flex-wrap justify-center gap-4">
                                    <a href="/update_support/yes/{{ language }}" class="form-button bg-green-600 hover:bg-green-700">{{ ' Agree to Support' if language == 'en' else 'Kubali Msaada' }}</a>
                                    <a href="/update_support/no/{{ language }}" class="form-button bg-red-600 hover:bg-red-700">{{ 'Do Not Agree to Support' if language == 'en' else 'Sikubali Msaada' }}</a>
                                </div>
                            </div>
                            {% if support == 'yes' %}
                            <div class="mb-8">
                                <p class="font-medium text-lg text-gray-800">{{ 'Support Options' if language == 'en' else 'Chaguzi za Msaada' }}</p>
                                <ul class="list-disc pl-6 text-base text-gray-600 space-y-3 mt-3">
                                    <li><a href="/support/{{ language }}" class="underline hover:text-blue-600 transition-colors">{{ 'Legal Support for GBV Survivors' if language == 'en' else 'Msaada wa Kisheria kwa Waathirika wa GBV' }}</a></li>
                                    <li><a href="/support/{{ language }}" class="underline hover:text-blue-600 transition-colors">{{ 'Counselling Support for GBV Survivors' if language == 'en' else 'Msaada wa Ushauri Nasaha kwa Waathirika wa GBV' }}</a></li>
                                </ul>
                            </div>
                            {% endif %}
                            <p class="mb-6 text-base text-gray-600 text-center">{{ 'Chat with our chatbot to learn more about GBV anonymously at right side bottom 💬.' if language == 'en' else 'Ongea na chatbot yetu kujifunza zaidi kuhusu GBV bila kujulikana upande wa kulia chini💬.' }}</p>
                            <div class="text-center">
                                <a href="/assessment" class="form-button">{{ 'Start Over' if language == 'en' else 'Anza Tena' }}</a>
                            </div>
                        </div>
                    </div>
                    <script src="https://cdn.botpress.cloud/webchat/v3.0/inject.js"></script>
                    <script src="https://files.bpcontent.cloud/2025/06/01/14/20250601145948-QV2AEO5Z.js"></script>
                </main>
                {{ footer | safe }}
                """
                return render_template_string(result_template, language=language, level=level, navbar=navbar, footer=footer, support=session.get('support'))

    return render_template_string(FORM_TEMPLATE, language=language, questions=enumerate(questions), show_questions=show_questions, age=age, gender=gender, error=error, navbar=navbar, footer=footer, agreed=agreed)

@app.route("/about")
def about():
    language = session.get('language', 'en')
    navbar = render_template_string(NAVBAR_TEMPLATE, language=language, request_path=request.path)
    footer = render_template_string(FOOTER_TEMPLATE, language=language)
    return render_template_string(ABOUT_TEMPLATE, language=language, navbar=navbar, footer=footer)

@app.route("/support/<lang>")
def support(lang):
    language = lang if lang in ['en', 'sw'] else 'en'
    navbar = render_template_string(NAVBAR_TEMPLATE, language=language, request_path=request.path)
    footer = render_template_string(FOOTER_TEMPLATE, language=language)
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

@app.route("/admin-login", methods=["GET", "POST"])
def admin():
    language = session.get('language', 'en')
    navbar = render_template_string(NAVBAR_TEMPLATE, language=language, request_path=request.path)
    footer = render_template_string(FOOTER_TEMPLATE, language=language)

    if request.method == "POST":
        password = request.form.get("password")
        if password == "admin123":  # In production, use proper authentication
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template_string("""
            {{ navbar | safe }}
            <main class="flex-grow">
                <div class="container p-6">
                    <div class="card p-8 max-w-md mx-auto">
                        <h1 class="text-3xl font-bold mb-6 text-center text-gray-800">{{ 'Admin Login' if language == 'en' else 'Ingia kama Msimamizi' }}</h1>
                        <p class="text-red-500 mb-6 text-base text-center">{{ 'Invalid password' if language == 'en' else 'Nenosiri si Sahihi' }}</p>
                        <form method="POST" class="space-y-6">
                            <div>
                                <label for="password" class="block text-lg font-medium text-gray-700 mb-2">{{ 'Password' if language == 'en' else 'Nenosiri' }}:</label>
                                <input type="password" name="password" id="password" class="form-input" required aria-describedby="password-error">
                            </div>
                            <div class="text-center">
                                <button type="submit" class="form-button">{{ 'Login' if language == 'en' else 'Ingia' }}</button>
                            </div>
                        </form>
                    </div>
                </div>
            </main>
            {{ footer | safe }}
            """, navbar=navbar, footer=footer, language=language)

    return render_template_string("""
    {{ navbar | safe }}
    <main class="flex-grow">
        <div class="container p-6">
            <div class="card p-8 max-w-md mx-auto">
                <h1 class="text-3xl font-bold mb-6 text-center text-gray-800">{{ 'Admin Login' if language == 'en' else 'Ingia kama Msimamizi' }}</h1>
                <form method="POST" class="space-y-6">
                    <div>
                        <label for="password" class="block text-lg font-medium text-gray-700 mb-2">{{ 'Password' if language == 'en' else 'Nenosiri' }}:</label>
                        <input type="password" name="password" id="password" class="form-input" required aria-describedby="password-error">
                    </div>
                    <div class="text-center">
                        <button type="submit" class="form-button">{{ 'Login' if language == 'en' else 'Ingia' }}</button>
                    </div>
                </form>
            </div>
        </div>
    </main>
    {{ footer | safe }}
    """, navbar=navbar, footer=footer, language=language)

@app.route("/admin", methods=["GET"])
def admin_dashboard():
    language = session.get('language', 'en')
    navbar = render_template_string(NAVBAR_TEMPLATE, language=language, request_path=request.path)
    footer = render_template_string(FOOTER_TEMPLATE, language=language)

    if not session.get('admin'):
        return redirect(url_for('admin'))

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
