from scipy.constants import c, Planck, pi
import numpy as np
from .signal import SignalInformation


class Line(object):
    def __init__(self, line_dict): # creating a line with a default number of channel equal to 10
        self._label = line_dict['label']
        self._length = line_dict['length']
        self._successive = {}
        self._state = ["free"]*10
        # ila number and parameters
        self._amplifiers = int(np.ceil(self.length / 80e3))
        self._span_length = self.length/self._amplifiers
        self._noise_figure = 50
        # fiber parameters
        self._alpha = 4.6e-5
        self._beta = 21.27e-27
        self._gamma = 1.27e-3

        self._gain = self.transparency()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        state = [s.lower().strip() for s in state]
        if set(state).issubset({"free", "occupied"}):
            self._state = state
        else:
            print("Wrong state value, cannot set")

    @property
    def label(self):
        return self._label

    @property
    def length(self):
        return self._length

    @property
    def successive(self):
        return self._successive

    @successive.setter
    def successive(self, successive):
        self._successive = successive

    @property
    def amplifiers(self):
        return self._amplifiers

    @property
    def span_length(self):
        return self._span_length

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, gain):
        self._gain = gain

    @property
    def noise_figure(self):
        return self._noise_figure

    @property
    def alpha(self):
        return self._alpha

    @property
    def beta(self):
        return self._beta

    @property
    def gamma(self):
        return self._gamma

    def latency_generaion(self):
        latency = self.length/(c*2/3)   # propagation time is length/speed, speed = 2/3c
        return latency

    def noise_generation(self, lightpath):
        return self.ase_generation() + self.nli_noise(lightpath.signal_power, lightpath.rs, lightpath.df)

    def ase_generation(self):
        h = Planck
        f = 193.4e12
        bn = 12.5e9
        # db to linear
        gain = 10**(self.gain/10)
        nf = 10**(self.noise_figure/10)
        return self.amplifiers * h * f * bn * nf * (gain - 1)

    def nli_noise(self, pwr, Rs, df):
        Nch = 10
        Bn = 12.5e9
        loss = np.exp(-self.alpha/self.span_length)
        gain = 10**(self.gain/10)
        N = self.amplifiers
        eta = 16/(27*pi)*np.log(pi**2 * self.beta * Rs**2 * Nch**(2*Rs/df) / (2 * self.alpha)) * self.gamma**2 / (4 * self.alpha * self.beta*Rs**3)
        return N*(pwr**3 * loss * gain * eta * Bn)

    def propagate(self, lightpath, occupation="free"):
        latency = self.latency_generaion()
        lightpath.add_latency(latency)

        noise = self.noise_generation(lightpath)
        lightpath.add_noise(noise)

        snr = lightpath.signal_power / noise
        lightpath.update_snr(snr)

        if occupation == "occupied":
            channel = lightpath.channel
            new_state = self.state.copy()
            new_state[channel] = "occupied"
            self.state = new_state

        # node A -> line AB -> node B
        node = self.successive[lightpath.path[0]]
        lightpath = node.propagate(lightpath, occupation)
        return lightpath

    def transparency(self):
        return 10*np.log10(np.exp(self._alpha*self.span_length))
