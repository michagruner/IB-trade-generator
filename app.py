from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from scipy.optimize import minimize
import numpy as np

app = Flask(__name__)


MAX_RISK = 200
TICK_SIZE = 0.25
TICK_VALUE = 1.25

def calculate_entry(stop, target, Rmultiple):
    def objective(x):
        return x[0]

    def constraint1(x):
        diff = x[0] - stop
        contract_number = (MAX_RISK / (diff / TICK_SIZE * TICK_VALUE))
        oneRScale = diff / TICK_SIZE * TICK_VALUE * 1 / 4 * contract_number
        restScale = (target - x[0]) / TICK_SIZE * TICK_VALUE * 3 / 4 * contract_number 
        return oneRScale + restScale - (Rmultiple * MAX_RISK)

    def constraint2(x):
        return x[0] - stop - 1  # difference between entry and stop should be greater than 1


    bounds = [(stop, target)]
    cons = [{'type': 'eq', 'fun': constraint1}, {'type': 'ineq', 'fun': constraint2}]
    res = minimize(objective, [stop + 1], bounds=bounds, constraints=cons, method='SLSQP')

    return round(res.x[0]*4)/4

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        stop = float(request.form['stop'])
        target = float(request.form['target'])
        Rmultiple = float(request.form['Rmultiple'])
        value = calculate_entry(stop, target, Rmultiple)
        stopSize = value - stop
        contract_number = (MAX_RISK / (stopSize / TICK_SIZE * TICK_VALUE))
        oneRScaleValue = value + stopSize
        oneRScaleContracts = round(1 / 4 * contract_number)
         
        
        if request.form.get('action') == 'submitTrade':
            value = value * 2
            
        return render_template('index.html', value=value)
        
    else:
        return render_template('index.html')

@app.route('/calculate_entry', methods=['POST'])
def calculate_entry_api():
    stop = float(request.json['stop'])
    target = float(request.json['target'])
    Rmultiple = float(request.json['Rmultiple'])
    value = calculate_entry(stop, target, Rmultiple)
    return jsonify({'value': value})


if __name__ == '__main__':
	app.run(debug=True)
