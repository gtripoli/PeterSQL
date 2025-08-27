import logging.config

LOG_FMT = "%(asctime)s %(process)s %(levelname)s %(name)s: %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(format=LOG_FMT, datefmt=DATE_FMT)

logger = logging.getLogger("PeterSQL")
logger.setLevel(logging.DEBUG)
