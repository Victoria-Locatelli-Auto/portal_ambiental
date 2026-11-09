# Publicacao do SIGA na VPS Hostinger (sem Docker)

Este roteiro considera **Ubuntu 24.04 LTS**, um dominio como
`siga.seudominio.com.br` e instalacao direta de Nginx, MySQL, Redis, Gunicorn e
Celery. Substitua dominio, senhas e e-mails antes de executar em producao.

## 1. Preparar a VPS

No hPanel, instale o Ubuntu 24.04 e acesse a VPS pelo Terminal do navegador ou
por SSH. Aponte o registro DNS do dominio para o IPv4 da VPS antes de emitir o
certificado SSL.

```bash
apt update && apt upgrade -y
apt install -y nginx mysql-server redis-server python3-venv python3-dev \
  default-libmysqlclient-dev build-essential pkg-config git certbot python3-certbot-nginx
adduser --system --group --home /opt/siga siga
usermod -a -G www-data siga
mkdir -p /etc/siga /var/www/siga/staticfiles /var/lib/siga/media /var/lib/siga/celerybeat
chown -R siga:www-data /opt/siga /var/www/siga /var/lib/siga
chmod 750 /etc/siga
```

Mantenha as portas do MySQL (3306) e Redis (6379) fechadas para a internet. O
servidor web precisa apenas de SSH, HTTP e HTTPS.

## 2. Criar o banco MySQL

```bash
mysql_secure_installation
mysql -u root -p
```

No console do MySQL, use uma senha exclusiva e forte:

```sql
CREATE DATABASE siga CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'siga'@'localhost' IDENTIFIED BY 'TROCAR_SENHA_MYSQL';
GRANT ALL PRIVILEGES ON siga.* TO 'siga'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 3. Enviar e configurar o projeto

Envie o repositorio para `/opt/siga` por Git/SFTP. Nao envie `.env`, `.venv`,
`media`, caches nem a base local. Depois:

```bash
cd /opt/siga
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
cp deploy/env.production.example /etc/siga/siga.env
chown root:siga /etc/siga/siga.env
chmod 640 /etc/siga/siga.env
```

Edite `/etc/siga/siga.env` e troque todos os valores indicados. Para gerar uma
chave segura do Django:

```bash
/opt/siga/.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## 4. Preparar Django e os servicos

```bash
cd /opt/siga
sudo -u siga .venv/bin/python manage.py migrate
sudo -u siga .venv/bin/python manage.py collectstatic --noinput
sudo -u siga .venv/bin/python manage.py check --deploy
sudo -u siga .venv/bin/python manage.py createsuperuser
cp deploy/systemd/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now siga-web siga-worker siga-beat
```

## 5. Ativar Nginx e HTTPS

Troque o dominio em `deploy/nginx/siga.conf` e execute:

```bash
cp deploy/nginx/siga.conf /etc/nginx/sites-available/siga
ln -s /etc/nginx/sites-available/siga /etc/nginx/sites-enabled/siga
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
certbot --nginx -d siga.seudominio.com.br
```

O certificado SSL depende de um dominio apontado para a VPS; ele nao pode ser
emitido para o endereco IP. Depois de validar o site, login, envio e download de
documentos, aumente gradualmente o HSTS no arquivo de ambiente.

## 6. Validacao e operacao

```bash
systemctl status siga-web siga-worker siga-beat nginx mysql redis-server
journalctl -u siga-web -u siga-worker -u siga-beat --since today
curl -I https://siga.seudominio.com.br/entrar/
```

Antes de liberar aos usuarios, valide: login e permissoes; envio, visualizacao e
historico de documentos; aprovacao e recusa; notificacoes internas; e-mail SMTP;
filtros e exportacao dos relatorios; rotinas de backup e restauracao.

## Atualizacoes futuras

```bash
cd /opt/siga
git pull
.venv/bin/pip install -r requirements.txt
sudo -u siga .venv/bin/python manage.py migrate
sudo -u siga .venv/bin/python manage.py collectstatic --noinput
sudo -u siga .venv/bin/python manage.py check --deploy
systemctl restart siga-web siga-worker siga-beat
```

Faça backup do MySQL, de `/var/lib/siga/media` e de `/etc/siga/siga.env` antes de
cada atualizacao relevante. Teste periodicamente a restauracao dos backups.
