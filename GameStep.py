import threading
from Entities import *
from bot import *
from APIMethods import *
from Constants import *
from Entities import *
from TimingMessageContext import *
from Roles.Ambassador import *

StepPrimaryActions = [StepAction.takeCoin.name,
                      StepAction.tryTakeTwo.name,
                      StepAction.simpleShot.name,
                      StepAction.shuffle.name,
                      StepAction.snipeShot.name,
                      StepAction.steal.name,
                      StepAction.takeThreeCoins.name]

class PlayerStepState(Enum):
    Unknown = 1
    ChooseAction = 2
    DeclarateAction = 3
    Doubt = 4
    InterruptAction = 4
    LoseDoubt = 5
    MakeAction = 6
    Protect = 7
    DoubtProtect = 8


class PlayerStateMachine:
    def __init__(self):
        self.state = PlayerStepState.Unknown

        self.transitions = {PlayerStepState.Unknown : [PlayerStepState.ChooseAction],
                            PlayerStepState.ChooseAction: [PlayerStepState.DeclarateAction, PlayerStepState.MakeAction],
                            PlayerStepState.DeclarateAction: [PlayerStepState.Doubt, PlayerStepState.MakeAction],
                            PlayerStepState.Doubt: [PlayerStepState.LoseDoubt, PlayerStepState.InterruptAction],
                            PlayerStepState.LoseDoubt: [PlayerStepState.MakeAction],
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
        self.doubtedPlayer = None

        self.stateMachine = PlayerStateMachine()

        self.activePlayerAction = None

        self.currentActivePlayerPersonalMessageId = 0
        self.currentTargetPlayerPersonalMessageId = 0
        self.doubtActivePlayerCommonMessageId = 0
        self.currentDoubtedPlayerPersonalMessageId = 0



    def startStep(self):
        self.game.sendCurrentGameState()

        buttons = [[{'text': 'Ходить', 'url': self.game.botDeeplink}]]
        sendMessage(self.game.gameGroupchatId, 'Ход {}'.format(self.activePlayer.user.combinedNameStrig()), buttons)

        personalMessage = self.activePlayer.playerStateString('\nВаш ход!', True)

        buttons = []
        if self.activePlayer.coinsCount >= 10:
            buttons.append([{'text': 'Выстрелить за 7 монет', 'callbackData': '{}'.format(StepAction.simpleShot.name)}])
        else:
            buttons.append([{'text': 'Взять монетку', 'callbackData': '{}'.format(StepAction.takeCoin.name)}])
            buttons.append([{'text': 'Попытаться взять 2 монетки', 'callbackData': '{}'.format(StepAction.tryTakeTwo.name)}])

            if self.activePlayer.coinsCount >= 7:
                buttons.append([{'text': 'Выстрелить за 7 монет', 'callbackData': '{}'.format(StepAction.simpleShot.name)}])

            buttons.append([{'text': 'Прикинуться Ambassador\nи порыться в колоде', 'callbackData': '{}'.format(StepAction.shuffle.name)}])
            if self.activePlayer.coinsCount >= 3:
                buttons.append([{'text': 'Прикинуться Assassin\nи пальнуть за 3 монетки', 'callbackData': '{}'.format(StepAction.snipeShot.name)}])
            buttons.append([{'text': 'Прикинуться Captain\nи украсть две 2 монетки', 'callbackData': '{}'.format(StepAction.steal.name)}])
            buttons.append([{'text': 'Прикинуться Duke\nи взять 3 монетки', 'callbackData': '{}'.format(StepAction.takeThreeCoins.name)}])

        self.currentActivePlayerPersonalMessageId = sendMessage(self.activePlayer.user.userId, personalMessage, buttons)

        self.stateMachine.applyState(PlayerStepState.ChooseAction)




    def handleStepPrimaryAction(self, action, chatId, userId, queryId, messageId):
        if userId != self.activePlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return

        if self.currentActivePlayerPersonalMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        # answerCallbackQuery(queryId)

        self.currentActivePlayerPersonalMessageId = 0

        if action == StepAction.takeCoin.name:
            answerCallbackQuery(queryId, '', self.game.groupchatDeeplink)
            self.handleTakeCoinAction(chatId, userId, queryId, messageId)
        elif action == StepAction.tryTakeTwo.name:
            answerCallbackQuery(queryId, '', self.game.groupchatDeeplink)
            self.handleTryTakeTwoCoinsAction(chatId, userId, queryId, messageId)
        elif action == StepAction.simpleShot.name:
            answerCallbackQuery(queryId)
            self.handleSimpleShotAction(chatId, userId, queryId, messageId)
        elif action == StepAction.shuffle.name:
            answerCallbackQuery(queryId, '', self.game.groupchatDeeplink)
            self.handleAmbassadorAction(chatId, userId, queryId, messageId)
        elif action == StepAction.snipeShot.name:
            answerCallbackQuery(queryId)
            self.handleAssassinAction(chatId, userId, queryId, messageId)
        elif action == StepAction.steal.name:
            answerCallbackQuery(queryId, '', self.game.groupchatDeeplink)
            self.handleCaptainAction(chatId, userId, queryId, messageId)
        elif action == StepAction.takeThreeCoins.name:
            answerCallbackQuery(queryId, '', self.game.groupchatDeeplink)
            self.handleDukeAction(chatId, userId, queryId, messageId)

    def handleTakeCoinAction(self, chatId, userId, queryId, messageId):
        self.stateMachine.applyState(PlayerStepState.MakeAction)

        activePlayer = self.activePlayer
        activePlayer.addCoins(1)

        sendMessage(self.game.gameGroupchatId, activePlayer.user.combinedNameStrig() + ' взял 🥇 монетку ')
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
        self.stateMachine.applyState(PlayerStepState.DeclarateAction)

        self.activePlayerAction = Card.Ambassador

        activePlayer = self.activePlayer
        baseText = '{} заявляет, что он Ambassador и хочет порыться📚 в колоде\nКто хочет усомниться?\n\n'.format(
            activePlayer.user.combinedNameStrig())
        baseText += 'У вас есть на это {} секунд'.format(DOUBT_TIMER)
        buttons = [[{'text': 'Я усомняюсь',
                     'callbackData': '{}{}{}'.format(StepAction.doubtActivePlayer.name, ACTION_DELIMETER, 'Duke')}]]

        text = baseText + '\n' + TimingMessageContext.timingStringFor(DOUBT_TIMER, DOUBT_TIMER)

        self.doubtActivePlayerCommonMessageId = sendMessage(self.game.gameGroupchatId, text, buttons)

        self.timingMessageContext = TimingMessageContext(DOUBT_TIMER, self.game.gameGroupchatId,
                                                         self.doubtActivePlayerCommonMessageId, baseText, buttons,
                                                         self.continueAction)
        self.timingMessageContext.startAnimate()

    def handleAssassinAction(self, chatId, userId, queryId, messageId):
        self.endStep()

    def handleCaptainAction(self, chatId, userId, queryId, messageId):
        self.endStep()

    def handleDukeAction(self, chatId, userId, queryId, messageId):
        self.stateMachine.applyState(PlayerStepState.DeclarateAction)

        self.activePlayerAction = Card.Duke

        activePlayer = self.activePlayer
        baseText = '{} заявляет, что он Duke и хочет взять 3 монеты🥉\nКто хочет усомниться?\n\n'.format(activePlayer.user.combinedNameStrig())
        baseText += 'У вас есть на это {} секунд'.format(DOUBT_TIMER)
        buttons = [[{'text': 'Я усомняюсь', 'callbackData': '{}{}{}'.format(StepAction.doubtActivePlayer.name, ACTION_DELIMETER, 'Duke')}]]

        text = baseText + '\n' + TimingMessageContext.timingStringFor(DOUBT_TIMER, DOUBT_TIMER)

        self.doubtActivePlayerCommonMessageId = sendMessage(self.game.gameGroupchatId, text, buttons)

        self.timingMessageContext = TimingMessageContext(DOUBT_TIMER, self.game.gameGroupchatId,
                                                         self.doubtActivePlayerCommonMessageId, baseText, buttons, self.continueAction)
        self.timingMessageContext.startAnimate()






    def handleStepComplexAction(self, action, chatId, userId, queryId, messageId):
        actionType = action.split(ACTION_DELIMETER)[0]

        if actionType == StepAction.simpleShot.name:
            self.handleSimpleShotChooseTarget(action, chatId, userId, queryId, messageId)
        elif actionType == StepAction.chooseCardToOpenByKill.name:
            self.handleChooseCardToOpenByKill(action, chatId, userId, queryId, messageId)
        elif actionType == StepAction.doubtActivePlayer.name:
            self.handleSomeoneDoubtActivePlayer(action, chatId, userId, queryId, messageId)
        elif actionType == StepAction.chooseCardToOpenByDoubt.name:
            self.handleChooseCardToOpenByDoubt(action, chatId, userId, queryId, messageId)
        elif actionType == StepAction.chooseCardForAmbassadoring.name:
            self.handleChooseCardForAmbassadoring(action, chatId, userId, queryId, messageId)

    def handleSimpleShotChooseTarget(self, action, chatId, userId, queryId, messageId):
        if userId != self.activePlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return

        if self.currentActivePlayerPersonalMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        answerCallbackQuery(queryId, '', self.game.groupchatDeeplink)

        self.stateMachine.applyState(PlayerStepState.MakeAction)

        targetUserId = action.split(ACTION_DELIMETER)[1]
        targetPlayer = self.game.findPlayerByUserId(targetUserId)
        self.targetPlayer = targetPlayer

        self.activePlayer.takeOutCoins(7)

        commonText = self.activePlayer.user.combinedNameStrig() + '\n'
        commonText += '🔫 выстрелил в:' + '\n'
        commonText += targetPlayer.user.combinedNameStrig() + '\n'

        if targetPlayer.cardsCount() == 2:
            sendMessage(self.game.gameGroupchatId, commonText)
            buttons = []
            for card in targetPlayer.cards:
                buttons.append([{'text': card.name(), 'callbackData': '{}{}{}'.format(StepAction.chooseCardToOpenByKill.name, ACTION_DELIMETER, card.name())}])
            self.currentTargetPlayerPersonalMessageId = sendMessage(targetPlayer.user.userId, 'Вас подстрелили 🏹\nКакую карту откроем?', buttons)

        elif targetPlayer.cardsCount() == 1:
            card = targetPlayer.killOneCard()
            commonText += 'и добил его 💀' + '\n'
            commonText += '❌ ' + card.openedString()
            sendMessage(self.game.gameGroupchatId, commonText)
            self.endStep()


    def handleChooseCardToOpenByKill(self, action, chatId, userId, queryId, messageId):
        if userId != self.targetPlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return

        if self.currentTargetPlayerPersonalMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        answerCallbackQuery(queryId)

        self.currentTargetPlayerPersonalMessageId = 0

        choosenCardName = action.split(ACTION_DELIMETER)[1]
        self.targetPlayer.killCardByName(choosenCardName)

        sendMessage(self.game.gameGroupchatId, '{}\nоткрыл ❌ {}'.format(self.targetPlayer.user.combinedNameStrig(), choosenCardName))

        self.endStep()

    def handleSomeoneDoubtActivePlayer(self, action, chatId, userId, queryId, messageId):
        # if userId == self.activePlayer.user.userId:
        #     answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
        #     return

        if self.doubtActivePlayerCommonMessageId != messageId:
            answerCallbackQuery(queryId, 'Поздно..')
            return

        if not self.stateMachine.applyState(PlayerStepState.Doubt):
            answerCallbackQuery(queryId, 'Поздно..')
            return

        answerCallbackQuery(queryId)

        self.timingMessageContext.stopAnimate()

        self.doubtActivePlayerCommonMessageId = 0

        doubtCardName = action.split(ACTION_DELIMETER)[1]
        doubtedPlayer = self.game.findPlayerByUserId(userId)
        self.doubtedPlayer = doubtedPlayer

        commonText = doubtedPlayer.user.combinedNameStrig() + '\n'
        commonText += 'усомнился '
        # commonText += 'усомнился в\n'
        # commonText += self.activePlayer.user.combinedNameStrig() + '\n'

        if self.activePlayer.hasCardByName(doubtCardName):

            commonText += 'и оказался не прав!'
            commonText += '\n\n'

            self.game.returnPlayerCardAndGetNew(self.activePlayer, doubtCardName)

            sendMessage(self.activePlayer.user.userId, self.activePlayer.playerCardsString())

            if doubtedPlayer.cardsCount() == 2:
                self.stateMachine.applyState(PlayerStepState.LoseDoubt)


                commonText += '{} вскрывает одну карту'.format(doubtedPlayer.user.combinedNameStrig()) + '\n\n'
                commonText += 'A {} утратил {} и взял новую карту из колоды'.format(self.activePlayer.user.combinedNameStrig(), doubtCardName)
                sendMessage(self.game.gameGroupchatId, commonText)

                buttons = []
                for card in doubtedPlayer.cards:
                    buttons.append([{'text': card.name(),
                                     'callbackData': '{}{}{}'.format(StepAction.chooseCardToOpenByDoubt.name, ACTION_DELIMETER,
                                                                     card.name())}])
                self.currentDoubtedPlayerPersonalMessageId = sendMessage(doubtedPlayer.user.userId,
                                                                        'Вы начали катить 🛢бочку и оказались не правы\nКакую карту откроем?',
                                                                        buttons)

            elif doubtedPlayer.cardsCount() == 1:
                card = doubtedPlayer.killOneCard()
                commonText += '{} самоубился 💀'.format(doubtedPlayer.user.combinedNameStrig()) + '\n'
                commonText += '❌ ' + card.openedString() + '\n\n'
                commonText += 'A {} утратил {} и взял новую карту из колоды'.format(
                    self.activePlayer.user.combinedNameStrig(), doubtCardName)
                sendMessage(self.game.gameGroupchatId, commonText)

                self.continueAction()


        else:
            self.stateMachine.applyState(PlayerStepState.InterruptAction)

            commonText += 'и оказался прав!'
            commonText += '\n\n'

            if self.activePlayer.cardsCount() == 2:
                commonText += '{} вскрывает одну карту'.format(self.activePlayer.user.combinedNameStrig()) + '\n'
                sendMessage(self.game.gameGroupchatId, commonText)

                buttons = []
                for card in self.activePlayer.cards:
                    buttons.append([{'text': card.name(),
                                     'callbackData': '{}{}{}'.format(StepAction.chooseCardToOpenByDoubt.name, ACTION_DELIMETER,
                                                                     card.name())}])
                self.currentActivePlayerPersonalMessageId = sendMessage(self.activePlayer.user.userId,
                                                                        'Вас уличили в обмане 🤥 \nКакую карту откроем?',
                                                                        buttons)

            elif self.activePlayer.cardsCount() == 1:
                card = self.activePlayer.killOneCard()
                commonText += '{} умер 💀'.format(self.activePlayer.user.combinedNameStrig()) + '\n'
                commonText += '❌ ' + card.openedString()
                sendMessage(self.game.gameGroupchatId, commonText)
                self.endStep()

    def handleChooseCardToOpenByDoubt(self, action, chatId, userId, queryId, messageId):
        currentPlayer = None
        currentMessageId = 0

        if self.stateMachine.state == PlayerStepState.LoseDoubt:
            currentPlayer = self.doubtedPlayer
            currentMessageId = self.currentDoubtedPlayerPersonalMessageId
        elif self.stateMachine.state == PlayerStepState.InterruptAction:
            currentPlayer = self.activePlayer
            currentMessageId = self.currentActivePlayerPersonalMessageId
        else:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        if userId != currentPlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return
        if currentMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        answerCallbackQuery(queryId)

        self.currentDoubtedPlayerPersonalMessageId = 0
        self.currentActivePlayerPersonalMessageId = 0

        choosenCardName = action.split(ACTION_DELIMETER)[1]
        currentPlayer.killCardByName(choosenCardName)

        sendMessage(self.game.gameGroupchatId,
                    '{}\nоткрыл ❌ {}'.format(currentPlayer.user.combinedNameStrig(), choosenCardName))

        if self.stateMachine.state == PlayerStepState.LoseDoubt:
            self.continueAction()
        elif self.stateMachine.state == PlayerStepState.InterruptAction:
            self.endStep()

    def handleChooseCardForAmbassadoring(self, action, chatId, userId, queryId, messageId):
        if userId != self.activePlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return

        if self.currentActivePlayerPersonalMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        answerCallbackQuery(queryId)

        self.action.handleChooseCard(action)




    def continueAction(self):
        self.stateMachine.applyState(PlayerStepState.MakeAction)

        self.doubtActivePlayerCommonMessageId = 0

        if self.activePlayerAction == Card.Ambassador:
            self.continueAmbassadorAction()
        elif self.activePlayerAction == Card.Duke:
            self.continueDukeAction()

    def continueAmbassadorAction(self):
        self.action = AmbassadorAction(self.activePlayer, self.game.deck, self.finalizeAmbassadorAction)
        self.currentActivePlayerPersonalMessageId = self.action.start()

    def finalizeAmbassadorAction(self):
        activePlayer = self.activePlayer

        sendMessage(activePlayer.user.userId, activePlayer.playerCardsString())

        sendMessage(self.game.gameGroupchatId,
                    activePlayer.user.combinedNameStrig() + ' порылся в колоде и что-то заменил, а что-то и не заменил')

        self.endStep()

    def continueDukeAction(self):
        activePlayer = self.activePlayer
        activePlayer.addCoins(3)

        sendMessage(self.game.gameGroupchatId, activePlayer.user.combinedNameStrig() + ' взял 3 монетки🥉')

        self.endStep()

    def endStep(self):
        self.game.endPlayerStep()

