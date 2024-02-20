# from pandas.io.xml import file_exists
import requests
import pandas as pd
import time
import sys
from api_key import api_key


bus_url = (
    """https://api.um.warszawa.pl/api/action/busestrams_get/?resource_id=f2e5503e-927d-4ad3-9500-4ab9e55deb59&apikey="""
    + api_key
    + "&type=1"
)


def get_bus_frame():
    r = requests.get(bus_url)
    return pd.DataFrame.from_dict(r.json()["result"])


def filter_bus_frame(df):
    now = pd.Timestamp.now()
    df = df[(now - pd.to_datetime(df["Time"])) / pd.Timedelta(minutes=1) < 5]
    return df


def download_new(file_name, first=False):
    # Trying in a loop, since sometimes causes error
    while True:
        try:
            df = filter_bus_frame(get_bus_frame())
            # df.to_csv(file_name, encoding="utf-8", index=False, mode="a", header=False)
            break
        except Exception:
            print("caught - trying again")
            time.sleep(3)
            continue
    if first:
        df.to_csv(file_name, encoding="utf-8", index=False)
    else:
        df.to_csv(file_name, encoding="utf-8", index=False, mode="a", header=False)


def gather_hour(file_name):
    download_new(file_name, first=True)
    for i in range(59):
        time.sleep(60)
        download_new(bus_url, file_name)
        print("written " + str(i + 1))


def gather_night(file_name):
    download_new(file_name, first=True)
    print("written 0")
    for i in range(239):
        time.sleep(60)
        download_new(file_name)
        print("written " + str(i + 1))


if __name__ == "__main__":
    gather_hour(sys.argv[1])

    # print("Going to sleep for two hours.")
    # time.sleep(120 * 60)
    # print("Now gathering data for four hours.")
    # gather_night(sys.argv[1])
    # print("Finished.")
