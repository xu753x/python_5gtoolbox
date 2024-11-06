# Preface
I tried to write 5G physical layer toolbox using Matlab in 2019. Later I figured out that it is almost not possible.
The main reason was that (1)there were no test cases to verify the code, and (2)I couldn't verify whether my understanding of the protocol was correct or not.

Now I have the opportunity to access Mathwork's 5g Toolbox, and learn 5G physical layer specification from Mathwork's 5g Toolbox code. More importantly, I can generate various test cases to verify the code I wrote. I re-started the development of the 5G physical layer toolbox again based on Python3 this time. The first version is currently completed (October 2024), which only supports 3GPP Release 15, supports the sending of uplink and downlink physical layer channels, but does not support receiving. More than 60K test cases were generated through matlab 5G toolbox to verify the code. The entire test took several weeks to run (149901 passed in 1875495.34s (21 days, 16:58:15), and most of the time was spent on PDSCH and PUSCH LDPC coding.

During the development process, I also found some [Matlab 5G toolbox bugs](./docs/Mathwork_5Gtoolbox_bugs.md).

# About the physical layer functions supported by Py5GPhy toolbox
3GPP 5G specification support too many features, but the 5G gNB products usually only implemented some features, such as:

| Standard | Product|
| ---- | ---- |
|Support sub-6 GHz and millimeter waves above 28GHz | most gNB only supports Sub-6GHz |
| One carrier supports multiple BWPs (bandwidth part) at the same time | Only supports one BWP |
| Different channels in one carrier support different subcarrier bandwidths<br>For example, SSB scs 15Khz, SIB scs 30KHz, UE specific PDSCH/PUSCH 60Khz, etc. | All channels use the same subcarrier bandwidth (15Khz or 30KHz) <br> 60Khz is not supported |
| Large-scale antenna arrays, such as 32/64/128/256 antenna arrays | Only 2 antennas or 4 antennas are supported <br> Intel FelxRAN 5G physical layer solution also supports up to 4 antennas |

To make is simple, I mainly focused on the functions supported by the product when I designed 5GPhy toolbox.

The functions supported by 5GPhy toolbox are in [release note](./5gtoolbox_release_note.md)

# Py5GPhy toolbox usage
## Suitable for learning 5G physical layer protocols, which is also the main purpose of this project
The writing style of 3GPP physical layer protocols has changed greatly from WCDMA to LTE. The LTE physical layer protocol is described more in mathematical language, which is very rigorous and error-free, but it is also more difficult to understand, especially for non-English speakers. The writing of the 5G physical layer protocol also continues the style of LTE, but the LTE protocol at least provides some diagrams to help understand it, while the 5G protocol does not provide diagrams to help understand it. Moreover, the 5G protocol is much more complicated than LTE, making it more difficult to learn.

The Py5GPhy toolbox implementation is close to the description of the protocol. Comments are added to the function to describe the name and chapter of the implemented protocol. it would be a good reference when learning 5G physical layer protocol.
By the way, I think the design of Matlab 5G toolbox is too complicated and not suitable for learning 5G physical layer protocols

## can be used to generate 5G physical layer uplink and downlink test cases to assist in 5G product development
A large number of test cases need to be provided to verify whether the implementation is correct ot not When developing 5G physical layer. Py5GPhy toolbox can be used to do this work

by the way, most tier-2 providers rely on Intel FlexRAN to provide 5G physical layer solution. I am afaird very few companies will develop the 5G physical layer by themselves for now(2024).

# Generate test model waveform for RU transmitter performance analysis
The RU implements many functions such as: IFFT, add CP, phase compensation, channel filter, CFR, DPD and other digital end processing, and then the data is converted to analog signal through DAC, and the signal is amplified by the analog mixer, band filter, and PA and sent out.

In order to test the RU transmission performance, the RU shall inputs various test model waveforms, and the output is connected to VSA. The ACLR, EVM and other indicators of the signal are measured on the VSA to verify whether these RU transmission meet the 3GPP requirements.

Py5GPhy toolbox can generate various test model waveforms

# Next development plan
1. Add uplink and downlink receiver design
* Downlink reception includes: SSB search, PDCCH blind detection, PDSCH reception, CSI-RS reception and other operations, and support delay and frequency offset estimation compensation
* Uplink reception includes: PRACH processing, PUCCH, PUSCH, SRS processing
2. Write document to introduce 5G physical layer
* Introduce physical layer system design
* channel filter, CFR, DPD...
# Py5GPhy toolbox installation and use
[ubuntu installation](./docs/ubuntu22_04_2_py5gphy_usage.md )

[macbook installation](./docs/macbook_M1chipset_py5gphy_usage.md)

Directly installing Poetry under Windows always reports an error. we can use VSCode in windows to run the code. how to use VSCode is at [use VSCode](./docs/use_vscode.md)

# How to learn Py5GPhy toolbox
The py5gphy/nr_default_config directory lists the default configuration of all channels, and the files in py5gphy/nr_waveform are the waveform generation entrances

In addition, each channel can also run test cases separately. For example, to learn PDSCH, you can enter py5gphy/nr_pdsch, open nr_dlsch.py ​​or nr_pdsch.py, then run the test cases directly

# additonal information
LDPC encode optimization explanation is [here](./docs/LDPC_encoder_optimization.pdf)