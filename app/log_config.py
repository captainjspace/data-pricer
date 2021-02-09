from logging.config import dictConfig
FORMAT = "[%(asctime)s] %(levelname)s: %(module)s: %(filename)s: %(funcName)s() : L%(lineno)s  %(message)s"
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': FORMAT, #'[%(asctime)s] %(levelname)s : %(funcName)20s() : %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


# import logging
# logger = logging.getLogger('root')
# FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
# logging.basicConfig(format=FORMAT)
# logger.setLevel(logging.DEBUG)