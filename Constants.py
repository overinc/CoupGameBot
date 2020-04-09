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

    tryBlockForeignAid = 12
    doubtForeignAidBlocker = 13

DOUBT_TIMER = 11

STEPS_PAUSE_TIMER = 2

PRINT_PLAYER_NAME_WITH_NICK = True

DEBUG_MODE = True
DEBUG_MANY_MONEY = False

