from APIMethods import *
from Constants import *
from TimingMessageContext import *
from DoubtContext import *
from Localization import *

class State(Enum):
    WantForeignAid = 1
    TryBlock = 2
    DoubtBlocker = 3

class StateMachine:
    def __init__(self):
        self.state = State.WantForeignAid

        self.transitions = {
                            State.WantForeignAid: [State.TryBlock],
                            State.TryBlock: [State.DoubtBlocker],
                            }

    def applyState(self, state):
        if state in self.transitions[self.state]:
            self.state = state
            return True
        return False




class ForeignAidAction:

    def __init__(self, activePlayer, game, completion):
        self.activePlayer = activePlayer
        self.game = game
        self.completion = completion

        self.wantForeignAidCommonMessageId = 0

        self.timingMessageContext = None
        self.doubtContext = None

        self.dukedPlayer = None

        self.stateMachine = StateMachine()

    def __del__(self):
        print('ForeignAidAction dealloc')

    def start(self):
        baseText = self.foreignAidAWelcomeText()
        buttons = [[{'text': 'Я блокирую',
                     'callbackData': StepAction.tryBlockForeignAid.name}]]

        text = baseText + '\n' + TimingMessageContext.timingStringFor(DOUBT_TIMER, DOUBT_TIMER)

        self.wantForeignAidCommonMessageId = sendMessage(self.game.gameGroupchatId, text, buttons)

        self.timingMessageContext = TimingMessageContext(DOUBT_TIMER, self.game.gameGroupchatId,
                                                         self.wantForeignAidCommonMessageId, baseText, buttons,
                                                         self.handleTimerEnd)
        self.timingMessageContext.startAnimate()

    def handleTimerEnd(self):
        self.endActionWithSuccess()

    def handleSomeoneTryBlockForeignAid(self, action, chatId, userId, queryId, messageId):

        applyStateResult = self.stateMachine.applyState(State.TryBlock)
        if applyStateResult == False:
            answerCallbackQuery(queryId, 'Поздно..')
            return
        if self.wantForeignAidCommonMessageId != messageId:
            answerCallbackQuery(queryId, 'Поздно..')
            return

        answerCallbackQuery(queryId)

        self.timingMessageContext.stopAnimate()
        self.wantForeignAidCommonMessageId = 0

        activePlayer = self.activePlayer
        dukedPlayer = self.game.findPlayerByUserId(userId)
        self.dukedPlayer = dukedPlayer

        self.doubtContext = DoubtContext(Card.Duke,
                                         self.game,
                                         dukedPlayer,
                                         StepAction.doubtSecondaryPlayer.name,
                                         doubt_welcome_text_title_foreign_aid_blocker,
                                         self.endActionWithBlocked,
                                         self.endActionWithSuccess)
        self.doubtContext.start()

    def handleSomeoneDoubtSecondaryPlayer(self, action, chatId, userId, queryId, messageId):
        if not DEBUG_MODE:
            if userId == self.dukedPlayer.user.userId:
                answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
                return

        applyStateResult = self.stateMachine.applyState(State.DoubtBlocker)
        if applyStateResult == False:
            answerCallbackQuery(queryId, 'Поздно..')
            return

        self.doubtContext.handleSomeoneDoubtActivePlayer(action, chatId, userId, queryId, messageId)





    def endActionWithBlocked(self):
        sendMessage(self.game.gameGroupchatId, '{} заблокировал взятие монеток'.format(self.dukedPlayer.user.combinedNameStrig()))

        self.completion()

    def endActionWithSuccess(self):
        self.activePlayer.addCoins(2)

        sendMessage(self.game.gameGroupchatId, self.activePlayer.user.combinedNameStrig() + ' взял 2 🥈монетки')

        self.completion()




    def foreignAidAWelcomeText(self):
        userName = self.activePlayer.user.combinedNameStrig()

        text = '{} хочет взять 2 монеты🥈 из колоды'.format(userName)

        text += '\nКто хочет прикинуться Duke и заблокировать?\n\n'
        text += 'У вас есть на это {} секунд'.format(DOUBT_TIMER)
        return text
