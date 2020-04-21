from flask import Flask, jsonify
from NLP import COMPANIES, calculateResult
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

company_list = []

def test():
    results = calculateResult()
    company_list.clear()
    for i in results:
        company_list.append({'name': COMPANIES.get(i[0]), 'ticker': i[0], 'sentiment': i[1]})

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=test, trigger='interval', minutes=5)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

# @app.route("/")
# def home():
    # return "hello STONKS"

@app.route("/sentiments")
def getSentiment():
    return jsonify(company_list)

if __name__ == "__main__":
    app.run(debug=True)
