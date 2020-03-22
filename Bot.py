import requests
import logging
import time
import json
from enum import Enum
from APIMethods import *
from Entities import *

BOTNICK = 'CoupGameBot'
BOTID = '762844961'

class GameState(Enum):
    Idle = 1
    Welcome = 2
    Game = 3

class StateMachine:
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
        self.stateMachine = StateMachine()

        self.clearGame()

        self.membersWelcomeMessageText = 'Добро пожаловать в Coup!\nКто будет играть - отмечайтесь'
        self.membersWelcomeMessageButtons = [[{'text': 'Я готов!', 'callbackData': 'wantPlay'}]]

        self.minPlayersCount = 1
        self.maxPlayersCount = 6

    def clearGame(self):
        self.gameGroupchatId = ""
        self.membersWelcomeMessageId = ""

        self.players = []
        self.currentPlayerIndex = 0

        self.deck = Deck()

        self.currentActivePersonalMessageId = 0

    def handleEvent(self, event):
        logging.info(event)
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
            if newMember['nick'] == BOTNICK:
                if self.stateMachine.applyState(GameState.Welcome) == False:
                    return

                self.clearGame()

                self.gameGroupchatId = chatId
                self.sendWelcomeMessage()

    def handleMessage(self, event):
        chatId = event['payload']['chat']['chatId']
        messageId = event['payload']['msgId']
        text = event['payload']['text'].lower()


        # if BOTNICK.lower() in text or BOTID in text:
        #     if self.stateMachine.applyState(GameState.Welcome) == False:
        #         return
        #     self.clearGame()
        #     self.gameGroupchatId = chatId
        #     self.sendWelcomeMessage()

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
        for player in self.players:
            player.addCard(self.deck.getCard())
            player.addCard(self.deck.getCard())

    def getCurrentPlayer(self):
        return self.players[self.currentPlayerIndex]

    def processNextPlayerStep(self):
        self.sendCurrentGameState()

        player = self.getCurrentPlayer()
        sendMessage(self.gameGroupchatId, 'Ход {}'.format(player.user.combinedNameStrig()))

        personalMessage = player.playerStateString('Ваш ход!')

        buttons = []
        if player.coinsCount >= 10:
            buttons.append([{'text': 'Выстрелить за 7 монет', 'callbackData': 'simpleShot'}])
        else:
            buttons.append([{'text': 'Взять монетку', 'callbackData': 'takeCoin'}])
            buttons.append([{'text': 'Попытаться взять две монетки', 'callbackData': 'tryTakeTwo'}])

            if player.coinsCount >= 7:
                buttons.append([{'text': 'Выстрелить за 7 монет', 'callbackData': 'simpleShot'}])

            buttons.append([{'text': 'Прикинуться Ambassador', 'callbackData': 'shuffle'}])
            buttons.append([{'text': 'Прикинуться Assassin', 'callbackData': 'snipeShot'}])
            buttons.append([{'text': 'Прикинуться Captain', 'callbackData': 'steal'}])
            buttons.append([{'text': 'Прикинуться Duke', 'callbackData': 'getThreeCoins'}])

        print(buttons)

        self.currentActivePersonalMessageId = sendMessage(player.user.userId, personalMessage, buttons)

    def processSimpleShot(self):
        currentPlayer = self.getCurrentPlayer()

        buttons = []
        for player in self.players:
            if player == currentPlayer:
                continue
            if player.isAlive():
                buttons.append([{'text': player.user.combinedNameStrig(), 'callbackData': 'simpleShotTarget|' + player.user.userId}])

        sendMessage(currentPlayer.user.userId, 'В кого стрелять будем?', buttons)


    def endPlayerStep(self):
        self.currentActivePersonalMessageId = 0

        self.currentPlayerIndex += 1
        if self.currentPlayerIndex >= len(self.players):
            self.currentPlayerIndex = 0

        self.processNextPlayerStep()



    def handleButtonTap(self, event):
        chatId = event['payload']['message']['chat']['chatId']
        userId = event['payload']['from']
        queryId = event['payload']['queryId']
        messageId = event['payload']['message']['msgId']
        callbackData = event['payload']['callbackData']

        if callbackData == 'wantPlay':
            self.handleWantPlayButtonTap(chatId, userId, queryId, messageId)
        elif callbackData == 'startGame':
            self.handleStartGameButtonTap(chatId, userId, queryId, messageId)

        elif callbackData == 'takeCoin':
            self.handleTakeCoinButtonTap(chatId, userId, queryId, messageId)
        elif callbackData == 'tryTakeTwo':
            self.handleTryTakeTwoCoinsButtonTap(chatId, userId, queryId, messageId)
        elif callbackData == 'simpleShot':
            self.handleSimpleShotButtonTap(chatId, userId, queryId, messageId)
        elif callbackData == 'shuffle':
            self.handleAmbassadorButtonTap(chatId, userId, queryId, messageId)
        elif callbackData == 'snipeShot':
            self.handleAssassinButtonTap(chatId, userId, queryId, messageId)
        elif callbackData == 'steal':
            self.handleCaptainButtonTap(chatId, userId, queryId, messageId)
        elif callbackData == 'getThreeCoins':
            self.handleDukeButtonTap(chatId, userId, queryId, messageId)

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



    def handleTakeCoinButtonTap(self, chatId, userId, queryId, messageId):
        if self.checkValidPersonalButtonTap(userId, messageId, queryId) == False:
            return
        answerCallbackQuery(queryId)

        player = self.getCurrentPlayer()
        player.coinsCount += 1

        sendMessage(self.gameGroupchatId, player.user.combinedNameStrig() + ' взял 💲 монетку ')
        self.endPlayerStep()


    def handleTryTakeTwoCoinsButtonTap(self, chatId, userId, queryId, messageId):
        if self.checkValidPersonalButtonTap(userId, messageId, queryId) == False:
            return
        answerCallbackQuery(queryId)

    def handleSimpleShotButtonTap(self, chatId, userId, queryId, messageId):
        if self.checkValidPersonalButtonTap(userId, messageId, queryId) == False:
            return
        answerCallbackQuery(queryId)

        self.processSimpleShot()


    def handleAmbassadorButtonTap(self, chatId, userId, queryId, messageId):
        if self.checkValidPersonalButtonTap(userId, messageId, queryId) == False:
            return
        answerCallbackQuery(queryId)

    def handleAssassinButtonTap(self, chatId, userId, queryId, messageId):
        if self.checkValidPersonalButtonTap(userId, messageId, queryId) == False:
            return
        answerCallbackQuery(queryId)

    def handleCaptainButtonTap(self, chatId, userId, queryId, messageId):
        if self.checkValidPersonalButtonTap(userId, messageId, queryId) == False:
            return
        answerCallbackQuery(queryId)

    def handleDukeButtonTap(self, chatId, userId, queryId, messageId):
        if self.checkValidPersonalButtonTap(userId, messageId, queryId) == False:
            return
        answerCallbackQuery(queryId)

    def checkValidPersonalButtonTap(self, userId, messageId, queryId):
        if self.stateMachine.state != GameState.Game:
            answerCallbackQuery(queryId, 'Куды тычишь!? Нет игры..')
            return False

        player = self.getCurrentPlayer()
        if userId != player.user.userId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не твое..')
            return False

        if self.currentActivePersonalMessageId != messageId:
            answerCallbackQuery(queryId, 'Куды тычишь!? Не туда..')
            return False

        return True




def poll(event_id):

    params = {'lastEventId': str(event_id), 'pollTime': 300, 'token': TOKEN}

    reply = requests.get(f"{base_url}/events/get", params)

    if reply.status_code != requests.codes.ok:
        return None

    json = None
    try:
        json = reply.json()
    except Exception as e:
        logging.error('Invalid JSON from server: {}'.format(e))
        logging.error(reply.content)
        return None
    return json

def run():
    max_event_id = 0

    game = Game()

    try:
        while (True):

                json = poll(max_event_id)

                if json is None:
                    continue

                if 'events' not in json:
                    logging.error('No events in JSON: {}'.format(json))
                    continue

                for event in json['events']:
                    max_event_id = max(max_event_id, game.handleEvent(event))
    except:
        pass

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y.%m.%d %I:%M:%S %p',
                        level=logging.DEBUG)

    run()
