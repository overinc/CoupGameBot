import threading
from Entities import *
from bot import *
from APIMethods import *
from Constants import *
from Entities import *
from DoubtContext import *
from Localization import *
from Actions.Ambassador import *
from Actions.ForeignAid import *
from Actions.Captain import *

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
    MakeAction = 7
    # Protect = 8
    # DoubtProtect = 9


class PlayerStateMachine:
    def __init__(self):
        self.state = PlayerStepState.Unknown

        self.transitions = {PlayerStepState.Unknown : [PlayerStepState.ChooseAction],
                            PlayerStepState.ChooseAction: [PlayerStepState.MakeAction],
                            }

    def applyState(self, state):
        if state in self.transitions[self.state]:
            self.state = state
            return True
        return False


class GameStep:
    def __init__(self, game, activePlayer):
        self.game = game

        self.activePlayer = activePlayer
        self.targetPlayer = None

        self.stateMachine = PlayerStateMachine()

        self.activePlayerActionType = None
        self.activePlayerAction = None

        self.foreignAidAction = None
        self.captainAction = None

        self.currentActivePlayerPersonalMessageId = 0
        self.currentTargetPlayerPersonalMessageId = 0
        self.currentDoubtedPlayerPersonalMessageId = 0



    def startStep(self):
        self.game.sendCurrentGameState()

        activePlayer = self.activePlayer

        buttons = [[{'text': 'Ходить', 'url': self.game.botDeeplink}]]
        sendMessage(self.game.gameGroupchatId, 'Ход игрока {}'.format(activePlayer.user.combinedNameStrig()), buttons)

        personalMessage = activePlayer.playerStateString('\nВаш ход!', True)

        buttons = []
        if activePlayer.coinsCount >= 10:
            buttons.append([{'text': 'Выстрелить за 7 монет', 'callbackData': '{}'.format(StepAction.simpleShot.name)}])
        else:
            buttons.append([{'text': 'Взять монетку', 'callbackData': '{}'.format(StepAction.takeCoin.name)}])

            buttons.append([{'text': 'Попытаться взять 2 монетки', 'callbackData': '{}'.format(StepAction.tryTakeTwo.name)}])

            if activePlayer.coinsCount >= 7:
                buttons.append([{'text': 'Выстрелить за 7 монет', 'callbackData': '{}'.format(StepAction.simpleShot.name)}])

            buttons.append([{'text': 'Прикинуться Ambassador\nи порыться в колоде', 'callbackData': '{}'.format(StepAction.shuffle.name)}])

            if activePlayer.coinsCount >= 3:
                buttons.append([{'text': 'Прикинуться Assassin\nи пальнуть за 3 монетки', 'callbackData': '{}'.format(StepAction.snipeShot.name)}])

            if len(self.game.playersToSteal(activePlayer)) > 0:
                buttons.append([{'text': 'Прикинуться Captain\nи украсть две 2 монетки', 'callbackData': '{}'.format(StepAction.steal.name)}])

            buttons.append([{'text': 'Прикинуться Duke\nи взять 3 монетки', 'callbackData': '{}'.format(StepAction.takeThreeCoins.name)}])

        self.currentActivePlayerPersonalMessageId = sendMessage(activePlayer.user.userId, personalMessage, buttons)

        self.stateMachine.applyState(PlayerStepState.ChooseAction)




    def handleStepPrimaryAction(self, action, chatId, userId, queryId, messageId):
        if userId != self.activePlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return

        if self.currentActivePlayerPersonalMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        self.currentActivePlayerPersonalMessageId = 0

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
        answerCallbackQuery(queryId, '', self.game.groupchatDeeplink)

        self.stateMachine.applyState(PlayerStepState.MakeAction)

        activePlayer = self.activePlayer
        if DEBUG_MANY_MONEY:
            activePlayer.addCoins(10)
        else:
            activePlayer.addCoins(1)

        sendMessage(self.game.gameGroupchatId, activePlayer.user.combinedNameStrig() + ' взял 1 🥇монетку')
        self.endStep()

    def handleTryTakeTwoCoinsAction(self, chatId, userId, queryId, messageId):
        answerCallbackQuery(queryId, '', self.game.groupchatDeeplink)

        self.foreignAidAction = ForeignAidAction(self.activePlayer, self.game, self.endStep)
        self.foreignAidAction.start()

    def handleSimpleShotAction(self, chatId, userId, queryId, messageId):
        answerCallbackQuery(queryId)

        activePlayer = self.activePlayer

        text = 'В кого стрелять будем?'
        buttons = []
        for player in self.game.players:
            if player == activePlayer:
                if not DEBUG_MODE:
                    continue
            if player.isAlive():
                buttons.append([{'text': player.user.combinedNameStrig(),
                                 'callbackData': '{}{}{}'.format(StepAction.simpleShot.name, ACTION_DELIMETER, player.user.userId)}])

        self.currentActivePlayerPersonalMessageId = sendMessage(activePlayer.user.userId, text, buttons)

    def handleAmbassadorAction(self, chatId, userId, queryId, messageId):
        answerCallbackQuery(queryId, '', self.game.groupchatDeeplink)

        self.activePlayerActionType = Card.Ambassador

        self.doubtContext = DoubtContext(self.activePlayerActionType,
                                         self.game,
                                         self.activePlayer,
                                         StepAction.doubtActivePlayer.name,
                                         doubt_welcome_text_title_ambassador,
                                         self.continueAction,
                                         self.endStep)
        self.doubtContext.start()

    def handleAssassinAction(self, chatId, userId, queryId, messageId):
        answerCallbackQuery(queryId)

        self.endStep()

    def handleCaptainAction(self, chatId, userId, queryId, messageId):
        answerCallbackQuery(queryId, '', self.game.groupchatDeeplink)

        self.captainAction = CaptainAction(self.activePlayer, self.game, self.endStep)
        self.captainAction.start()

    def handleDukeAction(self, chatId, userId, queryId, messageId):
        answerCallbackQuery(queryId, '', self.game.groupchatDeeplink)

        self.activePlayerActionType = Card.Duke

        self.doubtContext = DoubtContext(self.activePlayerActionType,
                                         self.game,
                                         self.activePlayer,
                                         doubt_welcome_text_title_duke,
                                         StepAction.doubtActivePlayer.name,
                                         self.continueAction,
                                         self.endStep)
        self.doubtContext.start()





    def handleSomeoneDoubtActivePlayer(self, action, chatId, userId, queryId, messageId):
        if not DEBUG_MODE:
            if userId == self.activePlayer.user.userId:
                answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
                return

        doubtContext = None
        if self.captainAction:
            doubtContext = self.captainAction.doubtContext
        elif self.doubtContext:
            doubtContext = self.doubtContext

        if doubtContext:
            doubtContext.handleSomeoneDoubtActivePlayer(action, chatId, userId, queryId, messageId)
        else:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')

    def handleSomeoneTryBlockForeignAid(self, action, chatId, userId, queryId, messageId):
        if not DEBUG_MODE:
            if userId == self.activePlayer.user.userId:
                answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
                return

        if not self.foreignAidAction:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        self.foreignAidAction.handleSomeoneTryBlockForeignAid(action, chatId, userId, queryId, messageId)

    def handleSomeoneDoubtForeignAidBlocker(self, action, chatId, userId, queryId, messageId):
        if not self.foreignAidAction:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        self.foreignAidAction.handleSomeoneDoubtForeignAidBlocker(action, chatId, userId, queryId, messageId)


    def handleStepComplexAction(self, action, chatId, userId, queryId, messageId):
        actionType = action.split(ACTION_DELIMETER)[0]

        if actionType == StepAction.simpleShot.name:
            self.handleChooseTargetForSimpleShot(action, chatId, userId, queryId, messageId)
        elif actionType == StepAction.chooseCardToOpenByKill.name:
            self.handleChooseCardToOpenByKill(action, chatId, userId, queryId, messageId)
        elif actionType == StepAction.chooseCardToOpenByDoubt.name:
            self.handleChooseCardToOpenByDoubt(action, chatId, userId, queryId, messageId)
        elif actionType == StepAction.chooseCardForAmbassadoring.name:
            self.handleChooseCardForAmbassadoring(action, chatId, userId, queryId, messageId)
        elif actionType == StepAction.steal.name:
            self.handleChooseTargetForStealing(action, chatId, userId, queryId, messageId)
        elif actionType == StepAction.chooseActionForBlockStealing.name:
            self.handleChooseActionForBlockStealing(action, chatId, userId, queryId, messageId)

    def handleChooseTargetForSimpleShot(self, action, chatId, userId, queryId, messageId):
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
                buttons.append([{'text': card.name, 'callbackData': '{}{}{}'.format(StepAction.chooseCardToOpenByKill.name, ACTION_DELIMETER, card.name)}])
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

    def handleChooseCardToOpenByDoubt(self, action, chatId, userId, queryId, messageId):
        doubtContext = None
        if self.foreignAidAction:
            doubtContext = self.foreignAidAction.doubtContext
        elif self.captainAction:
            doubtContext = self.captainAction.doubtContext
        elif self.doubtContext:
            doubtContext = self.doubtContext

        if doubtContext:
            doubtContext.handleChooseCardToOpenByDoubt(action, chatId, userId, queryId, messageId)
        else:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')

    def handleChooseCardForAmbassadoring(self, action, chatId, userId, queryId, messageId):
        if userId != self.activePlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return

        if self.currentActivePlayerPersonalMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        answerCallbackQuery(queryId)

        self.activePlayerAction.handleChooseCard(action)

    def handleChooseTargetForStealing(self, action, chatId, userId, queryId, messageId):
        if userId != self.activePlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return

        if not self.captainAction:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        self.captainAction.handleChooseTargetForStealing(action, chatId, userId, queryId, messageId)

    def handleChooseActionForBlockStealing(self, action, chatId, userId, queryId, messageId):
        if not self.captainAction:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        self.captainAction.handleChooseActionForBlockStealing(action, chatId, userId, queryId, messageId)



    def continueAction(self):
        self.doubtContext = None

        self.stateMachine.applyState(PlayerStepState.MakeAction)

        if self.activePlayerActionType == Card.Ambassador:
            self.continueAmbassadorAction()
        elif self.activePlayerActionType == Card.Duke:
            self.continueDukeAction()

    def continueAmbassadorAction(self):
        self.activePlayerAction = AmbassadorAction(self.activePlayer, self.game.deck, self.finalizeAmbassadorAction)
        self.currentActivePlayerPersonalMessageId = self.activePlayerAction.start()

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

