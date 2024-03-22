import time

class buffer:
    def __init__(self):
        self.buffer = []
        self.startTime = time.time()
        self.sentInitialBurst = False

    def append(self, data):
        self.buffer.append(data)

    def pop(self, index):
        if time.time() < self.startTime + 3 and not self.sentInitialBurst:
            return b'' 
        elif time.time() > self.startTime + 3 and not self.sentInitialBurst:
            self.sentInitialBurst = True
            val = b''
            for i in range(len(self.buffer)):
                val += self.buffer.pop(index)
            return val
        if self.buffer is not None and len(self.buffer) != 0:
            return self.buffer.pop(index) 
        elif self.buffer is not None and len(self.buffer) == 0:
            print("Client has exhausted buffer.")
            
        return b''
    
    def destroy(self):
        self.buffer = None

    def length(self):
        if self.buffer is not None:
            return len(self.buffer)
        else:
            return 0
