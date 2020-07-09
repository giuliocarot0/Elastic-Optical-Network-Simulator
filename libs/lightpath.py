class Lightpath(object):
    def __init__(self, path, channel, rs=32e9, df=50e9):
        self._signal_power = 0
        self._path = path
        self._channel = channel
        self._noise_power = 0
        self._latency = 0
        self._rs = rs
        self._df = df

    @property
    def signal_power(self):
        return self._signal_power

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def channel(self):
        return self._channel

    @property
    def noise_power(self):
        return self._noise_power

    @noise_power.setter
    def noise_power(self, noise):
        self._noise_power = noise

    @property
    def latency(self):
        return self._latency

    @latency.setter
    def latency(self, latency):
        self._latency = latency

    @property
    def rs(self):
        return self._rs

    @property
    def df(self):
        return self._df

    def add_noise(self, noise):
        self.noise_power += noise

    def add_latency(self, latency):
        self.latency += latency

    def next(self):
        self.path = self.path[1:]
