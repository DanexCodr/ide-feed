**JPEG XS** ([standardized](https://en.wikipedia.org/wiki/Technical_standard) as [ISO/IEC](https://en.wikipedia.org/wiki/ISO/IEC) 21122) is an image and video codec that offers both visually and mathematically lossless quality. It is a special-purpose codec that is specifically designed to allow for low-complexity and [low-latency](https://en.wikipedia.org/wiki/Low-latency) implementations.<sup>[[2]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-JPEG_XS-2)</sup><sup>[[3]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-3)</sup> Target applications of the standard include streaming high-quality content for [professional video over IP](https://en.wikipedia.org/wiki/Professional_video_over_IP) (SMPTE [ST 2022](https://en.wikipedia.org/wiki/SMPTE_2022) and [ST 2110](https://en.wikipedia.org/wiki/ST_2110)) in broadcast and other applications: [virtual reality](https://en.wikipedia.org/wiki/Virtual_reality), drones, autonomous vehicles using cameras, gaming.<sup>[[2]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-JPEG_XS-2)</sup><sup>[[4]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-4)</sup><sup>[[5]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-5)</sup> Although there is not an official acronym definition, XS was chosen to highlight the *extra small* and *extra speed* characteristics of the codec.

| JPEG XS |  |
| --- | --- |
| [![](https://thumb.wikimedia.org/wikipedia/commons/thumb/8/89/JPEG_XS_format_logo.svg/250px-JPEG_XS_format_logo.svg.png?utm_source=en.wikipedia.org&utm_campaign=parser&utm_content=thumbnail)](https://en.wikipedia.org/wiki/File:JPEG_XS_format_logo.svg) |  |
| [Filename extension](https://en.wikipedia.org/wiki/Filename_extension) | `.jxs` |
| [Internet media type](https://en.wikipedia.org/wiki/Media_type) | image/jxsc, video/jxsv<sup>[[1]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-1)</sup> |
| [Magic number](https://en.wikipedia.org/wiki/File_format#Magic_number) | `0xFF10 FF50` |
| Developed by | [Joint Photographic Experts Group](https://en.wikipedia.org/wiki/Joint_Photographic_Experts_Group) |
| Initial release | May 1, 2019; 7 years ago (2019-05-01) |
| Type of format | [Lossy](https://en.wikipedia.org/wiki/Lossy) and [lossless](https://en.wikipedia.org/wiki/Lossless) [image compression](https://en.wikipedia.org/wiki/Image_compression) [format](https://en.wikipedia.org/wiki/Image_format) |
| [Standard](https://en.wikipedia.org/wiki/International_standard) | ISO/IEC 21122 |
| Website | [jpeg.org/jpegxs/](https://jpeg.org/jpegxs/) |

## Features

Three main features are key to JPEG XS:

1. Visually transparent compression: XS compressed content is indistinguishable from the original uncompressed content (passing ISO/IEC 29170-2 tests, also called AIC-2) for compression ratios between 2:1 and 10:1.
2. Low latency: The total end-to-end latency, introduced by the JPEG XS compression-decompression cycle, is minimal. Depending on the configuration, XS typically imposes only between 1 and 32 lines of additional end-to-end latency, when compared to the same system using uncompressed video.
3. Lightweight: JPEG XS is designed to have low computational and memory complexity, allowing for efficient low-power and low-resource implementations on various platforms such as CPU, GPU, FPGA and ASIC.

Relying on these key features, JPEG XS is suitable for any application where uncompressed content is the norm, yet still allowing for significant savings in the required bandwidth usage, preserving quality and low latency. Among the targeted use cases are video transport over professional video links (like [SDI](https://en.wikipedia.org/wiki/Serial_digital_interface) and [professional video over IP](https://en.wikipedia.org/wiki/Professional_video_over_IP)), real-time video storage, memory buffers, omnidirectional video capture and rendering, and image sensor compression (for example in cameras and in the automotive industry).<sup>[[6]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-6)</sup> JPEG XS favors visually lossless quality in combination with low latency and low complexity, over data reduction through compression. It is not a direct competitor to alternative image codecs like [JPEG 2000](https://en.wikipedia.org/wiki/JPEG_2000) and [JPEG XL](https://en.wikipedia.org/wiki/JPEG_XL) or video codecs like [AV1](https://en.wikipedia.org/wiki/AV1), [AVC/H.264](https://en.wikipedia.org/wiki/AVC/H.264) and [HEVC/H.265](https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding) which tend to focus on compression efficiency.

Other important features are:

1. Exact bitrate allocation: JPEG XS allows an accurately targeted bitrate to perfectly match the available bandwidth (also referred to as constant bitrate).
2. Multi-generation robustness: JPEG XS allows for at least 10 encoding-decoding cycles without significant quality degradation.[[7]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-7) This feature allows, for example, transparent chaining of multiple devices that recompress the signal, without any significant quality degradation taking place.
3. Multi-platform interoperability: The algorithms used in JPEG XS allow for efficient implementations on different platforms, like CPU, GPU, FPGA and ASIC. Each of these platform architectures is best exploited when a specific degree of parallelism is available in the implementation. For instance, a multi-core CPU implementation will leverage coarse-grained parallelism, while a GPU or FPGA implementation will work better with fine-grained parallelism. Moreover, the choice of parallelism used in the implementation at the encoder will not affect that of the decoder. This means that real-time encoding and decoding between platforms is possible, without sacrificing the low-complexity, low-latency or high-quality properties.
4. Support for mathematical [lossless coding](https://en.wikipedia.org/wiki/Lossless_compression) (MLS): JPEG XS is also capable of coding images in a mathematically lossless way, to achieve perfect reconstruction at the decoder side (new profile supported by 2nd edition).
5. Support for [High Dynamic Range](https://en.wikipedia.org/wiki/High_Dynamic_Range) (HDR) content: The current version of JPEG XS supports bit-depths of up to 16 bits per component, and it provides several parameterizable non-linear transforms to efficiently compress HDR content.
6. Support for RAW Bayer/CFA compression: JPEG XS has also the capability to compress color filter array (CFA) content, such as RAW Bayer content produced by digital cameras. A special color transform, called Star-Tetrix, allows for efficient and direct compression of the original RAW sample values, without the need for converting the Bayer samples to RGB samples first.[[8]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-8)
7. Accurate flow control: A JPEG XS encoder continuously monitors the amount of bits sent out, and adjusts its rate allocation process to neither overflow nor underflow a normatively[[9]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-:1-9) defined decoder input buffer.

## Application domains

JPEG XS is actively used in several application domains.<sup>[[10]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-10)</sup>

Video bandwidth requirements are growing as video resolutions, frame rates, bit depths, and the number of video streams are constantly increasing. Although the capacities of video links and communication channels are also growing, there are applications where the reduced data rate afforded by JPEG-XS is advantageous.

Both the broadcast and pro-AV markets are shifting towards AV-over-IP-based infrastructure, with a preference going to [Gigabit Ethernet](https://en.wikipedia.org/wiki/Gigabit_Ethernet) links for remote production and faster fiber-based Ethernet for in-house facilities. Given the available bandwidth and infrastructure cost, relying on uncompressed video may be cost-prohibitive if 4K, 8K, increased bit depths for HDR, and higher frame rates need to be supported.

With XS, it is, for example, possible to repurpose existing SDI cables to transport 4K60 over a single 3G-SDI (at 4:1 compression ratio), and even over a single HD-SDI (at 8:1 compression ratio). Similar scenarios can be used to transport 8K60 content over various SDI cable types (e.g., 6G-SDI and 12G-SDI). Alternatively, XS enables transporting 4K60 content over Gigabit Ethernet and 8K60 over 5G or [10 Gigabit Ethernet](https://en.wikipedia.org/wiki/10_Gigabit_Ethernet), which would be impossible without compression.

The following table shows expected compression ranges for some typical use cases.

| Video stream | Video throughput | Link type | Available throughput | Compression ratio |
| --- | --- | --- | --- | --- |
| 2k 60 fps 4:2:2 10 bpc | 2.7 Gbit/s | HD-SDI | 1.33 Gbit/s | ~2:1 |
| 4k 60 fps 4:2:2 10 bpc | 10.6 Gbit/s | 3G-SDI | 2.65 Gbit/s | ~4:1 |
| 2k 60 fps 4:2:2 10 bpc | 2.7 Gbit/s | 1G Ethernet | 0.85 Gbit/s | ~3:1 |
| 2k 60 fps 4:4:4 12 bpc | 4.8 Gbit/s | 1G Ethernet | 0.85 Gbit/s | ~6:1 |
| 4k 60 fps 4:4:4 12 bpc | 19.1 Gbit/s | 10G Ethernet | 7.96 Gbit/s | ~2.2:1 |
| 8k 60 fps 4:2:2 10 bpc | 42.5 Gbit/s | 10G Ethernet | 7.96 Gbit/s | ~6:1 |
| 8k 120 fps 4:2:2 10 bpc | 84.9 Gbit/s | 25G Ethernet | 21.25 Gbit/s | ~4:1 |

Related to the transport of video streams is the storage and retrieval of high-resolution streams where bandwidth limitations similarly apply. For instance, video cameras use internal storage like [SSD drives](https://en.wikipedia.org/wiki/SSD_drive) or [SD cards](https://en.wikipedia.org/wiki/SD_card) to record high-resolution streams of images, yet the maximum data rates of such storage devices may be below that required to store uncompressed video in real time.

### Sensor compression

JPEG XS has built-in support for the direct compression of RAW [Bayer](https://en.wikipedia.org/wiki/Bayer_filter)/CFA images using the Star-Tetrix Color Transform. This transform takes a RAW Bayer pattern image and [decorrelates](https://en.wikipedia.org/wiki/Decorrelation) the samples into a 4-component image with each component having only a quarter of the resolution.<sup>[[11]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-11)</sup> This means that the total amount of samples to further process and compress remains the same, yet the values are decorrelated similarly to a classical Multiple Component Transform.

Avoiding such conversion prevents information loss and allows this processing step to be done outside of the camera. This is advantageous because it allows deferring [demosaicing](https://en.wikipedia.org/wiki/Demosaicing) the Bayer content from the moment of capturing to the production phase, where choices regarding artistic intent and various settings can be better made; The demosaicing process is irreversible and requires certain choices, like the choice of interpolation algorithm or the level of noise reduction, to be made upfront. The demosaicing process can be power-hungry and will also introduce extra latency and complexity.

## Standards

The JPEG XS coding system is an [ISO/IEC](https://en.wikipedia.org/wiki/ISO/IEC) suite of standards that consists of the following parts:

| Part | 1st edition | 2nd edition (in force) | 3rd edition | Title | Description |
| --- | --- | --- | --- | --- | --- |
| 1 | [2019](https://www.iso.org/standard/74535.html) | [2022](https://www.iso.org/standard/81551.html) | [2024](https://www.iso.org/standard/85247.html) [Amd1:2026](https://www.iso.org/standard/92696.html) | Core coding system | Describes the core coding system of JPEG XS. Defines the syntax and, similarly to other JPEG and MPEG image codecs, the decompression process to reconstruct a continuous-tone digital image from its encoded codestream. Provides some guidelines for the inverse process that compresses a digital image into a compressed codestream, the encoding process, but leaves implementation-specific optimizations and choices to the implementers. |
| 2 | [2019](https://www.iso.org/standard/74536.html) | [2022](https://www.iso.org/standard/81552.html) | [2024](https://www.iso.org/standard/85250.html) [Amd1:2026](https://www.iso.org/standard/93901.html) [DAmd2](https://www.iso.org/standard/94967.html) | Profiles and buffer models | Builds on top of Part 1 to segregate different applications and uses of JPEG XS into reduced coding tool subsets with tighter constraints. The definition of profiles, levels, and sublevels allows for reducing the complexity of implementations in particular application use cases, while also safeguarding interoperability. Profiles represent interoperability subsets of the codestream syntax specified in Part 1. In addition, levels and sublevels provide limits to the maximum throughput in the encoded (codestream) and the decoded (spatial and pixels) image domains. Also specifies a buffer model, consisting of a decoder model and a transmission channel model, to enable guaranteeing low latency requirements to a fraction of the frame size. |
| 3 | [2019](https://www.iso.org/standard/74537.html) | [2022](https://www.iso.org/standard/81553.html) | [2024](https://www.iso.org/standard/86420.html) | Transport and container formats | Specifies transport and container formats for JPEG XS codestreams. It defines the carriage of important metadata, like color spaces, mastering display metadata (MDM), and [Exif](https://en.wikipedia.org/wiki/Exif), to facilitate transport, editing, and presentation. Defines the XS-specific ISOBMFF boxes, an [Internet media type](https://en.wikipedia.org/wiki/Internet_media_type) registration, and additional syntax to allow embedding XS in formats like MP4, MPEG-2 TS, or the HEIF image file format. |
| 4 | [2020](https://www.iso.org/standard/74538.html) | [2022](https://www.iso.org/standard/82568.html) | [2025](https://www.iso.org/standard/88912.html) | Conformance testing | Provides conformance testing and buffer model verification. |
| 5 | [2020](https://www.iso.org/standard/74539.html) | [2022](https://www.iso.org/standard/82569.html) | [2025](https://www.iso.org/standard/89031.html) | Reference software | A reference software implementation (written in ISO C11) of the JPEG XS Part 1 decoder, conforming to the Part 2 profiles, levels and sublevels, as well as an exemplary encoder implementation. |

### RFC9134 - RTP Payload Format for ISO/IEC 21122 (JPEG XS)

RFC 9134<sup>[[12]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-12)</sup> describes a payload format for the [Real-Time Transport Protocol](https://en.wikipedia.org/wiki/Real-time_Transport_Protocol) (RTP) to carry JPEG XS encoded video. In addition, the recommendation also registers the official [media type](https://en.wikipedia.org/wiki/Media_type) registration for JPEG XS video as `video/jxsv`, along with its mapping of all parameters into the [Session Description Protocol](https://en.wikipedia.org/wiki/Session_Description_Protocol) (SDP).

The [RTP payload format](https://en.wikipedia.org/wiki/RTP_payload_format) for JPEG XS, in turn, enables the use of JPEG XS in [SMPTE 2110](https://en.wikipedia.org/wiki/SMPTE_2110) environments using SMPTE ST 2110-22 for CBR compressed video transport.

See also TR-08,<sup>[[13]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-13)</sup> published by the [Video Services Forum](https://en.wikipedia.org/wiki/Video_Services_Forum).

### NMOS with JPEG XS

A [Networked Media Open Specifications](https://en.wikipedia.org/wiki/Networked_Media_Open_Specifications) (NMOS) standard that enables registration, discovery, and connection management of JPEG XS endpoints uses the AMWA IS-04 and IS-05 NMOS specifications. See AMWA BCP-006-01,<sup>[[16]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-16)</sup> published by [Advanced Media Workflow Association](https://en.wikipedia.org/wiki/Advanced_Media_Workflow_Association).

[Internet Protocol Media Experience](https://en.wikipedia.org/wiki/Internet_Protocol_Media_Experience) (IPMX) is a suite of open standards and specifications to enable the carriage of compressed and uncompressed video, audio, and data over IP networks for the pro AV market. JPEG XS is supported under IPMX via VSF TR-10-8<sup>[[17]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-17)</sup> and TR-10-11.<sup>[[18]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-18)</sup>

[GenICam](https://en.wikipedia.org/wiki/GenICam) (Generic Interface for Cameras) is a set of freely available standards developed by the [European Machine Vision Association (EMVA)](https://www.emva.org) to provide a generic programming interface for industrial and machine vision devices. One of its specifications, the Generic Data Container (GenDC), defines a standardized format for transporting image data and metadata independently of the underlying transport interface. Support for JPEG XS encoded image data was added in [GenDC version 1.2](https://www.emva.org/wp-content/uploads/GenICam_GenDC_v1_2.pdf), enabling the use of JPEG XS across GenICam-compliant systems and transport standards that rely on GenDC, such as [GigE Vision](https://en.wikipedia.org/wiki/GigE_Vision), [USB3 Vision](https://en.wikipedia.org/wiki/USB3_Vision), [CoaXPress](https://en.wikipedia.org/wiki/CoaXPress) and [Camera Link](https://en.wikipedia.org/wiki/Camera_Link).

The JPEG committee started the standardization activity in 2016 with an open call for a high-performance, low-complexity image coding standard. The best-performing candidate technologies came from intoPIX and Fraunhofer IIS and formed the basis for the new standard. First implementations were demonstrated in April 2018 at the [NAB Show](https://en.wikipedia.org/wiki/NAB_Show) and later that year at the [International Broadcasting Convention](https://en.wikipedia.org/wiki/International_Broadcasting_Convention). JPEG XS was also presented at [CES](https://en.wikipedia.org/wiki/Consumer_Electronics_Show) in 2019. JPEG XS was formally standardized as ISO/IEC 21122 by the [Joint Photographic Experts Group](https://en.wikipedia.org/wiki/Joint_Photographic_Experts_Group) with the first edition published in 2019. A second edition was published in 2022,<sup>[[19]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-ieee_jpeg_xs_2021-19)</sup> adding support for direct compression of raw [Bayer CFA](https://en.wikipedia.org/wiki/Bayer_CFA) content, lossless compression, and support for 4:2:0 color subsampling. Today, the JPEG committee is still actively working on further improvements, with the third edition published in 2024.<sup>[*[needs update](https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Chronological_items)*]</sup> This edition adds support for a temporal decorrelation technology in the wavelet domain, called Temporal Differential Coding (TDC).

In 2025, JPEG XS received the EMMY® Award by the Television Academy for technical innovations in the US television industry.<sup>[[20]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-20)</sup>

### Core coding system

The JPEG XS standard is a [wavelet-based](https://en.wikipedia.org/wiki/Discrete_wavelet_transform) still-image codec without any frame buffer. While the standard<sup>[[21]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-21)</sup> defines JPEG XS based on a hypothetical reference decoder, JPEG XS is easier to explain through the steps a typical encoder performs:<sup>[[22]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-:0-22)</sup>

**Component up-scaling and optional component decorrelation:** In the first step, the DC gain of the input data is removed and pixels are upscaled to a 20-bit precision. Optionally, a multi-component generation, identical to the JPEG 2000 RCT, is applied. This transformation is a lossless approximation of an RGB to YUV conversion, generating one luma and two chroma channels.

**Wavelet transformation:** Input data is spacially decorrelated by a 5/3 [Le Gall–Tabatabai](https://en.wikipedia.org/wiki/Le_Gall–Tabatabai) [wavelet filter](https://en.wikipedia.org/wiki/Discrete_wavelet_transform).<sup>[*[citation needed](https://en.wikipedia.org/wiki/Wikipedia:Citation_needed)*]</sup> While a five-stage transformation is performed in the horizontal direction, only 0 to 2 transformations are run in the vertical direction. The reason for this asymmetrical filter is to minimize latency.

**Prequantization**: The output of the wavelet filter is converted to a sign-magnitude representation and pre-quantized by a [dead-zone quantizer](https://en.wikipedia.org/wiki/Dead-zone_quantizer) to 16-bit precision.

**Rate control and quantization**: The encoder determines by a proprietary process<sup>[[22]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-:0-22)</sup> the rate of each possible quantization setting and then quantizes data by either a dead-zone quantizer or a data-dependent uniform quantizer.

**Entropy coding**: JPEG XS uses minimalistic [entropy encoding](https://en.wikipedia.org/wiki/Entropy_encoding) for the quantized data, which proceeds in up to four passes over horizontal lines of quantized wavelet coefficients. The steps are:

- Significance coding: In the (optional) first pass, the significance of 32 consecutive wavelet coefficients is coded by a single bit.
- Bitplane count coding: In the second pass, the number of non-zero bitplanes of groups of four coefficients each, the so-called bitplane count, is entropy coded through a Golomb type code. This step may optionally use the bitplane counts of the preceding line as the source for prediction (differential pulse-code modulation) and then encode only the prediction difference.
- Data coding: The third pass inserts the raw bitplane values into the codestream without further coding.
- Sign coding: In the last optional coding pass, the sign bits of all non-zero coefficients are inserted into the codestream. If this coding pass is not present, sign bits are included in the data coding pass for all coefficients.

**Codestream packing**: All entropy-coded data are packed into a linear stream of bits (grouped in byte multiples) along with all of the required image metadata. This sequence of bytes is called the codestream and its high-level syntax is based on JPEG marker and marker segment syntax.<sup>[[23]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-23)</sup>

JPEG XS defines profiles in ISO/IEC 21122-2<sup>[[9]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-:1-9)</sup> that define subsets of coding tools that conforming decoders must support and limit the permitted parameter values and allowed markers. The following table represents an overview of all the profiles along with their most important properties.

| Profile | P<sub>pih</sub> | B[i] | N<sub>bpp,max</sub> | B<sub>w</sub> | B<sub>r</sub> | F<sub>q</sub> | Q<sub>pih</sub> | Horizontal DWT | Vertical DWT | Chroma sampling formats | C<sub>pih</sub> | Added by edition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Light 422.10 | `0x1500` | 8, 10 | 20 | 20 | 4 | 8 | 0 | 1 to 5 | 0, 1 | 4:0:0, 4:2:2 | 0 | 1 |
| Light 444.12 | `0x1A00` | 8, 10, 12 | 36 | 20 | 4 | 8 | 0 | 1 to 5 | 0, 1 | 4:0:0, 4:2:2, 4:4:4 | 0, 1 | 1 |
| Light-Subline 422.10 | `0x2500` | 8, 10 | 20 | 20 | 4 | 8 | 0, 1 | 1 to 5 | 0 | 4:0:0, 4:2:2 | 0 | 1 |
| Main 420.12 | `0x3240` | 8, 10, 12 | 18 | 20 | 4 | 8 | 0, 1 | 1 to 5 | 1 | 4:2:0 | 0 | 1 |
| Main 422.10 | `0x3540` | 8, 10 | 20 | 20 | 8 | 4 | 0, 1 | 1 to 5 | 0, 1 | 4:0:0, 4:2:2 | 0 | 1 |
| Main 444.12 | `0x3A40` | 8, 10, 12 | 36 | 20 | 4 | 8 | 0, 1 | 1 to 5 | 0, 1 | 4:0:0, 4:2:2, 4:4:4 | 0, 1 | 1 |
| Main 4444.12 | `0x3E40` | 8, 10, 12 | 48 | 20 | 4 | 8 | 0, 1 | 1 to 5 | 0, 1 | 4:0:0, 4:2:2, 4:4:4, 4:2:2:4, 4:4:4:4 | 0, 1 | 1 |
| High 420.12 | `0x4240` | 8, 10, 12 | 18 | 20 | 4 | 8 | 0, 1 | 1 to 5 | 1, 2 | 4:2:0 | 0 | 2 |
| High 444.12 | `0x4A40` | 8, 10, 12 | 36 | 20 | 4 | 8 | 0, 1 | 1 to 5 | 0, 1, 2 | 4:0:0, 4:2:2, 4:4:4 | 0, 1 | 1 |
| High 4444.12 | `0x4E40` | 8, 10, 12 | 48 | 20 | 4 | 8 | 0, 1 | 1 to 5 | 0, 1, 2 | 4:0:0, 4:2:2, 4:4:4, 4:2:2:4, 4:4:4:4 | 0, 1 | 1 |
| CHigh 444.12 | `0x4A44` | 8, 10, 12 | 36 | 20 | 4 | 8 | 0, 1 | 1 to 5 | 0, 1, 2 | 4:0:0, 4:2:2, 4:4:4 | 0, 1 | 3 |
| TDC 444.12 | `0x4A45` | 8, 10, 12 | 36 | 20 | 4 | 8 | 0, 1 | (3, 0) and (4, 0) if not 4:2:0, (4, 1), (5, 1), (5, 2) otherwise | 4:0:0, 4:2:0, 4:2:2, 4:4:4 | 0, 1 | 3 |  |
| TDC MLS 444.12 | `0x6A45` | 8, 10, 12 | 36 | B[i] | 4 | 0 | 0, 1 | (3, 0) and (4, 0) if not 4:2:0, (4, 1), (5, 1), (5, 2) otherwise | 4:0:0, 4:2:0, 4:2:2, 4:4:4 | 0, 1 | 3 |  |
| MLS.12 | `0x6EC0` | 8, 10, 12 | 48 | B[i] | 4 | 0 | 0, 1 | 1 to 5 | 0, 1, 2 | 4:0:0, 4:2:0, 4:2:2, 4:4:4, 4:2:2:4, 4:4:4:4 | 0, 1 | 2 |
| MLS.16 | `0x6ED0` | 8, 10, 12, 14, 16 | 64 | B[i] | 5 | 0 | 0, 1 | 1 to 5 | 0, 1, 2 | 4:0:0, 4:2:0, 4:2:2, 4:4:4, 4:2:2:4, 4:4:4:4 | 0, 1 | 3 |
| LightBayer | `0x9300` | 10, 12, 14, 16 | 64 | 18, 20 | 4 | 6, 8 | 0, 1 | 1 to 5 | 0 | Bayer | 3 | 2 |
| CMainBayer<sup>[[a]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-21122p2a2-24)</sup> | `0xB344` | 10, 12, 14, 16 | 64 | 18, 20 | 4 | 6, 8 | 0, 1 | 5 | 1 | Bayer | 3 | 3 |
| MainBayer | `0xB340` | 10, 12, 14, 16 | 64 | 18, 20 | 4 | 6, 8 | 0, 1 | 1 to 5 | 0, 1 | Bayer | 3 | 2 |
| HighBayer | `0xC340` | 10, 12, 14, 16 | 64 | 18, 20 | 4 | 6, 8 | 0, 1 | 1 to 5 | 0, 1, 2 | Bayer | 3 | 2 |

In addition, JPEG XS defines levels to represent a lower bound on the required throughput that conforming decoders need to support in the decoded image domain. The following table lists the levels as defined by JPEG XS. The maximums are given in the context of the sampling grid, so they refer to a per-pixel value where each pixel represents one or more component values. However, in the context of Bayer data, JPEG XS internally interprets the Bayer pattern as an interleaved grid of four components. This means that the number of sampling grid points required to represent a Bayer image is one-fourth the total number of Bayer sample points. Each group of 2 × 2 (four) Bayer values gets interpreted as one sampling grid point with four components. Thus, sensor resolutions should be divided by four to calculate the respective width, height and number of sampling grid points. For this reason, all levels also bear double names.

| Level | Max width | Max height | Max pixels (Lmax) | Max pixel rate (Rs,max) | Plev bits<sup>[[b]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-25)</sup> |
| --- | --- | --- | --- | --- | --- |
| Unrestricted | 65535 | 65535 | - | - | `0000 00xx xxxx xxxx` |
| 1k-1, Bayer2k-1 | 1280 | 5120 | 2621440 | 83558400 | `0000 01xx xxxx xxxx` |
| 2k-1, Bayer4k-1 | 2048 | 8192 | 4194304 | 133693440 | `0001 00xx xxxx xxxx` |
| 4k-1, Bayer8k-1 | 4096 | 16384 | 8912896 | 267386880 | `0010 00xx xxxx xxxx` |
| 4k-2, Bayer8k-2 | 4096 | 16384 | 16777216 | 534773760 | `0010 01xx xxxx xxxx` |
| 4k-3, Bayer8k-3 | 4096 | 16384 | 16777216 | 1069547520 | `0010 10xx xxxx xxxx` |
| 5k-1, Bayer10k-1<sup>[[c]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-21122p2a1-26)</sup> | 5120 | 16384 | 16777216 | 1069547520 | `0010 11xx xxxx xxxx` |
| 8k-1, Bayer16k-1 | 8192 | 32768 | 35651584 | 1069547520 | `0011 00xx xxxx xxxx` |
| 8k-2, Bayer16k-2 | 8192 | 32768 | 67108864 | 2139095040 | `0011 01xx xxxx xxxx` |
| 8k-3, Bayer16k-3 | 8192 | 32768 | 67108864 | 4278190080 | `0011 10xx xxxx xxxx` |
| 10k-1, Bayer20k-1 | 10240 | 40960 | 104857600 | 3342336000 | `0100 00xx xxxx xxxx` |

Similar to the concept of levels, JPEG XS defines sublevels to represent a lower bound on the required throughput that conforming decoders need to support in the encoded image domain. Each sublevel is defined by a nominal bit-per-pixel (N<sub>bpp</sub>) value that indicates the maximum number of bits per pixel for an encoded image of the maximum permissible number of sampling grid points according to the selected conformance level. Thus, decoders conforming to a particular level and sublevel shall conform to the following constraints derived from N<sub>bpp</sub>:

The following table lists the existing sublevels and their respective nominal N<sub>bpp</sub> values. Please refer to the standard for a complete specification of each level.

| Sublevel | Nominal bpp (N<sub>bpp</sub>) | Plev bits<sup>[[d]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-27)</sup> |
| --- | --- | --- |
| Unrestricted | - | `xxxx xxxx 0xx0 0000` |
| Full | Native image bpp | `xxxx xxxx 1xx0 0000` |
| Sublev12bpp | 12 | `xxxx xxxx 0xx1 0000` |
| Sublev9bpp | 9 | `xxxx xxxx 0xx0 1100` |
| Sublev6bpp | 6 | `xxxx xxxx 0xx0 1000` |
| Sublev4bpp | 4 | `xxxx xxxx 0xx0 0110` |
| Sublev3bpp | 3 | `xxxx xxxx 0xx0 0100` |
| Sublev2bpp | 2 | `xxxx xxxx 0xx0 0011` |

Usage of a TDC profile results in a TDC-enabled codestream that requires support for a frame buffer in the encoder and decoder. In this context, the concept of Frame Buffer Bandwidth (FBB) levels is used by JPEG XS to represent a lower bound on the required throughput that conforming decoders need to support for accessing the frame buffer. From the perspective of the codestream, the FBB level defines the minimal required read and write bandwidths of the frame buffer. This bandwidth is defined by a nominal bit-per-pixel (B<sub>f</sub>) value that is associated with a valid FBB level and used as an input parameter of the FBB model of JPEG XS. Please refer to the standard for more details.

The following table lists the existing FBB levels and their respective B<sub>f</sub> values.

| FBB level | Throughput bpp (B<sub>f</sub>) | Plev bits<sup>[[e]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-28)</sup> |
| --- | --- | --- |
| Unrestricted | - | `xxxx xx00 x00x xxxx` |
| FbblevFull | Unconstrained | `xxxx xx11 x11x xxxx` |
| Fbblev12bpp | 12 | `xxxx xx11 x00x xxxx` |
| Fbblev8bpp<sup>[[c]](https://en.wikipedia.org/wiki/JPEG_XS#cite_note-21122p2a1-26)</sup> | 8 | `xxxx xx01 x10x xxxx` |
| Fbblev4.5bpp | 4.5 | `xxxx xx01 x00x xxxx` |
| Fbblev3bpp | 3 | `xxxx xx00 x11x xxxx` |

1. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-21122p2a2_24-0) Defined in ISO/IEC 21122-2:2024/DAmd2
2. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-25) An 'x' indicates either a 0 or a 1, used to signal sublevel and FBB level.
3. [1](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-21122p2a1_26-0) [2](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-21122p2a1_26-1) Defined in ISO/IEC 21122-2:2024/Amd1:2026
4. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-27) An 'x' indicates either a 0 or a 1, used to signal level and FBB level.
5. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-28) An 'x' indicates either a 0 or a 1, used to signal level and sublevel.

1. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-1) ["Video format JXSV"](https://web.archive.org/web/20210927002506/https://www.iana.org/assignments/media-types/video/jxsv). Archived from [the original](https://www.iana.org/assignments/media-types/video/jxsv) on 2021-09-27.
2. [1](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-JPEG_XS_2-0) [2](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-JPEG_XS_2-1) ["Overview of JPEG XS"](https://jpeg.org/jpegxs/). *jpeg.org*. Retrieved 2019-07-31.
3. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-3) T. Richter, J. Keinert, S. Foessel, A. Descampe, G. Rouvroy and J. -B. Lorent, "JPEG-XS -- A High-Quality Mezzanine Image Codec for Video Over IP," in SMPTE Motion Imaging Journal, vol. 127, no. 9, pp. 39-49, Oct. 2018, doi: 10.5594/JMI.2018.2862098 [link](https://web.archive.org/web/20210826113823/https://ieeexplore.ieee.org/document/8470198).
4. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-4) Pessina, Laure-Anne (September 4, 2018), [*A new JPEG format for virtual reality, drones and self-driving cars*](https://actu.epfl.ch/news/a-new-jpeg-format-for-virtual-reality-drones-and-s/), [archived](https://web.archive.org/web/20230605095051/https://actu.epfl.ch/news/a-new-jpeg-format-for-virtual-reality-drones-and-s/) from the original on 2023-06-05 – via actu.epfl.ch
5. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-5) Keinert, Joachim; Lorent, Jean-Baptiste; Descampe, Antonin; Rouvroy, Gaël; Fößel, Siegfried. ["Introduction to JPEG XS"](https://www.ibc.org/introduction-to-jpeg-xs/2452.article). *IBC*. [Archived](https://web.archive.org/web/20230402121749/https://www.ibc.org/introduction-to-jpeg-xs/2452.article) from the original on 2023-04-02.
6. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-6) ["JPEG White paper: JPEG XS, a new standard for visually lossless low-latency lightweight image coding system"](http://ds.jpeg.org/whitepapers/jpeg-xs-whitepaper.pdf) (PDF).
7. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-7) Richter, Thomas; Keinert, Joachim; Descampe, Antonin; Rouvroy, Gael; Willeme, Alexandre (December 2017). "Multi-generation-robust Coding with JPEG XS". *2017 IEEE International Symposium on Multimedia (ISM)*. pp. 6–13. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/ISM.2017.12](https://doi.org/10.1109%2FISM.2017.12). [ISBN](https://en.wikipedia.org/wiki/ISBN_(identifier)) [978-1-5386-2937-6](https://en.wikipedia.org/wiki/Special:BookSources/978-1-5386-2937-6). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [32986247](https://api.semanticscholar.org/CorpusID:32986247).
8. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-8) T. Richter, S. Fößel, A. Descampe and G. Rouvroy, "Bayer CFA Pattern Compression With JPEG XS," in IEEE Transactions on Image Processing, vol. 30, pp. 6557-6569, 2021, doi: 10.1109/TIP.2021.3095421 [link](https://ieeexplore.ieee.org/document/9488288).
9. [1](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-:1_9-0) [2](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-:1_9-1) International Organization for Standardization. ["ISO/IEC 21122-2:2024"](https://www.iso.org/standard/85250.html). *ISO*.
10. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-10) ["ISO/IEC JTC 1/SC29/WG1 N100633, REQ "Use Cases and Requirements for JPEG XS v3.2""](https://ds.jpeg.org/documents/jpegxs/wg1n100633-101-REQ-Use_Cases_and_Requirements_for_JPEG_XS_v3_2.pdf) (PDF).
11. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-11) Richter, Thomas; Fößel, Siegfried; Descampe, Antonin; Rouvroy, Gaël (2021). ["Bayer CFA Pattern Compression With JPEG XS"](https://doi.org/10.1109%2FTIP.2021.3095421). *IEEE Transactions on Image Processing*. **30**: 6557–6569. [Bibcode](https://en.wikipedia.org/wiki/Bibcode_(identifier)):[2021ITIP...30.6557R](https://ui.adsabs.harvard.edu/abs/2021ITIP...30.6557R). [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/TIP.2021.3095421](https://doi.org/10.1109%2FTIP.2021.3095421). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[2078.1/249445](https://hdl.handle.net/2078.1%2F249445). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1941-0042](https://search.worldcat.org/issn/1941-0042). [PMID](https://en.wikipedia.org/wiki/PMID_(identifier)) [34270422](https://pubmed.ncbi.nlm.nih.gov/34270422). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [236001190](https://api.semanticscholar.org/CorpusID:236001190).
12. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-12) *RTP Payload Format for ISO/IEC 21122 (JPEG XS)*. [IETF](https://en.wikipedia.org/wiki/Internet_Engineering_Task_Force). [RFC](https://en.wikipedia.org/wiki/RFC_(identifier)) [9134](https://tools.ietf.org/html/rfc9134).
13. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-13) [TR-08: Transport of JPEG XS Video in ST 2110-22](https://vsf.tv/download/technical_recommendations/VSF_TR-08_2022-04-20.pdf)
14. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-14) ["ISO/IEC 13818-1:2023"](https://www.iso.org/standard/87619.html).
15. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-15) [TR-07: Transport of JPEG XS Video in MPEG-2 TS over IP](https://vsf.tv/download/technical_recommendations/VSF_TR-07_2022-04-20.pdf)
16. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-16) [AMWA BCP-006-01: NMOS With JPEG XS](https://specs.amwa.tv/bcp-006-01/)
17. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-17) [TR-10-8:2023-Internet Protocol Media Experience (IPMX): NMOS Requirements - DRAFT](https://vsf.tv/download/technical_recommendations/VSF_TR-10-8_2023-04-14.pdf)
18. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-18) [TR-10-11:2023-Internet Protocol Media Experience (IPMX): Constant Bit-Rate Compressed Video - DRAFT](https://vsf.tv/download/technical_recommendations/VSF_TR-10-11_2023-04-14.pdf)
19. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-ieee_jpeg_xs_2021_19-0) A. Descampe et al., "JPEG XS--A New Standard for Visually Lossless Low-Latency Lightweight Image Coding," in Proceedings of the IEEE, doi: 10.1109/JPROC.2021.3080916 [PDF](https://dial.uclouvain.be/pr/boreal/object/boreal:248275).
20. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-20) ["Fraunhofer IIS receives EMMY® Award for its JPEG XS high-quality, low-latency video codec"](https://www.iis.fraunhofer.de/en/pr/2025/pressrelease-emmy-jpegxs.html). *Fraunhofer Institute for Integrated Circuits IIS*. Retrieved 2026-04-25.
21. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-21) International Organization for Standardization. ["ISO/IEC 21122-1:2024"](https://www.iso.org/standard/85247.html). *ISO*.
22. [1](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-:0_22-0) [2](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-:0_22-1) Descampe, Antonin; Richter, Thomas; Ebrahimi, Touradj; Foessel, Siegfried; Keinert, Joachim; Bruylants, Tim; Pellegrin, Pascal; Buysschaert, Charles; Rouvroy, Gaël (September 2021). "JPEG XS—A New Standard for Visually Lossless Low-Latency Lightweight Image Coding". *Proceedings of the IEEE*. **109** (9): 1559–1577. [doi](https://en.wikipedia.org/wiki/Doi_(identifier)):[10.1109/JPROC.2021.3080916](https://doi.org/10.1109%2FJPROC.2021.3080916). [hdl](https://en.wikipedia.org/wiki/Hdl_(identifier)):[2078.1/248275](https://hdl.handle.net/2078.1%2F248275). [ISSN](https://en.wikipedia.org/wiki/ISSN_(identifier)) [1558-2256](https://search.worldcat.org/issn/1558-2256). [S2CID](https://en.wikipedia.org/wiki/S2CID_(identifier)) [236727596](https://api.semanticscholar.org/CorpusID:236727596).
23. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-23) ["codestream-parser"](https://github.com/thorfdbg/codestream-parser). June 16, 2022 – via GitHub.
24. [↑](https://en.wikipedia.org/wiki/JPEG_XS#cite_ref-29) ["JPEG XS Patent Pool"](https://www.jpegxspool.com/). *JPEG XS Patent Pool*.