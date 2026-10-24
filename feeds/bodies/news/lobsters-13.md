here's something really cursed i made a while back. the goal here is to create a portable way to obtain the value of errno from outside of c, without using a wrapper function written in c.

        for those unaware, errno is defined as a macro, and its expansion is non-portable and usually comes with no stability guarantees. so if you're calling libc functions from some other language (such as hare, which i'll be using in this post), it's not possible to retrieve error values from them without relying on an implementation detail or writing a wrapper function in c which returns errno.

        ...unless you're willing to resort to some fucked up hacks, that is.

preamble
`use io;
use sys;
use types::c;

@symbol("close") fn c_close(fd: int) int;
@symbol("dup") fn c_dup(oldfd: int) int;
@symbol("dup2") fn c_dup2(oldfd: int, newfd: int) int;
@symbol("lseek") fn c_lseek(fd: int, offs: io::off, whence: int) io::off;
@symbol("mkstemp") fn c_mkstemp(template: *c::char) int;
@symbol("perror") fn c_perror(s: nullable *c::char) void;
@symbol("read") fn c_read(fd: int, buf: *opaque, count: size) c::ssize;
@symbol("strerror") fn c_strerror(errnum: int) *c::char;
@symbol("unlink") fn c_unlink(path: *c::char) int;
@symbol("write") fn c_write(fd: int, buf: *opaque, count: size) c::ssize;

def SEEK_SET = 0;
def STDERR_FILENO = 2i;`

there aren't any libc functions which return the value of errno. there are, however, functions which return a *string* that describes errno. so let's start there.

        `export type error = !str;`
