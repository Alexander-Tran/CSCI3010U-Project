import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#Clean data
df = pd.read_csv('weatherstats_oshawa_100k.csv')
df = df.filter(['wind_speed'])
df['wind_speed'].dropna(inplace=True)

#Convert km/h to m/s^2
df['wind_speed'] /= 3.6
print(df['wind_speed'].value_counts())

#Generate histogram of wind speeds
plt.hist(df['wind_speed'], density=True)
plt.title('Normalized Wind Speeds in Oshawa, Ontario')
plt.xlabel('Wind Speed [m/s]')
plt.ylabel('Probability Density')
# plt.show()

df.to_csv('weather_cleaned.csv')