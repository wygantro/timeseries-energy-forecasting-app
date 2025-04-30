# get_consumer_data.py

import requests
import time
import pandas as pd

def fetch_data():
    url = "https://energy-consumption-api-wpyj5eetua-uc.a.run.app/api/v1/energy-consumption"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        #print("Failed to fetch data: Status code", response.status_code)
        return None

def run_every_minute():
    # {'dewpoint_value': 6.646, 'electric_demand': 149.587, 'humidity_value': 74.3305, 'temp_value': 11.7967, 'time_stamp': 'Sun, 13 May 0001 22:46:45 GMT'}
    # create an empty DataFrame with specified columns
    columns = ['time_stamp', 'electric_demand', 'temp_value', 'humidity_value', 'dewpoint_value']
    df = pd.DataFrame(columns=columns)
    while True:
        data = fetch_data()
        if data:
            print("Fetched data:", data)
            new_row = {'time_stamp': data['time_stamp'], 'electric_demand': data['electric_demand'], 'temp_value': data['temp_value'], 'humidity_value': data['humidity_value'], 'dewpoint_value': data['dewpoint_value']}
            df = df._append(new_row, ignore_index=True)
            # Save DataFrame to CSV
            df.to_csv('dataframe.csv', index=False)
            print("Fetched data appended to dataframe")
        time.sleep(60)

if __name__ == "__main__":
    run_every_minute()
