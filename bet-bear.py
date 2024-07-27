import json
import time
from web3 import Web3

def display_logo():
    logo = """
    
   ___       __  __            _ 
  / _ \     |  \/  |          (_)
 | | | |_  _| \  / | ___   ___ _ 
 | | | \ \/ / |\/| |/ _ \ / _ \ |
 | |_| |>  <| |  | | (_) |  __/ |
  \___//_/\_\_|  |_|\___/ \___|_|
                                 
                                 
    """
    print(logo)

# Display the logo
display_logo()

# Load contract ABI from a JSON file
with open('ContractABI.json', 'r') as abi_file:
    abi_content = json.load(abi_file)
    # Extract the ABI list if the file contains additional metadata
    if isinstance(abi_content, dict) and 'result' in abi_content:
        contract_abi = json.loads(abi_content['result'])
    else:
        contract_abi = abi_content

# Connect to Arbitrum network (replace with your provider)
w3 = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))

# Check if connected to the network
if not w3.is_connected():
    print("Failed to connect to the network")
    exit()

# Contract address (convert to checksum address)
contract_address = Web3.to_checksum_address('0x1cdc19b13729f16c5284a0ace825f83fc9d799f4')

# Initialize contract
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Get user inputs
private_key = input("Enter your private key: ")
public_address = input("Enter your public address: ")
bet_amount = float(input("Enter the amount to bet (in ETH): "))

# Convert bet amount to Wei
bet_amount_wei = w3.to_wei(bet_amount, 'ether')

def bet_bear(epoch):
    nonce = w3.eth.get_transaction_count(public_address)
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_priority_fee = w3.to_wei('2', 'gwei')
    max_fee_per_gas = base_fee + max_priority_fee
    gas_limit = 138860
    txn = contract.functions.betBear(epoch).build_transaction({
        'chainId': 42161,  # Arbitrum mainnet chain ID
        'gas': gas_limit,
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee,
        'nonce': nonce,
        'value': bet_amount_wei
    })
    signed_txn = w3.eth.account.sign_transaction(txn, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return tx_hash

def claim_rewards(epoch):
    nonce = w3.eth.get_transaction_count(public_address)
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_priority_fee = w3.to_wei('2', 'gwei')
    max_fee_per_gas = base_fee + max_priority_fee
    txn = contract.functions.claim([epoch]).build_transaction({
        'chainId': 42161,  # Arbitrum mainnet chain ID
        'gas': 138860,
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee,
        'nonce': nonce
    })
    signed_txn = w3.eth.account.sign_transaction(txn, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return tx_hash

def has_bet(epoch):
    # Check if the user has already placed a bet for the given epoch
    try:
        return contract.functions.ledger(epoch, public_address).call()[1] > 0
    except Exception as e:
        print(f"Error checking if bet is placed for epoch {epoch}: {e}")
        return False

def has_bet_bull(epoch):
    # Check if the user has already placed a betBull for the given epoch
    try:
        bet_info = contract.functions.ledger(epoch, public_address).call()
        return bet_info[1] > 0  # Assuming the second element in bet_info indicates betBull
    except Exception as e:
        print(f"Error checking if betBull is placed for epoch {epoch}: {e}")
        return False

def claim_last_5_epochs(current_epoch):
    # Check and claim rewards for the last 5 epochs
    for epoch_to_check in range(current_epoch - 5, current_epoch):
        if epoch_to_check > 0:
            if contract.functions.claimable(epoch_to_check, public_address).call():
                print(f"Claiming rewards for epoch {epoch_to_check}")
                claim_tx = claim_rewards(epoch_to_check)
                print(f"Claim transaction hash: {claim_tx.hex()}")

# Get the current epoch
current_epoch = contract.functions.currentEpoch().call()

# Claim rewards for the last 5 epochs at the start
claim_last_5_epochs(current_epoch)

previous_epoch = current_epoch
bet_placed_epoch = None

print(f"Starting script. Initial Epoch: {previous_epoch}")

try:
    while True:
        current_epoch = contract.functions.currentEpoch().call()
        
        if current_epoch > previous_epoch:
            print(f"Current Epoch: {current_epoch}")

            # Update the previous epoch
            previous_epoch = current_epoch
            bet_placed_epoch = None  # Reset bet placed epoch for new epoch

        # Check if a bet has already been placed for the current epoch
        if bet_placed_epoch != current_epoch and not has_bet(current_epoch) and not has_bet_bull(current_epoch):
            # Check if the account has enough funds to place the bet
            account_balance = w3.eth.get_balance(public_address)
            base_fee = w3.eth.get_block('latest')['baseFeePerGas']
            max_priority_fee = w3.to_wei('2', 'gwei')
            max_fee_per_gas = base_fee + max_priority_fee
            gas_limit = 138860
            total_cost = bet_amount_wei + (gas_limit * max_fee_per_gas)
            if account_balance < total_cost:
                print(f"Insufficient funds to place bet on epoch {current_epoch}. Needed: {total_cost}, Available: {account_balance}")
                break

            # Place a bet on the current epoch
            print(f"Placing bet on epoch {current_epoch}")
            bet_tx = bet_bear(current_epoch)
            print(f"Bet transaction hash: {bet_tx.hex()}")
            bet_placed_epoch = current_epoch  # Update bet placed epoch

        else:
            print(f"Already placed a bet on epoch {current_epoch}")

        # Check and claim rewards for the last 5 epochs
        claim_last_5_epochs(current_epoch)

        # Wait a short period before checking again
        time.sleep(5)  # Adjust the sleep time as needed for your use case

except KeyboardInterrupt:
    print("\nScript interrupted by user. Exiting gracefully...")
