#Imports
import pandas as pd
import zipfile
import io
from flask import Flask, request, jsonify, Response
from datetime import datetime
import os
from bs4 import BeautifulSoup
import edgar_utils
from edgar_utils import Filing

app = Flask(__name__)

# Global variables
visitors = {}
home_visits = 0
donation_clicks = {'A': 0, 'B': 0}
server_log_dataframe = pd.read_csv("server_log.zip", compression='zip')  
filing_documents_zip = zipfile.ZipFile("docs.zip")  

@app.route('/')
def home():
    global home_visits, donation_clicks
    home_visits += 1
    version = 'A' if home_visits % 2 == 0 else 'B'
    if home_visits > 10:
        version = 'A' if donation_clicks['A'] >= donation_clicks['B'] else 'B'
    color = "blue" if version == "A" else "red"
    with open("index.html") as f:
        html = f.read()
    return html.format(version, color)

@app.route('/browse')
@app.route('/browse.html')
def browse():
    if not os.path.exists("server_log.zip"):
        return Response("<p>Server log file not found.</p>", status=404)
    df = server_log_dataframe.head(500)  
    response_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Browse EDGAR Logs</title>
    </head>
    <body>
        <h1>Browse first 500 rows of rows.csv</h1>
        {df.to_html()}
    </body>
    </html>
    """
    return response_html

@app.route('/browse.json')
def browse_json():
    ip = request.remote_addr
    current_time = datetime.now()

    if ip in visitors:
        last_visit = visitors[ip]
        elapsed_time = (current_time - last_visit).total_seconds()
        if elapsed_time < 60:
            retry_after = 60 - elapsed_time
            return Response("429 TOO MANY REQUESTS", headers={'Retry-After': str(int(retry_after))}, status=429)

    visitors[ip] = current_time

    df = server_log_dataframe.head(500)  
    return jsonify(df.to_dict(orient='records'))

@app.route('/visitors.json')
def visitors_json():
    return jsonify(list(visitors.keys()))

@app.route('/donate.html')
def donate():
    global donation_clicks
    version = request.args.get('from', '')
    if version in donation_clicks:
        donation_clicks[version] += 1

    donate_html = """
    <html>
    <head>
        <title>Donate</title>
    </head>
    <body>
        <h1>Help Support Our Cause</h1>
        <p>Your donations help us continue our work.</p>
    </body>
    </html>
    """
    return donate_html

def question_1():
    with zipfile.ZipFile("server_log.zip") as zf:
        with zf.open("rows.csv") as file:
            df = pd.read_csv(file)
    ip_counts = df['ip'].value_counts().head(10).to_dict()
    return ip_counts

def question_2():
    sic_counts = {}
    for filename in filing_documents_zip.namelist():
        if filename.endswith(('.htm', '.html')):
            try:
                with io.TextIOWrapper(filing_documents_zip.open(filename), encoding="utf-8") as f:
                    html = f.read()
                    soup = BeautifulSoup(html, 'html.parser')
                    sic_tag = soup.find('acronym', text='SIC')
                    
                    if sic_tag and sic_tag.find_next('b'):
                        sic = sic_tag.find_next('b').text.strip()
                        if sic.isdigit():
                            sic_counts[sic] = sic_counts.get(sic, 0) + 1
            except Exception as e:
                print(f"Error processing file {filename}: {e}")

    top_sic_codes = sorted(sic_counts.items(), key=lambda x: (-x[1], x[0]))[:10]
    return dict(top_sic_codes)

@app.route('/analysis.html')
def analysis():
    Q1 = question_1()
    Q2 = question_2()
    with open("analysis.html") as f:
        html = f.read()
    return html.format(Q1, Q2, "Q3 Placeholder")

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, threaded=False)
