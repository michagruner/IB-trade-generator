from ib_insync import *
from pprint import pprint

# connect to the IB Gateway or TWS application
ib = IB()
ib.connect()

for o in ib.openOrders():
    pprint(vars(o))



ib.sleep(1)

# disconnect from the IB Gateway or TWS application
ib.disconnect()

