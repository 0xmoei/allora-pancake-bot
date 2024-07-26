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

# Track win/loss summary
won_epochs = 0
lost_epochs = 0

def bet_bear(epoch):
    nonce = w3.eth.get_transaction_count(public_address)
    gas_price = w3.to_wei('0.01', 'gwei')
    gas_limit = 138860
    txn = contract.functions.betBear(epoch).build_transaction({
        'chainId': 42161,  # Arbitrum mainnet chain ID
        'gas': gas_limit,
        'gasPrice': gas_price,
        'nonce': nonce,
        'value': bet_amount_wei
    })
    signed_txn = w3.eth.account.sign_transaction(txn, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return tx_hash

def claim_rewards(epoch):
    nonce = w3.eth.get_transaction_count(public_address)
    txn = contract.functions.claim([epoch]).build_transaction({
        'chainId': 42161,  # Arbitrum mainnet chain ID
        'gas': 138860,
        'gasPrice': w3.to_wei('0.01', 'gwei'),
        'nonce': nonce
    })
    signed_txn = w3.eth.account.sign_transaction(txn, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return tx_hash

def check_win_loss(epoch):
    global won_epochs, lost_epochs
    try:
        if contract.functions.claimable(epoch, public_address).call():
            won_epochs += 1
            print(f"Epoch {epoch} is claimable. You won!")
        else:
            lost_epochs += 1
            print(f"Epoch {epoch} is not claimable. You lost.")
    except Exception as e:
        print(f"Error checking win/loss for epoch {epoch}: {e}")

def has_bet(epoch):
    # Check if the user has already placed a bet for the given epoch
    try:
        return contract.functions.ledger(epoch, public_address).call()[0] > 0
    except Exception as e:
        print(f"Error checking if bet is placed for epoch {epoch}: {e}")
        return False

def has_bet_bull(epoch):
    # Check if the user has already placed a betBull for the given epoch
    try:
        bet_info = contract.functions.ledger(epoch, public_address).call()
        return bet_info[0] > 0  # Assuming the first element in bet_info indicates betBull
    except Exception as e:
        print(f"Error checking if betBull is placed for epoch {epoch}: {e}")
        return False

def claim_last_20_epochs(current_epoch):
    # Check and claim rewards for the last 20 epochs without counting them in win/loss summary
    for epoch_to_check in range(current_epoch - 20, current_epoch):
        if epoch_to_check > 0:
            if contract.functions.claimable(epoch_to_check, public_address).call():
                print(f"Claiming rewards for epoch {epoch_to_check}")
                claim_tx = claim_rewards(epoch_to_check)
                print(f"Claim transaction hash: {claim_tx.hex()}")

# Get the current epoch
current_epoch = contract.functions.currentEpoch().call()

# Claim rewards for the last 20 epochs at the start
claim_last_20_epochs(current_epoch)

previous_epoch = current_epoch

print(f"Starting script. Initial Epoch: {previous_epoch}")

try:
    while True:
        current_epoch = contract.functions.currentEpoch().call()
        
        if current_epoch > previous_epoch:
            print(f"Current Epoch: {current_epoch}")

            # Update the previous epoch
            previous_epoch = current_epoch

        # Check if a bet has already been placed for the current epoch
        if not has_bet(current_epoch) and not has_bet_bull(current_epoch):
            # Check if the account has enough funds to place the bet
            account_balance = w3.eth.get_balance(public_address)
            gas_price = w3.to_wei('0.01', 'gwei')
            gas_limit = 138860
            total_cost = bet_amount_wei + (gas_limit * gas_price)
            if account_balance < total_cost:
                print(f"Insufficient funds to place bet on epoch {current_epoch}. Needed: {total_cost}, Available: {account_balance}")
                break

            # Place a bet on the current epoch
            print(f"Placing bet on epoch {current_epoch}")
            bet_tx = bet_bear(current_epoch)
            print(f"Bet transaction hash: {bet_tx.hex()}")

            # Check and claim rewards for the second epoch behind after a successful bet
            second_epoch_behind = current_epoch - 2
            if second_epoch_behind > 0:
                try:
                    if contract.functions.claimable(second_epoch_behind, public_address).call():
                        print(f"Claiming rewards for epoch {second_epoch_behind}")
                        claim_tx = claim_rewards(second_epoch_behind)
                        print(f"Claim transaction hash: {claim_tx.hex()}")
                    check_win_loss(second_epoch_behind)
                except ValueError as e:
                    if 'nonce too low' in str(e):
                        print(f"Nonce too low error for epoch {second_epoch_behind}. Retrying...")
                        time.sleep(5)
                        continue
                    else:
                        raise e
        else:
            print(f"Already placed a bet on epoch {current_epoch}")

        # Print win/loss summary
        print(f"Summary: Won Epochs: {won_epochs}, Lost Epochs: {lost_epochs}")

        # Wait a short period before checking again
        time.sleep(5)  # Adjust the sleep time as needed for your use case

except KeyboardInterrupt:
    print("\nScript interrupted by user. Exiting gracefully...")
    print(f"Final Summary: Won Epochs: {won_epochs}, Lost Epochs: {lost_epochs}")
