from fabric.api import run, env, cd, sudo

env.use_ssh_config = True
env.hosts = ["Oxygen"]

def deploy_init():
    with cd('/home/projects'):
        run('git clone git@github.com:openstate/stemlokalen.git')
        with cd('/home/projects/stemlokalen/docker'):
            sudo('docker-compose up -d')

def deploy():
    with cd('/home/projects/stemlokalen/docker'):
        run('git pull git@github.com:openstate/stemlokalen.git')
        run('touch ../app/uwsgi-touch-reload')
        sudo('docker exec stm_nginx_1 nginx -s reload')
