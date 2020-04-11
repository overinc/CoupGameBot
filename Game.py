import requests
import logging
import time
import json
from enum import Enum
from bot import *
from APIMethods import *
from Entities import *
from GameStep import *

class GameState(Enum):
    Idle = 1
    Welcome = 2
    Game = 3

class GameStateMachine:
    def __init__(self):
        self.state = GameState.Idle

        self.transitions = {GameState.Idle : [GameState.Idle, GameState.Welcome],
                            GameState.Welcome : [GameState.Welcome, GameState.Game],
                            GameState.Game : [GameState.Idle]}

    def applyState(self, state):
        if state in self.transitions[self.state]:
            self.state = state
            return True
        return False



class Game:
    def __init__(self):
        self.stateMachine = GameStateMachine()

        self.clearGame()

        self.membersWelcomeMessageText = 'Добро пожаловать в Coup!\nКто будет играть - отмечайтесь'
        self.membersWelcomeMessageButtons = [[{'text': 'Я готов!', 'callbackData': 'wantPlay'}]]

        self.minPlayersCount = 2
        self.maxPlayersCount = 6

        if DEBUG_MODE:
            self.minPlayersCount = 1


    def clearGame(self):
        self.gameGroupchatId = ""
        self.membersWelcomeMessageId = ""

        self.players = []
        self.currentPlayerIndex = -1

        self.deck = Deck()

        self.currentGameStep = None

        self.botDeeplink = ''
        self.groupchatDeeplink = ''

    def handleEvent(self, event):
        try:
            if event['type'] == "newMessage":
                self.handleMessage(event)
            elif event['type'] == "newChatMembers":
                self.handleAddedToGroupchat(event)
            elif event['type'] == "callbackQuery":
                self.handleButtonTap(event)
        except:
            pass

        return event['eventId']

    def handleAddedToGroupchat(self, event):
        chatId = event['payload']['chat']['chatId']
        for newMember in event['payload']['newMembers']:
            if newMember['nick'] == BOT_NICK:
                if self.stateMachine.applyState(GameState.Welcome) == False:
                    return

                self.clearGame()

                self.gameGroupchatId = chatId
                self.sendWelcomeMessage()

    def handleMessage(self, event):
        chatId = event['payload']['chat']['chatId']
        messageId = event['payload']['msgId']
        text = event['payload']['text'].lower()

        if not DEBUG_MODE:
            if not '@' in chatId:
                return

        if BOT_NICK.lower() in text or BOT_ID in text:
            if self.stateMachine.applyState(GameState.Welcome) == False:
                return

            self.clearGame()
            self.gameGroupchatId = chatId
            self.sendWelcomeMessage()
        else:
            if DEBUG_MODE:
                if self.stateMachine.applyState(GameState.Welcome) == False:
                    return

                self.clearGame()
                self.gameGroupchatId = chatId
                self.sendWelcomeMessage()

    def sendWelcomeMessage(self):
        self.membersWelcomeMessageId = sendMessage(self.gameGroupchatId, self.membersWelcomeMessageText, self.membersWelcomeMessageButtons)

    def sendReadyToStartMessage(self):
        sendMessage(self.gameGroupchatId, 'Все готовы?', [[{'text': 'Начать игру', 'callbackData': 'startGame'}]])

    def sendCurrentGameState(self):
        text = 'В колоде 🃏 {} карт\n\n'.format(len(self.deck.cards))

        for player in self.players:
            text += player.playerStateString() + '\n\n'

        sendMessage(self.gameGroupchatId, text)

    def startGame(self):
        if self.stateMachine.applyState(GameState.Game) == False:
            return

        self.generateInitialState()

        self.processNextPlayerStep()

    def generateInitialState(self):
        # response = getInfo(self.gameGroupchatId)
        # print(response)
        # inviteLink = response['inviteLink']

        self.botDeeplink = 'https://icq.im/' + BOT_NICK
        self.groupchatDeeplink = 'https://icq.im/' + self.gameGroupchatId
        self.groupchatDeeplink = '' # Отключаем бесконечное проваливание по чатам

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


    def processNextPlayerStep(self):
        player = self.findNextPlayer()

        self.currentGameStep = GameStep(self, player)
        self.currentGameStep.startStep()

    def endPlayerStep(self):
        self.currentGameStep = None

        time.sleep(STEPS_PAUSE_TIMER)

        self.processNextPlayerStep()

    def findNextPlayer(self):
        self.currentPlayerIndex += 1
        if self.currentPlayerIndex >= len(self.players):
            self.currentPlayerIndex = 0

        player = self.players[self.currentPlayerIndex]
        if player.isDead():
           return self.findNextPlayer()

        return player


    def handleButtonTap(self, event):
        chatId = event['payload']['message']['chat']['chatId']
        userId = event['payload']['from']['userId']
        queryId = event['payload']['queryId']
        messageId = event['payload']['message']['msgId']
        callbackData = event['payload']['callbackData']

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
        userNick = response['nick']
        userFirstName = response['firstName']
        userLastName = response['lastName']
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

        if len(self.players) == self.minPlayersCount:
            self.sendReadyToStartMessage()

        answerCallbackQuery(queryId)

        updatedMessageText = self.membersWelcomeMessageText
        updatedMessageText += '\n\nГотовы играть: \n'
        for player in self.players:
            updatedMessageText += player.user.combinedNameStrig() + '\n'

        editMessage(chatId, self.membersWelcomeMessageId, updatedMessageText, self.membersWelcomeMessageButtons)

    def handleStartGameButtonTap(self, chatId, userId, queryId, messageId):
        answerCallbackQuery(queryId)

        self.startGame()

    def checkValidPersonalButtonTap(self, userId, messageId, queryId):
        if self.stateMachine.state != GameState.Game:
            answerCallbackQuery(queryId, 'Куды тычишь!? Нет игры..')
            return False

        return True