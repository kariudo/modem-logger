# Modem Logger

Parses the data returned by the Netgear CM500 status page to collect data for logging to InfluxDB.

## Usage

There are 4 required environment variables that default as below:

```
'INFLUX_URL', 'http://influxdb:8086'
'INFLUX_DB', 'modem'
'MODEM_PASSWORD', 'password'
'FREQUENCY_MINUTES', 1
```

### Docker

Can be built and run directy using the `dockerfile`, or using the provided `docker-compose.yml` either itself or as a template.

Best to share a stack with your `influxdb` container for the easiest configuration over the bridge.

### Manually

Can be run directly with :

`> python app.py`

## Cronograf

An example dashboard json for cronograf is included.