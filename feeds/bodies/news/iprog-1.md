Page 1 of 2As an applications programmer, you may have dismissed or overlooked containerization as not being relevant. Wrong. Containers are useful in every programming environment. The problem is becoming familiar with their quirks and idiosyncrasies. Help is at hand.  This is the first exclusive extract from the newly-published: **  
**

## Programmers Guide To Containers  
with Docker and Visual Studio Code

#### By Mike James

[](<https://www.amazon.com/dp/1871962684?_encoding=UTF8&qid=&sr=&linkCode=ll1&tag=iprog-20&linkId=13e3793e24ef8654297f065cab51686a&language=en_US&ref_=as_li_ss_tl>)

#### Contents****

  1. Chapter 1 Docker
  2. Chapter 2 Why Containers?
  3. Chapter 3 Getting Started With Docker  
Extract 1: [Starting](<https://www.i-programmer.info/programming/241-devops/19178-programmers-guide-to-containers-starting.html>) ***NEW!!!
  4. Chapter 4 Container As File System 
  5. Chapter 5 Docker Compose for Build and Run
  6. Chapter 6 Containers as Functions 
  7. Chapter 7 Connecting To Containers
  8. Chapter 8 A Web Server
  9. Chapter 9 VS Code Containers
  10. Chapter 10 Dev Containers
  11. Appendix I Reset Docker 
  12. Appendix II How Containers Work 

<ASIN:B0HKY1GQ5K>

## Getting Started With Docker

The current dominant way to create and manage containers is Docker, and even if you decide to migrate to some other tool, they are all based on Docker and compatible with it to some degree. In most cases, the use of the term “container” is synonymous with “Docker”.

## How To Use Docker

There are three main components to the Docker system:

  * Docker Engine – the program that actually looks after containers
  * Docker CLI – the command line program that can be used to create and monitor containers
  * Docker Desktop – a graphical user interface (GUI) that lets you create and monitor containers.

The most common way to encounter Docker for the first time is to use Docker Desktop, but using the CLI and VS Code (see later) is also a good way of working. Most users opt to work with Docker Desktop, but notice that this is a paid-for option for companies with 250 employees and more than $10 million annual revenue. This seems very reasonable, but also notice that you have to open a Docker user account and provide your email address. A more technical problem is that Desktop insists on running your containers inside a VM that it automatically creates, and this can be a problem if you try mixing containers from different sources. The Docker engine and CLI are fully open source and can be freely downloaded. The CLI is the way that other tools such as VS Code use to work with Docker and as such, there is a big advantage in knowing how it works. In short, it is better to start out using the Docker CLI and use Desktop if you find it helps later.

## Installing Docker

If you install Docker Desktop, then you automatically have the Docker Engine and the Docker CLI installed. This is the method recommended in the documentation for installing the Docker Engine even if you don’t intend to use Desktop. However, you can install the CLI and the Docker Engine without Docker Desktop and this results in a simpler configuration. How to do this is explained on the Docker web site under the heading Install Docker Engine:

    <https://docs.docker.com/engine/install>

At the time of writing, you don’t need a Docker account to install Docker CLI. All you have to do is select the operating system and architecture you are using and follow the instructions. The main complication is that the instructions ask you to use the Docker package repository rather than the packages provided by the distribution you are using. The reason for this complication is said to be the need to provide packages that are more up-to-date than most distributions provide. Most distributions do provide a version of Docker that you can simply install using the standard package manager, and often this works well enough as long as you don’t need to use a recently released feature. My advice is to install Docker Engine and the CLI and see if you need or want the full Docker Desktop after using it for a while. Docker Desktop has a way of making things more complicated to configure and hence it is the source of additional errors. Even using the Docker CLI installed alongside Docker Desktop in standalone mode can cause problems. You may discover that you can’t actually run Docker after installing it. If so, add the current user to the docker user group:

    sudo usermod -aG docker $USER 

log out and back in again or use:

    newgrp docker  

Another problem that occurs is permission to connect to Docker. For example, to let VS Code connect you need to use:

    sudo chmod 666 /var/run/docker.sock

It is important to only do these actions on a development machine as adding a user to the docker group gives that user root access to the file system via docker. Docker runs as root and this is a security problem in some situations and there are instructions for how to run it without root permissions on the web. For a development system running as root is simpler and of course safe.

## The Daemon

Although the command line occupies most of our attention, it is the Docker daemon that does all the work. This is the server that manages the running of our containers. Most installations configure and start the daemon automatically, but if you need to add auto-start manually use:

     sudo systemctl enable docker.service
     sudo systemctl enable containerd.service

and to stop it starting automatically:

     sudo systemctl disable docker.service
     sudo systemctl disable containerd.service

You can also manage it using systemd unit files and start, stop and restart it using:

     sudo systemctl _action_ docker

where _a_ _ction_ is one of start, stop or restart. Although it isn’t often necessary, you can also customize the way that the daemon runs using the daemon.json file, which is usually stored in /etc/docker/ or in ~/.config/docker/. There are a very large number of configuration options, most of which you will probably never need to use. See the documentation for details. One common customization is the need to set the daemon to use a proxy for internet access:

    {
      "proxies": {
        "http-proxy": "<http://proxy.example.com>:3128",
        "https-proxy": "<http://proxy.example.com>:3128",
        "no-proxy": "*.test.example.com,.example.org,12  
                                        7.0.0.0/8"
      }
    }

The daemon receives its commands to run or terminate a container via a standard Inter-Process Communication (IPC) socket, /var/run/docker.sock. This is also the method that allows other programs to control Docker via an API. There are Go and Python libraries that let you do everything you can do with Docker but under program control. The functions in each of the languages follow the standard Docker commands and aren’t covered in this book, but you should have no problem using them if you need to. One possibility that using a socket makes available is remote operation by converting the local IPC into a network IP socket. This allows you to use Docker commands to set up and manage containers on a remote machine. Details of this are beyond the scope of this book, so refer to the documentation if you choose to do this.