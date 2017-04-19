# LAVA Control

This project provides a `lava-ctl` command to facilitate and also automate the 
task of testing a IIoTI OS images in our device testing framework.

## Installing the bash-wrapper

To avoid typing too much, this project includes a small hash script that can be 
used to skip typing the docker commands. You can then "install" this app by 
executing

```bash
docker run docker.web-of-systems.com/lava-ctl bash > lava-ctl
chmod +x lava-ctl
./lava-ctl --help
```

## Configuration file

You can find the default configuration file in `lava/config/default.cfg`. In 
case you need a particular configuration, these are the settings available:

```ini
[lava.server]
addr = hostname // IP address or hostname of the lava master
port = 1234 // port of the lava http interface
url = http://%(addr)s:%(port)s // leave this
files = %(url)s/lava-files // http server url from where to get the images
user = %(LAVA_USER)s // lava user
token = %(LAVA_TOKEN)s // lava user's token

[lava.sftp]
user =  %(LAVA_STORAGE_FTP_USER)s   // FTP user name to upload the files
pass =  %(LAVA_STORAGE_FTP_PASS)s   // FTP user password
port = 2040 // sftp port (same as ssh usually)

[lava.jobs]
sleep = 5 // waiting time on each polling loop iteration
waiting_timeout = 600 // timeout when waiting in the queue
running_timeout = 120 // timeout when the job is running
```

You can specify you configuration file using the `-c` option. For example:

```
lava-ctl -c /path/to/my/config.cfg kernel.bin filesystem.ext4.gz
```

## Submitting a LAVA job

You can submit a test job with

```bash
lava-ctl -v /path/to/kernel.bin /path/to/filesystem.ext4.gz
```

## Debugging

This image uses environment variables for the configuration. In case of 
trouble, you can show the configuration used by the App with the 
`--show-config` option:

```
lava-ctl --show-config kernel.bin filesystem.ext4.gz
```
