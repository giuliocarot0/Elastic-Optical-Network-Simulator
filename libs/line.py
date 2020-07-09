from scipy.constants import c
from .signal import SignalInformation


class Line(object):
    def __init__(self, line_dict): # creating a line with a default number of channel equal to 10
        self._label = line_dict['label']
        self._length = line_dict['length']
        self._successive = {}
        self._state = ["free"]*10

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

    def latency_generaion(self):
        latency = self.length/(c*2/3)   # propagation time is length/speed, speed = 2/3c
        return latency

    def noise_generation(self, signal_power):
        noise = signal_power / (2*self.length)
        return noise

    def propagate(self, lightpath, occupation="free"):
        latency = self.latency_generaion()
        lightpath.add_latency(latency)

        signal_power = lightpath.signal_power
        noise = self.noise_generation(signal_power)
        lightpath.add_noise(noise)

        if occupation == "occupied":
            channel = lightpath.channel
            new_state = self.state.copy()
            new_state[channel] = "occupied"
            self.state = new_state

        # node A -> line AB -> node B
        node = self.successive[lightpath.path[0]]
        lightpath = node.propagate(lightpath, occupation)
        return lightpath
