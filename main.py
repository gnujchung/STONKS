from flask import Flask, jsonify
from NLP import COMPANIES, calculateResult, sentiments
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

company_list = []

for i in sentiments:
    company_list.append({"name" : COMPANIES.get(i[0]), "ticker" : i[0] , "sentiment" : i[1]})

def updateSentiment():
    results = calculateResult()
    company_list.clear()
    for i in results:
        company_list.append({"name": COMPANIES.get(i[0]), "ticker": i[0], "sentiment": i[1]})

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=updateSentiment, trigger="interval", minutes=60)
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
