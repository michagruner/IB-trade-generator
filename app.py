from quart import Quart
from quart import render_template
from quart import request
from quart import jsonify
from quart import redirect
from quart import session
from quart import url_for

from scipy.optimize import minimize
import asyncio
import numpy as np
import json
import ib_insync
import asyncio
from pprint import pprint
 

app = Quart(__name__)
app.secret_key = 'my_trade_app'


async def check_TWS():
   try: 
       ib = ib_insync.IB()
       await ib.connectAsync()
       ib.disconnect()
       session['Online'] = True
   except:
       session['Online'] = False
   return

    
#create and place the bracket order to trade the contract
async def Future_bracket_order(action, quantity, entryPrice, stopLossPrice, takeProfitPrice1, takeProfitQuantity1, takeProfitPrice2, takeProfitQuantity2):
    # connect to the IB Gateway or TWS application
    ib = ib_insync.IB()
    await ib.connectAsync()

    contract = ib_insync.Future(session['Symbol'],session['Expiry'],'CME')
    #pprint(vars(contract))

    assert action in ('BUY', 'SELL')
    reverseAction = 'BUY' if action == 'SELL' else 'SELL'

    parent = ib_insync.LimitOrder(
        action, quantity, entryPrice,
        orderId=ib.client.getReqId(),
        transmit=False)

    takeProfit = ib_insync.LimitOrder(
        reverseAction, quantity, takeProfitPrice1,
        orderId=ib.client.getReqId(),
        transmit=False,
        scaleInitLevelSize = takeProfitQuantity1,
        scaleSubsLevelSize = takeProfitQuantity2,
        scalePriceIncrement = (abs(float(takeProfitPrice2)-float(takeProfitPrice1))),
        parentId=parent.orderId)

    stopLoss = ib_insync.StopOrder(
        reverseAction, quantity, stopLossPrice,
        orderId=ib.client.getReqId(),
        transmit=True,
        parentId=parent.orderId)

    # place the bracket order
    ib.placeOrder(contract, parent)
    ib.placeOrder(contract, takeProfit)
    ib.placeOrder(contract, stopLoss)

    # disconnect from the IB Gateway or TWS application
    ib.disconnect()

#optimize for the long-entry given a stop, target, multiple and risk
def optimize_long(stop, target, Rmultiple, MAX_RISK, TICK_SIZE, TICK_VALUE):

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
    #calculate all the data based on the entry
    entry = round(res.x[0]*4)/4
    return entry

#optimize for the short entry given a stop, target, multiple and risk
def optimize_short(stop, target, Rmultiple, MAX_RISK, TICK_SIZE, TICK_VALUE):

    def objective(x):
        return x[0]

    def constraint1(x):
        diff = stop - x[0] 
        contract_number = (MAX_RISK / (diff / TICK_SIZE * TICK_VALUE))
        oneRScale = diff / TICK_SIZE * TICK_VALUE * 1 / 4 * contract_number
        restScale = (x[0] - target) / TICK_SIZE * TICK_VALUE * 3 / 4 * contract_number 
        return oneRScale + restScale - (Rmultiple * MAX_RISK)

    def constraint2(x):
        return stop - x[0] - 1  # difference between entry and stop should be greater than 1


    bounds = [(target, stop)]
    cons = [{'type': 'eq', 'fun': constraint1}, {'type': 'ineq', 'fun': constraint2}]
    res = minimize(objective, [stop - 1], bounds=bounds, constraints=cons, method='SLSQP')
    #calculate all the data based on the entry
    entry = round(res.x[0]*4)/4
    return entry



#calculate the data for the long entry
def calculate_entry_long(stop, target, Rmultiple):

    MAX_RISK = int(session['MaxRisk'])
    TICK_SIZE = float(session['TickSize'])
    TICK_VALUE = float(session['TickValue'])

    entry = round(optimize_long(stop, target, Rmultiple, MAX_RISK, TICK_SIZE, TICK_VALUE)*4)/4
    diff = entry - stop
    entryCont = round((MAX_RISK / (diff / TICK_SIZE * TICK_VALUE)))
    oneRScale = entry + diff 
    oneRScaleCont = round(1/4*((MAX_RISK / (diff / TICK_SIZE * TICK_VALUE))))
    highProbCont = entryCont - oneRScaleCont
    return entry, entryCont , oneRScale, oneRScaleCont, highProbCont


#calculate the data for the short entry
def calculate_entry_short(stop, target, Rmultiple):

    MAX_RISK = int(session['MaxRisk'])
    TICK_SIZE = float(session['TickSize'])
    TICK_VALUE = float(session['TickValue'])

    entry = round(optimize_short(stop, target, Rmultiple, MAX_RISK, TICK_SIZE, TICK_VALUE)*4)/4
    diff = stop - entry
    entryCont = round((MAX_RISK / (diff / TICK_SIZE * TICK_VALUE)))
    oneRScale = entry - diff 
    oneRScaleCont = round(1/4*((MAX_RISK / (diff / TICK_SIZE * TICK_VALUE))))
    highProbCont = entryCont - oneRScaleCont
    return entry, entryCont , oneRScale, oneRScaleCont, highProbCont


