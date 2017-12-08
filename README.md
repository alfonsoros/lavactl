<!-- Copyright (c) 2017 Siemens AG
Author: Alfonso Ros Dos Santos

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. -->

# LAVA Control

[LAVA](https://www.linaro.org/initiatives/lava/) is a framework for testing 
Linux images within different hardware devices. It offers the functionality 
necessary for setting up a continuous integration process for the development 
of custom Linux distributions. 

LAVA Control is a tool designed to help on the integration of such projects 
with the LAVA framework. For that, LAVA Control tries to hide and default as 
much configuration from the user as possible. The minimum parameters required 
for running a hardware test are the URLs from where to get the Kernel and the 
root file system, together with the corresponding device type.

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

## Usage

You can use this project in two different ways. You can either install
`lava-ctl` as a python package or use it's docker image. To install it as a
python package, you can simply clone this project and execute:

```sh
python setup.py install
```

This will provide the `lava-ctl` command to your path. After this you should be
able to execute:

```sh
lava-ctl --help
```

If you don't want to install `lava-ctl` as a python package and you have docker
installed, you can pull the docker image:

```
docker pull docker.web-of-systems.com/lava-ctl
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

In order to use this feature, you have to set an SFTP server in the same host 
as the LAVA master, where we upload and store different images for testing. 
For using the FTP server, it is necessary to specify the port of the 
server using the parameter `lava.sftp.port`. Additionally, you could use the 
`lava.sftp.user` and `lava.sftp.pass` to specify the user and the password for 
the SFTP server. Alternatively, you can set the environment variables 
`LAVA_STORAGE_FTP_USER` and `LAVA_STORAGE_FTP_PASS` with the same information.

Once the information is set, you can upload an image using the command:

```bash
./lava-ctl.py upload-image --device qemux86 --prefix latest --kernel kernel-file.bin --rootfs rootfs-file.ext4.gz
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

LAVA Control defines a YAML schema to represent an arbitrary number of tests
to be applied inside a single image. For example, one can write a very simple
test inside a YAML file `test.yaml` with the following content:

```yaml
---
tests:
  - name: 'emtpy-file-creation'
    steps:
    - lava-test-case touch-file --shell touch example.txt
```

The test will check if we can create file inside the image. This type of test
is known as _inline_ test in the LAVA documentation because we are specifying
the commands to run in the test directly.

We can use `lava-ctl` to run this tests in a image that we have already
uploaded to the LAVA master using the `lava-ctl upload-image` command. Let's
suppose that we named that image 'qemu-latest' using the `--prefix` flag. To
run this test in the 'qemu-latest' image, we can simply execute:

```sh
lava-ctl run-test --image qemu-latest test.yaml
```

You can also version-control the `test.yaml` file and simply input the reference to the git repository:

```sh
lava-ctl run-test --image qemu-latest --repo git@host/me/my_test_repo.git test.yaml
```

## Configuration

You can find the default configuration in the file `lava_ctl/resources/default_conf.yaml`. In 
case you need a particular configuration, these are the settings available:

```yaml
---
lava:
  server:
    host: "127.0.0.1" #Replace with the IP Address of your LAVA server
    port: 80 #Replace with the port number of your LAVA server
    jobs:
      timeout: 600 # 10 min

  publisher:
    port: 5500 #Replace with the port number of the publisher

  sftp:
    port: 22 #Replace with the port number of the SFTP server

default_image:
  device: qemux86  #Replace with the device type of the default image
  kernel: "http://host/linux-kernel.bin"  #Replace with the url of the kernal image
  rootfs: "http://host/root-filesystem.ext4"  #Replace with the url of the root file system image
  compressed: false  #State whether the rootfs image is compressed
```

You can overwrite this configuration with your own one by giving the path to 
your configuration file with the `-c` flag. For example:

```
lava-ctl -c /path/to/my/config.cfg upload-image --kernel kernel.bin --rootfs filesystem.ext4.gz
```

It is also possible to overwrite individual parameters using the `-p` 
flag. To specify parameters, we use the dot-notation. For example, to 
specify the LAVA user name, you can run:

```
lava-ctl -p lava.server.user=myuser upload-image --kernel kernel.bin --rootfs filesystem.ext4.gz
```
