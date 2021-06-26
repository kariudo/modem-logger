import functools
import logging
import os
import sys

from modem_logger import CM500Parser
from modem_logger.influx import InfluxClient

from apscheduler.schedulers.blocking import BlockingScheduler

# Configuration
influx_base = os.environ.get('INFLUX_URL', 'http://influxdb:8086')
influx_db = os.environ.get('INFLUX_DB', 'modem')
modem_password = os.environ.get('MODEM_PASSWORD', 'password')
frequency = os.environ.get('FREQUENCY_MINUTES', 1)

# Setup logging to STDOUT
logger = logging.getLogger('modemScraper')
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)


def log_exception(function):
    """Exception logging wrapper."""
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except:
            err = "There was an exception in  "
            err += function.__name__
            logger.exception(err)

    return wrapper


@log_exception
def parse_and_log_modem():
    """Parse and log current modem status."""
    logger.info("Querying modem...")
    parser = CM500Parser('admin', modem_password)
    data = parser.query_data_from_modem()
    influxClient = InfluxClient(influx_base)
    influxClient.submit_data(influx_db, data)


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    logger.info(("Configuration loaded as:\n"
                 "\tinflux_url: {}\n"
                 "\tinflux_db: {}\n"
                 "\tmodem_password: {}\n"
                 "\tfrequency_minutes: {}").format(
        influx_base, influx_db, modem_password, frequency))
    logger.info(
        "Starting scheduler, running every {} minute(s).".format(frequency))
    scheduler.add_job(parse_and_log_modem, 'cron',
                      minute='*/{}'.format(frequency))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
