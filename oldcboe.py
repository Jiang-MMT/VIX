import glob
import os
import pandas as pd
from datetime import datetime, date, timedelta
import matplotlib.font_manager as font_manager
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.mlab import csv2rec
from matplotlib.ticker import Formatter
from matplotlib.dates import datestr2num, date2num
from matplotlib import colors as mcolors
from matplotlib import dates as mdates
from matplotlib import ticker as mticker
from mpl_finance import _candlestick, candlestick_ohlc, candlestick2_ohlc
import matplotlib
def combine_data():
    os.system("/usr/local/bin/gsed -i '/^CFE data.*/d' CFE*.csv")
    os.system("/usr/local/bin/gsed -i 's/,\r*$//g' CFE*.csv")
    os.system("/usr/local/bin/gsed -i '/^$/d' CFE*.csv")
    # os.system("/usr/local/bin/gsed -n 1p CFE_V04_VX.csv > cmb_file.csv")

    os.system("/usr/local/bin/awk 'BEGIN {OFS=FS=\",\"} {if (NR==1) {print \"Source\", $0} else { print FILENAME, $0}}' CFE_*.csv > temp1.csv")
    os.system("/usr/local/bin/awk '!/^CFE_*.*Interest[\t]*[\r]*$/' temp1.csv > temp2.csv")
    os.system("/usr/local/bin/awk 'BEGIN {OFS=FS=\",\"} {if ($2!=\"\") {print $0}}' temp2.csv > master.csv")
    # os.system("/usr/local/bin/gsed '/^[A-Z].*/d' CFE*.csv >> cmb_file.csv")
    # os.system("/usr/local/bin/gsed '/^[A-Z].*/d' CFE*.csv >> master1.csv")
    os.system("/usr/local/bin/gsed -i 's/,\r*$//g' master.csv")
def find_third_wed(t_obj):
    # t_obj = datetime.strptime(t_str, '%b %y')
    while t_obj.weekday() != 2 or t_obj.day > 23 or t_obj.day < 15:
        t_obj += timedelta(days=1)
    return t_obj

def proc_file():
    f = 'master.csv'
    df = pd.read_csv(f)
    # df = df.dropna(subset=['Trade Date'], inplace=True)
    df['Days_to_expire'] = df['Futures'].str.extract('^[A-Z] \((.*)\)', expand=False)
    df['Days_to_expire'] = pd.to_datetime(df['Days_to_expire'], format='%b %y')
    df.dropna(subset=['Trade Date'], inplace=True)
    df['Days_to_expire'] = df['Days_to_expire'].apply(find_third_wed)
    df['Year'] = df['Days_to_expire'].dt.year
    df['Month'] =df['Days_to_expire'].dt.month
    df['Day'] = df['Days_to_expire'].dt.day
    df['Days_to_expire'] = (df['Days_to_expire'] - pd.to_datetime(df['Trade Date'])).dt.days
    df = df.set_index(['Year', 'Month', 'Day',  'Trade Date'])
    df.sort_index()
    df.to_csv('VX_Master.csv')
