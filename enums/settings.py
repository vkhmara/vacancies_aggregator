from enum import Enum


class BotCommandType(str, Enum):
    HELP = "help"
    LAST_VACANCY_CHECK_DATE = "last_vacancy_check_date"
    START = "start"
    STOP = "stop"
    VACANCIES = "vacancies"
    INCLUDED_WORDS = "included_words"
    ADD_INCLUDED_WORD = "add_included_word"
    DELETE_INCLUDED_WORD = "delete_included_word"
    EXCLUDED_WORDS = "excluded_words"
    ADD_EXCLUDED_WORD = "add_excluded_word"
    DELETE_EXCLUDED_WORD = "delete_excluded_word"
