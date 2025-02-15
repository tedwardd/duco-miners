import subprocess
import requests
from requests.exceptions import HTTPError
import json
import sys
import time
from tabulate import tabulate
from operator import itemgetter

def format_hashrate(hr):
    unit = ''
    if hr < 1000:
        unit = 'H'
    elif hr < 1000000:
        hr /= 1000
        unit = 'kH'
    else:
        hr /= 1000000
        unit = 'mH'
    return '{:.2f} {}/s'.format(hr, unit)

def main():
    subprocess.call("clear")

    username = None
    while not username:
        username = input('Enter your DUCO username: ')

    print("Fetching miners list…")

    prev_balance = 0

    last_update = None

    while True:
        try:
            miners_response = requests.get("https://server.duinocoin.com/miners.json")
            miners_response.raise_for_status()
            miners_json_data = json.loads(miners_response.text)

            balances_response = requests.get("https://server.duinocoin.com/balances.json")
            balances_response.raise_for_status()
            balances_json_data = json.loads(balances_response.text)

            api_response = requests.get("https://server.duinocoin.com/api.json")
            api_response.raise_for_status()
            api_json_data = json.loads(api_response.text)

        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            time.sleep(10)
            continue
        except Exception as err:
            print(f'Other error occurred: {err}')
            time.sleep(10)
            continue
        except KeyboardInterrupt:
            print('Exiting…')
            sys.exit()
        
        if miners_json_data and balances_json_data and api_json_data:
            subprocess.call("clear")

            duco_price_usd = api_json_data.get('Duco price', 0)

            user_miners = [v for v in miners_json_data.values() if v["User"] == username]

            if not user_miners:
                print("No miners found.")

            miners = []
            total_hash = 0
            totalSharerate = 0
            totalAccepted = 0
            for v in user_miners:
                if v["User"] == username:
                    hashrate = int(v.get("Hashrate", 0))
                    total_hash += hashrate

                    accepted = int(v.get("Accepted", 0))
                    rejected = int(v.get("Rejected", 0))
                    sharerate = int(v.get("Sharerate", 0)) 
                    
                    if sharerate < (accepted + rejected):
                            sharerate = accepted + rejected

                    totalSharerate += sharerate
                    totalAccepted += accepted

                    
                    successRate = f'{accepted}/{sharerate}'
                    
                    algo = v["Algorithm"]
                    diff = int(v.get("Diff", 0))
                    id = v["Identifier"]
                    software = v["Software"]

                    miners.append([id, software, algo, successRate, format_hashrate(hashrate), diff])
            
            miners.sort(key=itemgetter(0))

            user_balance_str = balances_json_data.get(username, "0 DUCO").replace(' DUCO', ' ᕲ')
            user_balance = float(user_balance_str.replace(' ᕲ', ''))

            balance_difference = user_balance - prev_balance
            time_difference = time.time() - last_update if last_update else 0
            daily_average = balance_difference*float((60/time_difference)*60*24) if time_difference != 0 else 0

            total_success_pc = int((totalAccepted/totalSharerate)*100) if totalSharerate > 0 else 0
            total_success = f'{total_success_pc}% ({totalAccepted}/{totalSharerate})'
            print(tabulate([[user_balance_str, len(miners), format_hashrate(total_hash), f'{total_success}', f'{daily_average} ᕲ']], headers=["Balance", "Total miners", "Total hashrate", "Total success", "Daily profit"]))
            
            if miners:
                print(tabulate(miners, headers=["ID", "Software", "Algo", "Success", "Hashrate", "Diff"], tablefmt='fancy_grid'))
            
            prev_balance = user_balance
            last_update = time.time()

            time.sleep(15)

if __name__ == "__main__":
    main()