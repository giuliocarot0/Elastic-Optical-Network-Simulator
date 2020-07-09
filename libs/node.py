class Node(object):
    def __init__(self, node_dict):
        self._node_name = node_dict['label']
        self._position = node_dict['position']
        self._successive = {}
        self._connected_nodes = node_dict['connected_nodes']

    @property
    def label(self):
        return self._node_name

    @property
    def position(self):
        return self._position

    @property
    def successive(self):
        return self._successive

    @property
    def connected_nodes(self):
        return self._connected_nodes

    @successive.setter
    def successive(self, successive):
        self._successive = successive

    def propagate(self, lightpath, occupation="free"):
        path = lightpath.path
        if len(path) > 1:
            line_label = path[:2]
            line = self.successive[line_label]
            lightpath.next()
            lightpath = line.propagate(lightpath, occupation)
        return lightpath
