import copy
import pandas as pd
from libs.conenction import Connection
from libs.network import Network
import itertools as it
from random import shuffle
import numpy as np

class MonteCarlo(object):
    def __init__(self, file):
        self._netfile = file
        self._mc_node_pairs = []
        self._mc_streamed = []
        self._mc_line_state = []
        self._transceiver = "shannon"
        self._avg_snr = []
        self._avg_rbl = []
        self._traffic = []

    @property
    def mc_node_pairs(self):
        return self._mc_node_pairs

    @property
    def mc_streamed(self):
        return self._mc_streamed

    @property
    def mc_line_state(self):
        return self._mc_line_state

    @property
    def avg_snr(self):
        return self._avg_snr

    @property
    def avg_rbl(self):
        return self._avg_rbl

    @property
    def traffic(self):
        return self._traffic

    @property
    def transceiver(self):
        return self._transceiver

    @transceiver.setter
    def transceiver(self, transceiver):
        self._transceiver = transceiver

    def realize(self, rate, multiplier=1, nch=10, upgrade_line=""):
        net = Network(self._netfile, nch, upgrade_line)
        net.connect()
        traffic_matrix = self.create_traffic_matrix(net.nodes.keys(), rate, multiplier)
        nodes = list(net.nodes.keys())

        pairs = list(filter(lambda n: n[0] != n[1], it.product(nodes, nodes)))
        shuffle(pairs)
        self._mc_node_pairs.append(copy.deepcopy(pairs))
        connections = []
        for node_pair in pairs:
            conn = Connection(node_pair[0], node_pair[-1], float(traffic_matrix.loc[node_pair[0], node_pair[-1]]))
            connections.append(conn)
        streamed = net.stream(connections, best='snr', transceiver=self._transceiver)
        self._mc_streamed.append(streamed)
        self._mc_line_state.append(net.lines)

    def create_traffic_matrix(self, nodes, rate, multiplier=1):
        s = pd.Series(data=[0.0] * len(nodes), index=nodes)
        df = pd.DataFrame(float(rate*multiplier), index=s.index, columns=s.index, dtype=s.dtype)
        np.fill_diagonal(df.values, s)
        return df

    def compute_results(self):
        mc_streamed = self.mc_streamed

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

        [self._traffic.append(np.sum(lpt)) for lpt in mc_rbl]
        [self._avg_snr.append(np.mean(list(filter(lambda s: s != 0, snr)))) for snr in mc_snrs]
        [self._avg_rbl.append(np.mean(list(lpb))) for lpb in mc_rbl]

    def avg_congestion(self):
        lines = list(self._mc_line_state[0].keys())
        congestion_set = {name: [] for name in lines}
        for line_state in self._mc_line_state:
            for line_label, line in line_state.items():
                cong_rate = line.state.count("occupied") / len(line.state)
                congestion_set[line_label].append(cong_rate)

        avg_congestion = {label: [] for label in lines}
        for line_label, cong in congestion_set.items():
            avg_congestion[line_label] = np.mean(cong)

        return avg_congestion