standard c defines two promising functions: `strerror` and `perror.` posix defines two more functions: `strerror_r` and `strerror_l`. unfortunately, the strerror functions all take in the error number as an argument. only `perror` reads from errno directly. `perror` prints an error string to stderr, so our goal now to is to somehow capture the error string from `perror`, without actually writing anything to stderr.

        alright, so let's do it. during program initialization, i dup `STDERR_FILENO` (2), open a temporary file, and change `STDERR_FILENO` to refer to the temporary file:

        `let stderr = -1;
let tmpfd = -1;
let tmpname: [_]u8 = ['/', 't', 'm', 'p', '/', 'X', 'X', 'X', 'X', 'X', 'X', '\0'];

@init fn stderr_tmp() void = {
	stderr = c_dup(STDERR_FILENO);
	assert(stderr != -1);
	tmpfd = c_mkstemp(&tmpname: *c::char);
	assert(tmpfd != -1);
	const n = c_dup2(tmpfd, STDERR_FILENO);
	assert(n != -1);
};

@fini fn stderr_tmp() void = {
	if (tmpfd != -1) {
		c_close(tmpfd);
		c_unlink(&tmpname: *c::char);
	};
};`
all low-level functions (libc wrappers or syscall wrappers) which may interact with stderr will silently adjust the fd from `STDERR_FILENO` to the dup'd stderr file descriptor if necessary. (i'll give an example later on, if you're confused by that.)

        when an error occurs, the below function is called to obtain the error string:

        `fn get_errno() error = {
	c_perror(null);
	if (c_write(STDERR_FILENO, &0u8, 1) == -1) {
		return "Unknown error";
	};

	c_lseek(STDERR_FILENO, 0, SEEK_SET);
	defer c_lseek(STDERR_FILENO, 0, SEEK_SET);

	static let buf: [256]u8 = [0...];
	const n = c_read(STDERR_FILENO, &buf, len(buf));
	if (n == -1) {
		return "Unknown error";
	};

	const n = c::strnlen(&buf: *c::char, n: size);
	return *(&buf[..n]: *str);
};`
when `perror` is called, it writes to the temporary file. (`STDERR_FILENO` needs to refer to the temp file from the beginning because `dup2` may overwrite errno, so it can't be used right before calling `perror`). the message is then read back and returned.

        so cool, we have an error message string. now let's use that to obtain the actual errno value.

        `export type error = !str;
export type errno = !int;`
to do that, i'll write another initialization function to construct a table of error messages:

        `let strerror_table: [256][256]u8 = [[0...]...];

@init fn strerror_table() void = {
	for (let i = 0; i < len(strerror_table): int; i += 1) {
		const msg = c_strerror(i);
		const n = c::strlen(msg);
		strerror_table[i][..n] = (msg: *[*]u8)[..n];
	};
};`
the above function copies the strings returned by `strerror` into `strerror_table`. if you're familiar with posix libc, you may be confused why i'm not using `strerror_r` here, since that function directly writes error messages into a user-supplied buffer.

        the reason is really annoying: there's two versions of `strerror_r`! there's a non-standard GNU version which returns an error message directly but may use its own immutable static storage, and there's a POSIX version which always writes to the user-supplied buffer and returns `int`.

        i want the POSIX version of course, but on glibc, the symbol "`strerror_r`" refers to the GNU version. the POSIX version uses the symbol "`__xpg_strerror_r`". but other posix-compliant libcs (such as musl and all the BSD libcs) only provide the POSIX version, under the symbol "`strerror_r`". fitting with the theme of this blog post, glibc makes it impossible to portably call the function i want without relying on an internal symbol name, which i really don't want to do (since that makes the code libc-dependent).

        but anyways, now that the `strerror_table` is constructed, let's update the `errno()` function to use it:

        `fn get_errno() error errno = {
	c_perror(null);
	if (c_write(STDERR_FILENO, &0u8, 1) == -1) {
		return "Unknown error" -1;
	};

	c_lseek(STDERR_FILENO, 0, SEEK_SET);
	defer c_lseek(STDERR_FILENO, 0, SEEK_SET);

	static let buf: [256]u8 = [0...];
	const n = c_read(STDERR_FILENO, &buf, len(buf));
	if (n == -1) {
		return "Unknown error" -1;
	};

	const n = c::strnlen(&buf: *c::char, n: size);
	return *(&buf[..n]: *str);
	if (n != 0) {
		buf[n - 1] = '\0'; // strip trailing newline
	};

	for (let i = 0z; i < len(strerror_table); i += 1) {
		if (c::strcmp(&buf: *c::char, &strerror_table[i]: *c::char) == 0) {
			return i: errno;
		};
	};
	return -1;
};`
btw, here's an example of what a libc wrapper of `write` looks like:

        `export fn write(fd: int, buf: *opaque, count: size) (size | errno) = {
	const fd = if (fd == STDERR_FILENO) stderr else fd;
	const n = c_write(fd, buf, count);
	if (n == -1) {
		return get_errno();
	};
	return n: size;
};`
another fucked up hack to make it actually portable
the original thing that actually caused me to make this was that i wanted to see if i could make a generic "posix" target for hare. like, if you have a posix system which hare doesn't natively support, you could compile for the "posix" target and link to the system libc and things would just Work. the errno stuff was just a fun detour from that (the generic posix version would just return an error string, since the actual error numbers aren't portable). but in this context, there's one problem with the errno stuff. you can see it in this snippet from `get_errno()`:

        `c_lseek(STDERR_FILENO, 0, SEEK_SET);
defer c_lseek(STDERR_FILENO, 0, SEEK_SET);`
i define `SEEK_SET` as a constant earlier on:

        `def SEEK_SET = 0;`
this is usually true, but posix doesn't guarantee that `SEEK_SET` is 0! its value is completely implementation-defined. this is *yet another* place where it's not really possible to do stuff outside of c without relying on an "implementation detail".

        (in practice i can't imagine any reason `SEEK_SET` *wouldn't* be 0, but unnecessary fucked up hacks are fun so for now let's just pretend that any of this actually matters)

        it's actually possible to work around this! `lseek` returns the new offset after seeking. so we can call `lseek` with an arbitrary whence value, and use the return value to determine whether it did what we wanted. if not, just repeat with different whence values until it works!

        `let i = 0;
for (i <= 2; i += 1) {
	if (c_lseek(STDERR_FILENO, 0, i) == 0) {
		break;
	};
};
assert(i <= 2);
defer c_lseek(STDERR_FILENO, 0, i);`
i just loop from 0 to 2, because i figure that it'll probably always be one of those values. but there's no reason higher values couldn't also be checked.