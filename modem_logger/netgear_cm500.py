import re
import requests
import sys
import os
from .influx import InfluxDataPoint, InfluxClient


class CM500Parser(object):
    """Handles the parsing of data from a Netgear CM500 cable modem."""

    def __init__(self, username, password):
        self._auth = (username, password)

    def query_data_from_modem(self):
        """Parse required data from the modem status page."""
        s = requests.Session()

        # Hit the status page twice to deal with the auth challenge
        status_page = 'http://192.168.100.1/DocsisStatus.htm'
        r = s.get(status_page, auth=self._auth)
        r = s.get(status_page, auth=self._auth)

        if r.status_code != 200:
            print("bad response: ", r.status_code, r.text)
            sys.exit(1)

        influx_points = []

        # Parse the downstream channels
        regex = r"(?P<CHANNEL>\d+)\|(?P<STATUS>\w+)\|(?P<MODULATION>\w+)\|(?P<CHANNEL_ID>\w+)\|(?P<FREQUENCY>\d*) Hz\|(?P<POWER>[-\d\.]*)\|(?P<SNR>[\d\.]*)\|(?P<CORRECTABLES>[\d]*)\|(?P<UNCORRECTABLES>[\d\.]*)\|"
        matches = re.finditer(regex, r.text, re.MULTILINE)
        for chan in matches:
            d = InfluxDataPoint("cablemodem")\
                .with_tag('direction', 'downstream')\
                .with_tag('channel', chan.group('CHANNEL'))\
                .with_field('status', chan.group('STATUS'))\
                .with_field('is_locked', 1 if chan.group('STATUS') == "Locked" else 0)\
                .with_field('modulation', chan.group('MODULATION'))\
                .with_field('frequency', int(chan.group('FREQUENCY')))\
                .with_field('frequency', int(chan.group('CHANNEL_ID')))\
                .with_field('power', float(chan.group('POWER')))\
                .with_field('snr', float(chan.group('SNR')))\
                .with_field('codewords_correctable', int(chan.group('CORRECTABLES')))\
                .with_field('codewords_uncorrectable', int(chan.group('UNCORRECTABLES')))
            influx_points.append(d)

        # Parse the upstream channels
        regex = r"\|(?P<channel>\d*)\|(?P<status>[\w\s]*)\|(?P<modulation>\w*)\|(?P<channel_id>\d*)\|(?P<symbol_rate>\d*)\|(?P<frequency>\d*) Hz\|(?P<power>[\d\.]*)"
        matches = re.finditer(regex, r.text, re.MULTILINE)
        for chan in matches:
            d = InfluxDataPoint("cablemodem")\
                .with_tag('direction', 'upstream')\
                .with_tag('channel', chan.group('channel'))\
                .with_field('status', chan.group('status'))\
                .with_field('is_locked', 1 if chan.group('status') == "Locked" else 0)\
                .with_field('modulation', chan.group('modulation'))\
                .with_field('frequency', int(chan.group('frequency')))\
                .with_field('power', float(chan.group('power')))
            influx_points.append(d)
        return influx_points


def main():
    """Run directly for testing logging without scheduler and error handler."""
    influx_base = os.environ.get('INFLUX_URL', 'http://influxdb:8086')
    influx_db = os.environ.get('INFLUX_DB', 'modem')
    p = CM500Parser('admin', os.environ.get('MODEM_PASSWORD', 'password'))
    data = p.query_data_from_modem()
    print("Collected {}/20 data points.".format(len(data)))
    c = InfluxClient(influx_base)
    c.submit_data(influx_db, data)


if __name__ == "__main__":
    main()
    sys.exit(0)
