import random
from enum import Enum
from APIMethods import *
from Entities import *
from GameStep import *

class GameState(Enum):
    Idle = 1
    CollectPlayers = 2
    Game = 3

class GameStateMachine:
    def __init__(self):
        self.state = GameState.Idle

        self.transitions = {GameState.Idle : [GameState.Idle, GameState.CollectPlayers],
                            GameState.CollectPlayers : [GameState.CollectPlayers, GameState.Game],
                            GameState.Game : [GameState.Idle]}

    def applyState(self, state):
        if state in self.transitions[self.state]:
            self.state = state
            return True
        return False



class Game:
    def __init__(self, gameGroupchatId, completion):
        self.gameGroupchatId = gameGroupchatId
        self._completion = weakref.WeakMethod(completion)

        self.botDeeplink = 'https://icq.im/' + BOT_NICK
        self.groupchatDeeplink = 'https://icq.im/' + self.gameGroupchatId
        self.groupchatDeeplink = ''  # Отключаем бесконечное проваливание по чатам

        self.stateMachine = GameStateMachine()

        self.clearGame()

        self.gameEnded = False

        self.membersWelcomeMessageButtons = [[{'text': 'Я готов!', 'callbackData': 'wantPlay'}],
                                             [{'text': 'Написать боту', 'url': self.botDeeplink}]]

        self.minPlayersCount = 2
        self.maxPlayersCount = 6
        if DEBUG_MODE:
            self.minPlayersCount = 1

    def __del__(self):
        print('Game dealloc')


    def clearGame(self):
        self.membersWelcomeMessageId = ""

        self.players = []
        self.currentPlayerIndex = -1
        self.roundNumber = 1

        self.deadPlayersOrdered = []

        self.deck = Deck()

        self.currentGameStep = None

    def startCollectPlayers(self):
        applyStateResult = self.stateMachine.applyState(GameState.CollectPlayers)
        if applyStateResult == False:
            return

        self.clearGame()
        self.sendWelcomeMessage()


    def sendWelcomeMessage(self):
        self.membersWelcomeMessageId = sendMessage(self.gameGroupchatId, collect_players_base_message_text, self.membersWelcomeMessageButtons)

    def sendReadyToStartMessage(self):
        sendMessage(self.gameGroupchatId, 'Начинать игру можно от 2 до 6 игроков.\nВсе готовы?', [[{'text': 'Начать игру', 'callbackData': 'startGame'}]])

    def sendCurrentGameState(self, chatId):
        text = 'В колоде 🃏 {} карт\n\n'.format(len(self.deck.cards))

        for player in self.players:
            text += player.playerStateString() + '\n\n'

        sendMessage(chatId, text)

    def startGame(self):
        ok = self.checkPlayersApproved()
        if not ok:
            return

        applyStateResult = self.stateMachine.applyState(GameState.Game)
        if applyStateResult == False:
            return

        self.generateInitialState()

        self.processNextPlayerStep()

    def checkPlayersApproved(self):
        badPlayers = []
        for player in self.players:
            messageId = sendMessage(player.user.userId, 'Игра начинается...')
            if messageId == None:
                badPlayers.append(player)

        if not badPlayers:
            return True
        else:
            text = players_need_connect_bot_text + '\n\n'
            text += 'Эти игроки еще не написали боту:\n'
            for player in badPlayers:
                text += player.user.combinedNameStrig() + '\n'

            buttons = [[{'text': 'Написать боту', 'url': self.botDeeplink}]]

            sendMessage(self.gameGroupchatId, text, buttons)
            return False


    def generateInitialState(self):
        random.shuffle(self.players)

        for player in self.players:
            player.addCard(self.deck.getCard())
            player.addCard(self.deck.getCard())

        for player in self.players:
            sendMessage(player.user.userId, player.playerCardsString())

    def findPlayerByUserId(self, userId):
        for player in self.players:
            if player.user.userId == userId:
                return player
        return None

    def returnPlayerCardAndGetNew(self, player, cardName):
        card = player.returnCardByName(cardName)
        self.deck.putCard(card)
        player.addCard(self.deck.getCard())

    def playersToShot(self, activePlayer):
        players = []
        for player in self.players:
            if player == activePlayer:
                if not DEBUG_MODE:
                    continue
            if player.isAlive():
                players.append(player)
        return players

    def playersToSteal(self, activePlayer):
        players = []
        for player in self.players:
            if player == activePlayer:
                if not DEBUG_MODE:
                    continue
            if player.isAlive():
                if player.coinsCount > 0:
                    players.append(player)
        return players

    def onPlayerDead(self, player):
        self.deadPlayersOrdered.insert(0, player)
        self.checkGameEnd()

    def checkGameEnd(self):
        alivePlayers = 0
        alivePlayer = None
        for player in self.players:
            if player.isAlive():
                alivePlayers += 1
                alivePlayer = player

        if alivePlayers <= 1:
            self.gameEnded = True

            time.sleep(STEPS_PAUSE_TIMER)

            self.sendFinalMessage(alivePlayer)
            self.clearGame()
            self.stateMachine = GameStateMachine()
            self._completion()(self)


    def sendFinalMessage(self, winner):
        text = 'Игра окончена!'
        text += '\n\n'
        text += '🥇Победил {}'.format(winner.user.combinedNameStrig())
        text += '\n\n'
        text += 'Остальные места:'
        text += '\n'
        for i in range(len(self.deadPlayersOrdered)):
            player = self.deadPlayersOrdered[i]
            playerName = player.user.combinedNameStrig()
            prefix = ''
            if i == 0:
                prefix = '🥈'
            elif i == 1:
                prefix = '🥉'
            else:
                prefix = '{}. '.format(i + 2)
            text += prefix + playerName
            text += '\n'
        sendMessage(self.gameGroupchatId, text)




    def processNextPlayerStep(self):
        player = self.findNextPlayer()

        self.currentGameStep = GameStep(self, player)
        self.currentGameStep.startStep(self.roundNumber)

    def endPlayerStep(self):
        self.currentGameStep = None

        if self.gameEnded:
            return

        time.sleep(STEPS_PAUSE_TIMER)

        self.processNextPlayerStep()

    def findNextPlayer(self):
        self.currentPlayerIndex += 1
        if self.currentPlayerIndex >= len(self.players):
            self.currentPlayerIndex = 0
            self.roundNumber += 1

        player = self.players[self.currentPlayerIndex]
        if player.isDead():
           return self.findNextPlayer()

        return player


    def handleButtonTap(self, event):
        chatId = event.data.get('message').get('chat').get('chatId')
        userId = event.data.get('from').get('userId')
        queryId = event.data.get('queryId')
        messageId = event.data.get('message').get('msgId')
        callbackData = event.data.get('callbackData')

        if callbackData == 'wantPlay':
            self.handleWantPlayButtonTap(chatId, userId, queryId, messageId)
        elif callbackData == 'startGame':
            self.handleStartGameButtonTap(chatId, userId, queryId, messageId)

        elif callbackData in StepPrimaryActions:
            if not self.checkValidPersonalButtonTap(userId, messageId, queryId):
                return
            self.currentGameStep.handleStepPrimaryAction(callbackData, chatId, userId, queryId, messageId)

        elif callbackData == StepAction.doubtActivePlayer.name:
            if not self.checkValidPersonalButtonTap(userId, messageId, queryId):
                return
            self.currentGameStep.handleSomeoneDoubtActivePlayer(callbackData, chatId, userId, queryId, messageId)

        elif callbackData == StepAction.tryBlockForeignAid.name:
            if not self.checkValidPersonalButtonTap(userId, messageId, queryId):
                return
            self.currentGameStep.handleSomeoneTryBlockForeignAid(callbackData, chatId, userId, queryId, messageId)

        elif callbackData == StepAction.doubtSecondaryPlayer.name:
            if not self.checkValidPersonalButtonTap(userId, messageId, queryId):
                return
            self.currentGameStep.handleSomeoneDoubtSecondaryPlayer(callbackData, chatId, userId, queryId, messageId)

        elif ACTION_DELIMETER in callbackData:
            if not self.checkValidPersonalButtonTap(userId, messageId, queryId):
                return
            self.currentGameStep.handleStepComplexAction(callbackData, chatId, userId, queryId, messageId)

    def handleWantPlayButtonTap(self, chatId, userId, queryId, messageId):
        response = getInfo(userId)
        userNick = response.get('nick')
        userFirstName = response.get('firstName')
        userLastName = response.get('lastName')
        userName = userFirstName
        if userLastName:
            userName += " " + userLastName

        if len(self.players) >= self.maxPlayersCount:
            answerCallbackQuery(queryId, "Шесть - максимальное количество игроков, больше нельзя(")
            return

        user = User(userId, userNick, userName)
        player = Player(user)

        if player in self.players:
            answerCallbackQuery(queryId)
            return

        self.players.append(player)

        answerCallbackQuery(queryId)

        updatedMessageText = collect_players_base_message_text
        updatedMessageText += '\n\nГотовы играть: \n'
        for player in self.players:
            updatedMessageText += player.user.combinedNameStrig() + '\n'

        editMessage(chatId, self.membersWelcomeMessageId, updatedMessageText, self.membersWelcomeMessageButtons)

        if len(self.players) == self.minPlayersCount:
            self.sendReadyToStartMessage()

    def handleStartGameButtonTap(self, chatId, userId, queryId, messageId):
        answerCallbackQuery(queryId)

        self.startGame()

    def checkValidPersonalButtonTap(self, userId, messageId, queryId):
        if self.stateMachine.state != GameState.Game:
            answerCallbackQuery(queryId, 'Куды тычишь!? Нет игры..')
            return False

        for player in self.deadPlayersOrdered:
            if player.user.userId == userId:
                answerCallbackQuery(queryId, 'Куды тычишь!? Не мешай другим играть..')
                return False

        return True