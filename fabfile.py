from fabric.api import run, env, cd, sudo

env.use_ssh_config = True
env.hosts = ["Oxygen"]


def deploy():
    with cd('/home/projects/stembureaus'):
        run('git pull git@github.com:openstate/stembureaus.git')
        sudo('docker exec -it stm_nodejs_1 gulp')
        run('touch uwsgi-touch-reload')
        #sudo('docker exec stm_nginx_1 nginx -s reload')
