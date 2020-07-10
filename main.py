import numpy as np
from libs.conenction import Connection
from libs.network import Network
from random import shuffle
import matplotlib.pyplot as plt

network = Network('nodes.json')
network.connect()
network.show_topology()


nodes = list(network.nodes.keys())
connections = []
connections_occupied = []

for i in range(100):
    shuffle(nodes)
    connection = Connection(nodes[0], nodes[-1])
    connections.append(connection)

streamed2 = network.stream(connections, 'snr', "occupied")
snr_o = [connection.snr for connection in streamed2]
if 0 in snr_o:
    print("Conenction blocked")
plt.hist(snr_o)
plt.title("SNRs distribution w/ occupied ")
plt.show()

rbs = [connection.calculate_capacity() for connection in streamed2]
plt.hist(rbs)
plt.title('Bitrate Distribution [ Gbps ]')
plt.show()
print('Total Capacity : {:.2f} Tbps'.format(np.sum(rbs)*1e-3))
print('Avg Capacity : {:.2f} Gbps'.format(np.mean(rbs)))
