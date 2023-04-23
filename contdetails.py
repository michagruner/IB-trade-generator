import ib_insync

# Connect to the IB API
ib = ib_insync.IB()
ib.connect()

# Define the contract for the E-mini future on S&P 500 for June 2023
contract = ib_insync.Future('ES', '202306', 'CME')

# Retrieve the contract details
details = ib.reqContractDetails(contract)

# Print the contract details
for d in details:
    print(d.contract)

