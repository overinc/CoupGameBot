
import threading
from APIMethods import *

class TimingMessageContext:
    def __init__(self, seconds, chatId, messageId, text, buttons, callback):
        self.totalSeconds = seconds
        self.currentSeconds = seconds
        self.chatId = chatId
        self.messageId = messageId
        self.text = text
        self.buttons = buttons
        self.callback = callback

        self.stopped = False

    def startAnimate(self):
        t = threading.Timer(1, self.tickTimer)
        t.start()

    def tickTimer(self):
        if self.stopped:
            return

        self.currentSeconds -= 1

        text = self.text + '\n' + TimingMessageContext.timingStringFor(self.totalSeconds, self.currentSeconds)

        editMessage(self.chatId, self.messageId, text, self.buttons)

        if self.currentSeconds == 0:
            self.callback()
            return

        t = threading.Timer(1, self.tickTimer)
        t.start()

    def stopAnimate(self):
        self.stopped = True

    @classmethod
    def timingStringFor(cls, totalCount, remainingCount):
        string = ''
        for i in range(totalCount - remainingCount):
            string += '🌕'
        for i in range(remainingCount):
            string += '🌑'
        return string