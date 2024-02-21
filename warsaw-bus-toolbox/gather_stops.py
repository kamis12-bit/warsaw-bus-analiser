import requests
import pandas as pd
import time
import sys
from api_key import api_key

output_file = sys.argv[1]

stops_url = (
    "https://api.um.warszawa.pl/api/action/dbstore_get/?id=ab75c33d-3a26-4342-b36a-6e5fef0a3ac3&apikey="
    + api_key
)


def get_stop_lines_url(busstopId, busstopNr):
    return (
        "https://api.um.warszawa.pl/api/action/dbtimetable_get?id=88cd555f-6f31-43ca-9de4-66c479ad5942&busstopId="
        + busstopId
        + "&busstopNr="
        + busstopNr
        + "&apikey="
        + api_key
    )


def get_stop_times_url(busstopId, busstopNr, line):
    return (
        "https://api.um.warszawa.pl/api/action/dbtimetable_get?id=e923fa0e-d96c-43f9-ae6e-60518c9f3238&busstopId="
        + busstopId
        + "&busstopNr="
        + busstopNr
        + "&line="
        + line
        + "&apikey="
        + api_key
    )


def try_get_json(url):
    while True:
        try:
            r = requests.get(url)
            break
        except Exception:
            print("caught - trying again")
            time.sleep(3)
    return r.json()["result"]


def get_times():
    stops = try_get_json(stops_url)
    print("there are " + str(len(stops)) + " stops in Warsaw")
    i = 0
    header = True
    for stop in stops:
        busstopId = stop["values"][0]["value"]  # 'zespol'
        busstopNr = stop["values"][1]["value"]  # 'slupek'
        stop_lat = stop["values"][4]["value"]  # latitude
        stop_lon = stop["values"][5]["value"]  # longitude
        lines = try_get_json(get_stop_lines_url(busstopId, busstopNr))

        print("there are " + str(len(lines)) + " lines")
        for line in lines:
            # marking progress
            i += 1
            print(i)

            lineNr = line["values"][0]["value"]  # 'linia'
            times_json = try_get_json(get_stop_times_url(busstopId, busstopNr, lineNr))

            brigades = {record["values"][2]["value"] for record in times_json}
            times = {record["values"][5]["value"] for record in times_json}
            df = pd.DataFrame(list(zip(brigades, times)), columns=["Brigade", "Times"])
            df["Lats"] = stop_lat
            df["Lons"] = stop_lon
            df["Lines"] = lineNr
            mode = "w" if header else "a"
            df.to_csv(
                output_file, encoding="utf-8", index=False, mode=mode, header=header
            )
            header = False


if __name__ == "__main__":
    get_times()
