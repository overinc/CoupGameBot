from enum import Enum
from random import randrange, choice

class Player:
    def __init__(self, user):
        self.user = user

        self.coinsCount = 2

        self.cards = []
        self.lostedCards = []

    def __eq__(self, other):
        return self.user.userId == other.user.userId

    def __hash__(self):
        return hash(self.user.userId)

    def addCard(self, card):
        self.cards.append(card)

    def cardsCount(self):
        return len(self.cards)

    def hasCardByName(self, cardName):
        for card in self.cards:
            if card.name() == cardName:
                return True
        return False

    def killCardByName(self, cardName):
        for card in self.cards:
            if card.name() == cardName:
                self.cards.remove(card)
                self.lostedCards.append(card)
                break

    def killOneCard(self):
        pos = randrange(len(self.cards))
        card = self.cards.pop(pos)
        self.lostedCards.append(card)
        return card

    def returnCardByName(self, cardName):
        for card in self.cards:
            if card.name() == cardName:
                self.cards.remove(card)
                return card


    def isAlive(self):
        return len(self.cards) > 0

    def isDead(self):
        return len(self.cards) == 0

    def addCoins(self, count):
        self.coinsCount += count

    def takeOutCoins(self, count):
        self.coinsCount -= count
        if self.coinsCount < 0:
            self.coinsCount = 0

    def playerStateString(self, additionalText="", personalMessage = False):
        text = self.user.combinedNameStrig()
        if additionalText:
            text += ' ' + additionalText
        text += '\n'

        cardsCount = len(self.cards)
        if self.isDead():
            text += '💀 Умер' + '\n'
        elif cardsCount == 1:
            text += '☯️ 1 жизнь' + '\n'
        elif cardsCount == 2:
            text += '☯️ 2 жизни' + '\n'

        if (personalMessage):
            text += self.playerCardsString()

        text += self.playerLostedCardsString()

        if self.isDead():
            return text

        text += self.playerCoinsString()
        return text

    def playerCardsString(self):
        if self.isDead():
            return ''

        text = 'Ваши карты:\n'
        for card in self.cards:
            text += '✅ ' + card.name() + '\n'
        return text

    def playerLostedCardsString(self):
        if len(self.lostedCards) == 0:
            return ''

        text = ''
        for lostedCard in self.lostedCards:
            text += '❌ ' + lostedCard.openedString() + '\n'
        return text

    def playerCoinsString(self):
        text = ''
        if self.coinsCount == 0:
            text = '0 монет'
        elif self.coinsCount == 1:
            text = '1 монета'
        elif self.coinsCount >= 2 and self.coinsCount <= 4:
            text = '{} монеты'.format(self.coinsCount)
        elif self.coinsCount >= 5:
            text = '{} монет'.format(self.coinsCount)
        return '💰️ ' + text

class User:
    def __init__(self, userId, nick, name):
        self.userId = userId
        self.nick = nick
        self.name = name

    def combinedNameStrig(self):
        return self.name + ' (' + '@' + self.nick +')'

class Deck:
    def __init__(self):
        self.cards = []

        for i in range(3):
            self.cards.append(Card.Ambassador)
            self.cards.append(Card.Assassin)
            self.cards.append(Card.Captain)
            self.cards.append(Card.Duke)
            self.cards.append(Card.Contessa)

    def getCard(self):
        pos = randrange(len(self.cards))
        card = self.cards.pop(pos)
        return card

    def putCard(self, card):
        self.cards.append(card)


class Card(Enum):
    Ambassador = 1
    Assassin = 2
    Captain = 3
    Duke = 4
    Contessa = 5

    def name(self):
        if self == Card.Ambassador:
            return 'Ambassador'
        if self == Card.Assassin:
            return 'Assassin'
        if self == Card.Captain:
            return 'Captain'
        if self == Card.Duke:
            return 'Duke'
        if self == Card.Contessa:
            return 'Contessa'

    def openedString(self):
        if self == Card.Ambassador:
            return 'Открыт Ambassador'
        if self == Card.Assassin:
            return 'Открыт Assassin'
        if self == Card.Captain:
            return 'Открыт Captain'
        if self == Card.Duke:
            return 'Открыт Duke'
        if self == Card.Contessa:
            return 'Открыта Contessa'