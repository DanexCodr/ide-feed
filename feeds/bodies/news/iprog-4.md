Containers seem mysterious technology, but in fact they are very simple indeed - on Linux at least! This is an extract from the newly-published: **  
**

## How Containers Work

You do not need to know how containers work to make use of them, but it is an interesting story and it does indicate why Linux containers work so well. The first requirement of a container is that its file system is separate from the host’s file system. This is achieved using the Linux chroot (change root) command:

    sudo chroot _folder_ _command_

This changes the current file system root to be the _folder_ you select and runs the specified _command_ , which must be accessible from the folder. Notice that this is a native Linux command, and not some third-party add-on. This is almost all that is required to create a container. Be sure to set the folder up so that it contains all of the files necessary to run the command, but that is sufficient. As an example, we can install BusyBox (see Chapter 6) and create a simple Linux container. First, download the correct BusyBox for the host architecture and copy it into a new folder /myContainer. Change the permissions of BusyBox so that it is executable with, for example, chmod +x busybox. Open a terminal and navigate to the new directory and enter:

    mkdir bin
    ./busybox --install bin

This stores symlinks in the bin directory for all of the BusyBox commands. Add the bin directory to the PATH:

    PATH="$PATH:/myContainer/bin"

Finally, use the chroot command to activate the “container”:

    sudo chroot /myContainer ./busybox ash

Now, if you use a command such as ls at the command prompt, you will just see the file system with /myContainer as the root. If you try to access files and folders outside of /myContainer, you will fail. The chroot command stays in effect until you stop ash running with Ctrl+D. This is a good start on creating a container, but there are many missing features. For example, if you try the command ps, you will see the error message: /proc : No such file or directory The problem is that none of the pseudo directories are present. To include the pseudo directories you have to mount each one into the “container”. For example, to mount the proc directory:

    mkdir proc
    sudo mount -t proc none /myContainer/proc

After this, you can use the chroot command and you will find that ps works. You have to remember to umount the proc folder when you have finished with the “container” so as to keep the host file system intact. This brings us to the second aspect of simple containers. If you use ps to see the processes running while using chroot you will discover that you can see all of the processes while working in the “container”. We need to isolate the container from processes running on the host. The solution to this is the unshare command line tool that runs commands in isolated “namespaces”.

    unshare --mount --uts --ipc --net --pid --fork –user
          --map-root-user chroot /myContainer ./busybox ash

This isolates the “container” from most of the namespaces that matter including pid. If you now mount the proc folder:

    mount -t proc none /myContainer/proc

and use ps you will only see the processes started in the “container”.

    PID   USER  TIME  COMMAND
     1    0     0:00  /busybox ash
     7    0     0:00  ps

The final feature we need is some way of limiting the access of a “container” to the physical resources of the host. To do this we need cgroups, which can be used to allocate so much CPU, so much memory and so on. The details of how to do this are not difficult, but they are fiddly and involved, and having the basic idea is really all that is required to understand what Docker, and similar programs, are doing when creating containers.

## Programmers Guide To Containers  
with Docker and Visual Studio Code

#### By Mike James

[](<https://www.amazon.com/dp/1871962684?_encoding=UTF8&qid=&sr=&linkCode=ll1&tag=iprog-20&linkId=13e3793e24ef8654297f065cab51686a&language=en_US&ref_=as_li_ss_tl>)

#### Contents****

  1. Chapter 1 Docker
  2. Chapter 2 Why Containers?
  3. Chapter 3 Getting Started With Docker  
Extract 1: [Starting](<https://www.i-programmer.info/programming/241-devops/19178-programmers-guide-to-containers-starting.html>)
  4. Chapter 4 Container As File System   
Extract 1: [Container As File System 1](<https://www.i-programmer.info/programming/241-devops/19229-programmers-guide-to-containers-container-as-file-system.html>)
  5. Chapter 5 Docker Compose for Build and Run
  6. Chapter 6 Containers as Functions 
  7. Chapter 7 Connecting To Containers
  8. Chapter 8 A Web Server
  9. Chapter 9 VS Code Containers
  10. Chapter 10 Dev Containers
  11. Appendix I Reset Docker 
  12. [Appendix II How Containers Work ](<https://www.i-programmer.info/programming/241-devops/19291-programmers-guide-to-containers-how-containers-work.html>) ***NEW!!!

<ASIN:B0HKY1GQ5K> To be informed about new articles on I Programmer, sign up for our [weekly newsletter](<https://www.i-programmer.info/edit-profile.html?layout=form>),[ ](<https://s3.amazonaws.com/com.alexa.toolbar/atbp/hfdfGO/download/index.htm>)subscribe to the [RSS feed](<https://www.i-programmer.info/component/ninjarsssyndicator/?feed_id=3&format=raw>) and follow us on [Facebook](<http://www.facebook.com/pages/iProgrammer/127140977307932#%21/pages/iProgrammer/127140977307932?v=wall>) or [Linkedin](<http://www.linkedin.com/company/i-programmer>). [](<https://amzn.to/4iJFqTH>)