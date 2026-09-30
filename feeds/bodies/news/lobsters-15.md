Espressif Systems' ESP32 microcontrollers are well known for their Wi-Fi and Bluetooth capabilities.
Over the past few months (and with the help of LLMs), we have found an undocumented feature that allows the firmware to bypass the fixed-function modems to capture raw IQ baseband samples.
This opens up the possibility of using the ESP32 as a low-cost software-defined radio (SDR) platform, capable of receiving signals in the 2.4 GHz band (and the 5 GHz band on the ESP32-C5).

## Try it out in your browser (Web Serial)

To prove the concept, we made a simple web interface that displays the live power spectrum and waterfall of the captured IQ samples (at **a very low** duty cycle).
Use a browser with [Web Serial](https://developer.mozilla.org/en-US/docs/Web/API/Web_Serial_API) support.

#### 1
Flash ESP-SDR firmware to your board

Connect your board over USB and install the SDR firmware using the browser flasher.
Supported chips are the **original ESP32**, **ESP32-C3**, **ESP32-C5**, **ESP32-C6**, **ESP32-C61**, **ESP32-S2**, **ESP32-S3** and **ESP32-S31**.
The original ESP32 requires a USB-to-UART bridge, often built into the development board.

#### 2
Explore the live radio spectrum

After flashing, unplug the board for five seconds and reconnect. Open ESP-WebSDR and select your device to see the live spectrum.

## How it works

We assume that Espressif engineers left the IQ sampling path in place for testing and debugging the modem,
for example for on-wafer testing in the fab.
The exact capture mechanism, trigger modes and memory allocation differ between chips, but the general idea is the same:
special debug registers configure the modem's sample-dump engine to write raw IQ samples directly into the chip's internal SRAM, bypassing normal Wi-Fi processing.
The firmware reserves SRAM so that the heap cannot use it, then lets the modem write raw IQ into that memory.

For example, on the ESP32-C61, the capture mechanism works as follows:
The SRAM inside the ESP32 is organized into banks.
Our firmware uses two of these banks and organizes them as a ring buffer.
One of the banks is temporarily owned by the modem, which writes raw IQ samples into it, while the other bank is owned by the CPU, which copies the completed samples to a buffer for transfer to the host.
The firmware tracks the hardware write pointer to detect when the modem moves to the next bank.

### IQ sample format

The exact format of the IQ samples is configurable. In our implementation, each complex sample occupies one 32-bit word in memory.
Bits 19–10 hold I and bits 9–0 hold Q, both signed 10-bit two's-complement values
(−512 to +511). Bits 27–20 report the receiver gain setting (an index into the gain table), while bits 31–28
are most likely the internal state of the automatic gain control's finite state machine.

### Capture settings

#### Tuning

2.2–2.7 GHz  
4.8–6.0 GHz

5 GHz is only available on ESP32-C5. Exact tuning limits differ by chip.

#### Sample rate

Up to 80 MSa/s

Raw complex IQ capture into memory, with transfer to the host at a low duty cycle.

#### Bandwidth

~13–54 MHz

Analog RX bandwidth. Exact limits depend on the chip and filter settings.

#### Gain control

Automatic or manual

Internal hardware AGC or a manually selected fixed receiver gain.

With ESP-SDR, the ESP32 can even capture IQ data *beyond* the officially supported tuning range.
For example, the ESP32-C61 can capture signals up to 2.7 GHz, which includes some **LTE and 5G NR cellular bands**, such as LTE band 7 and 5G NR band n7 around 2.6 GHz.

### How we discovered this

Our starting point was the `adctrig` function in Espressif's `librftest` library.
With the help of LLMs, we reverse engineered this function to understand how it configures the hardware to capture raw IQ samples.
These findings formed the basis of ESP-SDR's capture implementation.

## What this means for ESPARGOS

Without any hardware modifications, [ESPARGOS One](https://espargos.net/espargos-one) can now *phase-coherently* capture raw IQ samples.
If you already have an [ESPARGOS One](https://espargos.net/espargos-one), [update its firmware](https://espargos.net/firmware/) to the latest version from the *dev* branch to enable this capability. The hardware already supports it.
We currently provide the "IQ Signal Analyzer" demo application, but are working on additional demo applications, including an adapted real-time augmented reality demo for arbitrary signals.

The IQ sampling implementation on [ESPARGOS One](https://espargos.net/espargos-one) is even more powerful than the browser-based demo (ESP-WebSDR):

- Higher throughput / duty cycle: ESPARGOS One uses an internal SPI transport interface, which is much faster than the UART interface used by ESP-WebSDR.
- Signal trigger: Instead of streaming all samples (mostly silence), ESPARGOS One can be configured to stream samples only when a signal is detected.

In addition to the existing Wi-Fi channel state information (CSI)-based demos, [ESPARGOS One](https://espargos.net/espargos-one) can now also be used as a low-cost, eight-channel SDR platform for the 2.4 GHz ISM band, operating at a low duty cycle.
The benefits of raw IQ capture over processed CSI include:

- Localize arbitrary signals: ESPARGOS One can now be used to localize arbitrary signals in the 2.4 GHz ISM band, not just Wi-Fi signals. This includes Bluetooth and Bluetooth Low Energy, Zigbee, and Wi-Fi formats that were previously unsupported for CSI capture (e.g., 802.11b and Wi-Fi signals with multiple spatial streams).
- Array gain: Signal processing and decoding can be performed centrally, improving weak-signal performance.
- Special waveforms: ESPARGOS One can now be used with waveforms more suitable for specific applications, e.g., pulse compression radar. Even better, some preprocessing for such special applications can happen on the chip itself, so they are not throughput-constrained.

## Limitations

At 80 MSa/s and 32 bits per sample, the modem writes **2,560 Mbit/s** into SRAM.
Getting those samples off the chip is the bottleneck: the output links are much slower.

Therefore, our firmware streams the IQ samples at a very low duty cycle, which is enough to display a live spectrum and waterfall in the browser.
Packets that arrive between capture windows may be missed.

## SoapyESPSDR: GNU Radio & gqrx

[SoapyESPSDR](https://github.com/ESPARGOS/SoapyESPSDR) is our receive-only
SoapySDR driver for the **ESP32-S31**. It streams IQ samples over Gigabit Ethernet
from a board running ESP-SDR firmware, making the receiver available to applications such as
**GNU Radio** and **gqrx** through their SoapySDR support.

The S31 supports continuous reception at 8 and 16 MSa/s; higher sample rates require a reduced
duty cycle.

**Under development:** We will release firmware and SoapySDR driver repositories soon, once everything is ready.

Coming soon.

## More information and firmware

- ESP-SDR firmware: firmware source code and build instructions.
- ESP-WebSDR browser interface: browser-based spectrum viewer and firmware flasher.
- The firmware of ESPARGOS One remains closed source for now, but we are considering on open-sourcing it now that this "secret" IQ functionality that we were keeping private has been revealed.

## FAQs

No, this is a feature of the ESP32's modem that was not documented in the public datasheet.
As far as we are concerned, it is not a security vulnerability, but rather an undocumented capability that can be used for SDR applications.
That being said, many ESP32-powered devices are connected to various cloud services which allow the manufacturer of to update the firmware remotely.
If sensitive data is transmitted without encryption in the ISM bands, this could pose a security concern. In that case, the underlying issue is the unencrypted transmission.
The ability of the ESP32 to transmit arbitrary signals, on the other hand, could be abused for jamming or other malicious purposes, which is why we are not providing a transmitter implementation at this time.

Due to the low duty cycle achievable for most ESP32 models, it does not make much sense to use the SDR mode with these applications.
For the ESP32-S31, our [SoapyESPSDR driver](https://espargos.net/espsdr/#soapyespsdr) provides
integration with GNU Radio, gqrx and other SoapySDR-compatible applications over Gigabit Ethernet.

ESP-SDR currently supports the original ESP32, ESP32-C3, ESP32-C5, ESP32-C6, ESP32-C61, ESP32-S2, ESP32-S3 and ESP32-S31. We are working to extend the range of supported ESP32 chips. Support for additional models will most likely be possible, but each chip needs its own implementation.

Yes, this is possible. An external mixer can translate signals from other frequency bands into the ESP32's transmit / receive range. We already have multi-channel prototype hardware for this.

## Acknowledgements

User *h0m3us3r* first disclosed this capability for the ESP32-S3 [on Reddit](https://www.reddit.com/r/esp32/comments/1wq37xz/got_raw_iq_streaming_out_of_an_esp32s3_at_80_mss/), including firmware source code, a few days before our announcement.
They achieve 80 MSa/s of sustained throughput using an additional FPGA to handle the transfer.
Since we have been independently working on IQ capture for several months now, we also wanted to share our findings with the community.