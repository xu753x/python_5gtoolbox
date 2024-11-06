# 前言
2019年曾经试着用Matlab写5G物理层toolbox，做了一段时间发现没办法继续下去，主要原因是没有测试用例，没办法验证自己对协议的理解正确与否，也没办法验证代码的正确性。

现在有机会接触到Mathwork的5g Toolbox，可以参考里面的代码来学习5G物理层协议，更重要的是可以生成各种测试用例来验证自己写的代码,这样我才从新开始5G物理层toolbox的开发。新的5G物理层toolbox基于Python3，当前（2024年10月）完成的是第一版，只支持3GPP Release 15，支持上行和下行物理层信道的发送，不支持接收。通过matlab 5G toolbox生成了60K多的测试用例来验证代码。整个测试跑下来需要几周的时间(149901 passed in 1875495.34s (21 days, 16:58:15)，绝大部分时间都用在PDSCH和PUSCH LDPC编码。

开发过程中花了很多时间来理解Matlab 5G toolbox，并且发现了里面的一些[bugs](./docs/Mathwork_5Gtoolbox_bugs.md).

# 关于Py5GPhy toolbox支持的物理层功能
5G标准制定的时候雄心勃勃，同时支持很多功能，但是gNB产品实现很多时候只支持其中的部分功能，比如：

| 标准 | 产品|
| ---- | ---- |
|支持sub-6 GHz 和28GHz以上毫米波 | 主流只支持Sub-6GHz |
| 一个载波同时支持多个BWP（bandwidth part）| 只支持一个BWP|
| 一个载波的不同信道支持不同的子载波带宽<br>比如SSB scs 15Khz, SIB scs 30KHz, UE specific PDSCH/PUSCH 60Khz等等| 所有信道使用同一个子载波带宽(15Khz or 30KHz) <br>不支持60Khz|
| 大规模天线阵列,such as 32/64/128/256个天线阵列|只支持2天线或者4天线<br>intel FelxRAN 5G物理层solution也最大支持4天线 |

为了简单起见，我在设计5GPhy toolbox的时候，主要是针对产品支持的功能。
5GPhy toolbox支持的功能在[release note](./5gtoolbox_release_note.md)

# Py5GPhy toolbox的用途
## 适合用来学习5G物理层协议，这也是最主要的用途
3GPP物理层协议的编写从3G WCDMA到LTE风格大变，LTE物理层协议更多采用数学的语言来描述，很严谨，不会出错，但是同时也更难懂，对于母语非英语的人更是难上加难。5G物理层协议编写也延续了LTE的风格，但是LTE协议至少还提供一些图用来帮助理解，5G协议都没有了，而且5G协议比LTE复杂太多，学习起来难度更大。

Py5GPhy toolbox实现更加贴近协议的描述，函数里面添加注释来描述实现的协议名称和章节，以帮助参考协议进行学习。
By the way,我觉得Matlab 5G toolbox的设计太复杂，不太适合用于学习5G物理层协议

## 用于生成5G物理层上下行测试用例，以协助5G产品开发
现在是2024年，估计很少有公司再重新开发5G物理层了。
物理层开发的时候需要提供大量的测试用例来验证实现是否正确，Py5GPhy toolbox可以用来做这个工作

# 生成test model waveform,用于RU发送端性能分析
 RU发送端实现IFFT，add CP，phase compensation, channel filter, CFR, DPD 等数字端处理，然后数据经过DAC转为模拟信号，经过模拟端混频器，band filter, PA放大信号发送出去。

 为了测试RU发送性能，RU端输入各种test model waveform,输出连接VSA，在VSA上显示信号的ACLR，EVM等指标，验证RU这些指标是否满足3GPP requirements。

 Py5GPhy toolbox可以生成各种test model waveform

# 下一步开发计划
1. 增加上行和下行接收机设计
    * 下行接收需要支持SSB搜索，PDCCH盲检，PDSCH接收，CSI-RS接收等操作，并且支持时延，频偏估计补偿
    * 上行接收需要支持PRACH处理，PUCCH，PUSCH，SRS处理
2. write document 介绍5G物理层
    * 介绍物理层系统设计
    * channel filter, CFR, DPD...
# Py5GPhy toolbox安装使用
[ubuntu安装](./docs/ubuntu22_04_2_py5gphy_usage.md )

[macbook安装](./docs/macbook_M1chipset_py5gphy_usage.md)

Windows下直接安装Poetry总是报错，通过VScode Create venv，然后就可以安装Poetry，执行Py5GPhy toolbox

[use VSCode](./docs/use_vscode.md)

# 如何学习Py5GPhy toolbox
py5gphy/nr_default_config目录列出所有channel的default配置，py5gphy/nr_waveform里面的文件时waveform geeration入口

另外每个channel还可以单独运行测试用例，比如学些PDSCH，可以进入py5gphy/nr_pdsch,打开nr_dlsch.py or nr_pdsch.py.直接运行里面的测试用例

# additonal information
LDPC encode optimization explanation is [here](./docs/LDPC_encoder_optimization.pdf)