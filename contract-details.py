from ib_insync import *
from pprint import pprint

# connect to the IB Gateway or TWS application
ib = IB()
ib.connect()

mes = Future('MES','202306','CME')

mesDetails = ib.reqContractDetails(mes)
print(mesDetails[0].minTick)
print(mesDetails[0].contract.multiplier)
print(mesDetails[0].longName)
#pprint(vars(mesDetails))



ib.sleep(1)

# disconnect from the IB Gateway or TWS application
ib.disconnect()

