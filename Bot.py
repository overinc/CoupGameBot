import requests
import logging
import time
import json

from APIMethods import *
from Entities import *

BOTNICK = 'CoupGameBot'
BOTID = '762844961'

class Game:
    def __init__(self):
        self.clearGame()

        self.membersWelcomeMessageText = 'Добро пожаловать в Coup!\nКто будет играть - отмечайтесь'
        self.membersWelcomeMessageButtons = [[{"text": "Я готов!", "callbackData": "wantPlay"}]]

        self.minPlayersCount = 1
        self.maxPlayersCount = 6

    def clearGame(self):
        self.gameGroupchatId = ""
        self.membersWelcomeMessageId = ""

        self.players = set()

        self.deck = Deck()

    def handleEvent(self, event):
        logging.info(event)
        try:
            if event['type'] == "newMessage":
                self.handleNewMessageEvent(event)
            elif event['type'] == "newChatMembers":
                self.handleNewChatMembersEvent(event)
            elif event['type'] == "callbackQuery":
                self.handleCallbackQueryEvent(event)
        except:
            pass

        return event['eventId']

    def handleNewChatMembersEvent(self, event):
        chatId = event['payload']['chat']['chatId']
        for newMember in event['payload']['newMembers']:
            if newMember['nick'] == BOTNICK:
                self.clearGame()

                self.gameGroupchatId = chatId
                self.sendWelcomeMessage()

    def handleNewMessageEvent(self, event):
        chatId = event['payload']['chat']['chatId']
        messageId = event['payload']['msgId']
        text = event['payload']['text'].lower()

        # if BOTNICK.lower() in text or BOTID in text:
        #     self.clearGame()
        #     self.gameGroupchatId = chatId
        #     self.sendWelcomeMessage()

        self.clearGame()
        self.gameGroupchatId = chatId
        self.sendWelcomeMessage()

    def sendWelcomeMessage(self):
        self.membersWelcomeMessageId = sendMessage(self.gameGroupchatId, self.membersWelcomeMessageText, self.membersWelcomeMessageButtons)

    def sendReadyToStartMessage(self):
        sendMessage(self.gameGroupchatId, 'Все готовы?', [[{"text": "Начать игру", "callbackData": "startGame"}]])

    def sendCurrentGameState(self):
        text = 'В колоде {} карт\n\n'.format(len(self.deck.cards))

        for player in self.players:
            text += player.playerStateString() + '\n\n'

        sendMessage(self.gameGroupchatId, text)

    def generateInitialState(self):
        for player in self.players:
            player.addCard(self.deck.getCard())
            player.addCard(self.deck.getCard())

    def handleCallbackQueryEvent(self, event):
        chatId = event['payload']['message']['chat']['chatId']
        userId = event['payload']['from']
        queryId = event['payload']['queryId']
        messageId = event['payload']['message']['msgId']
        callbackData = event['payload']['callbackData']

        if callbackData == 'wantPlay':
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

            self.players.add(player)

            if len(self.players) == self.minPlayersCount:
                self.sendReadyToStartMessage()

            answerCallbackQuery(queryId)

            updatedMessageText = self.membersWelcomeMessageText
            updatedMessageText += '\n\nГотовы играть: \n'
            for player in self.players:
                updatedMessageText += player.user.combinedNameStrig() + '\n'

            editMessage(chatId, self.membersWelcomeMessageId, updatedMessageText, self.membersWelcomeMessageButtons)

        elif callbackData == 'startGame':
            answerCallbackQuery(queryId)

            self.generateInitialState()

            self.sendCurrentGameState()


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
