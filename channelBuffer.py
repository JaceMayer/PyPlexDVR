import time

class channelBuffer:
    def __init__(self):
        self.buffer = []
        self.startTime = time.time()

    def append(self, data):
        self.buffer.append(data)

    def pop(self, index):
        if time.time() < self.startTime + 3:
            return b'' 
        if self.buffer != None and len(self.buffer) != 0:
            return self.buffer.pop(index)
        elif self.buffer != None and len(self.buffer) == 0:
            print("Client has exhausted buffer.")
            
        return b''
    
    def destroy(self):
        self.buffer = None

    def length(self):
        if self.buffer != None:
            return len(self.buffer)
        else:
            return 0
