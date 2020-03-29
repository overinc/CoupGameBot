from enum import Enum

ACTION_DELIMETER = '|'

class StepAction(Enum):
    takeCoin = 1
    tryTakeTwo = 2
    simpleShot = 3
    shuffle = 4
    snipeShot = 5
    steal = 6
    takeThreeCoins = 7

    chooseCardToOpenByKill = 8

    doubtActivePlayer = 9
    chooseCardToOpenByDoubt = 10

    chooseCardForAmbassadoring = 11

DOUBT_TIMER = 1

