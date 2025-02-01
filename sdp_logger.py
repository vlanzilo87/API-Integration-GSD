#!/usr/bin/env python3
import datetime
import sys, logging, platform
from pathlib import Path
from logging import handlers

# * * * FEATURES * * * 
# 1. Log to multiple outputs at once
#   - muiltiple rsyslog facilities
#   - and/or stdout/stderr and/or file(s)
#
# 2. Have multiple output formatting in same logger by calling set_logging_format between
#   handler instantiations
# 
# 3. Customizable handlers to log multiple output streams at different logging levels

# * * * NOTES * * * 
# - Messaging functions only take 1 argument, the message (or the exception)
#   - The exception function should be passed an exception object as it will print the full exception with it's message

LOGGER = None


def log():
    if LOGGER is None:
        raise KeyError("No logger has been initiated")
    return LOGGER


def create_logger(filename):
    global LOGGER
    filename_without_fq = Path(filename).name
    if LOGGER is None:
        LOGGER = sdp_logger(filename_without_fq)
    return LOGGER


def _get_unique_name(filename):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"{timestamp}.{filename}"


class sdp_logger:

    def __init__(self, filename):

        # Get name of file the logger is running in
        logger_name = _get_unique_name(filename)
        self.logger = logging.getLogger(logger_name)

        self.loglevels = {
            "debug" : logging.DEBUG,
            "info" : logging.INFO,
            "warning" : logging.WARNING,
            "error" : logging.ERROR,
            "critical" : logging.CRITICAL
        }

        self.streams = {
            "stdout" : sys.stdout,
            "stderr" : sys.stderr
        }

        self.formatter = logging.Formatter(f'{filename}[%(process)d] %(funcName)s:: %(levelname)s :: %(message)s')
        self.default_syslog_format = logging.Formatter(f'{filename}[%(process)d]: %(levelname)s :: %(message)s')
        self.logger.setLevel(logging.DEBUG)


    def set_logging_format(self, format):
        try:
            self.formatter = logging.Formatter(format)
        except:
            print(self.logger.name + " -- Incorrect logging Formatter!")


    def set_logging_level(self, level):
        # Values MUST be: "debug", "info", "warning", "error", "critical"
        self.logger.setLevel(self.loglevels[level])


    def setup_syslog(self, facility_, level="debug"):
        if platform.system() == "Linux":
            handler = handlers.SysLogHandler(address="/dev/log", facility=facility_)
        elif platform.system() == "Darwin":
            handler = handlers.SysLogHandler(address="/var/run/syslog", facility=facility_)
        else:
            handler = handlers.SysLogHandler(facility=facility_)
        handler.setLevel(self.loglevels[level])
        handler.setFormatter(self.default_syslog_format)
        self.logger.addHandler(handler)

    def setup_file_out(self, outFile, level="debug"):
        handler = logging.FileHandler(outFile)
        handler.setLevel(self.loglevels[level])
        handler.setFormatter(self.formatter)
        self.logger.addHandler(handler)


    def setup_stream_out(self, outStream="stdout", level="debug"):
        handler = logging.StreamHandler(self.streams[outStream])
        handler.setLevel(self.loglevels[level])
        handler.setFormatter(self.formatter)
        self.logger.addHandler(handler)


    def debug(self, msg):
        if(self.logger.hasHandlers()):
            self.logger.debug(msg)
        else:
            print(self.logger.name + " -- Handler not instantiated!")
            logging.critical(self.logger + " -- Handler not instantiated!")

    def info(self, msg):
        if(self.logger.hasHandlers()):
            self.logger.info(msg)
        else:
            print(self.logger.name + " -- Handler not instantiated!")
            logging.critical(self.logger + " -- Handler not instantiated!")

    def warning(self, msg):
        if(self.logger.hasHandlers()):
            self.logger.warning(msg)
        else:
            print(self.logger.name + " -- Handler not instantiated!")
            logging.critical(self.logger + " -- Handler not instantiated!")

    def error(self, msg):
        if(self.logger.hasHandlers()):
            self.logger.error(msg)
        else:
            print(self.logger.name + " -- Handler not instantiated!")
            logging.critical(self.logger + " -- Handler not instantiated!")

    def critical(self, msg):
        if(self.logger.hasHandlers()):
            self.logger.critical(msg)
        else:
            print(self.logger.name + " -- Handler not instantiated!")
            logging.critical(self.logger + " -- Handler not instantiated!")

    # Exception info is always added to this logging function
    # Should only be called from an exception handler
    # Gets logged at error level
    def exception(self, msg):
        if(self.logger.hasHandlers()):
            self.logger.exception(msg)
        else:
            print(self.logger.name + " -- Handler not instantiated!")
            logging.critical(self.logger + " -- Handler not instantiated!")
    
    # Adding SMTP Handler
    def smtp_handler(self, level="error"): # or level="exception"
        handler = handlers.SMTPHandler(
            mailhost = 'smtp.philasd.org',
            fromaddr = 'esignature@philasd.org',
            toaddrs = ['ti-admin@philasd.org'],
            subject = 'Error Log',
            secure = None
        )

        handler.setLevel(self.loglevels[level])
        self.logger.addHandler(handler)
