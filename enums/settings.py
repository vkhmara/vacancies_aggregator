from enum import Enum


class BotCommandType(str, Enum):
    HELP = "help"
    LAST_VACANCY_CHECK_DATE = "last_vacancy_check_date"
    START = "start"
    STOP = "stop"
    VACANCIES = "vacancies"
