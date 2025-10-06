import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="darkgrid")
import urllib
import urllib.parse as urlp
import io
import warnings
warnings.filterwarnings("ignore")

#%matplotlib inline

userStartDate = "YYYY-MM-DD"#input("Enter start date (YYYY-MM-DD): ")
userEndDate = "2022-01-01"#input("Enter end date (YYYY-MM-DD): ")
userLatitude = 38.89#input("Enter latitude (e.g. 38.89): ")
userLongitude = -88.18#input("Enter longitude (e.g. -88.18): ")

start_date="2012-01-01T00"
end_date="2021-12-01T00"
latitude=38.89
longitude=-88.18

def get_time_series(start_date,end_date,latitude,longitude,variable):
    """
    Calls the data rods service to get a time series
    """
    base_url = "https://hydro1.gesdisc.eosdis.nasa.gov/daac-bin/access/timeseries.cgi"
    query_parameters = {
        "variable": variable,
        "type": "asc2",
        "location": f"GEOM:POINT({longitude}, {latitude})",
        "startDate": start_date,
        "endDate": end_date,
    }
    full_url = base_url+"?"+ \
         "&".join(["{}={}".format(key,urlp.quote(query_parameters[key])) for key in query_parameters])
    # print(full_url)
    iteration = 0
    done = False
    while not done and iteration < 5:
        r=requests.get(full_url)
        if r.status_code == 200:
            done = True
        else:
            iteration +=1
    
    if not done:
        raise Exception(f"Error code {r.status_code} from url {full_url} : {r.text}")
    
    return r.text

def parse_time_series(ts_str):
    """
    Parses the response from data rods.
    """
    lines = ts_str.split("\n")
    parameters = {}
    for line in lines[2:11]:
        key,value = line.split("=")
        parameters[key] = value
    
    
    df = pd.read_table(io.StringIO(ts_str),sep="\t",
                       names=["time","data"],
                       header=10,parse_dates=["time"])
    return parameters, df

df_precip = parse_time_series(
            get_time_series(
                start_date, 
                end_date,
                userLatitude,
                userLongitude,
                variable="NLDAS2:NLDAS_FORA0125_H_v2.0:Rainf"
            )
        )

df_soil = parse_time_series(
            get_time_series(
                start_date, 
                end_date,
                userLatitude,
                userLongitude,
                variable="NLDAS2:NLDAS_NOAH0125_H_v2.0:SoilM_0_100cm"
          )
        )

# df_soil[1]['data']

d = {'time': pd.to_datetime(df_precip[1]['time'], unit='s'), 
    'Rainf': df_precip[1]['data'], 
    'SoilM_0_100cm': df_soil[1]['data']}
    
df = pd.DataFrame(data=d)
df.head()

fig, (ax1, ax2) = plt.subplots(2, figsize=(21, 8), sharex=True)

# Aggregate over days
daily_precip = df[['time', 'Rainf']].groupby(pd.Grouper(key='time', freq='1D')).sum().reset_index()
daily_soil = df[['time', 'SoilM_0_100cm']].groupby(pd.Grouper(key='time', freq='1D')).mean().reset_index()

ax1.plot(daily_precip["time"], daily_precip["Rainf"], color="blue")
ax1.set_ylim(-2, 150)
ax1.legend(["Rainf"])
ax1.set_ylabel("Daily Precipitation (mm)")

ax2.fill_between(daily_soil["time"], 200, daily_soil["SoilM_0_100cm"], color="green", alpha=0.25)
ax2.set_ylim(198, 400)
ax2.legend(["SoilM_0_100cm"])
ax2.set_ylabel("Mean Top 0-100cm Soil Moisture Content (mm)")
ax2.set_xlabel("Date")

fig.suptitle("NLDAS-2 Daily Total Rainf and Daily Mean SoilM_0_100cm (38.9375, -88.1875) from 2022-07-01T00 - 2022-09-01T00", size=15)
# plt.show()

# print("df_precip:")
# print(df_precip)
# print()
# print("daily_precip:")
# print(daily_precip)
# print()
print("Average daily precipitation (mm):")
print(avg_precip := daily_precip["Rainf"].mean())

startMonth = []
endMonth = []
monthly = []
currMonthVals = []
nextMonth = daily_precip['time'][0].month + 1
i = 0
for r in daily_precip['time']:
    currMonth = r.month
    if str(r.month) == start_date[5:7] or str(r.month) == start_date[6:7]:
        startMonth.append(daily_precip['Rainf'][i])
    if str(r.month) == end_date[5:7] or str(r.month) == end_date[6:7]:
        endMonth.append(daily_precip['Rainf'][i])
    if (currMonth != nextMonth):
        # print("in month")
        currMonthVals.append(daily_precip['Rainf'][i])
    elif (currMonth == nextMonth and (start_date[5:7] != end_date[5:7] or start_date[6:7] != end_date[6:7]) or  (str(r) == end_date[0:10])):
        print("new month")
        monthly.append(sum(currMonthVals)/len(currMonthVals) if len(currMonthVals) > 0 else 0)
        currMonth = nextMonth
        nextMonth += 1
        currMonthVals = []
    i += 1


print("Average for start month throughout range (mm):")
avgStartValue = sum(startMonth)/len(startMonth) if len(startMonth) > 0 else 0
print(avgStartValue)
print("Average for end month throughout range (mm):")
avgEndValue = sum(endMonth)/len(endMonth) if len(endMonth) > 0 else 0
print(avgEndValue)
print("Average for each month in range (mm):")
for i in range(len(monthly)):
    print(monthly[i])

print("Predictions for 6 months after end date:")
userEndMonth = int(userEndDate[5:7])
for i in range(userEndMonth, userEndMonth + 6):
    print(monthly[i])
