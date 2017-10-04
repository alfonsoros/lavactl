# LAVA Control
[![pipeline 
status](https://code.siemens.com/iot/DOPS/lava-ctl/badges/master/pipeline.svg)](https://code.siemens.com/iot/DOPS/lava-ctl/commits/master)

[LAVA](https://www.linaro.org/initiatives/lava/) is a framework for testing 
Linux images within different hardware devices. It offers the functionality 
necessary for setting up a continuous integration process for the development 
of custom Linux distributions such as for example the [Embeddedd 
System](https://code.siemens.com/webofsystems/ebs-yocto) project. 

LAVA Control is a tool designed to help on the integration of such projects 
with the LAVA framework. For that, LAVA Control tries to hide and default as 
much configuration from the user as possible. The minimum parameters required 
for running a hardware test are the URL from where to get the Kernel and root 
file system, together with the corresponding device type.

For example, you can write the following to a `test.yaml` file:

```yaml
image:
  kernel: http://host/linux-kernel.bin
  rootfs: http://host/root-filesystem.ext4
  device: qemux86
```

and then simply call `lava-ctl.py` as follows:

```bash
./lava-ctl.py run-test test.yaml
```

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

| Command                              | Description                                                     |
|--------------------------------------|-----------------------------------------------------------------|
| [submit-job](#submitting-a-lava-job) | Submits a LAVA job definition from a file                       |
| [upload-image](#uploading-an-image)  | Uploads a Linux image to the FTP server                         |
| [list-images](#listing-the-images)   | Lists the identifiers for the images already in the LAVA server |
| [run-test](#running-a-test-job)      | Test an image                                                   |


## Submitting a LAVA job

This command is equivalent to the `lava-tool submit-job` command. With this 
command you can specify a LAVA Job definition from a file and submit it to the 
LAVA master. Please refer to the [linaro documentation](https://validation.linaro.org/static/docs/v2/first-job.html) on 
how to write these job definitions.

```bash
lava-ctl submit-job job.yaml
```

## Uploading an image

This is a feature specific to our LAVA set up. We have set a SFTP server in the 
same host as the LAVA master where we upload and store different images for 
testing. For using the FTP server, it is necessary to specify the port of the 
server using the parameter `lava.sftp.port`. Additionally, you could use the 
`lava.sftp.user` and `lava.sftp.pass` to specify the user and the password for 
the SFTP server. Alternatively, you can set the environment variables 
`LAVA_STORAGE_FTP_USER` and `LAVA_STORAGE_FTP_PASS` with the same information.

Once the information is set, you can upload an image using the command:

```bash
./lava-ctl.py upload-image --device qemux86 --prefix latest kernel-file.bin rootfs-file.ext4.gz
```

where the `--prefix` option is used as an identifier for the uploaded image. 
After uploading it to the FTP server, you can use this image for testing by 
simply referencing to the image `prefix`. For example, you can create a 
`test.yaml` with the following content:

```yaml
image: "latest"
```

and run the test with: `./lava-ctl.py run-test test.yaml`

## Listing the images

All the images uploaded using the [upload-image](#uploading-an-image) command, 
are stored together with the meta-data necessary to reference them in tests. 
You can list the current available images using the `list-images` command.

```bash
./lava-ctl.py list-images
```

You can refer to these images in the test file.


## Running a Test Job

LAVA Control defines a YAML schema for representing a arbitrary number of tests 
in a single image or also defining muti-node tests. The tests can be written 
separately and version-controlled in separate repositories. Each test of this 
kind must specify a name, git source url and revision hash. Additionally, it is 
also possible to specify a set of key-value pairs of parameters to be available 
inside the test.

For example, we can write a `test.yaml` file that looks as follow:

```yaml
---
image: 'qemux862017-10-02'
tests:
  - repository: 'git@code.siemens.com:iot/DOPS/device-integration-test.git'
    name: 'agents-integration'
    revision: '6e196e9bd1950b49a953f9092cacaaef175b1627'
    params:
      hello: 'world'
```

This test will run the `agents-integration.yaml` test definition inside the 
`qemux862017-20-02` image and report the results.


## Configuration

You can find the default configuration file in `conf/default.yaml`. In 
case you need a particular configuration, these are the settings available:

```yaml
---
lava:
  server:
    host: "139.25.40.26"
    port: 2041
    jobs:
      timeout: 600 # 10 min

  publisher:
    port: 2042

  sftp:
    port: 2040
```

You can overwrite this configuration with your own one by giving the path to 
the configuration file with the `-c` flag. For example:

```
lava-ctl -c /path/to/my/config.cfg upload-image kernel.bin filesystem.ext4.gz
```

It is also possible to just overwrite individual parameters using the `-p` 
flag. To specify the parameter, we use the dot-notation. For example, to 
specify the LAVA user name, you can run:

```
lava-ctl -p lava.server.user=myuser upload-image kernel.bin filesystem.ext4.gz
```
