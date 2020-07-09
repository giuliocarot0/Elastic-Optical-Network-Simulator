class Lightpath(object):
    def __init__(self, path, channel=0, rs=32e9, df=50e9):
        self._signal_power = 0
        self._path = path
        self._channel = channel
        self._noise_power = 0
        self._latency = 0
        self._rs = rs
        self._df = df

        self._snr = None
        self._optimized_powers = {}

    @property
    def optimized_powers(self):
        return self._optimized_powers

    @optimized_powers.setter
    def optimized_powers(self, optimized_powers):
        self._optimized_powers = optimized_powers

    @property
    def snr(self):
        return self._snr

    @snr.setter
    def snr(self, snr):
        self._snr = snr

    def update_snr(self, snr):
        if self._snr is None:
            self._snr = snr
        else:
            self._snr = 1/(1/self.snr + 1/snr)

    @property
    def signal_power(self):
        return self._signal_power

    @signal_power.setter
    def signal_power(self, signal_power):
        self._signal_power = signal_power

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
