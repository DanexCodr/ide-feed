i found a neat trick which lets you take advantage of CoW to duplicate memory without allocating anything upfront. maybe some people already know about this, but i just discovered it and i think it's cool (and i kinda wish it was easier to take advantage of this with higher-level stdlib functions)

        start by creating a memory-backed file descriptor and mmaping it (error handling omitted):

        `int fd = memfd_create("foo", MFD_CLOEXEC);
ftruncate(fd, SIZE);
char *template = mmap(NULL, SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);`
write some "template" to it (this is what will be dup'd later):

        `memset(template, 67, SIZE);`
now, to allocate a chunk of memory with this template, use `mmap` with `MAP_PRIVATE`:

        `char *copy = mmap(NULL, SIZE, PROT_READ | PROT_WRITE, MAP_PRIVATE, fd, 0);`
this is cool because regardless of the size of the initial allocation, the copy isn't taking up any physical memory. and say you mutate the copy now:

        `copy[i] = 69;`
this will only allocate a single page of memory (4 KiB); the rest of the pages are still shared with the original template!

        i did a test here where i allocated 32 MiB, and then "copied" it with what would be another 32 MiB allocation, but the total physical memory usage was 32.004 MiB.

        i wonder if it would be possible to do this with a continuous memory region. like, 32 MiB of virtual memory, but because it's all filled with the same (non-zero) stuff, only 1 page of physical memory is allocated upfront. this feels like it could be useful maybe