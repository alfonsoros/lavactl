import os

SLEEP = 5
WAITING_TIMEOUT = 600
RUNNING_TIMEOUT = 120

lava_server = os.environ['LAVA_SERVER_ADDR']
lava_port = 2041

lava_user = os.environ['LAVA_USER']
lava_token = os.environ['LAVA_TOKEN']

lava_ftp_usr =  os.environ['LAVA_STORAGE_FTP_USER']
lava_ftp_pwd =  os.environ['LAVA_STORAGE_FTP_PASS']

lava_rpc_url = "http://%s:%s@%s/RPC2" % (lava_user, lava_token, lava_server)
