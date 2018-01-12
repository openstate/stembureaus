from fabric.api import run, env, cd, sudo

env.use_ssh_config = True
env.hosts = ["Oxygen"]

def deploy():
    with cd('/home/projects/stemlokalen/docker'):
        run('git pull git@github.com:openstate/stemlokalen.git')
        run('touch ../app/uwsgi-touch-reload')
