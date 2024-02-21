from numpy import NaN
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import sys


RE = 6378.137  # radius of Earth
rl = RE * math.cos(
    52.22977 * math.pi / 180
)  # radius of the latitude line circle passing through Warsaw

# dataset_name = sys.argv[1]

# boundaries
high_speed = 50  # km/h
unreasonable_speed = 80  # km/h
close_distance = 1500  # meters
lots_of_busses = 40
near_stop = 100  # meters


def lat_to_dist(l1, l2):
    dl = (l2 - l1) * math.pi / 180
    return dl * RE * 1000


def lon_to_dist(l1, l2):
    dl = (l2 - l1) * math.pi / 180
    return dl * rl * 1000


def print_warsaw_coord_distances():
    print("52.2 to 52.3 is " + str(int(lat_to_dist(52.2, 52.3))) + " meters")
    print("21.0 to 21.1 is " + str(int(lon_to_dist(21.0, 21.1))) + " meters")


def distance(d1, d2):
    return np.sqrt(d1 * d1 + d2 * d2)


def coord_dist(lat1, lon1, lat2, lon2):
    return distance(lat_to_dist(lat1, lat2), lon_to_dist(lon1, lon2))


def load_and_preprocess(dataset_name):
    # loading and sorting data
    df = pd.read_csv(dataset_name)
    df = df.sort_values(by=["VehicleNumber", "Time"])

    # calculating time from beginning of frame
    min_time = pd.to_datetime(df["Time"].min())
    df["RelTime"] = (pd.to_datetime(df["Time"]) - min_time).astype(
        "timedelta64[s]"
    ).astype(int) / 60

    # calculating speed
    df["time_delta"] = pd.to_datetime(df["Time"]) - pd.to_datetime(df["Time"]).shift()
    df["lat_dist"] = lat_to_dist(
        df["Lat"].astype(float), df["Lat"].shift().astype(float)
    )
    df["lon_dist"] = lon_to_dist(
        df["Lon"].astype(float), df["Lon"].shift().astype(float)
    )
    df["space_delta"] = distance(df["lat_dist"], df["lon_dist"])

    df["speed"] = (
        (60 / 1000) * df["space_delta"] / (df["time_delta"] / pd.offsets.Minute(1))
    )

    # filtering for the data that makes sense
    df = df[
        (df["time_delta"] != NaN)
        & (df["time_delta"] >= pd.Timedelta(0))
        & (df["speed"] < unreasonable_speed)
        & (df["Lat"] < 52.6)
    ]
    # dropping now-useless data
    df = df.drop(columns=["lat_dist", "lon_dist"])
    df = df.drop(columns=["time_delta", "space_delta"])
    return df


def show_map(df, x="Lon", y="Lat", c="speed", title="Speed map"):
    fig, ax = plt.subplots()
    im = ax.scatter(x=df[x], y=df[y], c=df[c], s=20)
    fig.colorbar(im, ax=ax).ax.set_title(c)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title)
    plt.show(block=False)
    # return ax
    # plt.show()


# def show_time_map(df, x="Lon", y="Lat", c="RelTime"):
#     df.plot.scatter(x=x, y=y, c=c, s=20)
#     plt.show()


def vis_brigade(df, brigade, speed=True):
    df = df[df["Brigade"] == brigade]
    c = "speed" if speed else "RelTime"
    show_map(df, c="RelTime", title="Map of " + brigade + " brigade")


def vis_line(df, line, speed=True):
    df = df[df["Lines"] == line]
    c = "speed" if speed else "RelTime"
    show_map(df, c=c, title="Map of " + line + " line")


def find_fast_busses(df):
    # analysing moments where busses went over 50 km/h
    new_df = df[df["speed"] > high_speed]
    print(
        "There are "
        + str(
            pd.DataFrame(new_df, columns=["VehicleNumber", "speed"])
            .groupby("VehicleNumber")
            .max()
            .count()["speed"]
        )
        + " fast (over "
        + str(high_speed)
        + " km/h) busses out of "
        + str(len(df["VehicleNumber"].unique()))
    )

    xmin = new_df["Lon"].min()
    ymin = new_df["Lat"].min()
    fast_points = pd.DataFrame(columns=["Lon", "Lat"])

    # searching in a grid for points with lots of bus speed around
    for i in range(50):
        x = xmin + i * 0.02
        for j in range(50):
            y = ymin + j * 0.01
            temp_df = new_df[
                coord_dist(new_df["Lat"], new_df["Lon"], y, x) < close_distance
            ]
            if temp_df.shape[0] > lots_of_busses:
                fast_points.loc[-1] = [x, y]
                fast_points.index = fast_points.index + 1
                fast_points = fast_points.sort_index()

    fig, ax = plt.subplots()
    ax.scatter(x=new_df["Lon"], y=new_df["Lat"])
    ax.set_title("Places of high speed bus")
    ax.scatter(x=fast_points["Lon"], y=fast_points["Lat"])

    show_map(df, title="Warsaw bus speed map")


def calc_delays(dataset_name, stop_file_name):
    df = pd.read_csv(dataset_name)
    df = df.drop_duplicates(keep=False)
    df = df.sort_values(by=["VehicleNumber", "Time"])
    df = df.drop(["VehicleNumber"], axis=1)

    # filtering stop times for the concerned window
    df["Time"] = pd.to_datetime(df["Time"]).dt.strftime("%X")
    min_time = df["Time"].min()
    max_time = df["Time"].max()
    st = pd.read_csv(stop_file_name).sort_values(by="Times")

    # to make sure hours are in [0..23] range
    st["Times"] = pd.to_timedelta(st["Times"]).astype(str).str[-8:]

    # two possibilities, in case midnight is between min_time and max_time
    if min_time < max_time:
        st = st[(min_time <= st["Times"]) & (st["Times"] < max_time)]
    else:  # midnight case
        st = st[(st["Times"] <= min_time) | (max_time <= st["Times"])]

    # joining frames to find minimal arrival of a good bus at stop
    res = pd.merge(df, st, how="inner", on=["Lines"])
    res["Time"] = pd.to_datetime(res["Time"], format="%X")  # bus arrival
    res["Times"] = pd.to_datetime(res["Times"], format="%X")  # planned arrival
    res = res[
        (coord_dist(res["Lat"], res["Lon"], res["Lats"], res["Lons"]) < near_stop)
        & (res["Times"] < res["Time"])
    ]
    # getting min
    res = res.groupby(["Lons", "Lats", "Times", "Lines"], as_index=False)["Time"].min()
    res["delay"] = res["Time"] - res["Times"]
    # transforming delay to minutes
    res["delay"] = res["delay"].astype("timedelta64[s]").astype(int) / 60
    res["delay"] = res["delay"].astype(int)

    show_map(res, x="Lons", y="Lats", c="delay", title="Delay map")
    # show_map(res, x="Lons", y="delay", c="delay", title="Delay height density")
    return res


def calc_statistics(sd):  # sd = stop_delays
    delay = sd["delay"]
    minim = delay.min()
    maxim = delay.max()
    average = delay.mean()
    median = delay.median()
    print("\nDelay statistics (in minutes):")
    print("Minimum delay is " + str(minim))
    print("Maximum delay is " + str(maxim))
    print("Average delay is " + str(average))
    print("Median delay is " + str(median))


def all():
    df = load_and_preprocess(sys.argv[1])
    find_fast_busses(df)
    sd = calc_delays(sys.argv[1], "stop_data.csv")
    calc_statistics(sd)
    vis_brigade(df, "1")
    vis_line(df, "521")
    vis_line(df, "172")
    plt.show()


if __name__ == "__main__":
    all()
