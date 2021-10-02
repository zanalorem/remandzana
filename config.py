MAX_CONTENT_SIZE = 1024
SECRET_KEY = NotImplemented

# enable the debug panopticon
REMANDZANA_DEBUG = True

# period in which to record metrics
REMANDZANA_METRICS_PERIOD = 86400
# period in which not to make new metrics calculations
REMANDZANA_METRICS_COOLDOWN = 60

# period for which an authentication key should last
REMANDZANA_AUTH_TIMEOUT = 600
# period in which not to generate a new authentication key
REMANDZANA_AUTH_COOLDOWN = 10

# directory to store feedback as JSON
REMANDZANA_FEEDBACK_DIRECTORY = "feedback"
