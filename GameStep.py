from enum import Enum
from Bot import *
from APIMethods import *

class StepAction(Enum):
    takeCoin = 1
    tryTakeTwo = 2
    simpleShot = 3
    shuffle = 4
    snipeShot = 5
    steal = 6
    takeThreeCoins = 7

StepActions = [StepAction.takeCoin.name,
               StepAction.tryTakeTwo.name,
               StepAction.simpleShot.name,
               StepAction.shuffle.name,
               StepAction.snipeShot.name,
               StepAction.steal.name,
               StepAction.takeThreeCoins.name]


class PlayerStepState(Enum):
    Unknown = 1
    ChooseAction = 2

class PlayerStateMachine:
    def __init__(self):
        self.state = PlayerStepState.Unknown

        self.transitions = {PlayerStepState.Unknown : [PlayerStepState.Unknown, PlayerStepState.ChooseAction],
                            }

    def applyState(self, state):
        if state in self.transitions[self.state]:
            self.state = state
            return True
        return False


class PlayerStep:
    def __init__(self, game, activePlayer):
        self.game = game

        self.activePlayer = activePlayer
        self.opponentPlayer = None

        self.stateMachine = PlayerStateMachine()

        self.currentActivePersonalMessageId = 0

    def startStep(self):
        self.game.sendCurrentGameState()
        sendMessage(self.game.gameGroupchatId, 'Ход {}'.format(self.activePlayer.user.combinedNameStrig()))

        personalMessage = self.activePlayer.playerStateString('\nВаш ход!')

        buttons = []
        if self.activePlayer.coinsCount >= 10:
            buttons.append([{'text': 'Выстрелить за 7 монет', 'callbackData': '{}'.format(StepAction.simpleShot.name)}])
        else:
            buttons.append([{'text': 'Взять монетку', 'callbackData': '{}'.format(StepAction.takeCoin.name)}])
            buttons.append([{'text': 'Попытаться взять две монетки', 'callbackData': '{}'.format(StepAction.tryTakeTwo.name)}])

            if self.activePlayer.coinsCount >= 7:
                buttons.append([{'text': 'Выстрелить за 7 монет', 'callbackData': '{}'.format(StepAction.simpleShot.name)}])

            buttons.append([{'text': 'Прикинуться Ambassador', 'callbackData': '{}'.format(StepAction.shuffle.name)}])
            buttons.append([{'text': 'Прикинуться Assassin', 'callbackData': '{}'.format(StepAction.snipeShot.name)}])
            buttons.append([{'text': 'Прикинуться Captain', 'callbackData': '{}'.format(StepAction.steal.name)}])
            buttons.append([{'text': 'Прикинуться Duke', 'callbackData': '{}'.format(StepAction.takeThreeCoins.name)}])

        self.currentActivePersonalMessageId = sendMessage(self.activePlayer.user.userId, personalMessage, buttons)

    def handleStepPrimaryAction(self, action, chatId, userId, queryId, messageId):
        if self.currentActivePersonalMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        answerCallbackQuery(queryId)

        if action == StepAction.takeCoin.name:
            self.handleTakeCoinAction(chatId, userId, queryId, messageId)
        elif action == StepAction.tryTakeTwo.name:
            self.handleTryTakeTwoCoinsAction(chatId, userId, queryId, messageId)
        elif action == StepAction.simpleShot.name:
            self.handleSimpleShotAction(chatId, userId, queryId, messageId)
        elif action == StepAction.shuffle.name:
            self.handleAmbassadorAction(chatId, userId, queryId, messageId)
        elif action == StepAction.snipeShot.name:
            self.handleAssassinAction(chatId, userId, queryId, messageId)
        elif action == StepAction.steal.name:
            self.handleCaptainAction(chatId, userId, queryId, messageId)
        elif action == StepAction.takeThreeCoins.name:
            self.handleDukeAction(chatId, userId, queryId, messageId)

    def handleTakeCoinAction(self, chatId, userId, queryId, messageId):
        player = self.activePlayer
        player.coinsCount += 1

        sendMessage(self.game.gameGroupchatId, player.user.combinedNameStrig() + ' взял 💲 монетку ')
        self.endStep()

    def handleTryTakeTwoCoinsAction(self, chatId, userId, queryId, messageId):
        self.endStep()

    def handleSimpleShotAction(self, chatId, userId, queryId, messageId):
        activePlayer = self.activePlayer

        buttons = []
        for player in self.game.players:
            if player == activePlayer:
                continue
            if player.isAlive():
                buttons.append([{'text': player.user.combinedNameStrig(),
                                 'callbackData': 'simpleShotTarget|' + player.user.userId}])

        sendMessage(activePlayer.user.userId, 'В кого стрелять будем?', buttons)

    def handleAmbassadorAction(self, chatId, userId, queryId, messageId):
        self.endStep()

    def handleAssassinAction(self, chatId, userId, queryId, messageId):
        self.endStep()

    def handleCaptainAction(self, chatId, userId, queryId, messageId):
        self.endStep()

    def handleDukeAction(self, chatId, userId, queryId, messageId):
        self.endStep()



    def endStep(self):
        self.currentActivePersonalMessageId = 0

        self.game.endPlayerStep()

