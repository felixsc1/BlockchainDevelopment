from solcx import compile_standard
import json
from web3 import Web3
import os

from dotenv import load_dotenv  # allows loading environment variables in .env file
load_dotenv()

with open("./test.sol", "r") as file:
    test_file = file.read()
    # print(test_file)


"""
Compiling Solidity code
For details: https://solcx.readthedocs.io/en/latest/index.html
the low level compiler settings: https://docs.soliditylang.org/en/latest/using-the-compiler.html#commandline-compiler
"""

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"test.sol": {"content": test_file}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.7.0",
)
# print(compiled_sol)  #print ABI and bytecode, equivalent of what we get from remix

with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)

# get bytecode for deployment
# ['contract']['test.sol']..etc. --> see compiled_code.json, we're walking down the tree of objects there
bytecode = compiled_sol["contracts"]["test.sol"]["SimpleStorage"]["evm"]["bytecode"][
    "object"
]
# get abi
abi = compiled_sol["contracts"]["test.sol"]["SimpleStorage"]["abi"]

# connect to rinkeby
w3 = Web3(Web3.HTTPProvider("https://rinkeby.infura.io/v3/4685edb7f6004c03a6a17893e9e605aa"))
chain_id = 4
my_address = "0xfDd914771a2BdF809FFEbc0E436c5b79BeDF059b"
private_key = os.getenv("PRIVATE_KEY")  # note: may have to manually at 0x in front
# print(private_key)

simplestorage = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.getTransactionCount(
    my_address
)  # an increasing number do ID each transaction
# print(nonce)

# 1. build transaction
transaction = simplestorage.constructor().buildTransaction(
    {"chainId": chain_id, "from": my_address, "nonce": nonce}
)
# print(transaction)

# 2. sign transaction
# so far, everyone could send this transaction, only becomes valid when signed with my private key
signed_tx = w3.eth.account.sign_transaction(transaction, private_key=private_key)

# 3. send transaction
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
# print(tx_receipt)

# working with an already contract, provide address (instead of bytecode) and abi
simple_storage = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

# Two ways to interact with a function in solidity:
# Call -> Just simulates a function interaction, does not make a state change (blue buttons in remix) only retrieves return value
# Transact -> Actually make a change (orange buttons in remix)
# store and receive are functions we defined in the test.sol file
# print(simple_storage.functions.store(15).call())
# print(simple_storage.functions.retrieve().call())  # 0 (default)
# still zero, because store(15) before was just a call
# retrieve is a function in our test.sol contract, should print default value (0) if it works

# Now do actual transaction
# again the 3 steps of creating, signing, sending
store_transaction = simple_storage.functions.store(15).buildTransaction(
    {"chainId": chain_id, "from": my_address, "nonce": nonce + 1}
    # nonce can only be used once, must be different than the one used to deploy contract
)
signed_store_transaction = w3.eth.account.sign_transaction(
    store_transaction, private_key=private_key
)
send_store_hash = w3.eth.send_raw_transaction(signed_store_transaction.rawTransaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(send_store_hash)
# print(simple_storage.functions.retrieve().call())  # now shows 15
