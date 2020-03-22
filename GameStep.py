from enum import Enum
from bot import *
from APIMethods import *

class StepAction(Enum):
    takeCoin = 1
    tryTakeTwo = 2
    simpleShot = 3
    shuffle = 4
    snipeShot = 5
    steal = 6
    takeThreeCoins = 7

    chooseCardToOpen = 11


StepPrimaryActions = [StepAction.takeCoin.name,
                      StepAction.tryTakeTwo.name,
                      StepAction.simpleShot.name,
                      StepAction.shuffle.name,
                      StepAction.snipeShot.name,
                      StepAction.steal.name,
                      StepAction.takeThreeCoins.name]

ACTION_DELIMETER = '|'

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
        self.targetPlayer = None

        self.stateMachine = PlayerStateMachine()

        self.currentActivePlayerPersonalMessageId = 0
        self.currentTargetPlayerPersonalMessageId = 0

    def startStep(self):
        self.game.sendCurrentGameState()
        sendMessage(self.game.gameGroupchatId, 'Ход {}'.format(self.activePlayer.user.combinedNameStrig()))

        personalMessage = self.activePlayer.playerStateString('\nВаш ход!', True)

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

        self.currentActivePlayerPersonalMessageId = sendMessage(self.activePlayer.user.userId, personalMessage, buttons)

    def handleStepPrimaryAction(self, action, chatId, userId, queryId, messageId):
        if userId != self.activePlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return

        if self.currentActivePlayerPersonalMessageId != messageId:
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
        player.addCoins(10)

        sendMessage(self.game.gameGroupchatId, player.user.combinedNameStrig() + ' взял 💲 монетку ')
        self.endStep()

    def handleTryTakeTwoCoinsAction(self, chatId, userId, queryId, messageId):
        self.endStep()

    def handleSimpleShotAction(self, chatId, userId, queryId, messageId):
        activePlayer = self.activePlayer

        buttons = []
        for player in self.game.players:
            if player == activePlayer:
                if len(self.game.players) >= 2: # для дебаг игры с самим собой
                    continue
            if player.isAlive():
                buttons.append([{'text': player.user.combinedNameStrig(),
                                 'callbackData': '{}{}{}'.format(StepAction.simpleShot.name, ACTION_DELIMETER, player.user.userId)}])

        self.currentActivePlayerPersonalMessageId = sendMessage(activePlayer.user.userId, 'В кого стрелять будем?', buttons)

    def handleAmbassadorAction(self, chatId, userId, queryId, messageId):
        self.endStep()

    def handleAssassinAction(self, chatId, userId, queryId, messageId):
        self.endStep()

    def handleCaptainAction(self, chatId, userId, queryId, messageId):
        self.endStep()

    def handleDukeAction(self, chatId, userId, queryId, messageId):
        self.endStep()


    def handleStepComplexAction(self, action, chatId, userId, queryId, messageId):
        actionType = action.split(ACTION_DELIMETER)[0]

        if actionType == StepAction.simpleShot.name:
            self.handleSimpleShotChooseTarget(action, chatId, userId, queryId, messageId)
        elif actionType == StepAction.chooseCardToOpen.name:
            self.handleChooseCardToOpen(action, chatId, userId, queryId, messageId)

    def handleSimpleShotChooseTarget(self, action, chatId, userId, queryId, messageId):
        if userId != self.activePlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return

        if self.currentActivePlayerPersonalMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        answerCallbackQuery(queryId)

        targetUserId = action.split(ACTION_DELIMETER)[1]
        targetPlayer = self.game.getPlayerByUserId(targetUserId)
        self.targetPlayer = targetPlayer

        self.activePlayer.takeOutCoins(7)

        commonText = self.activePlayer.user.combinedNameStrig() + '\n'
        commonText += '🔫 выстерил в:' + '\n'
        commonText += targetPlayer.user.combinedNameStrig() + '\n'

        if targetPlayer.cardsCount() == 2:
            sendMessage(self.game.gameGroupchatId, commonText)

            buttons = []
            for card in targetPlayer.cards:
                buttons.append([{'text': card.name(), 'callbackData': '{}{}{}'.format(StepAction.chooseCardToOpen.name, ACTION_DELIMETER, card.name())}])
            self.currentTargetPlayerPersonalMessageId = sendMessage(targetPlayer.user.userId, 'Вас подстрелили 🏹\nКакую карту откроем?', buttons)


        elif targetPlayer.cardsCount() == 1:
            card = targetPlayer.killOneCard()
            commonText += 'и добил его 💀' + '\n'
            commonText += '❌ ' + card.openedString()
            sendMessage(self.game.gameGroupchatId, commonText)
            self.endStep()


    def handleChooseCardToOpen(self, action, chatId, userId, queryId, messageId):
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

        self.endStep()


    def endStep(self):
        self.game.endPlayerStep()

