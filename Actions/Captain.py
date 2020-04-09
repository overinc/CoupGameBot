from APIMethods import *
from Constants import *
from TimingMessageContext import *
from DoubtContext import *
from Localization import *

BLOCK_STEALING_BY_AMBASSADOR = 'ambassador'
BLOCK_STEALING_BY_CAPTAIN = 'captain'
BLOCK_STEALING_NOTHING = 'nothing'

class State(Enum):
    ChooseTarget = 1
    DeclareTarget = 2
    DeclareProtect = 3

class StateMachine:
    def __init__(self):
        self.state = State.ChooseTarget

        self.transitions = {
                            State.ChooseTarget: [State.DeclareTarget],
                            State.DeclareTarget: [State.DeclareProtect],
                            }

    def applyState(self, state):
        if state in self.transitions[self.state]:
            self.state = state
            return True
        return False




class CaptainAction:

    def __init__(self, activePlayer, game, completion):
        self.activePlayer = activePlayer
        self.game = game
        self.completion = completion

        self.wantForeignAidCommonMessageId = 0

        self.timingMessageContext = None
        self.doubtContext = None

        self.targetPlayer = None

        self.stateMachine = StateMachine()

    def start(self):
        text = "У кого воровать будем?"
        buttons = []
        players = self.game.playersToSteal(self.activePlayer)
        for player in players:
            buttons.append([{'text': player.user.combinedNameStrig(),
                             'callbackData': '{}{}{}'.format(StepAction.steal.name, ACTION_DELIMETER,
                                                             player.user.userId)}])
        sendMessage(self.activePlayer.user.userId, text, buttons)

    def handleChooseTargetForStealing(self, action, chatId, userId, queryId, messageId):
        applyStateResult = self.stateMachine.applyState(State.DeclareTarget)
        if applyStateResult == False:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        answerCallbackQuery(queryId)

        targetUserId = action.split(ACTION_DELIMETER)[1]
        self.targetPlayer = self.game.findPlayerByUserId(targetUserId)

        doubtWelcomeTextTitle = '{} {}'.format(doubt_welcome_text_title_captain, self.targetPlayer.user.combinedNameStrig())

        self.doubtContext = DoubtContext(Card.Captain,
                                         self.game,
                                         self.activePlayer,
                                         StepAction.doubtActivePlayer.name,
                                         doubtWelcomeTextTitle,
                                         self.continueAction,
                                         self.completion)


        self.doubtContext.start()

    def continueAction(self):
        text = "Попытка воровства продолжается. Слово за {}".format(self.targetPlayer.user.combinedNameStrig())
        buttons = [[{'text': 'Выбрать действие', 'url': self.game.botDeeplink}]]
        sendMessage(self.game.gameGroupchatId, text, buttons)

        text = "Что будем делать?"
        buttons = []
        buttons.append([{'text': 'Прикинуться Ambassador', 'callbackData': '{}{}{}'.format(StepAction.chooseActionForBlockStealing.name, ACTION_DELIMETER, BLOCK_STEALING_BY_AMBASSADOR)}])
        buttons.append([{'text': 'Прикинуться Captain', 'callbackData': '{}{}{}'.format(StepAction.chooseActionForBlockStealing.name, ACTION_DELIMETER, BLOCK_STEALING_BY_CAPTAIN)}])
        buttons.append([{'text': 'Ничего не делать', 'callbackData': '{}{}{}'.format(StepAction.chooseActionForBlockStealing.name, ACTION_DELIMETER, BLOCK_STEALING_NOTHING)}])
        sendMessage(self.targetPlayer.user.userId, text, buttons)

    def handleChooseActionForBlockStealing(self, action, chatId, userId, queryId, messageId):
        applyStateResult = self.stateMachine.applyState(State.DeclareProtect)
        if applyStateResult == False:
            answerCallbackQuery(queryId, 'Поздно..')
            return

        answerCallbackQuery(queryId)

        protectAction = action.split(ACTION_DELIMETER)[1]

        if protectAction == BLOCK_STEALING_BY_AMBASSADOR:
            self.finishAction()
        elif protectAction == BLOCK_STEALING_BY_CAPTAIN:
            self.finishAction()
        elif protectAction == BLOCK_STEALING_NOTHING:
            self.finishAction()

    def finishAction(self):
        if self.targetPlayer.coinsCount == 1:
            self.activePlayer.addCoins(1)
        else:
            self.activePlayer.addCoins(2)

        self.targetPlayer.takeOutCoins(2)

        text = '{} не воспротивился, и {} украл у него 2 🥈монетки'.format(self.targetPlayer.user.combinedNameStrig(), self.activePlayer.user.combinedNameStrig())
        sendMessage(self.game.gameGroupchatId, text)

        self.completion()