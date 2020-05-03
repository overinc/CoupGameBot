from APIMethods import *
from Constants import *
from DoubtContext import *
from Localization import *

BLOCK_SNIPE_SHOT_BY_CONTESSA = 'contessa'
BLOCK_SNIPE_SHOT_NOTHING = 'nothing'

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


class AssassinAction:

    def __init__(self, activePlayer, game, completion):
        self.activePlayer = activePlayer
        self.game = game
        self.completion = completion

        self.doubtContext = None

        self.targetPlayer = None

        self.stateMachine = StateMachine()

    def __del__(self):
        print('AssassinAction dealloc')

    def start(self):
        text = "В кого стрелять будем?"

        buttons = []
        players = self.game.playersToShot(self.activePlayer)
        for player in players:
            buttons.append([{'text': player.user.rawNameStrig(),
                             'callbackData': '{}{}{}'.format(StepAction.snipeShot.name, ACTION_DELIMETER,
                                                             player.user.userId)}])
        sendMessage(self.activePlayer.user.userId, text, buttons)

    def handleChooseTargetForSnipeShot(self, action, chatId, userId, queryId, messageId):
        applyStateResult = self.stateMachine.applyState(State.DeclareTarget)
        if applyStateResult == False:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        answerCallbackQuery(queryId)

        targetUserId = action.split(ACTION_DELIMETER)[1]
        self.targetPlayer = self.game.findPlayerByUserId(targetUserId)

        self.activePlayer.takeOutCoins(3)

        doubtWelcomeTextTitle = '{} {}'.format(doubt_welcome_text_title_assassin,
                                               self.targetPlayer.user.combinedNameStrig())

        self.doubtContext = DoubtContext(Card.Assassin,
                                         self.game,
                                         self.activePlayer,
                                         StepAction.doubtActivePlayer.name,
                                         doubtWelcomeTextTitle,
                                         self.continueAction,
                                         self.completion)

        self.doubtContext.start()

    def continueAction(self):
        self.doubtContext = None

        text = "Стрельба продолжается. Слово за {}".format(self.targetPlayer.user.combinedNameStrig())
        buttons = [[{'text': 'Выбрать действие', 'url': self.game.botDeeplink}]]
        sendMessage(self.game.gameGroupchatId, text, buttons)

        text = "В вас стреляет Assasin. Что будем делать?"
        buttons = []
        buttons.append([{'text': '{} Contessa'.format(use_card_text if self.targetPlayer.hasCardByName(Card.Contessa.name) else morph_card_text),
                         'callbackData': '{}{}{}'.format(StepAction.chooseActionForBlockSnipeShot.name, ACTION_DELIMETER,
                                                         BLOCK_SNIPE_SHOT_BY_CONTESSA)}])

        buttons.append([{'text': 'Ничего не делать',
                         'callbackData': '{}{}{}'.format(StepAction.chooseActionForBlockSnipeShot.name, ACTION_DELIMETER,
                                                         BLOCK_SNIPE_SHOT_NOTHING)}])
        sendMessage(self.targetPlayer.user.userId, text, buttons)

    def handleChooseActionForBlockSnipeShot(self, action, chatId, userId, queryId, messageId):
        applyStateResult = self.stateMachine.applyState(State.DeclareProtect)
        if applyStateResult == False:
            answerCallbackQuery(queryId, 'Поздно..')
            return

        answerCallbackQuery(queryId)

        protectAction = action.split(ACTION_DELIMETER)[1]

        if protectAction == BLOCK_SNIPE_SHOT_BY_CONTESSA:
            self.tryBlockAction()
        elif protectAction == BLOCK_SNIPE_SHOT_NOTHING:
            self.processSnipeShot()

    def tryBlockAction(self):
        self.doubtContext = DoubtContext(Card.Contessa,
                                         self.game,
                                         self.targetPlayer,
                                         StepAction.doubtSecondaryPlayer.name,
                                         doubt_welcome_text_title_assassin_blocker_by_contessa,
                                         self.blockSuccessAction,
                                         self.processSnipeShot)

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
        text = '{} заблокировал 🔫выстрел, а {} потерял 3 монеты🥉'.format(self.targetPlayer.user.combinedNameStrig(),
                                                                         self.activePlayer.user.combinedNameStrig())
        sendMessage(self.game.gameGroupchatId, text)

        self.completion()

    def processSnipeShot(self):

        if self.targetPlayer.isDead():
            self.completion()
            return

        activePlayerName = self.activePlayer.user.combinedNameStrig()
        targetPlayerName = self.targetPlayer.user.combinedNameStrig()

        if self.stateMachine.state == State.DeclareProtect:
            text = '{} не воспротивился, и {} выстрелил в него за 3 монетки'.format(targetPlayerName, activePlayerName)

            if self.targetPlayer.cardsCount() == 2:
                text += '\nТеперь он вскрывает одну карту'
                sendMessage(self.game.gameGroupchatId, text)

                buttons = []
                for card in self.targetPlayer.cards:
                    buttons.append([{'text': card.name,
                                     'callbackData': '{}{}{}'.format(StepAction.chooseCardToOpenByKill.name,
                                                                     ACTION_DELIMETER, card.name)}])
                self.currentTargetPlayerPersonalMessageId = sendMessage(self.targetPlayer.user.userId,
                                                                        'Вас подстрелили 🏹\nКакую карту откроем?',
                                                                        buttons)

            elif self.targetPlayer.cardsCount() == 1:
                card = self.targetPlayer.killOneCard()
                text += 'и добил💀 его\n'
                text += '❌ ' + card.openedString()
                sendMessage(self.game.gameGroupchatId, text)

                self.game.onPlayerDead(self.targetPlayer)

                self.completion()
        elif self.stateMachine.state == State.DoubtProtect:
            card = self.targetPlayer.killOneCard()
            text = '{} попытался заблокировать выстрел, но его уличили, и {} добил💀 его выстрелом\n'.format(
                targetPlayerName, activePlayerName)
            text += '❌ ' + card.openedString()
            sendMessage(self.game.gameGroupchatId, text)

            self.game.onPlayerDead(self.targetPlayer)

            self.completion()

    def handleChooseCardToOpenByKill(self, action, chatId, userId, queryId, messageId):
        if userId != self.targetPlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return

        if self.currentTargetPlayerPersonalMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        answerCallbackQuery(queryId)

        choosenCardName = action.split(ACTION_DELIMETER)[1]
        self.targetPlayer.killCardByName(choosenCardName)

        sendMessage(self.game.gameGroupchatId, '{}\nоткрыл ❌ {}'.format(self.targetPlayer.user.combinedNameStrig(), choosenCardName))

        self.completion()