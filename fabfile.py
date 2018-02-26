from fabric.api import run, env, cd, sudo

env.use_ssh_config = True
env.hosts = ["Oxygen"]


def deploy_init():
    with cd('/home/projects'):
        run('git clone git@github.com:openstate/stembureaus.git')
        with cd('/home/projects/stembureaus/docker'):
            sudo('docker-compose up -d')


def deploy():
    with cd('/home/projects/stembureaus'):
        run('git pull git@github.com:openstate/stembureaus.git')
        run('touch uwsgi-touch-reload')
        #sudo('docker exec stm_nginx_1 nginx -s reload')
