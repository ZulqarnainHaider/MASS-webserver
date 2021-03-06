# Install requirements
 * Install Python 3 (version >= 3.6.9) and python3-pip. For example, `sudo apt install python3`
 * Install PostgreSQL (any version) and `postgresql-server-dev-all`. For example, `sudo apt install postgresql postgresql-server-dev-all`
 * Start PosgreSQL, create a new user login, and configure database information in `server_config.yaml`. Example commands are:
     * `sudo su`
     * `su - postgres`
     * `psql`
     * `create user optimizer with password '123456';`
     * `create database optimizerdb;`
     * `\q` then `exit` twice
 * Clone/Download this repository: `git clone https://github.com/minhhpham/MASS-webserver`
 * `cd MASS-webserver`
 * `pip3 install -r requirements.txt`
 * Run server in development mode: `sudo python3 MASS-webserver.py`
 * If seeing a bug that says <span style="color:red"> Peer authentication failed for user "optimizer" </span>, do the following:
    * Navigate to file Postgres' config file named `pg_hba.conf`, usually located at `/etc/postgresql/10/main/pg_hba.conf`
    * Open file with root privilege: `sudo nano /etc/postgresql/10/main/pg_hba.conf`
    * Navigate to end of file, there will be a table. Change the entire last column to <span style="color:red"> 'md5'</span>
    * Save file and restart Postgres service with `sudo systemctl restart postgresql`

# Deploy:
 * First install Nginx:
     * `sudo apt-get install nginx`
     * `sudo cp nginx-MASS-flask.conf /etc/nginx/conf.d/`
     * `sudo systemctl restart nginx`

 * Run server:
    * `sudo python3 setup.py`
    * `sudo systemctl daemon-reload && sudo systemctl start MASS-flask`

# Use the web app:
Go to your browser and type `localhost:10000`