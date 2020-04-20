from flask import Flask
from NLP import RESULTS, COMPANIES
from flask import jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "hello STONKS"

@app.route("/test")
def test():
    company_list = []
    for i in RESULTS:
        company_list.append([COMPANIES.get(i[0]), i[0], i[1]]) 
    return jsonify(company_list)


if __name__ == "__main__":
    app.run(debug=True)
