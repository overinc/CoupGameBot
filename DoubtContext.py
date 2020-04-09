from enum import Enum
from TimingMessageContext import *
from Constants import *
from Entities import *


class DoubtState(Enum):
    DoubtWelcome = 1
    DoubtStart = 2
    InterruptAction = 3
    LoseDoubt = 4

class DoubtStateMachine:
    def __init__(self):
        self.state = DoubtState.DoubtWelcome

        self.transitions = {
                            DoubtState.DoubtWelcome: [DoubtState.DoubtStart],
                            DoubtState.DoubtStart: [DoubtState.InterruptAction, DoubtState.LoseDoubt],
                            }

    def applyState(self, state):
        if state in self.transitions[self.state]:
            self.state = state
            return True
        return False



class DoubtContext:

    def __init__(self, actionType, game, activePlayer, callbackDataAlias, doubtWelcomeTextTitle, continueActionHandler, abortActionHandler):
        self.actionType = actionType
        self.game = game
        self.activePlayer = activePlayer
        self.doubtedPlayer = None
        self.callbackDataAlias = callbackDataAlias
        self.doubtWelcomeTextTitle = doubtWelcomeTextTitle
        self.continueActionHandler = continueActionHandler
        self.abortActionHandler = abortActionHandler

        self.timingMessageContext = None
        self.currentDoubtedPlayerPersonalMessageId = 0

        self.stateMachine = DoubtStateMachine()

    def start(self):
        baseText = self.doubtWelcomeText()
        buttons = [[{'text': 'Я усомняюсь',
                     'callbackData': self.callbackDataAlias}]]

        text = baseText + '\n' + TimingMessageContext.timingStringFor(DOUBT_TIMER, DOUBT_TIMER)

        self.doubtActivePlayerCommonMessageId = sendMessage(self.game.gameGroupchatId, text, buttons)

        self.timingMessageContext = TimingMessageContext(DOUBT_TIMER, self.game.gameGroupchatId,
                                                         self.doubtActivePlayerCommonMessageId, baseText, buttons,
                                                         self.handleTimerEnd)
        self.timingMessageContext.startAnimate()

    def handleTimerEnd(self):
        self.continueActionHandler()

    def handleSomeoneDoubtActivePlayer(self, action, chatId, userId, queryId, messageId):

        applyStateResult = self.stateMachine.applyState(DoubtState.DoubtStart)
        if applyStateResult == False:
            answerCallbackQuery(queryId, 'Поздно..')
            return

        if self.doubtActivePlayerCommonMessageId != messageId:
            answerCallbackQuery(queryId, 'Поздно..')
            return

        answerCallbackQuery(queryId)

        self.timingMessageContext.stopAnimate()
        self.doubtActivePlayerCommonMessageId = 0

        activePlayer = self.activePlayer
        doubtedPlayer = self.game.findPlayerByUserId(userId)
        self.doubtedPlayer = doubtedPlayer

        doubtCardName = self.actionType.name

        wrong = activePlayer.hasCardByName(doubtCardName)
        die = False
        if wrong:
            if doubtedPlayer.cardsCount() == 1:
                die = True
        else:
            if activePlayer.cardsCount() == 1:
                die = True

        if wrong:
            self.game.returnPlayerCardAndGetNew(activePlayer, doubtCardName)

            sendMessage(activePlayer.user.userId, activePlayer.playerCardsString())

            if die:
                lostedCard = doubtedPlayer.killOneCard()
                self.sendDoubtResultMessage(wrong, die, lostedCard, doubtCardName)

                self.continueActionHandler()
            else:
                self.stateMachine.applyState(DoubtState.LoseDoubt)

                self.sendDoubtResultMessage(wrong, die, '', doubtCardName)
                self.sendCardOpenPersonalMessage(doubtedPlayer, False)


        else:
            self.stateMachine.applyState(DoubtState.InterruptAction)

            if die:
                lostedCard = activePlayer.killOneCard()
                self.sendDoubtResultMessage(wrong, die, lostedCard, doubtCardName)
                self.abortActionHandler()

            else:
                self.sendDoubtResultMessage(wrong, die, '', doubtCardName)
                self.sendCardOpenPersonalMessage(activePlayer, True)

    def handleChooseCardToOpenByDoubt(self, action, chatId, userId, queryId, messageId):
        currentPlayer = None
        if self.stateMachine.state == DoubtState.LoseDoubt:
            currentPlayer = self.doubtedPlayer
        elif self.stateMachine.state == DoubtState.InterruptAction:
            currentPlayer = self.activePlayer
        else:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        if userId != currentPlayer.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return
        if self.currentDoubtedPlayerPersonalMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return

        answerCallbackQuery(queryId)

        choosenCardName = action.split(ACTION_DELIMETER)[1]
        currentPlayer.killCardByName(choosenCardName)

        sendMessage(self.game.gameGroupchatId,
                    '{}\nоткрыл ❌ {}'.format(currentPlayer.user.combinedNameStrig(), choosenCardName))

        if self.stateMachine.state == DoubtState.LoseDoubt:
            self.continueActionHandler()
        elif self.stateMachine.state == DoubtState.InterruptAction:
            self.abortActionHandler()




    def doubtWelcomeText(self):
        userName = self.activePlayer.user.combinedNameStrig()

        text = '{} {}'.format(userName, self.doubtWelcomeTextTitle)
        text += '\nКто хочет усомниться?\n\n'
        text += 'У вас есть на это {} секунд'.format(DOUBT_TIMER)
        return text

    def sendDoubtResultMessage(self, wrong, die, lostedCard, doubtCardName):
        activePlayer = self.activePlayer
        doubtedPlayer = self.doubtedPlayer

        text = doubtedPlayer.user.combinedNameStrig() + '\n'
        text += 'усомнился '
        # text += 'усомнился в\n'
        # text += activePlayer.user.combinedNameStrig() + '\n'

        if wrong:
            if die:
                text += ', НО оказался НЕ прав и самоубился! 💀' + '\n'
                text += '❌ ' + lostedCard.openedString()
            else:
                text += 'и оказался НЕ прав!' + '\n'
                text += 'Теперь он вскрывает одну карту'

            text += '\n\n'
            text += 'A {} утратил {} и взял новую карту из колоды'.format(
                activePlayer.user.combinedNameStrig(), doubtCardName)
        else:
            text += 'и оказался ПРАВ!'
            text += '\n\n'

            if die:
                text += '{} умер 💀'.format(activePlayer.user.combinedNameStrig()) + '\n'
                text += '❌ ' + lostedCard.openedString()
            else:
                text += '{} вскрывает одну карту'.format(activePlayer.user.combinedNameStrig()) + '\n'

        sendMessage(self.game.gameGroupchatId, text)

    def sendCardOpenPersonalMessage(self, player, active):
        text = ''
        if active:
           text = 'Вас уличили в обмане 🤥 \nКакую карту откроем?'
        else:
           text = 'Вы начали катить 🛢бочку и оказались не правы\nКакую карту откроем?'

        buttons = []
        for card in player.cards:
            buttons.append([{'text': card.name,
                             'callbackData': '{}{}{}'.format(StepAction.chooseCardToOpenByDoubt.name,
                                                             ACTION_DELIMETER,
                                                             card.name)}])
        self.currentDoubtedPlayerPersonalMessageId = sendMessage(player.user.userId,
                                                                 text,
                                                                 buttons)