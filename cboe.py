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
import pylab


def pull_data():
    url = 'http://cfe.cboe.com/data/historicaldata.aspx#'
    ans = raw_input('What do you need? \n VX, VXTY, VU, VA, VAO \n VSW, VM, VN, VXEM, VXEW, GV, OV, \nRPXC, VT, BX, VR, VA, DV \n')
    print 'pulling %s'% ans

    path = os.path.join(os.getenv('HOME'), 'CBOE', ans)
    if not os.path.exists(path):
        os.makedirs(path)

    os.chdir(path)
    os.system('/usr/local/bin/wget -nd -nc -r -l1 -A _{}.csv {}'.format(ans, url))


def combine_data():
    cwd = os.getcwd()
    os.chdir(cwd)
    os.system("/usr/local/bin/gsed -i '/^CFE data.*/d' CFE*.csv")
    os.system("/usr/local/bin/gsed -i 's/,\r*$//g' CFE*.csv")
    os.system("/usr/local/bin/awk 'BEGIN {OFS=FS=\",\"} {if (NR==1) {print \"Source\", $0} else { print FILENAME, $0}}' CFE_*.csv > temp.csv")
    os.system("/usr/local/bin/awk '!/^CFE_*.*Interest[\t]*[\r]*$/' temp.csv > master.csv")
    # os.system("/usr/local/bin/gsed '/^[A-Z].*/d' CFE*.csv >> master.csv")
    # os.system("/usr/local/bin/gsed -i 's/,\r*$//g' master.csv")


def find_third_wed(t_obj):
    while t_obj.weekday() != 2 or t_obj.day > 23 or t_obj.day < 15:
        t_obj += timedelta(days=1)
    return t_obj


def process_file():
    f = 'master.csv'
    df = pd.read_csv(f)
    df['Days_to_expire'] = df.ix[:, 2].str.extract('^[A-Z] \((.*)\)', expand=False)
    df['Days_to_expire'] = pd.to_datetime(df['Days_to_expire'], format='%b %y')
    df['Days_to_expire'] = df['Days_to_expire'].apply(find_third_wed)
    df['Year'] = df['Days_to_expire'].dt.year
    df['Month'] = df['Days_to_expire'].dt.month
    df['Day'] = df['Days_to_expire'].dt.day
    df['Days_to_expire'] = (df['Days_to_expire'] - pd.to_datetime(df['Trade Date'])).dt.days
    df = df.set_index(['Year', 'Month', 'Day', 'Trade Date'])
    df = df.sort_index()
    df.to_csv('VX_Master.csv')
    return df


def get_data(f): # get data into record array
    print 'loading %s' % f
    r = csv2rec(f)
    return r


class MyFormatter(Formatter):
    def __init__(self, dates, fmt='%Y-%m-%d'):
        self.dates = dates
        self.fmt = fmt

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        ind = int(np.round(x))
        if ind >= len(self.dates) or ind < 0:
            return ''

        return self.dates[ind].strftime(self.fmt)


def mva(x, n, kind='simple'):
    x = np.asarray(x)
    if kind == 'simple':
        weights = np.ones(n)
    else:
        weights = np.exp(np.linspace(-1., 0., n))

    weights /= weights.sum()

    a = np.convolve(x, weights, mode='full')[:len(x)]
    a[:n] = a[n]
    return a


def plot_ohlc(ax, dates, opens, highs, lows, closes):

    ohlc = zip(dates, opens, highs, lows, closes)
    candlestick_ohlc(ax, ohlc, width=.42, colorup='#53c156', colordown='#ff1717')

    
def plot_mva(ax, dates, closes, period, kind='simple'):
    ma = mva(closes, period, kind)
    ax.plot(dates, ma, color='yellow', label='MA%d'%period)
    props = font_manager.FontProperties(size=10)
    leg = ax.legend(loc='best', shadow=True, fancybox=True, prop=props)
    leg.get_frame().set_alpha(0.5)

    
def plot_data(f, period=None, kind=None, ohlc=False):
    r = get_data(f)
    dates = date2num(r.trade_date)
    opens = r.open[np.nonzero(r.open)]
    highs = r.high[np.nonzero(r.high)]
    lows = r.low[np.nonzero(r.low)]
    r.close[r.close==0.0] = np.nan
    closes = r.close
    volume = r.total_volume
    # plot closes
    fig = plt.figure(figsize=(10,5), facecolor='#07000d')
    ax  = plt.subplot2grid((4,4), (0,0), rowspan=3, colspan=4,axisbg='#07000d')
    ax.plot(dates, closes, 'w-', lw=2)
    ax.grid(True, color='w')
    plt.ylabel('Price')
    ax.xaxis.set_major_locator(mticker.MaxNLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.yaxis.label.set_color("w")
    ax.spines['bottom'].set_color("#5998ff")
    ax.spines['top'].set_color("#5998ff")
    ax.spines['left'].set_color("#5998ff")
    ax.spines['right'].set_color("#5998ff")
    ax.tick_params(axis='y', colors='w')
    plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(prune='upper'))
    ax.tick_params(axis='x', colors='w')
    plt.setp(ax.get_xticklabels(), visible=False)
    plt.suptitle('Contract %s'%f.split('.')[0], color='w')
    
    # plot volume
    axv = plt.subplot2grid((4,4), (3,0), sharex=ax, rowspan=1, colspan=4, axisbg='#07000d')
    axv.bar(dates, volume)
    axv.grid(True, color='w')
    plt.ylabel('Volume')
    axv.spines['bottom'].set_color("#5998ff")
    axv.spines['top'].set_color("#5998ff")
    axv.spines['left'].set_color("#5998ff")
    axv.spines['right'].set_color("#5998ff")
    axv.axes.yaxis.set_ticklabels([])
    axv.tick_params(axis='x', colors='w')
    axv.yaxis.label.set_color("w")
    axv.tick_params(axis='y', colors='w')
    for label in axv.xaxis.get_ticklabels():
        label.set_rotation(45)
    plt.subplots_adjust(left=.1, right=.9, top=.9, bottom=.2, hspace=0, wspace=.2)

    if period is not None:
        plot_mva(ax, dates, closes, period, kind)

    # add candlestick line

    if ohlc:
        plot_ohlc(ax, dates, opens, highs, lows, closes)

    #save figure
    path =  os.path.join(os.getcwd(), 'Graphs')
    # fig.savefig('%s.png'%f.split('.')[0], facecolor=fig.get_facecolor())
    if not os.path.exists(path):
        os.makedirs(path)
    fig.savefig('{}/{}.png'.format(path, f.split('.')[0]), facecolor='#07000d')


def plot_all():
    for f in glob.glob('CFE*.csv'):
        plot_data(f)

if __name__ == '__main__':
    pull_data()
    combine_data()
    print 'Processing data...'
    df = process_file()
    print 'Data finished processed!'
    r = raw_input('Do you want to plot data? \ny/n\n')
    if r == 'y':
        plot_all()
        print 'plotting data...'
    print 'All done!'
