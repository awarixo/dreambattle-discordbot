import os
import logging
from logging.config import dictConfig

LOGGING_CONFIG = {
    "version":1,
    "disable_existing_loggers": False,
    "formatters":{
        "verbose":{
            "format": "%(asctime)s - %(levelname)-10s - %(module)-17s : %(message)s",
            "datefmt": "%H:%M:%S"
        },
        "standard":{
            "format": "%(levelname)-10s - %(module)-15s : %(message)s"
        }
    },
    "handlers":{
        "console": {
            'level': "DEBUG",
            'class': "logging.StreamHandler",
            'formatter': "verbose",
        },
        "console2": {
            "level":"INFO",
            "class":"logging.StreamHandler",
            "formatter":"verbose",
        },
        "file": {
            'level': "INFO",
            'class': "logging.FileHandler",
            "formatter":"verbose",
            'filename' : "infos.log",
            'mode': "w",
        },

    },
    "loggers":{
        "bot":{
            'handlers': ['console'],
            'level':"INFO",
            "propagate": False,
        },
        "discord":{
            'handlers': ['console', 'file'],
            'level': "INFO",
            "propagate": False,
        }
    }
    }
    
dictConfig(LOGGING_CONFIG)