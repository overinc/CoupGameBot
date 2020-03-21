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

    def playerStateString(self):
        text = self.user.combinedNameStrig() + '\n'

        cardsCount = len(self.cards)
        if cardsCount == 0:
            text += 'Умер' + '\n'
        elif cardsCount == 1:
            text += '1 жизнь' + '\n'
        elif cardsCount == 2:
            text += '2 жизни' + '\n'

        for lostedCard in self.lostedCards:
            text += lostedCard.openedString() + '\n'

        if cardsCount == 0:
            return text

        text += self.pluralCoinsString()
        return text

    def pluralCoinsString(self):
        if self.coinsCount == 0:
            return '0 монет'
        elif self.coinsCount == 1:
            return '1 монета'
        elif self.coinsCount >= 2 and self.coinsCount <= 4:
            return '{} монеты'.format(self.coinsCount)
        elif self.coinsCount >= 5:
            return '{} монет'.format(self.coinsCount)

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