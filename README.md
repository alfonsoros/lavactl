# LAVA Control

This project provides a `lava-ctl` command to facilitate and also automate the 
task of testing a IIoTI OS image in our device testing framework.

### Submitting a LAVA job

To submit a job with the Docker image, the directory with the files 
corresponding to the image being tested must be mounted inside the container. 
For example, if the current directory has the files:

```bash
$ ls
kernel.bin
filesystem.ext4.gz
```

you can submit a test job with

```bash
docker run --rm -v $PWD:/files -t docker.web-of-systems.com/lava-ctl /files/kernel.bin /files/filesystem.ext4.gz
```

