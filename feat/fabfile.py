from time import sleep
import os
from fabric.api import (
    env, 
    task,
    hosts,
    local, 
    run, 
    lcd, 
    cd, 
    sudo,
    execute,
    prompt,
    abort,
    puts,
    put,
    settings,
)
from fabric.contrib.files import exists

# import fabric_gunicorn as gunicorn

# HOST SETTINGS
PRODUCTION_SERVER = '10.1.93.203'
STAGING_SERVER = "10.1.90.126"
env.hosts = [PRODUCTION_SERVER]
env.user = "feat"
env.key_filename = "~/.ssh/psteinberg1.pem"

# REMOTE SETTINGS
env.user_home = "/home/feat/"
env.install_supervisord = True
env.server_deployment_dir = "%s%s" % (env.user_home, "FEAT/")

@task
def deploy_production(env_name="feat_env"):
    run('cd %sxdata-2015/bokeh_app/' % (env.user_home))
    run('source activate %s' % env_name)
    run('git pull')

    run('sh clean_running.sh')
    run('supervisord')

@task
def bokeh_install_env_server(env_name="bokeh_server", install_supervisor=True, py_version='2.7'):
    run('conda create --yes -n %s python=%s bokeh' % (env_name, py_version))
    run('source activate %s' % env_name)
    run('conda install --yes -n %s redis redis-py' % env_name)
    run('conda install --yes -n %s gunicorn' % env_name)

    if env.install_supervisord:
        run('conda install --yes -n %s -c https://conda.binstar.org/binstar supervisor' % env_name)

@task
def bokeh_install_env_local(env_name="bokeh_server", install_supervisor=True, py_version='2.7'):
    local('conda create --yes -n %s python=%s bokeh' % (env_name, py_version))
    local('source activate %s' % env_name)
    local('conda install --yes -n %s redis redis-py' % env_name)
    local('conda install --yes -n %s gunicorn' % env_name)

    if install_supervisor:
        local('conda install --yes -n %s -c https://conda.binstar.org/binstar supervisor' % env_name)

@task
def bokeh_remove_env_local(env_name="bokeh_server"):
    local('conda remove --yes -n %s --all' % env_name)

@task
def bokeh_config_env_server():
    # upload the source tarball to the temporary folder on the server

    # run('''python -c "import os;os.mkdir('%s')''' % (env.server_deployment_dir))
    run('''python -c "import os\nif not os.path.exists('%s'):\n    try:\n      os.makedirs('%s')\n    except:  exit(2)" ''' %
        (env.server_deployment_dir, env.server_deployment_dir))
    put("config.py", env.server_deployment_dir)
    put("forwarder.py", env.server_deployment_dir)
    put("start_redis.sh", env.server_deployment_dir)
    put("start_bk_gunicorn.sh", env.server_deployment_dir)
    put("start_forwarder.sh", env.server_deployment_dir)
    put("supervisord.conf", env.server_deployment_dir)
    put("xapp/cols_schema.py", env.server_deployment_dir)
    put("xapp/dashboard.py", env.server_deployment_dir)
    put("xapp/actions.py", env.server_deployment_dir)
    for _file in os.listdir('xapp'):
        if _file.endswith(".py"):
            put("xapp/%s" % _file, env.server_deployment_dir)

    run('''python -c "import os\nif not os.path.exists('%splugins'):\n    try:\n      os.makedirs('%splugins')\n    except:  exit(2)" ''' %
        (env.server_deployment_dir, env.server_deployment_dir))
    for _file in os.listdir('xapp/plugins'):
        if _file.endswith(".py"):
            put("xapp/plugins/%s" % _file, env.server_deployment_dir + 'plugins')

    run('''python -c "import os\nif not os.path.exists('%sdata'):\n    try:\n      os.makedirs('%sdata')\n    except:  exit(2)" ''' %
        (env.server_deployment_dir, env.server_deployment_dir))
    run('''python -c "import os\nif not os.path.exists('%sdata/securities'):\n    try:\n      os.makedirs('%sdata/securities')\n    except:  exit(2)" ''' %
        (env.server_deployment_dir, env.server_deployment_dir))

    for _file in os.listdir('xapp/data/securities'):
        if _file.endswith(".csv"):
            put("xapp/data/securities/%s" % _file, env.server_deployment_dir + 'data/securities')

@task
def bokeh_config_env_local(apps_paths=None):
    # upload the source tarball to the temporary folder on the server
    # run('mkdir %s' % env.server_deployment_dir)
    put("config.py", env.server_deployment_dir)
    put("forwarder.py", env.server_deployment_dir)
    put("start_redis.sh", env.server_deployment_dir)
    put("start_bk_gunicorn.sh", env.server_deployment_dir)
    put("start_forwarder.sh", env.server_deployment_dir)
    put("supervisord.conf", env.server_deployment_dir)
    put("crossfilter", env.server_deployment_dir)
