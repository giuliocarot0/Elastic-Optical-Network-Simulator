import numpy as np

class Connection(object):
    def __init__(self, inp, output, rate_request):
        self._input = inp
        self._output = output
        self._signal_power = 0
        self._latency = 0.0
        self._snr = []
        self._bitrate = None

        self._rate_request = float(rate_request)
        self._residual_rate_request = float(rate_request)

        self._lightpaths = []

    @property
    def lightpaths(self):
        return self._lightpaths

    @lightpaths.setter
    def lightpaths(self,lightpaths):
        self._lightpaths.append(lightpaths)

    @property
    def rate_request(self):
        return self._rate_request

    @property
    def residual_rate_request(self):
        return self._residual_rate_request

    @property
    def bitrate(self):
        return self._bitrate

    @bitrate.setter
    def bitrate(self, bitrate):
        self._bitrate = bitrate

    def calculate_capacity(self):
        self.bitrate = sum([l.bitrate for l in self.lightpaths])
        return self.bitrate

    @property
    def input_node(self):
        return self._input

    @property
    def output_node(self):
        return self._output

    @property
    def signal_power(self):
        return self._signal_power

    @signal_power.setter
    def signal_power(self, signal_pwr):
        self._signal_power = signal_pwr

    @property
    def latency(self):
        return self._latency

    @latency.setter
    def latency(self, latency):
        self._latency = latency

    @property
    def snr(self):
        return self._snr

    @snr.setter
    def snr(self, snr):
        self._snr.append(snr)

    def clear_lightpaths(self):
        self._lightpaths = []

    def set_connection(self, lightpath):
        self._signal_power = lightpath.signal_power
        self.latency = max(self.latency, lightpath.latency)
        self.snr = 10 * np.log10(lightpath.snr)
        self.lightpaths = lightpath

        self._residual_rate_request = self._residual_rate_request-lightpath.bitrate
        return self

    def block_connection(self):
        self.latency = None
        self.snr = 0
        self.bitrate = 0
        self.clear_lightpaths()

        return self