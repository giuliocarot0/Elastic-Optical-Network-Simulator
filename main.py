import numpy as np
import pandas as pd
import itertools as it
from libs.conenction import Connection
from libs.network import Network
from random import shuffle
import matplotlib.pyplot as plt


def create_traffic_matrix(nodes, rate):
    s = pd.Series(data=[0.0] * len(nodes), index=nodes)
    df = pd.DataFrame(float(rate), index=s.index, columns=s.index, dtype=s.dtype)
    np.fill_diagonal(df.values, s)
    return df


def plot3dbars(t):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    x, y = np.meshgrid(np.arange(t.shape[1]), np.arange(t.shape[0]))
    x = x.flatten()
    y = y.flatten()
    z = t.flatten()
    ax.bar3d(x, y, np.zeros(len(z)), 1, 1, z)
    plt.show()


def main():
    network = Network('nodes.json')
    network.connect()
    network.show_topology()

    nodes = list(network.nodes.keys())
    T = create_traffic_matrix(nodes, 1200)
    t = T.values

    connections = []
    node_pairs = list(filter(lambda x: x[0] != x[1], list(it.product(nodes, nodes))))
    shuffle(node_pairs)

    for node_pair in node_pairs:
        connection = Connection(node_pair[0], node_pair[1], float(T.loc[node_pair[0], node_pair[-1]]))
        connections.append(connection)

    streamed = network.stream(connections, best='snr', transceiver='flex-rate')
    snrs = []
    [snrs.extend(connection.snr) for connection in streamed]

    rbl = []
    for connection in streamed:
        for lightpath in connection.lightpaths:
            rbl.append(lightpath.bitrate)

    plt.hist(snrs)
    plt.title("SNRs distribution w/ occupied ")
    plt.show()

    rbc = [connection.calculate_capacity() for connection in streamed]
    plt.hist(rbc)
    plt.title('Connection Bitrate Distribution [ Gbps ]')
    plt.show()

    plt.hist(rbl)
    plt.title('Lightpath Bitrate Distribution [ Gbps ]')
    plt.show()

    s = pd.Series(data=[0.0] * len(nodes), index=nodes)
    df = pd.DataFrame(0.0, index=s.index, columns=s.index, dtype=s.dtype)
    print(df)
    for connection in streamed:
        df.loc[connection.input_node, connection.output_node] = connection.bitrate

    print(df)
    plot3dbars(t)
    plot3dbars(df.values)


if __name__ == '__main__':
    main()
