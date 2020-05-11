import logging
from Front import *

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y.%m.%d %I:%M:%S %p',
                        level=logging.DEBUG)

    front = Front()
    front.start()