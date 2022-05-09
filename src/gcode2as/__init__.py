import coloredlogs
import logging

coloredlogs.install(fmt='%(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s', logging.DEBUG)

__version__ = "0.0.1"