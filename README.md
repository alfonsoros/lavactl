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
Linux images among different hardware devices. It presents itself as a possible 
solution for the continuous integration process of Embedded Linux systems.

LAVA Control is a tool that aims to help on the management of the continuous 
integration process that uses the LAVA framework. It does so through a single 
`YAML` configuration file that can be added to your project which specifies 3 
things:

* The URL where to get the image to be tested.
* The device template to use for the device configuration.
* The test suites to execute.

Here is an example of the configuration files used by `lava-ctl`:

```yaml
---
image:
  kernel: http://my_artifacts/linux-kernel.bin
  rootfs: http://my_artifacts/root-filesystem.ext4
  rootfs_compressed: false
device: qemux86
test_repos:
  - url: git@github.com:my_embedded_linux/test.git
    branch: ssh_tests
    tests:
      - ssh/ssh.yaml
      - ssh/scp.yaml
```

After configuring the tool, this file can be passed directly to `lava-ctl` and 
start the tests execution.

```bash
lava-ctl run test.yaml
```

## Usage

Before using using this tool you have to set the corresponding configuration 
to your LAVA setup. You can use this with the `lava-ctl config` command.

Here is the list of the configuration parameters. 

| Parameter             | Description                                                          |
|-----------------------|----------------------------------------------------------------------|
| `lava.server.host`    | IP or domain name of your LAVA master instance (default `localhost`) |
| `lava.server.port`    | Port number of the LAVA service (default `80`)                       |
| `lava.server.user`    | LAVA user name that will be used by the tool to send the jobs        |
| `lava.server.token`   | LAVA user's token used for authentication with the master            |
| `lava.publisher.port` | Port number of the LAVA publisher (used for notifications)           |


You can set each parameters permanently with the [config command](#config-command) like this:

```sh
lava-ctl config --set lava.server.host=192.168.0.10
```

or use the `-p` flag to override them when executing `lava-ctl` like this:

```sh
lava-ctl -p lava.server.host=192.168.0.10 run tests/qemux86.yaml
```

## Commands

| Command                   | Description                            |
|---------------------------|----------------------------------------|
| [run](#run-command)       | Test an image                          |
| [config](#config-command) | Test an image                          |
| submit-job                | Same as `lava-tool submit-job` command |
| version                   | Prints out the `lava-ctl` version      |


## Run Command

LAVA Control defines a YAML schema to represent an arbitrary number of tests
to be applied inside a single image. 

```yaml
---
image:
  kernel: http://my_artifacts/linux-kernel.bin
  rootfs: http://my_artifacts/root-filesystem.ext4
  rootfs_compressed: false
device: qemux86
test_repos:
  - url: git@github.com:my_embedded_linux/test.git
    branch: ssh_tests
    tests:
      - ssh/ssh.yaml
      - ssh/scp.yaml
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

## Config Command

The `config` command allows you to either `--set` or `--get` the configuration 
parameters listed in the [usage section](#usage).  Here is the default 
configuration file installed with `lava-ctl`:

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

default_image:
  device: qemux86  #Replace with the device type of the default image
  kernel: "http://host/linux-kernel.bin"  #Replace with the url of the kernal image
  rootfs: "http://host/root-filesystem.ext4"  #Replace with the url of the root file system image
  compressed: false  #State whether the rootfs image is compressed
```

You can override the parameters using _dot-notation_ to access the particular 
keys. For example, if you want to set the `timeout` parameter for the LAVA jobs 
to `1000` seconds, you can run:

```
lava-ctl config --set lava.server.jobs.timeout=1000
```

You can also overwrite the entire configuration with your own one by giving the 
path to your configuration file with the `-c` flag. For example:

```
lava-ctl -c /path/to/my/config.yaml run my_test.yaml
```

It is also possible to overwrite individual parameters using the `-p` 
flag. For example, to specify the LAVA user name, you can run:

```
lava-ctl -p lava.server.user=myuser run my_test.yaml
```
