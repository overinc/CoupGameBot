import requests
import logging
import time
import json
from Game import *
from APIMethods import *
from Credentials import *

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
