class channelBuffer:
    def __init__(self):
        self.buffer = []

    def append(self, data):
        self.buffer.append(data)

    def pop(self, index):
        if self.buffer != None and len(self.buffer) != 0:
            return self.buffer.pop(index)
        else:
            return b''
    
    def destroy(self):
        self.buffer = None

    def length(self):
        if self.buffer != None:
            return len(self.buffer)
        else:
            return 0
