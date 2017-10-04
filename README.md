# LAVA Control

This tool is designed to help in the continuous integration process of the 
[Embeddedd System](https://code.siemens.com/webofsystems/ebs-yocto) project.  
This tool is used to first boot the Linux images produced by this project and 
then running different types of tests for the supported set of devices.

## Installing the bash-wrapper

To avoid typing too much, this project includes a small hash script that can be 
used to skip typing the docker commands. You can then "install" this app by 
executing

```bash
docker run docker.web-of-systems.com/lava-ctl bash > lava-ctl
chmod +x lava-ctl
./lava-ctl --help
```

## Commands

| Command      | Functionality                                                   |
|--------------|-----------------------------------------------------------------|
| submit-job   | Submits a LAVA job definition from a file                       |
| upload-image | Uploads a Linux image to the FTP server                         |
| list-images  | Lists the identifiers for the images already in the LAVA server |
| run-test     | Test an image                                                   |


## Submitting a LAVA job

This command is equivalent to the `lava-tool submit-job` command. With this 
command you can specify a LAVA Job definition from a file and submit it to the 
LAVA master. Please refer to the [linaro documentation](https://validation.linaro.org/static/docs/v2/first-job.html) on 
how to write these job definitions.

```bash
lava-ctl submit-job job.yaml
```

## Testing a LAVA Test

It might be the case that you are developing a test to be run on the images, in 
that case, you can submit a test job to try your test on the latest image of 
in the artifactory. You will need to specify 2 things, the git URL of the 
repository containing the test and the name of the test file. Optionally you 
can also specify the revision of the test.

In order to have an 'easy' way to specify these 3 things as a command line
argument, we have decided to concatenate these 3 in a string joined by `#`
characters in the following order:

```
git@repository.com/test/repo.git#smoke-tests.yaml#12345678
```

#### Example

Here is an example on how the integration test are evaluated:

```bash
lava-ctl --test-repo git@code.siemens.com:iot/device-integration-test.git#agents-integration.yaml#a3e2b765
```

## Debugging

This image uses environment variables for the configuration. In case of 
trouble, you can show the configuration used by the App with the 
`--debug` option:

```
lava-ctl --debug --kernel kernel.bin --rootfs filesystem.ext4.gz
```

## Configuration file

You can find the default configuration file in `config/default.cfg`. In 
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

[artifactory]
user = %(ATF_USER)s
pass = %(ATF_PASS)s
server = https://wosatf.ct.siemens.com/artifactory
latest = wos-images-snapshot/ses-qemux86-devel-EMBS-P-0.4-r1-92-g3e76cfc
kernel = bzImage-qemux86.bin
rootfs = ses-image-devel-qemux86.ext4
```

You can specify you configuration file using the `-c` option. For example:

```
lava-ctl -c /path/to/my/config.cfg --kernel kernel.bin --rootfs filesystem.ext4.gz
```
