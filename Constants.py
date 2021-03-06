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
    doubtSecondaryPlayer = 10
    chooseCardToOpenByDoubt = 11

    chooseCardForAmbassadoring = 12
    tryBlockForeignAid = 13
    chooseActionForBlockStealing = 14
    chooseActionForBlockSnipeShot = 15

DOUBT_TIMER = 11

STEPS_PAUSE_TIMER = 2

PRINT_PLAYER_NAME_WITH_NICK = False

DEBUG_MODE = False
DEBUG_MANY_MONEY = False

