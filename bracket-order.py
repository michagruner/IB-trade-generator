from ib_insync import *

# connect to the IB Gateway or TWS application
ib = IB()
ib.connect()

# define the contract you want to trade
contract = Future('MES', '202306', 'CME')

# define the order quantities and prices
quantity = 5
entryPrice = 4190
stopLossPrice = 4199
takeProfitPrice1 = 4189.75
takeProfitQuantity1 = 2
takeProfitPrice2 = 4188
takeProfitQuantity2 = 3

action = 'SELL'
assert action in ('BUY', 'SELL')
reverseAction = 'BUY' if action == 'SELL' else 'SELL'

parent = LimitOrder(
    action, quantity, entryPrice,
    orderId=ib.client.getReqId(),
    transmit=False)

takeProfit = LimitOrder(
    reverseAction, quantity, takeProfitPrice1,
    orderId=ib.client.getReqId(),
    transmit=False,
    scaleInitLevelSize = takeProfitQuantity1,
    scaleSubsLevelSize = takeProfitQuantity2,
    scalePriceIncrement = (abs(takeProfitPrice2-takeProfitPrice1)),
    parentId=parent.orderId)

stopLoss = StopOrder(
    reverseAction, quantity, stopLossPrice,
    orderId=ib.client.getReqId(),
    transmit=True,
    parentId=parent.orderId)

# place the bracket order
ib.placeOrder(contract, parent)
ib.placeOrder(contract, takeProfit)
ib.placeOrder(contract, stopLoss)

ib.sleep(1)

# disconnect from the IB Gateway or TWS application
ib.disconnect()

