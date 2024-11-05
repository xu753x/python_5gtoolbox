# Mathwork 5G Toolbox release I used
5G Toolbox Version 2.6 (R2023a) 19-Nov-2022

Mathwork 5G Toolbox的设计有些过于复杂了，不太适合学习，主要有以下几点。
* project 结构不合理，几乎所有文件都放到一个文件夹，没有按照channel,模块等分别放在不同文件夹
* 设计上把简单的功能复杂化，无谓的函数嵌套，还有大量冗余的处理
    * 基本上每个channel的设计都或多或少有这个问题，其中设计的最繁琐的就是SSB模块
    * SSB模块的resource mapping部分有很多莫名其妙的操作，整个实现特别复杂，我一直都没有完成搞懂。而我的实现非常简单，物理含义也非常清晰。
* 倾向于把太多功能放到一个函数/文件，导致程序结构复杂
    * 比如nrWaveformGenerator模块有快2000行，里面包含很多函数，把上行和下行数据处理都放到这个文件里面，理解起来非常费力。上下行分开，大文件拆分成多个文件更好理解
    * processAndGeneratePXSCH函数，把PDSCH和PUSCH处理放到着一个函数里面，只会把函数变得复杂难懂

The design of Mathwork 5G Toolbox is a bit too complicated and not suitable for learning.
* The project structure is not reasonable, almost all the files are put into one folder.
* The design is too complicated for some should-be-simple functions, it also includes unnecessary function nesting, and a lot of redundant processing.
    * SSB module is the typical one.
    * SSB module resource mapping part has a lot of inexplicable operations, the whole implementation is particularly complex which make me very hard to understand. My implementation is quite simple, and the physical meaning is also very clear.
* put too many functions into one function/file, resulting in a complex program structure
    * For example, the nrWaveformGenerator module is almost 2000 lines long and contains many functions. Putting both upstream and downstream data processing into this file is very laborious to understand. Separate the upstream and downstream lines, and split the large file into multiple files for better understanding.
    * processAndGeneratePXSCH function, put the PDSCH and PUSCH processing into a function, it will only make the function complex and difficult to understand.

Translated with DeepL.com (free version)

# bugs I found in Mathwork 5G Toolbox

* PDSCH targetcode rate calculation didn't exactly follow 3GPP spec.

  38.214 5.1.3.1 provide tables which indicate the mudulation order and target code rate that PDSCH support.
  while in the toolbox any PDSCH targetcode rate can use used.

* PDSCH rate matching didn;t calculate TBS_LBRM

  I_LBRM =1(38.212 7.2.5) which means Ncb selection should count TBS_LBRM(38.212 5.4.2.1).
  TBS_LBRM value should be calculated based on PDSCH configuration. But Tooblox set TBS_LBRM to constant value 25344

* nPC and nPCwm calculation in nr5g.internal.polar.construct for Polor encoder has issue

  the processing has a little difference between DL and UL. toolbox didn't check DL and UL.
  the bug will be triggered if DL DCI K is in [18,25]

* PRACh module C2 format has some issues

  it happens on TDD mode PRACH configuration index from 189-210 which use PRACH format C2. the CP length calculation is wrong. 

* PUCCH format 3

  PRB size should be multiple of 2,3,5. toolbox didn't check it

* PUCCH format 4 has bug when SpreadingFactor=4

  it happens in file getPUCCHObject.m

* PUSCH validation has issue

 when TransformPrecoding = 1, number of layer shall be 1, prb num shall be (2^m)*(3^n)*(5^s)

* Ninfo calculation bug in nrTBS.m

  ```matlab
   % Calculate the intermediate number of information bits (N_info)
    Ninfo = S.*NRE.*R.*Qm.*nLayers;
  ```
  S is TBscaling in above code and should be not used for TB size calculation

* SSB module didn;t support carrier scs != ssb scs case case

* a bug in modulation processing in hSSBurst.m
  below carrierFreq + info.FrequencyOffsetSSB should be carrierFreq
  ``` matlab
    % Modulate grid
    waveform = nr5g.internal.wavegen.nrOFDMModulateCallForCodegen(c, grid, ...
        burstSCS, burstCP, windowingProp, burst.SampleRate, carrierFreq + info.FrequencyOffsetSSB);
    
    % Apply time-domain frequency offset if required
    if (info.FrequencyOffsetSSB~=0)
        t = (0:size(waveform,1)-1).' / info.SampleRate;
        waveform = waveform .* exp(1i*2*pi*info.FrequencyOffsetSSB*t);
    end
   ```