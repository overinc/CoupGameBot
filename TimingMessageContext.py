import weakref
import threading
from APIMethods import *

class TimingMessageContext:
    def __init__(self, seconds, chatId, messageId, text, buttons, completion):
        self.totalSeconds = seconds
        self.currentSeconds = seconds
        self.chatId = chatId
        self.messageId = messageId
        self.text = text
        self.buttons = buttons
        self._completion = weakref.WeakMethod(completion)

        self.stopped = False

    def __del__(self):
        print('TimingMessageContext dealloc')

    def startAnimate(self):
        self.startTimer()

    def tickTimer(self):
        if self.stopped:
            return

        self.currentSeconds -= 1

        text = self.text + '\n' + TimingMessageContext.timingStringFor(self.totalSeconds, self.currentSeconds)

        editMessage(self.chatId, self.messageId, text, self.buttons)

        if self.currentSeconds == 0:
            self.timer = None
            self._completion()()
            return

        self.startTimer()

    def startTimer(self):
        def callback(weakTimingContext):
            timingContext = weakTimingContext()
            if timingContext is not None:
                timingContext.tickTimer()

        weakSelf = weakref.ref(self)
        self.timer = threading.Timer(1, callback, [weakSelf])
        self.timer.start()

    def stopAnimate(self):
        self.timer = None
        self.stopped = True

    @classmethod
    def timingStringFor(cls, totalCount, remainingCount):
        string = ''
        for i in range(totalCount - remainingCount):
            string += '🌕'
        for i in range(remainingCount):
            string += '🌑'
        return string