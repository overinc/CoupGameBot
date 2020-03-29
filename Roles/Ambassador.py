from APIMethods import *
from Constants import *

MESSAGE_TEXT = 'Вы вытянули из колоды две новые карты.\nВыберете карты, которые оставите у себя:'

KEEP_CARD_ACTION = 'keep'
GET_CARD_ACTION = 'get'


class AmbassadorAction:

    def __init__(self, player, deck, completion):
        self.player = player
        self.deck = deck

        self.playersCards = []
        self.newCards = []

        self.ambassadoringMessageId = ''

        self.completion = completion


    def start(self):
        for card in self.player.cards:
            self.playersCards.append(card)

        self.player.cards.clear()

        for i in range(2):
            card = self.deck.getCard()
            self.newCards.append(card)

        self.ambassadoringMessageId = sendMessage(self.player.user.userId, MESSAGE_TEXT, self.generateButtons())
        return self.ambassadoringMessageId

    def handleChooseCard(self, action):
        actionType = action.split(ACTION_DELIMETER)[1]
        cardName = action.split(ACTION_DELIMETER)[2]

        if actionType == KEEP_CARD_ACTION:
            for card in self.playersCards:
                if card.name() == cardName:
                    self.playersCards.remove(card)
                    self.player.addCard(card)
                    break

        if actionType == GET_CARD_ACTION:
            for card in self.newCards:
                if card.name() == cardName:
                    self.newCards.remove(card)
                    self.player.addCard(card)
                    break

        if len(self.playersCards) + len(self.newCards) > 2:
            editMessage(self.player.user.userId, self.ambassadoringMessageId, MESSAGE_TEXT, self.generateButtons())
        else:
            for card in self.playersCards:
                self.deck.putCard(card)
            for card in self.newCards:
                self.deck.putCard(card)

            self.completion()


    def generateButtons(self):
        buttons = []
        for card in self.playersCards:
            buttons.append([{'text': 'Оставить {}'.format(card.name()),
                             'callbackData': '{}{}{}{}{}'.format(StepAction.chooseCardForAmbassadoring.name,
                                                                 ACTION_DELIMETER,
                                                                 KEEP_CARD_ACTION,
                                                                 ACTION_DELIMETER,
                                                                 card.name())}])

        for card in self.newCards:
            buttons.append([{'text': 'Взять {}'.format(card.name()),
                             'callbackData': '{}{}{}{}{}'.format(StepAction.chooseCardForAmbassadoring.name,
                                                                 ACTION_DELIMETER,
                                                                 GET_CARD_ACTION,
                                                                 ACTION_DELIMETER,
                                                                 card.name())}])

        return buttons

