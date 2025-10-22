### for Redis use Upstash

### create EC2 with ~20 GB , t3.micro

### Add Security Group 22 (SSH), 80 (HTTP), 443 (HTTPS) and additional ports if need

### in EC2 
* sudo apt update && sudo apt upgrade -y
* sudo apt install -y python3 python3-venv python3-pip nginx git
* git clone <your-repo-url>
* cd repo-name
* python3 -m venv venv
* source venv/bin/activate
* pip install -r requirements.txt

### creating service to run continuously
* create /etc/systemd/system/flask.service
* content for flask.service in /service-flask
### to start service
* sudo systemctl daemon-reload
* sudo systemctl enable flask
* sudo systemctl start flask
* sudo journalctl -u flask -f


### on revisit of ec2 to re-start
* cd repo-app
* source venv/bin/activate
* pip install -r requirements.txt

    