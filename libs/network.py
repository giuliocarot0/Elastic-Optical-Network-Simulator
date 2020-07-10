import json

from scipy.special import erfcinv

from .node import Node
from .line import Line
from .lightpath import Lightpath
from .signal import  SignalInformation
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


class Network(object):
    def __init__(self, input_file):
        self._nodes = {}
        self._lines = {}
        self._connected = False
        self._weighted_paths = None
        self._route_space = None
        node_json = json.load(open(input_file, 'r'))
        for node_name in node_json:
            node_dict = node_json[node_name]
            node_dict['label'] = node_name
            node = Node(node_dict)
            self._nodes[node_name] = node
            for next_node in node_dict['connected_nodes']:
                line_dict = {}
                line_label = node_name + next_node
                line_dict['label'] = line_label
                node0_position = np.array(node_json[node_name]['position'])
                node1_position = np.array(node_json[next_node]['position'])
                line_dict['length'] = np.sqrt(np.sum(node0_position - node1_position) ** 2)  # distance among points
                line = Line(line_dict)
                self._lines[line_label] = line

    @property
    def nodes(self):
        return self._nodes

    @property
    def lines(self):
        return self._lines

    @property
    def connected(self):
        return self._connected

    @property
    def weighted_paths(self):
        return self._weighted_paths

    @property
    def route_space(self):
        return self._route_space

    def show_topology(self):
        nodes = self.nodes
        for node_l in nodes:
            n0 = nodes[node_l]
            x0 = n0.position[0]
            y0 = n0.position[1]
            for connected_node in n0.connected_nodes:
                n1 = nodes[connected_node]
                x1 = n1.position[0]
                y1 = n1.position[1]
                plt.plot([x0, x1], [y0, y1], 'b')
        plt.title("Network Topology")
        plt.show()

    def connect(self):
        if not self.connected:
            nodes_dict = self.nodes
            lines_dict = self.lines

            for node_l in nodes_dict:
                node = nodes_dict[node_l]
                for connected_node in node.connected_nodes:
                    line = lines_dict[node_l + connected_node]
                    line.successive[connected_node] = nodes_dict[connected_node]
                    node.successive[node_l + connected_node] = line
            self._connected = True

    def find_paths(self, in_node, out_node):
        crossable_nodes = [i for i in self.nodes.keys() if ((i != in_node) & (i != out_node))]
        crossable_lines = self.lines.keys()

        inn_paths = {}
        inn_paths['0'] = in_node  # init path array

        for i in range(len(crossable_nodes) + 1):
            inn_paths[str(i + 1)] = []
            for inner_path in inn_paths[str(i)]:
                inn_paths[str(i + 1)] += [inner_path + crossable_node
                                          for crossable_node in crossable_nodes
                                          if ((inner_path[-1] + crossable_node in crossable_lines) & (crossable_node not in inner_path))]
        paths = []
        for i in range(len(crossable_nodes) + 1):
            for path in inn_paths[str(i)]:
                if path[-1] + out_node in crossable_lines:
                    paths.append(path + out_node)
        return paths

    def propagate(self, signal_information, occupation="free"):
        path = signal_information.path
        start_node = self.nodes[path[0]]
        propagated_signal_information = start_node.propagate(signal_information, occupation)
        return propagated_signal_information

    def set_weighted_paths(self):   # collect data propagating signal
        if not self.connected:
            self.connect()
        node_names = self.nodes.keys()
        pairs = []
        for n1 in node_names:
            for n2 in node_names:
                if n1 != n2:
                    pairs.append(n1+n2)

        df = pd.DataFrame()
        paths = []
        latencies = []
        noises = []
        snrs = []

        for pair in pairs:
            for path in self.find_paths(pair[0], pair[1]):
                pathstring = ''
                for node in path:
                    pathstring += node + '->'
                paths.append(pathstring[:-2])

                # propagate signal through the computed path
                signal = Lightpath(path)
                signal = self.optimization(signal)
                signal = self.propagate(signal)
                latencies.append(signal.latency)
                noises.append(signal.noise_power)
                snrs.append(10*np.log10(signal.snr))

        df['path'] = paths
        df['latency'] = latencies
        df['noise'] = noises
        df['snr'] = snrs
        self._weighted_paths = df

        rs = pd.DataFrame()
        rs['path'] = paths
        for i in range(10):
            rs[str(i)] = ['free']*len(paths)
        self._route_space = rs

    def stream(self, connections, best="latency", transceiver='shannon', occupation="occupied"):
        streamed = []
        if self.weighted_paths is None:
            self.set_weighted_paths()
        for connection in connections:
            in_node = connection.input_node
            out_node = connection.output_node
            if best == 'snr':
                path = self.find_best_snr(in_node, out_node)
            elif best == 'latency':
                path = self.find_best_latency(in_node, out_node)
            else:
                print("Unrecognized best input parameter")
                continue
            if path:
                p = path.replace('', '->')[2:][:-2]
                path_status = self.route_space.loc[self.route_space.path == p].T.values[1:]
                channel = [i for i in range(len(path_status)) if path_status[i] == 'free'][0]
                in_signal = Lightpath(path, channel)
                in_signal = self.optimization(in_signal)
                out_sign = self.propagate(in_signal, occupation)

                out_sign.bitrate = self.calculate_bitrate(out_sign, transceiver)
                if out_sign.bitrate == 0.0:
                    [self.update_route(l.path, l.channel, "free") for l in connection.lightpaths]
                    connection.block_connection()
                else:
                    connection.set_connection(out_sign)
                    self.update_route(path, channel, "occupied")
                    if connection.residual_rate_request > 0:
                        self.stream([connection], best, transceiver)

            else:
                [self.update_route(l.path, l.channel, "free") for l in connection.lightpaths]
                connection.block_connection()
            streamed.append(connection)
        return streamed

    def available_paths(self, input_node, output_node):
        if self.weighted_paths is None:
            self.weighted_paths(1)
        all_paths = [path for path in self.weighted_paths.path.values if((path[0] == input_node) & (path[-1] == output_node))]
        busy_lines = [line for line in self.lines if self.lines[line].state == "occupied"]
        paths = []
        for path in all_paths:
            path_free_channels = self.route_space.loc[self.route_space.path == path].T.values[1:]
            if "free" in path_free_channels:
                paths.append(path)
        return paths

    def find_best_snr(self, input, output):
        paths = self.available_paths(input, output)
        best = None
        if paths:
            matched_path = [path for path in paths if ((path[0] == input) & (path[-1] == output))]
            matched_path_data = self.weighted_paths.loc[self.weighted_paths.path.isin(matched_path)]
            best_snr = max(matched_path_data.snr.values)
            best = matched_path_data.loc[matched_path_data.snr == best_snr].path.values[0].replace('->', '')
        return best

    def find_best_latency(self, input, output):
        paths = self.available_paths(input, output)
        best = None
        if paths:
            matched_path = [path for path in paths if ((path[0] == input) & (path[-1] == output))]
            matched_path_data = self.weighted_paths.loc[self.weighted_paths.path.isin(matched_path)]
            best_latency = max(matched_path_data.latency.values)
            best = matched_path_data.loc[matched_path_data.latency == best_latency].path.values[0].replace('->', '')
        return best

    @staticmethod
    def to_set(path):
        path = path.replace('->', '')
        p_set = set([path[i]+path[i+1] for i in range(len(path) - 1)])
        return p_set

    def update_route(self, path, channel, state):
        p_set = [self.to_set(p) for p in self.route_space.path.values]
        states = self.route_space[str(channel)]
        path_lines = self.to_set(path)
        for i in range(len(p_set)):
            line_set = p_set[i]
            if path_lines.intersection(line_set):
                states[i] = state
        self.route_space[str(channel)] = states

    def optimization(self, lightpath):
        path = lightpath.path
        node0 = self.nodes[path[0]]
        o_lightpath = node0.optimize(lightpath)
        o_lightpath.path = path
        return o_lightpath

    @staticmethod
    def calculate_bitrate(lightpath, bert=1e-3):
        rb = 0
        snr = lightpath.snr
        bn = 12.5e9
        rs = lightpath.rs
        if lightpath.transceiver.lower() == 'fixed-rate':
            snrt = 2 * erfcinv(2 * bert) * (rs / bn)
            rb = np.piecewise(snr, [snr < snrt, snr >= snrt], [0, 100])
        elif lightpath.transceiver.lower() == 'flex-rate':
            snrt1 = 2 * erfcinv(2 * bert) ** 2 * (rs / bn)
            snrt2 = (14 / 3) * erfcinv(3 / 2 * bert) ** 2 * (rs / bn)
            snrt3 = 10 * erfcinv(8 / 3 * bert) ** 2 * (rs / bn)
            cond1 = (snr < snrt1)
            cond2 = (snrt1 <= snr < snrt2)
            cond3 = (snrt2 <= snr < snrt3)
            cond4 = (snr >= snrt3)
            rb = np.piecewise(snr, [cond1, cond2, cond3, cond4], [0, 100, 200, 400])
        elif lightpath.transceiver.lower() == 'shannon':
            rb = 2 * rs * np.log2(1 + snr * (rs / bn)) * 1e-9
        return float(rb)
