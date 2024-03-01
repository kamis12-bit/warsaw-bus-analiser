# Warsaw bus toolbox

Toolbox for gathering and analysing data concerning busses in Warsaw.
**Important:** insert your own api_key into the `api_key.py` file, so that you can gather data
There are three major files: gather_data, gather_stops, analyse.

### `gather_data`

Allows gathering positions of buses in Warsaw, for one hour or four hours (gather_night). The data is gathered in real life (there is no online archive of this data), so the script takes so long, as long is the data it gathers. `bus-data` is a collection of data gathered using this script.
Takes as argument path and name of file where output is to be stored.

### `gather_stops`

Allows gathering of all expected arrivals at all stops in Warsaw. This script requires just under 30000 requests, so it takes a while (~5 hours for me). `stop_data.csv` is the result of running this script.

### `analyse`

Functionalities include: calculating the speed of buses, visualising different aspects on longitude-latitude plot, calculating information about the delays. `vis_line_script.py` is an example script utilising analyse.vis_line.
Takes as argument path of .csv file with data to analyse (as gathered by `gather_hour` function from `gather_data`)