@app.route('/', methods=['GET', 'POST'])
async def index():
    if request.method == 'POST':
        
        return await render_template('index.html', entry=entry)
        
    else:
        if 'MaxRisk' not in session:
            await check_TWS()
            if session['Online']:
                return redirect(url_for('config_online'))
            else:
                return redirect(url_for('config_offline'))

        default_Rmultiple = session['Rmultiple']
        MAX_RISK = session['MaxRisk']
        ContName = session['ContName']
        Expiry = session['Expiry']
        TickValue = session['TickValue']

        return await render_template('index.html' ,default_Rmultiple=default_Rmultiple, maxRisk=MAX_RISK, ContName=ContName, Expiry=Expiry, TickValue=TickValue)

@app.route('/submitTrade', methods=['GET'])
async def submitTrade():
    
    args = request.args
    transactionType = args.get("transaction-type")
    entryCont = args.get("entryCont")
    entry = args.get("entry")
    stop = args.get("stop")
    oneRScale = args.get("oneRScale")
    oneRScaleCont = args.get("oneRScaleCont")
    target = args.get("target")
    highProbCont = args.get("highProbCont")


    await check_TWS()
    if session['Online']:
        print('Submitting trade')
        await Future_bracket_order( transactionType , entryCont, entry, stop, oneRScale, oneRScaleCont, target, highProbCont)
    else:
        print('not connected to TWS')
    return redirect('/')


#endpoint for taking in the values for stop target and risk multiples and returning all the trade data
@app.route('/calculate_entry', methods=['POST'])
async def calculate_entry_api():
    try:
        stop = float((await request.json)['stop'])
        target = float((await request.json)['target'])
        Rmultiple = float((await request.json)['Rmultiple'])
        transactionType = str((await request.json)['transactionType'])
        if transactionType == 'BUY':
           entry, entryCont, oneRScale, oneRScaleCont, highProbCont = calculate_entry_long(stop, target, Rmultiple)
        else:
           entry, entryCont, oneRScale, oneRScaleCont, highProbCont = calculate_entry_short(stop, target, Rmultiple)
        return jsonify({'entry': entry, 'entryCont': entryCont, 'oneRScale': oneRScale, 'oneRScaleCont': oneRScaleCont, 'highProbCont': highProbCont })
    except:
       print("no resonable values for stop, target, multiple or transaction type provided")

    return jsonify({'entry': 0, 'entryCont': 0, 'oneRScale': 0, 'oneRScaleCont': 0, 'highProbCont': 0 })

# Endpoint for setting the configuration data (online-version with connection to TWS)
@app.route('/config_online', methods=['GET', 'POST'])
async def config_online():
    if request.method == 'POST':
        # Get the form data
        form = await request.form
        if form['save_button'] == 'save':
            try:
               ib = ib_insync.IB()
               await ib.connectAsync()

               contract = ib_insync.Future(str(form['Contract']), str(form['expiryMonth']), 'CME')
               mesDetails = await ib.reqContractDetailsAsync(contract)
               tickSize=float(mesDetails[0].minTick)
               multiplier=float(mesDetails[0].contract.multiplier)
               symbol=str(form['Contract'])
               expiry=str(mesDetails[0].contract.lastTradeDateOrContractMonth)
               name=str(mesDetails[0].longName)
               ib.disconnect()

               session['Rmultiple'] = float(form['Rmultiple'])
               session['MaxRisk'] = float(form['MaxRisk'])
               session['TickSize'] = tickSize
               session['TickValue'] = tickSize * multiplier
               session['ContName'] = name
               session['Expiry'] = expiry
               session['Symbol'] = symbol
               session['Online'] = True
            except:
               return redirect('/config')
            print("Session variables filled")
        return redirect('/')

    else:
        #first call of the config page
        if 'MaxRisk' not in session:
           print("Session variables not filled")
           config = {
               'Rmultiple': '2.5',
               'MaxRisk': '200',
               'TickSize': '0.25',
               'TickValue': '1.25'
           }
        #config already set, so render the existing values
        else:
           config = {
               'Rmultiple': session['Rmultiple'],
               'MaxRisk': session['MaxRisk'],
               'TickSize': session['TickSize'],
               'TickValue': session['TickValue']
           }
        # Render the config page template with the current config
        return await render_template('config_online.html', config=config)


# Endpoint for setting the configuration data (online-version with connection to TWS)
@app.route('/config_offline', methods=['GET', 'POST'])
async def config_offline():
    if request.method == 'POST':
        # Get the form data
        form = await request.form
        if form['save_button'] == 'save':

            session['Rmultiple'] = float(form['Rmultiple'])
            session['MaxRisk'] = float(form['MaxRisk'])
            session['TickSize'] = float(form['TickSize'])
            session['TickValue'] = float(form['TickValue'])
            session['ContName'] = str(form['Contract'])
            session['Online'] = False
            print("Session variables filled")
        return redirect('/')

    else:
        #first call of the config page
        if 'MaxRisk' not in session:
           print("Session variables not filled")
           config = {
               'Rmultiple': '2.5',
               'MaxRisk': '200',
               'TickSize': '0.25',
               'TickValue': '1.25'
           }
        #config already set, so render the existing values
        else:
           config = {
               'Rmultiple': session['Rmultiple'],
               'MaxRisk': session['MaxRisk'],
               'TickSize': session['TickSize'],
               'TickValue': session['TickValue']
           }
        # Render the config page template with the current config
        return await render_template('config_offline.html', config=config)

@app.route('/config', methods=['GET', 'POST'])
async def config():
    await check_TWS()
    if session['Online']:
        return redirect('/config_online')
    else:
        return redirect('/config_offline')
    return redirect('/')


if __name__ == '__main__':
	app.run(debug=True)
