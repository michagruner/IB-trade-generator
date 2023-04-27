from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from scipy.optimize import minimize
import numpy as np
import json

app = Flask(__name__)


default_Rmultiple = 2.5
MAX_RISK = 0
TICK_SIZE = 0
TICK_VALUE = 0


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
        with open('config.json') as f:
           config = json.load(f)

        default_Rmultiple = config['Rmultiple']
        MAX_RISK = config['MaxRisk']
        TICK_SIZE = config['TickSize']
        TICK_VALUE = config['TickValue']
        return render_template('index.html' ,default_Rmultiple=default_Rmultiple)

@app.route('/calculate_entry', methods=['POST'])
def calculate_entry_api():
    stop = float(request.json['stop'])
    target = float(request.json['target'])
    Rmultiple = float(request.json['Rmultiple'])
    value = calculate_entry(stop, target, Rmultiple)
    return jsonify({'value': value})

# Endpoint for loading the configuration data
@app.route('/load_config')
def load_config():
    with open('config.json') as f:
        config_data = json.load(f)
    return jsonify(config_data)

# Endpoint for saving the configuration data
@app.route('/save_config', methods=['POST'])
def save_config():
    config_data = request.json
    with open('config.json', 'w') as f:
        json.dump(config_data, f)
    return jsonify({'success': True})

@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        # Get the form data
        new_config = {
            'Rmultiple': float(request.form.get('Rmultiple')),
            'MaxRisk': float(request.form.get('MaxRisk')),
            'TickSize': float(request.form.get('TickSize')),
            'TickValue': float(request.form.get('TickValue'))
        }

        # Save the new config to the file
        with open('config.json', 'w') as f:
            json.dump(new_config, f, indent=4)

        # Redirect back to the index page
        return redirect('/')

    else:
        # Load the current config from the file
        with open('config.json', 'r') as f:
            config = json.load(f)

        # Render the config page template with the current config
        return render_template('config.html', config=config)


if __name__ == '__main__':
	app.run(debug=True)
