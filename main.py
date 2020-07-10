import numpy as np
import pandas as pd
import copy
import itertools as it
from libs.conenction import Connection
from libs.network import Network
from random import shuffle
import matplotlib.pyplot as plt


def create_traffic_matrix(nodes, rate, multiplier=1):
    s = pd.Series(data=[0.0] * len(nodes), index=nodes)
    df = pd.DataFrame(float(rate*multiplier), index=s.index, columns=s.index, dtype=s.dtype)
    np.fill_diagonal(df.values, s)
    return df


def plot3dbars(t, i):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    x, y = np.meshgrid(np.arange(t.shape[1]), np.arange(t.shape[0]))
    x = x.flatten()
    y = y.flatten()
    z = t.flatten()
    ax.bar3d(x, y, np.zeros(len(z)), 1, 1, z)
    plt.show()


def main():
    nmc = 50
    # monte-carlo output arrays
    mc_node_pairs = []
    mc_streamed = []
    mc_line_state = []

    for i in range(nmc):
        print("Monte-Carlo {:.1f}% (Realization #{:d})".format((i+1)*100/nmc, i))
        net = Network('nodes.json', nch=2, upgrade_line="CA")
        net.connect()
        # net.plot_topography()

        nodes = list(net.nodes.keys())
        t_matrix = create_traffic_matrix(nodes, 400, 1)
        rates = t_matrix.values

        node_pairs = list(filter(lambda n: n[0] != n[1], it.product(nodes, nodes)))
        shuffle(node_pairs)
        mc_node_pairs.append(copy.deepcopy(node_pairs))
        connections = []
        for node_pair in node_pairs:
            conn = Connection(node_pair[0],node_pair[-1], float(t_matrix.loc[node_pair[0], node_pair[-1]]))
            connections.append(conn)

        streamed = net.stream(connections, best='snr', transceiver='flex-rate')
        mc_streamed.append(streamed)
        mc_line_state.append(net.lines)

        # avg result
        mc_snrs = []
        mc_rbl = []
        mc_rbc = []

        for streamed in mc_streamed:
            snrs = []
            rbl = []
            [snrs.extend(connection.snr) for connection in streamed]
            for cn in streamed:
                for lp in cn.lightpaths:
                    rbl.append(lp.bitrate)

            rbc = [cn.calculate_capacity() for cn in streamed]
            mc_snrs.append(snrs)
            mc_rbl.append(rbl)
            mc_rbc.append(rbc)

    avg_snr = []
    avg_rbl = []
    traffic = []

    [traffic.append(np.sum(lpt)) for lpt in mc_rbl]
    [avg_snr.append(np.mean(list(filter(lambda s: s != 0, snr)))) for snr in mc_snrs]
    [avg_rbl.append(np.mean(list(lpb))) for lpb in mc_rbl]

    lines = list(mc_line_state[0].keys())
    congestion_set = {name: [] for name in lines}
    for line_state in mc_line_state:
        for line_label, line in line_state.items():
            cong_rate = line.state.count("occupied")/len(line.state)
            congestion_set[line_label].append(cong_rate)

    avg_congestion = {label: [] for label in lines}
    for line_label, cong in congestion_set.items():
        avg_congestion[line_label] = np.mean(cong)

    plt.bar(range(len(avg_congestion)), list(avg_congestion.values()), align='center')
    plt.xticks(range(len(avg_congestion)), list(avg_congestion.keys()))
    plt.show()

    print('Avg Total Traffic: {:.2f} Tbps'.format(np.mean(traffic)))
    print('Avg Lightpath Bitrate: {:.2f} Gbps'.format(np.mean(avg_rbl)))
    print('Avg Lightpath SNR: {:.2f} dB'.format(np.mean(avg_snr)))
    print('Line to upgrade: {}'.format(max(avg_congestion, key=avg_congestion.get)))
    s = pd.Series(data=[0.0] * len(nodes), index=nodes)
    df = pd.DataFrame(0.0, index=s.index, columns=s.index, dtype=s.dtype)
    print(df)
    for connection in streamed:
        df.loc[connection.input_node, connection.output_node] = connection.bitrate
    print(df)
    plot3dbars(rates, i)
    plot3dbars(df.values, i)


if __name__ == '__main__':
    main()
