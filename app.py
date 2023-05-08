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
import pprint
 

class Order:
    def __init__(self, parent_id, parent_lmt=None, parent_action=None, stop_id=None, stop_lmt=None, take_profit_id=None, take_profit_lmt1=None, take_profit_lmt2=None):
        self.parent_id = parent_id
        self.parent_lmt = parent_lmt
        self.parent_action = parent_action
        self.stop_id = stop_id
        self.stop_lmt = stop_lmt
        self.take_profit_id = take_profit_id
        self.take_profit_lmt1 = take_profit_lmt1
        self.take_profit_lmt2 = take_profit_lmt2

    def __str__(self):
        return f"Parent ID: {self.parent_id}, Parent LMT: {self.parent_lmt}, Parent Action: {self.parent_action}, Stop ID: {self.stop_id}, Stop LMT: {self.stop_lmt}, Take Profit ID: {self.take_profit_id}, Take Profit LMT1: {self.take_profit_lmt1}, Take Profit LMT2: {self.take_profit_lmt2}"


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

@app.route('/orders', methods=['GET', 'POST'])
async def orders():
    # connect to the IB Gateway or TWS application
    ib = ib_insync.IB()
    await ib.connectAsync()

    # Create a dictionary to store the orders by parent ID
    orders = {}
    for t in ib.trades():
        #only do this if the orderId is not null
        if t.order.orderId:
            parent_id = t.order.parentId or t.order.orderId
            if parent_id not in orders:
                orders[parent_id] = Order(parent_id)
            order = orders[parent_id]
            #parent order
            if t.order.parentId == 0:
                order.parent_lmt = t.order.lmtPrice
                order.parent_action = t.order.action
            #take profit order
            elif t.order.orderType == 'LMT':
                if t.order.action == 'SELL':
                    take_profit_lmt2 = t.order.lmtPrice + t.order.scalePriceIncrement
                else:
                    take_profit_lmt2 = t.order.lmtPrice - t.order.scalePriceIncrement
                order.take_profit_id = t.order.orderId
                order.take_profit_lmt1 = t.order.lmtPrice
                order.take_profit_lmt2 = take_profit_lmt2
            #stop order
            elif t.order.orderType == 'STP':
                order.stop_id = t.order.orderId
                order.stop_lmt = t.order.auxPrice

    # Print the orders
    pp = pprint.PrettyPrinter(indent=4)
    for order in orders.values():
        #print(f"Parent ID: {parent_id}")
        pp.pprint(vars(order))

    # Disconnect from the IB Gateway or TWS application
    ib.disconnect()

    # Render the orders template
    return await render_template('orders.html', orders_by_parent_id=orders)

@app.route('/update_order/<int:parent_id>', methods=['POST'])
async def update_order(parent_id):

    # Create a dictionary to store the orders by parent ID
    orders_by_id = {}
    contracts_by_id = {}
    form = await request.form
    # connect to the IB Gateway or TWS application
    ib = ib_insync.IB()
    await ib.connectAsync()
    for trade in ib.trades():
        orders_by_id[trade.order.orderId]=trade.order
        contracts_by_id[trade.order.orderId]=trade.contract

    #original order
    order = orders_by_id[parent_id]
    contract = contracts_by_id[parent_id]
    order.lmtPrice = float(form['parent_lmt'])
    ib.placeOrder(contract, order)
    
    #take profit order
    takeProfitID = float(form['take_profit_id'])
    order = orders_by_id[takeProfitID]
    contract = contracts_by_id[takeProfitID]
    order.lmtPrice = float(form['take_profit_limit_1'])
    scaleInc = (abs(float(form['take_profit_limit_2'])-float(form['take_profit_limit_1'])))
    order.scalePriceIncrement = scaleInc
    ib.placeOrder(contract, order)

    stopID = float(form['stop_id'])
    order = orders_by_id[stopID]
    contract = contracts_by_id[stopID]
    order.auxPrice = float(form['stop_limit']) 
    ib.placeOrder(contract, order)

    ib.disconnect()
    #order.parentLMT = float(request.form['parent_lmt'])
    #order.takeProfitId = int(request.form['take_profit_id'])
    #order.takeProfitLimit1 = float(request.form['take_profit_limit_1'])
    #order.takeProfitLimit2 = float(request.form['take_profit_limit_2'])
    #order.stopID = int(request.form['stop_id'])
    #order.stopLimit = float(request.form['stop_limit'])
    return redirect('/')


if __name__ == '__main__':
	app.run(debug=True)
