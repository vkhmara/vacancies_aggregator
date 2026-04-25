class RedisConfig:
    LAST_VACANCY_CHECKED_DATE_FIELD = "last_checked_field"


class Config:
    REDIS: RedisConfig = RedisConfig()


CONFIG = Config()
