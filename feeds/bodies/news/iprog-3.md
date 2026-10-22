Page 1 of 2Containers are functional systems, but they are first and foremost file systems. How do you get the files where you want them? This is the first exclusive extract from the newly-published: **  
**

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
Extract 1: [Container As File System 1](<https://www.i-programmer.info/programming/241-devops/19229-programmers-guide-to-containers-container-as-file-system.html>) ***NEW!!!
  5. Chapter 5 Docker Compose for Build and Run
  6. Chapter 6 Containers as Functions 
  7. Chapter 7 Connecting To Containers
  8. Chapter 8 A Web Server
  9. Chapter 9 VS Code Containers
  10. Chapter 10 Dev Containers
  11. Appendix I Reset Docker 
  12. Appendix II How Containers Work 

<ASIN:B0HKY1GQ5K>

## Container As File System

A container has its own complete file system starting from / root. The most basic Linux container has a complete pseudo file system, i.e. folders and files which are created by the kernel. This represents a minimal file system that a running program would expect to be present. Our next task is to add to this to create a file system that the program needs to work. It is worth, even at this early stage, distinguishing between files that do not change as the program is run and those that are used by it to record state. The files that are essentially read-only are stored in the container and are the same each time the container is run. You can think of these as the runtime environment of the program. The files that you can think of as read/write hold the state of the system and in this case we most likely do want them to be updated each time the container is run – i.e. these files should be persistent and associated with the container.

## Copy & Add

At its most basic, a container is a private file system. The question is how do we get files and folders into it? The answer is that there are commands that we can include in the dockerfile that will copy files and folders from a variety of sources. The most basic is:

    COPY [OPTIONS] <src> ... <dest>

You can either use simple file specification or JSON to pass the parameters. The advantage of using the JSON format is that you can pass parameters that contain spaces. In general it is simpler to standardize on the JSON parameter format. If the source is a list of files, or uses the wildcard characters * and ?, then the destination has to be a folder and end with a slash, /. All of the files are copied to the folder. If the source is a directory then its contents, including subfolders, are copied, but the directory is not copied. If you want to copy a directory together with its contents, you have to specify the destination directory. For example:

    COPY /mydir /mydir

copies the contents of mydir to the folder /mydir in the image, creating a new folder if necessary. There are some useful options that control how the copy is performed: \--from Specifies where to copy from By default the source is assumed to be in the build context, see the next section, but it can also be specified to be another image, a previous stage (see Chapter 6), or a specific named context. \--chmod Sets destination file permissions \--chown Sets the owner of the destination file \--parents Automatically adds src parent folders to dest \--exclude Specifies a path to exclude from the copy. The ADD command does more or less the same thing as COPY but it has a larger range of supported sources. The COPY instruction just copies files on the host file system. The ADD command can download resources from the web or other remote sources:

    ADD [OPTIONS] <src> ... <dest>

If <src> is a local file or directory, the contents of the directory are copied to the specified destination. In this case ADD works like COPY. If <src> is a local tar archive, it is decompressed and extracted to the specified destination. If <src> is a URL, the contents of the URL are downloaded and placed at the specified destination. If <src> is a Git repository, the repository is cloned to the specified destination. The destination works in the same way as for COPY – if it ends with / then it is a directory, which will be created if it doesn’t exist. The OPTIONS are the same as for COPY with the following additions: \--keep-git-dir Keeps the top level git directory in dest \--checksum Specifies a checksum \--unpack Automatically unpacks tar archives A commonly used way of implementing the creation of an image is to take all of the files and folders needed and create a tar file that contains them. All of the files can then be added to an image using:

    ADD --unpack=true 
     https://mydomain.info/myfolder/archive.tar.gz /myfolder

## Layers and Caching

Docker uses layers to structure the building of the image. Each instruction in the dockerfile that modifies the file system constitutes a new layer. So if you have a dockerfile that reads:

    FROM debian
    COPY ["/MyData/MyText","/test1/"]
    COPY ["/MyData/MyText","/test2/"]
    COPY ["/MyData/MyText","/test3/"]

then each COPY creates a new layer in the image. The final image is a collapsing of all of the layers into a single file system. If you build the image you will see:

     => [1/4] FROM docker.io/library/debian:latest@sha256:34cd9e9fd437c0a095e  8.1s
     => => resolve docker.io/library/debian:latest@sha256:34cd9e9fd437c0a095e  0.0s
     => => sha256:1da3cb2f93f2ca3c5bdaf4c024a7f1ebd717938d2 49.31MB / 49.31MB  6.4s
     => => extracting sha256:1da3cb2f93f2ca3c5bdaf4c024a7f1ebd717938d20c858e4  1.5s
     => [internal] load build context                                          0.0s
     => => transferring context: 82B                                           0.0s
     => [2/4] COPY [/MyData/MyText,/test1/]                                    1.2s
     => [3/4] COPY [/MyData/MyText,/test2/]                                    1.1s
     => [4/4] COPY [/MyData/MyText,/test3/]  

and each of the four steps is a layer which is cached independently. If you examine the cache:

    docker builder du --verbose

you will see an image for each of the steps:

    ID:           3ebmxphtowsdznroeuynxtywf
    Parents:
     - uandxlnva11yfthf5u8f98g6q
    Created at:   2026-08-21 16:55:51.564709281 +0000 UTC
    Mutable:      false
    Reclaimable:  true
    Shared:       true
    Size:         12.44kB
    Description:  [4/4] COPY [/MyData/MyText,/test3/]
    Usage count:  1
    Last used:    47 seconds ago
    Type:         regular  

    ID:           uandxlnva11yfthf5u8f98g6q
    Parents:
     - vbkuuwzgmn5b3jkrc8msizl1i
    Created at:   2026-08-21 16:55:50.280803168 +0000 UTC
    Mutable:      false
    Reclaimable:  true
    Shared:       true
    Size:         12.44kB
    Description:  [3/4] COPY [/MyData/MyText,/test2/]
    Usage count:  1
    Last used:    47 seconds ago
    Type:         regular  

    ID:           vbkuuwzgmn5b3jkrc8msizl1i
    Parents:
     - rs53d36l8ikgpcbs88utz6qgr
    Created at:   2026-08-21 16:55:49.106388609 +0000 UTC
    Mutable:      false
    Reclaimable:  true
    Shared:       true
    Size:         12.44kB
    Description:  [2/4] COPY [/MyData/MyText,/test1/]
    Usage count:  1
    Last used:    47 seconds ago
    Type:         regular

These images are not part of the saved images, and they only exist in the cache. If you build the image a subsequent time, each step is examined and, if it hasn’t changed, then it is not executed. If a step has changed, then the cache from that step on is invalidated and it and subsequent steps are reimplemented, i.e. the cache isn’t used after the first changed step. Of course, there will be occasions when the step has changed but Docker has no way of knowing it. In such cases, you need to clear the cache:

    docker image prune -a

There is also an opportunity for some optimization. If you know that a particular operation changes frequently, then split it out as a separate step and put it late in the proceedings, so that when it does change it invalidates as little of the cache as possible.