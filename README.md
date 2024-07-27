# allora-pancake-bot
![GTZv4vzX0AAWbc0](https://github.com/user-attachments/assets/c9523153-78a9-4607-9b3d-8d7f93c9756e)

* Connect your EVM metamask wallet [here](https://app.allora.network/points/campaign/pancakeswap-predictions?ref=eyJyZWZlcnJlcl9pZCI6IjliM2ZlN2JjLWE1YTYtNGZjOC1iNWM3LWU2NTY1ODcyZTE2MSJ9)
* The more we bet on [pancake](https://pancakeswap.finance/prediction?token=ETH&chain=arb) the more we get Allora points

## Install Dependecies
```console
sudo apt-get update
sudo apt install git screen python3 python3-pip pip3

pip3 install web3
```
```console
git clone https://github.com/0xmoei/allora-pancake-bot
cd allora-pancake-bot
```

## Run Bot
* We can run 1 or 2 wallets with betting x amount of ETH per epoch
* 2 Wallets with opposite bets decrease the risk
### Wallet 1
```console
screen -S bull

python3 bet-bull.py
```
Ctrl+A+D


### Wallet 2
```console
screen -S bear

python3 bet-bear.py
```
Ctrl+A+D

## Help this guide
Don't forget to add pull request to correct the repository issues or add your ideas
