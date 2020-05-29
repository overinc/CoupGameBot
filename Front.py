import json
from bot.bot import Bot
from bot.handler import *
from Game import *
from Credentials import *

class Front:
    def __init__(self):
        self.bot = Bot(token=TOKEN)

        self.games = {}

    def start(self):
        bot = self.bot

        response = bot.events_get(0)
        while response.json()['events']:
            response = bot.events_get(0)

        def messageEventHandler(bot, event):
            if '@chat.agent' in event.from_chat:
                self.processGroupMessage(event)
            else:
                self.processUserMessage(event)

        def addedToGroupchatEventHandler(bot, event):
            self.processAddedToGroupchat(event)

        def buttonTapEventHandler(bot, event):
            self.processButtonTap(event)

        bot.dispatcher.add_handler(MessageHandler(callback=messageEventHandler))
        bot.dispatcher.add_handler(NewChatMembersHandler(callback=addedToGroupchatEventHandler))
        bot.dispatcher.add_handler(BotButtonCommandHandler(callback=buttonTapEventHandler))

        bot.start_polling()
        bot.idle()


    def processUserMessage(self, event):
        userId = event.from_chat
        eventText = event.text.lower()

        text = 'Возможность игры активирована\n\n' \
               'Для того чтобы поиграть в Coup добавьте меня в группу где будет проходить игра'

        self.bot.send_text(chat_id=event.from_chat, text=text, inline_keyboard_markup=self.rulesButtons())

        if DEBUG_MODE:
            self.sendWelcomeMessage(userId)

            if '/new' in eventText or '/newgame' in eventText:
                self.processNewGameCommand(userId)
            elif '/cancel' in eventText:
                self.processCancelCommand(userId)

    def processGroupMessage(self, event):
        chatId = event.from_chat
        eventText = event.text.lower()

        if BOT_NICK.lower() in eventText or BOT_ID in eventText:
            self.sendWelcomeMessage(chatId)
        elif '/start' in eventText or '/help' in eventText:
            self.sendWelcomeMessage(chatId)
        elif '/new' in eventText or '/newgame' in eventText:
            self.processNewGameCommand(chatId)
        elif '/cancel' in eventText:
            self.processCancelCommand(chatId)

    def processAddedToGroupchat(self, event):
        chatId = event.data.get('chat').get('chatId')
        for newMember in event.data.get('newMembers'):
            if newMember['userId'] == BOT_ID:
                self.sendWelcomeMessage(chatId)

    def sendWelcomeMessage(self, chatId):
        bot = self.bot

        text = 'Добро пожаловать в Coup!\n\n' \
               '/start - показать это сообщение\n\n' \
               '/new - начать новую игру\n' \
               '/cancel - отменить игру'

        bot.send_text(chat_id=chatId, text=text, inline_keyboard_markup=self.rulesButtons())

    def rulesButtons(self):
        buttons = []
        buttons.append(
            [{'text': 'Правила игры', 'url': 'https://upload.snakesandlattes.com/rules/c/CoupTheResistance.pdf'}])
        buttons.append(
            [{'text': 'Локализованные правила', 'url': 'https://tesera.ru/images/items/200514/coup_short_rules_ru_v_1_1.pdf'}])
        return json.dumps(buttons)

    def processNewGameCommand(self, chatId):
        games = self.games

        # chatInfo = self.bot.get_chat_info(chatId)

        if chatId in games.keys():
            game = Game(chatId, self.onGameEnded)
            games.update({chatId: game})
            game.startCollectPlayers()
        else:
            game = Game(chatId, self.onGameEnded)
            games.update({chatId: game})
            game.startCollectPlayers()

    def processCancelCommand(self, chatId):
        games = self.games

        if chatId in games.keys():
            games.pop(chatId)
            self.bot.send_text(chatId, 'Игра завершена')

    def processButtonTap(self, event):
        chatId = event.data.get('message').get('chat').get('chatId')
        queryId = event.data.get('queryId')
        games = self.games

        if '@chat.agent' in chatId:
            if chatId in games.keys():
                game = games.get(chatId)
                game.handleButtonTap(event)
            else:
                self.bot.answer_callback_query(queryId, "Сейчас в этой группе нет игры")
        else:
            for game in games.values():
                if game.findPlayerByUserId(chatId):
                    game.handleButtonTap(event)
                    return

            if DEBUG_MODE:
                if chatId in games.keys():
                    game = games.get(chatId)
                    game.handleButtonTap(event)
                    return

            self.bot.answer_callback_query(queryId, "Вы не участвуюте ни в одной игре")

    def onGameEnded(self, game):
        self.games.pop(game.gameGroupchatId)