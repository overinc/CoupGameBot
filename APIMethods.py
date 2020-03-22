import requests
import logging
import time
import json
from Credentials import *

base_url = "https://rapi.icq.net/botapi"

def sendMessage(chatId, message, buttons=[]):

    queryParams = {'token': TOKEN}
    queryParams.update({'chatId': chatId})

    queryParams.update({'text': message})

    if buttons:
        queryParams.update({'inlineKeyboardMarkup': json.dumps(buttons)})

    response = requests.get(f"{base_url}/messages/sendText", queryParams)
    print(response.text)
    return json.loads(response.text)['msgId']

def editMessage(chatId, messageId, message, buttons=[]):
    queryParams = {'token': TOKEN}

    queryParams.update({'chatId': chatId})

    queryParams.update({'msgId': messageId})

    queryParams.update({'text': message})

    if buttons:
        queryParams.update({'inlineKeyboardMarkup': json.dumps(buttons)})

    response = requests.get(f"{base_url}/messages/editText", queryParams)
    print(response.text)

def getChatMembers(chatId):
    queryParams = {'token': TOKEN}

    queryParams.update({'chatId': chatId})

    response = requests.get(f"{base_url}/chats/getMembers", queryParams)
    print(response.text)

def answerCallbackQuery(queryId, text=""):
    queryParams = {'token': TOKEN}

    queryParams.update({'queryId': queryId})

    if text:
        queryParams.update({'text': text})

    response = requests.get(f"{base_url}/messages/answerCallbackQuery", queryParams)
    print(response.text)

def getInfo(chatId):
    queryParams = {'token': TOKEN}

    queryParams.update({'chatId': chatId})

    response = requests.get(f"{base_url}/chats/getInfo", queryParams)
    print(response.text)
    return json.loads(response.text)
