import time

from config import dvrConfig


# The client channel buffer
class buffer:
    def __init__(self):
        self.__buffer = []
        self.__startTime = time.time()
        self.__sentInitialBurst = False

    # Used by the channel to append data to the clients buffer
    def append(self, data):
        self.__buffer.append(data)

    def getAndFlushBuffer(self):
        val = b''.join(self.__buffer)
        self.__buffer = []
        return val

    def pop(self, index):
        if time.time() < self.__startTime + dvrConfig["Client"]['initalBufferTime'] and not self.__sentInitialBurst:
            return b''
        elif time.time() > self.__startTime + dvrConfig["Client"]['initalBufferTime'] and not self.__sentInitialBurst:
            self.__sentInitialBurst = True
            return self.getAndFlushBuffer()
        if self.__buffer is not None and len(self.__buffer) != 0:
            if len(self.__buffer) > dvrConfig["Client"]['maxBufferSize']:
                return self.getAndFlushBuffer()
            return self.__buffer.pop(index)

        return b''

    def destroy(self):
        self.__buffer = None

    def length(self):
        if self.__buffer is not None:
            return len(self.__buffer)
        else:
            return 0
