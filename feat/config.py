import datetime

# bokeh-server configuration
pub_zmqaddr ="ipc:///tmp/0"
sub_zmqaddr ="ipc:///tmp/1"
run_forwarder = False
model_backend = {'type' : 'redis', 'redis_port' : 7001, 'start-redis' : False}
secret_key = "foobarbazsecret"
multi_user = False
scripts = ['dashboard.py']

# general FEAT APP configuration
date_range = ('01-01-2014', '07-01-2015')