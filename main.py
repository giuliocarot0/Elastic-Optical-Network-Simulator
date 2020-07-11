import numpy as np
import pandas as pd
import copy
import itertools as it
from libs.conenction import Connection
from libs.network import Network
from random import shuffle
import matplotlib.pyplot as plt

from montecarlo import MonteCarlo


def plot3dbars(t, i):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    x, y = np.meshgrid(np.arange(t.shape[1]), np.arange(t.shape[0]))
    x = x.flatten()
    y = y.flatten()
    z = t.flatten()
    ax.bar3d(x, y, np.zeros(len(z)), 1, 1, z)
    plt.show()


def main1():
    for j in range(10):
        start_value = 10    # Value equal to #channel (each channel have ca 500gbps rate)
        nmc = 10
        load_margin = 5e-4
        montecarlo = MonteCarlo('nodes.json')
        print("Starting Montecarlo Analysis w/ multiplier = {:d}".format(j+start_value))
        print('\n')
        for i in range(nmc):
            print("     Monte-Carlo {:.1f}% (Realization #{:d})".format((i+1)*100/nmc, i))
            montecarlo.transceiver = "shannon"
            montecarlo.realize(rate=400, multiplier=start_value + j, nch=10, upgrade_line="")

        montecarlo.compute_results()

        avg_snr = montecarlo.avg_snr
        avg_rbl = montecarlo.avg_rbl
        traffic = montecarlo.traffic
        avg_congestion = montecarlo.avg_congestion()

        plt.bar(range(len(avg_congestion)), list(avg_congestion.values()), align='center')
        plt.xticks(range(len(avg_congestion)), list(avg_congestion.keys()))
        plt.title("Multiplier = {:d}".format(j+start_value))
        plt.show()

        if np.mean(list(avg_congestion.values())) >= 1.0 - load_margin:
            print("     ---------------NETWORK FULLY LOADED!-------------------")
            print("     max rate_multiplier value = {:d}".format(j+start_value))
            print('     Avg Total Traffic: {:.2f} Tbps'.format(np.mean(traffic)))
            print('     Avg Lightpath Bitrate: {:.2f} Gbps'.format(np.mean(avg_rbl)))
            print('     Avg Lightpath SNR: {:.2f} dB'.format(np.mean(avg_snr)))
            print('     Line to upgrade: {}'.format(max(avg_congestion, key=avg_congestion.get)))
            exit()

        print('     Avg Total Traffic: {:.2f} Tbps'.format(np.mean(traffic)))
        print('     Avg Lightpath Bitrate: {:.2f} Gbps'.format(np.mean(avg_rbl)))
        print('     Avg Lightpath SNR: {:.2f} dB'.format(np.mean(avg_snr)))
        print('     Line to upgrade: {}'.format(max(avg_congestion, key=avg_congestion.get)))
        print('\n')
        # s = pd.Series(data=[0.0] * len(nodes), index=nodes)
        # df = pd.DataFrame(0.0, index=s.index, columns=s.index, dtype=s.dtype)
        # print(df)
        # for connection in streamed:
        #     df.loc[connection.input_node, connection.output_node] = connection.bitrate
        # print(df)
        # plot3dbars(rates, i)
        # plot3dbars(df.values, i)


def main2():
    nmc = 10
    load_margin = 5e-4
    montecarlo = MonteCarlo('nodes.json')
    print("Starting Montecarlo Analysis w/ multiplier = {:d}".format(16))
    print('\n')
    for i in range(nmc):
        print("     Monte-Carlo {:.1f}% (Realization #{:d})".format((i+1)*100/nmc, i))
        montecarlo.transceiver = "shannon"
        montecarlo.realize(rate=400, multiplier=16, nch=15, upgrade_line="DB")

    montecarlo.compute_results()

    avg_snr = montecarlo.avg_snr
    avg_rbl = montecarlo.avg_rbl
    traffic = montecarlo.traffic
    avg_congestion = montecarlo.avg_congestion()

    plt.bar(range(len(avg_congestion)), list(avg_congestion.values()), align='center')
    plt.xticks(range(len(avg_congestion)), list(avg_congestion.keys()))
    plt.title("Multiplier = {:d}".format(16))
    plt.show()
    print('     Avg Total Traffic: {:.2f} Tbps'.format(np.mean(traffic)))
    print('     Avg Lightpath Bitrate: {:.2f} Gbps'.format(np.mean(avg_rbl)))
    print('     Avg Lightpath SNR: {:.2f} dB'.format(np.mean(avg_snr)))
    print('     Line to upgrade: {}'.format(max(avg_congestion, key=avg_congestion.get)))
    print('\n')


if __name__ == '__main__':
    main1()
