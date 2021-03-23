import numpy as np

class Memory:
    
    def __init__(self, max_memory):
        self._max_memory = max_memory
        self._samples = []
    
    def add_sample(self, sample):
        self._samples.append(sample)
        if (len(self._samples) > self._max_memory):
            self._samples.pop(0)
    
    def sample(self, num_samples):
        return [
            self._samples[index] 
            for index in np.random.choice(len(self._samples),
                                          min(num_samples, 
                                              len(self._samples)))
        ]
