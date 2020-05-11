from Credentials import *

collect_players_base_message_text = 'Собираем игроков в Coup!\n\n' \
                                    'Для игры участникам сначала надо написать @{} личное сообщение\n\n' \
                                    'Кто готов играть - отмечайтесь'.format(BOT_NICK)

morph_card_text = 'Прикинуться'
use_card_text = 'Воспользоваться'

choose_start_action_text_ambassador = '{} Ambassador\nи порыться в колоде'
choose_start_action_text_captain = '{} Captain\nи украсть две 2 монетки'
choose_start_action_text_assassin = '{} Assassin\nи пальнуть за 3 монетки'
choose_start_action_text_duke = '{} Duke\nи взять 3 монетки'

doubt_welcome_text_title_ambassador = 'заявляет, что он Ambassador и хочет порыться📚 в колоде.'
doubt_welcome_text_title_duke = 'заявляет, что он Duke и хочет взять 3 монеты🥉.'
doubt_welcome_text_title_foreign_aid_blocker = 'заявляет, что он Duke и блокирует взятие монет.'
doubt_welcome_text_title_captain = 'заявляет, что он Captain и хочет украсть 2 монеты🥈 у'
doubt_welcome_text_title_captain_blocker_by_ambassador = 'заявляет, что он Ambassador и блокирует кражу'
doubt_welcome_text_title_captain_blocker_by_captain = 'заявляет, что он Captain и блокирует кражу'
doubt_welcome_text_title_assassin = 'заявляет, что он Assassin и хочет выстрелить🔫 в'
doubt_welcome_text_title_assassin_blocker_by_contessa = 'заявляет, что он Contessa и блокирует выстрел'