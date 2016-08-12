import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

file_log_handler = logging.FileHandler('{}.log'.format(__name__))
logger.addHandler(file_log_handler)

stderr_log_handler = logging.StreamHandler()
logger.addHandler(stderr_log_handler)


format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(format_string)
file_log_handler.setFormatter(formatter)
stderr_log_handler.setFormatter(formatter)
