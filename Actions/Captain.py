import weakref
from APIMethods import *
from Constants import *
from DoubtContext import *
from Localization import *

BLOCK_STEALING_BY_AMBASSADOR = 'ambassador'
BLOCK_STEALING_BY_CAPTAIN = 'captain'
BLOCK_STEALING_NOTHING = 'nothing'

class State(Enum):
    ChooseTarget = 1
    DeclareTarget = 2
    DeclareProtect = 3
    DoubtProtect = 4

class StateMachine:
    def __init__(self):
        self.state = State.ChooseTarget

        self.transitions = {
                            State.ChooseTarget: [State.DeclareTarget],
                            State.DeclareTarget: [State.DeclareProtect],
                            State.DeclareProtect: [State.DoubtProtect],
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
        self._completion = weakref.WeakMethod(completion)

        self.doubtContext = None

        self.targetPlayer = None

        self.stateMachine = StateMachine()

    def __del__(self):
        print('CaptainAction dealloc')

    def start(self):
        text = "У кого воровать будем?"
        buttons = []
        players = self.game.playersToSteal(self.activePlayer)
        for player in players:
            buttons.append([{'text': player.user.rawNameStrig(),
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
                                         self._completion())


        self.doubtContext.start()

    def continueAction(self):
        self.doubtContext = None

        text = "Попытка воровства продолжается. Слово за {}".format(self.targetPlayer.user.combinedNameStrig())
        buttons = [[{'text': 'Выбрать действие', 'url': self.game.botDeeplink}]]
        sendMessage(self.game.gameGroupchatId, text, buttons)

        text = "У вас ворует монетки Captain. Что будем делать?"
        buttons = []
        buttons.append([{'text': '{} Ambassador'.format(use_card_text if self.targetPlayer.hasCardByName(Card.Ambassador.name) else morph_card_text),
                         'callbackData': '{}{}{}'.format(StepAction.chooseActionForBlockStealing.name, ACTION_DELIMETER, BLOCK_STEALING_BY_AMBASSADOR)}])
        buttons.append([{'text': '{} Captain'.format(use_card_text if self.targetPlayer.hasCardByName(Card.Captain.name) else morph_card_text),
                         'callbackData': '{}{}{}'.format(StepAction.chooseActionForBlockStealing.name, ACTION_DELIMETER, BLOCK_STEALING_BY_CAPTAIN)}])
        buttons.append([{'text': 'Ничего не делать',
                         'callbackData': '{}{}{}'.format(StepAction.chooseActionForBlockStealing.name, ACTION_DELIMETER, BLOCK_STEALING_NOTHING)}])
        sendMessage(self.targetPlayer.user.userId, text, buttons)

    def handleChooseActionForBlockStealing(self, action, chatId, userId, queryId, messageId):
        applyStateResult = self.stateMachine.applyState(State.DeclareProtect)
        if applyStateResult == False:
            answerCallbackQuery(queryId, 'Поздно..')
            return

        answerCallbackQuery(queryId)

        protectAction = action.split(ACTION_DELIMETER)[1]

        if protectAction == BLOCK_STEALING_BY_AMBASSADOR or protectAction == BLOCK_STEALING_BY_CAPTAIN:
            self.tryBlockAction(protectAction)
        elif protectAction == BLOCK_STEALING_NOTHING:
            self.finishAction()

    def tryBlockAction(self, blockType):
        card = None
        doubtWelcomeTextTitle = ''
        if blockType == BLOCK_STEALING_BY_AMBASSADOR:
            card = Card.Ambassador
            doubtWelcomeTextTitle = doubt_welcome_text_title_captain_blocker_by_ambassador
        elif blockType == BLOCK_STEALING_BY_CAPTAIN:
            card = Card.Captain
            doubtWelcomeTextTitle = doubt_welcome_text_title_captain_blocker_by_captain

        self.doubtContext = DoubtContext(card,
                                         self.game,
                                         self.targetPlayer,
                                         StepAction.doubtSecondaryPlayer.name,
                                         doubtWelcomeTextTitle,
                                         self.blockSuccessAction,
                                         self.finishAction)

        self.doubtContext.start()

    def handleSomeoneDoubtSecondaryPlayer(self, action, chatId, userId, queryId, messageId):
        if not DEBUG_MODE:
            if userId == self.targetPlayer.user.userId:
                answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
                return

        applyStateResult = self.stateMachine.applyState(State.DoubtProtect)
        if applyStateResult == False:
            answerCallbackQuery(queryId, 'Поздно..')
            return

        self.doubtContext.handleSomeoneDoubtActivePlayer(action, chatId, userId, queryId, messageId)

    def blockSuccessAction(self):
        text = '{} заблокировал кражу'.format(self.targetPlayer.user.combinedNameStrig())
        sendMessage(self.game.gameGroupchatId, text)

        self._completion()()

    def finishAction(self):
        if self.targetPlayer.coinsCount == 1:
            self.activePlayer.addCoins(1)
        else:
            self.activePlayer.addCoins(2)

        self.targetPlayer.takeOutCoins(2)

        text = ''
        activePlayerName = self.activePlayer.user.combinedNameStrig()
        targetPlayerName = self.targetPlayer.user.combinedNameStrig()
        if self.stateMachine.state ==  State.DeclareProtect:
            text = '{} не воспротивился, и {} украл у него 2 🥈монетки'.format(targetPlayerName, activePlayerName)
        elif self.stateMachine.state ==  State.DoubtProtect:
            text = '{} попытался заблокировать кражу, но его уличили, и {} украл у него 2 🥈монетки'.format(targetPlayerName, activePlayerName)

        sendMessage(self.game.gameGroupchatId, text)

        self._completion()()