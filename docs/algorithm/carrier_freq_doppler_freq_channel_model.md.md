# 前言
无线系统发送和接收之间存在定时偏差，载波频偏，以及运动场景下多普勒频移。

载波频偏指的是发送机和接收机之间的本振频率偏差，与多普勒频偏不同。多普勒频偏是通过发送机和接收机间相对运动产生，载波频偏是由于发送机和接收机间晶体振荡题频率偏差导致。

晶体振荡器频偏带来几个影响。

1. 载波频率偏差，比如对3GHz载波，相对频偏0.1ppm的晶体振荡器频偏导致$3^9*0.1*10^-6=300Hz$频偏
2. 采样时钟偏差，比如期望采样时钟32.76Mhz，实际得到$32.76MHz*(1+\rho)$,$\rho$是相对频偏
3. 定时偏差，比如一秒钟定时偏差为$\rho$，1ms定时偏差为$\rho10^{-3}$

多普勒频偏：$\frac{vf_c}{C}$,其中 $v$为发送和接收机互相靠近的相对速度。如果接收机远离发送机运动，多普勒频率为负数。反之为正。

本文分析这些因素对系统的影响，以及估计和补偿方法，内容包括：
1. 定时频偏，载波频偏和多普勒频偏下接收信号数学模型，频偏导致的SINR分析
2. 定时偏差估计和补偿
3. 载波频偏以及多普勒频偏估计和补偿

# 载波频偏和多普勒频偏下接收信号数学模型

IDFT公式为：$x(n)=\frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1} X[k]e^{j2\pi kn/N}$

只考虑一个子载波$X_k$,其他$X(k)=0$, 则OFDM符号的时域离散接收信号为：
$$
\begin{align}
x(n)&=\frac{1}{N}h_kX_ke^{j2\pi(k+\frac{f_i}{f_c}\rho+\frac{f_d}{f_c})(n(1+\rho)+L_m\rho-\delta)/N} \nonumber \\
&=\frac{1}{N}h_kX_ke^{j2\pi(k+M\rho+\varepsilon)(n(1+\rho)+L_m\rho-\delta)/N}
\end{align}
$$ 

这个公式是以接收机为基准：
* $h_k$为子载波$k$的信道响应，$X_k$为子载波$k$发送信号
* 发送机晶体振荡器相对频偏$\rho$
* 载波频率$f_i$
* 子载波带宽$f_c$
* 采样时钟带宽$T_C$
* 多普勒频移$f_d$
* $\frac{f_i}{f_c}\rho=M\rho$为发送机相对于子载波频率的载波频偏, $M$为载波频率和子载波带宽比值
* $\frac{f_d}{f_c}$为相对于子载波频率的多普勒频偏
* $(1+\rho)$为发送机相对采样时钟
* $L_m\rho$为发送机晶体振荡器相对频偏导致的符号$m$的采样定时偏差
* $\delta$为发送机相对接收机的符号定时偏差，$\delta$为正代表发送机滞后发送，为负表示发送机超前发送


例子：假设一个5G carrier，载波频率$f_i=3GHz$，带宽100MHz，子载波带宽$f_c=30KHz$，时域采样频率为$$122.88MHz$,则采样时钟带宽$T_C=1/122.88MHz$,晶体振荡器相对频偏$\rho=0.1ppm$，移动速度$v=216km/hour=60m/s$，发送机和接收机间符号定时偏差$\delta=2.5$

1ms内14个符号，每个符号sample长度为4096，符号0 CP长度为352，其他符号CP长度为288.

symbol 0 长度为352CP+4096 sample, symbol 1 长度为288CP+4096sample, symbol2 CP = 288,$m=2$符号距离slot起始位置有$L_m=(352+4096+288+4096+200)\rho=9120\rho$。假设符号2和9为DMRS符号，用于时偏和频偏估计

根据上面公式可以得到：
* 多普勒频移$f_d=\frac{vf_c}{C}=600Hz$，相对多普勒频偏$\varepsilon=600/30K=0.02$
* $M=\frac{f_i}{f_c}=10^5$
* 相对载波频偏 $M\rho=0.01$
* 符号2时偏：$L_m\rho-\delta=(4096*2+352+288*2)\rho-2.5=9120*10^{-7}-2.5$
* 符号9时偏：$L_m\rho-\delta=(4096*9+352+288*9)\rho-2.5=39808*10^{-7}-2.5$
* FFT size $N=1/(f_cT_c)=4096$


对$x(n)$做DFT，得到：
$$
\begin{align}
X_m(K)&=\displaystyle\sum\limits_{n=0}^{N-1}\frac{1}{N}h_kX_ke^{j2\pi(k+M\rho+\varepsilon)(n(1+\rho)+L_m\rho-\delta)/N}e^{-2\pi nk/N} \nonumber \\
&\approx \frac{1}{N}h_kX_ke^{j2\pi[k(L_m\rho-\delta)+(M\rho+\varepsilon)(L_m\rho-\delta)]/N}\displaystyle\sum\limits_{n=0}^{N-1}e^{j2\pi(k\rho+M\rho+\varepsilon)n/N} \nonumber \\
&= \frac{1}{N}h_kX_ke^{j2\pi[k(L_m\rho-\delta)+(M\rho+\varepsilon)(L_m\rho-\delta)]/N}e^{j\pi(N-1)(k\rho+M\rho+\varepsilon)/N} \frac{sin(\pi(k\rho+M\rho+\varepsilon))}{sin(\pi(k\rho+M\rho+\varepsilon)/N)} \nonumber \\
&\approx \frac{1}{N}h_kX_ke^{j\pi [k(2(L_m\rho-\delta)+\rho)+(M\rho+\varepsilon)(2(L_m\rho-\delta)+1))]/N}\frac{sin(\pi(k\rho+M\rho+\varepsilon))}{sin(\pi(k\rho+M\rho+\varepsilon)/N)}
\end{align}
$$ 

其中：
* $L_m\rho-\delta$为符号$m$的时偏，
* $j\pi [k(2(L_m\rho-\delta)+\rho)+(M\rho+\varepsilon)(2(L_m\rho-\delta)+1))]=j\pi [k(2(L_m\rho-\delta)+\rho)+(M\rho+\varepsilon)(2(L_m\rho-\delta)+1)+\varphi_m]$为符号$m$子载波$k$相位，其中$\varphi_m=(M\rho+\varepsilon)(2(L_m\rho-\delta)+1))$

可以看出，
* 在一个符号内部，$\varphi_m$值不变，每个子载波相位$j\pi [k(2(L_m\rho-\delta)+\rho)]$变化跟$k$有关，有这个特性可以估计每个DMRS符号的时偏$2(L_m\rho-\delta)+\rho)$值。如果有两个DMRS符号，可以估计晶体振荡器相对频偏$\rho$值

## SINR 分析
假设发送的子载波$k$信号功率为$|X_k|^2=1$，如果不考虑路损$|h_k|^2=1$,，接收信号总功率也是$1$

接收信号子载波$k$功率为：
$$
\begin{align}
|X_m(K)|^2 &=\frac{1}{N^2}|X_k|^2(\frac{sin(\pi(k\rho+M\rho+\varepsilon))}{sin(\pi(k\rho+M\rho+\varepsilon)/N)})^2  \nonumber \\
& \approx \frac{1}{N^2}(\frac{sin(\pi(M\rho+\varepsilon))}{sin(\pi(M\rho+\varepsilon)/N)})^2 \: \:for \:M>> k\nonumber \\
& \approx 1-\frac{1}{3}(\pi(M\rho+\varepsilon))^2
\end{align}
$$

where：

泰勒展开：$sin(x) \approx x - \frac{1}{3!}(x)^3 =>sin^2(x) \approx x^2 - \frac{1}{3}(x)^4$

and:
$$
\begin{align}
(\frac{sin(\pi(M\rho+\varepsilon))}{sin(\pi(M\rho+\varepsilon)/N)})^2 \approx\frac{(\pi(M\rho+\varepsilon))^2-(\pi(M\rho+\varepsilon))^4/3}{((\pi(M\rho+\varepsilon)/N)^2-(\pi(M\rho+\varepsilon)/N)^4/3)} \approx N^2(1-\frac{1}{3}(\pi(M\rho+\varepsilon))^2)
\end{align}
$$

子载波$k$对其他载波的干扰为：$1-|X_m(K)|^2=\frac{1}{3}(\pi(M\rho+\varepsilon))^2$

这是一个子载波对其他载波的干扰，如果发送$N$个子载波，那么总的干扰为$N(\frac{1}{3}(\pi(M\rho+\varepsilon))^2)$,平均每个子载波收到的其他载波干扰为$\frac{1}{3}(\pi(M\rho+\varepsilon))^2$.

频偏导致的SNR为：$SNR = \frac {1-\frac{1}{3}(\pi(M\rho+\varepsilon))^2}{\frac{1}{3}(\pi(M\rho+\varepsilon))^2}=3(\pi(M\rho+\varepsilon))^{-2}$

SNR dB值： $SNR_dB \approx -5.17-20log10(M\rho+\varepsilon)$

## OFDM系统如何仿真载波频偏和多普勒频偏下的信道模型
前面假设一个子载波$X_k$,其他$X(k)=0$, 则OFDM符号的时域离散接收信号为：
$$
\begin{align}
x(n)&=\displaystyle\sum\limits_{k=0}^{N-1}\frac{1}{N}h_kX_ke^{j2\pi(k+\frac{f_i}{f_c}\rho+\frac{f_d}{f_c})(n(1+\rho)+L_m\rho-\delta)/N} \nonumber \\
&=\displaystyle\sum\limits_{k=0}^{N-1}\frac{1}{N}h_kX_ke^{j2\pi(k+M\rho+\varepsilon)(n(1+\rho)+L_m\rho-\delta)/N}  \nonumber \\
&=e^{j2\pi (M\rho+\varepsilon)(L_m\rho-\delta)/N}e^{j2\pi (M\rho+\varepsilon)n(1+\rho)/N}\displaystyle\sum\limits_{k=0}^{N-1}\frac{1}{N}h_kX_ke^{j2\pi k(n(1+\rho)+L_m\rho-\delta)/N}  \nonumber \\
& \approx e^{j2\pi (M\rho+\varepsilon)(L_m\rho-\delta)/N}e^{j2\pi (M\rho+\varepsilon)n/N}\displaystyle\sum\limits_{k=0}^{N-1}\frac{1}{N}h_kX_ke^{j2\pi k(n(1+\rho)+L_m\rho-\delta)/N} 
\end{align}
$$ 
上面公式第一项为OFDM时域信号symbol的固定相位偏差，注意这个相位与$L_m$有关，说明每个符号的固定相位偏差不同。

第二项$e^{j2\pi (M\rho+\varepsilon)n/N}$为频偏导致的时域每个采样点相位变化

第三项$\displaystyle\sum\limits_{k=0}^{N-1}\frac{1}{N}h_kX_ke^{j2\pi k(n(1+\rho)+L_m\rho-\delta)/N}=\displaystyle\sum\limits_{k=0}^{N-1}\frac{1}{N}h_kX_ke^{j2\pi k(n\rho+L_m\rho-\delta)/N}e^{j2\pi kn/N}$，也就是发送的频域信号做IDFT前，每个子载波数据做$2\pi k(n\rho+L_m\rho-\delta)/N$相位调整

# 时偏估计以及晶体振荡器相对频偏$\rho$估计
接收DMRS符号首先做LS估计，也就是与DMRS符号的共轭相乘，得到的结果为：
$$
\begin{align}
H_m(k)&=\frac{1}{N}h_ke^{j\pi [k(2(L_m\rho-\delta)+\rho)+(M\rho+\varepsilon)(2(L_m\rho-\delta)+1))]/N}\frac{sin(\pi(k\rho+M\rho+\varepsilon))}{sin(\pi(k\rho+M\rho+\varepsilon)/N)} \nonumber \\
&\approx \frac{1}{N}h_ke^{j2\pi [k(L_m\rho-\delta)+(M\rho+\varepsilon)(2(L_m\rho-\delta)+1))]/N}\frac{sin(\pi(k\rho+M\rho+\varepsilon))}{sin(\pi(k\rho+M\rho+\varepsilon)/N)}
\end{align}
$$
其中假设$L_m\rho-\delta >> \rho$

时偏估计算法分为时域估计和频域估计两种。其中时域估计是通过对时域接收信号滑动相关实现，估计的最小颗粒度为一个采样时钟宽度，无法估计小于采样时钟精度。频域估计可以估计的更精细。下面只介绍频域估计算法。

每个DMRS 符号LS估计结果做下面频域时偏估计：
$$
\hat{t_m}=L_m\rho-\delta=\frac{N}{2\pi}arg({\displaystyle\sum\limits_{k=1}^{N-1}H_m[k]H_m^*[k-1]})
$$

晶体振荡器相对频偏$\rho$估计
$$
\hat{\rho}=\frac{\hat{t_{m2}}-\hat{t_{m1}}}{L_{m2}-L_{m1}}
$$

$$
\hat{\delta}=\frac{L_{m1}\hat{t_{m2}}-L_{m2}\hat{t_{m1}}}{L_{m2}-L_{m1}}
$$
## 时偏补偿
对每一个OFDM频域符号，做
$$
\hat{Y[k]} = Y[k]e^{-j2\pi k\hat{\delta}/N}
$$

# 定时偏差接收机的数学模型，时偏估计和补偿

## 数学模型
时域接收信号表示为： $x(n)=\frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1} X[k]e^{j2\pi k(n+\delta)/N}$

其中$\delta$为归一化时偏

对时域信号做FFT，得到：
$$
\begin{align}
Y(m) &= \displaystyle\sum\limits_{n=0}^{N-1} \frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1} X[k]e^{j2\pi k(n+\delta)/N} e^{-j2\pi mn/N} \nonumber \\
&=\frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1} X[k]e^{j2\pi k\delta/N} \displaystyle\sum\limits_{n=0}^{N-1}e^{-j2\pi (k-m)n/N} \nonumber \\
&=X[m]e^{j2\pi m\delta/N}
\end{align}
$$
 
其中
$$
\begin{align}
& \displaystyle\sum\limits_{n=0}^{N-1}e^{-j2\pi (k-m)n/N} \nonumber \\
&= \frac{1-e^{j2\pi (k-m)}}{1-e^{j2\pi (k-m)/N}} \nonumber \\
&= \frac{e^{j\pi (k-m)}}{e^{j\pi (k-m)/N}}  \frac{e^{-j\pi (k-m)}-e^{j\pi (k-m)}}{e^{-j\pi (k-m)/N}-e^{j\pi (k-m)/N}} \nonumber \\
&= e^{j\pi (k-m)(N-1)/N} \frac{sin(\pi (k-m))}{sin(\pi (k-m)/N)} \nonumber \\
&= \begin{cases}N & k=m \\0 & k \neq m\end{cases}
\end{align}
$$
注：‘MIMO-OFDM无线通信技术及MATLAB实现’书中公式(2)有点错误，不过不影响结果。

式（1）表明，定时偏差会导致DFT后的频域信号相位旋转。

# 时偏估计
基站因为同时接收多个手机信号，只会做频域时偏估计，不会做时域时偏估计。
上行PUSCH，PUCCH，SRS信号可用于时偏估计

频域时偏估计：
$$
\hat{\delta}=\frac{N}{2\pi}arg({\displaystyle\sum\limits_{k=1}^{N-1}Y[k]Y^*[k-1]})
$$

## 时偏补偿
$$
\hat{Y[k]} = Y[k]e^{-j2\pi k\hat{\delta}/N}
$$


# 接收机频率偏差数学模型，SINR分析
时域接收信号： $y(n)=\frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1}H(k)X(k)e^{j2\pi (k+\varepsilon)n/N} + w(n)$

其中$\varepsilon=f_e/f_c$是归一化频偏。$f_c$是子载波带宽，$f_e$是绝对频率偏差.

$w(n)$是外部噪声

$y(n)$做DFT，得到：
$$
\begin{align}
Y[m] &=\displaystyle\sum\limits_{n=0}^{N-1}y(n)e^{-j2\pi nm/N} \nonumber \\
&=\displaystyle\sum\limits_{n=0}^{N-1} \frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1}H(k)X(k)e^{j2\pi (k+\varepsilon)n/N} e^{-j2\pi nm/N}+ W(m) \nonumber \\
&=\frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1}H(k)X(k)\displaystyle\sum\limits_{n=0}^{N-1}e^{j2\pi (k-m+\varepsilon)n/N} + W(m) \nonumber \\
&= \frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1}H(k)X(k) \frac{1-e^{j2\pi N(k-m+\varepsilon)/N}}{1-e^{j2\pi (k-m+\varepsilon)/N}} + W(m)\nonumber \\
&=\frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1}H(k)X(k)\frac{sin(\pi (k-m+\varepsilon))}{sin(\pi (k-m+\varepsilon)/N)}e^{j\pi (N-1)(k-m+\varepsilon)/N} + W(m)\nonumber \\
&=H(m)X(m)\frac{sin(\pi\varepsilon)}{Nsin(\pi\varepsilon /N)}e^{j\pi (N-1)\varepsilon/N}  \\
&+\displaystyle\sum\limits_{k=0 \\ k!=m}^{N-1}H(k)X(k) \frac{sin(\pi (k-m+\varepsilon))}{sin(\pi (k-m+\varepsilon)/N)}e^{j\pi (N-1)(k-m+\varepsilon)/N} + W(m) \\
\end{align}
$$
式$(3)$为幅度衰减和相位偏移后的信号，式$(4)为频偏导致的子载波干扰

assume $E(|H(k)X(k)|^2)=C$, and $E(X(k)X(n)^*)=0 \: if \: k\neq n$

接收信号功率：
$$
\begin{align}
S_m&=E(|H(m)X(m)\frac{sin(\pi\varepsilon)}{Nsin(\pi\varepsilon /N)}e^{j\pi (N-1)\varepsilon/N}|^2) \nonumber \\
&=E(|H(m)X(m)|^2)(\frac{sin(\pi\varepsilon)}{Nsin(\pi\varepsilon /N)})^2
\end{align}
$$
泰勒展开：$sin(\pi\varepsilon) \approx \pi\varepsilon - \frac{1}{3!}(\pi\varepsilon)^3$
we get:
$$
\begin{align}
(\frac{sin(\pi\varepsilon)}{Nsin(\pi\varepsilon /N)})^2 \approx\frac{(\pi\varepsilon)^2-(\pi\varepsilon)^4/3}{N^2((\pi\varepsilon/N)^2-(\pi\varepsilon/N)^4/3)} \approx 1-\frac{1}{3}(\pi\varepsilon)^2
\end{align}
$$

from $(5),(6)$ we get: 
$$
\begin{align}
S_m \approx C(1-\frac{1}{3}(\pi\varepsilon)^2) 
\end{align}
$$


$Y(m)$功率：
$$
\begin{align}
|Y(m)|^2&=E(|\frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1}H(k)X(k)\frac{sin(\pi (k-m+\varepsilon))}{sin(\pi (k-m+\varepsilon)/N)}e^{j\pi (N-1)(k-m+\varepsilon)/N}|^2) + |W(m)|^2 \nonumber \\
&=\frac{1}{N^2}E(\displaystyle\sum\limits_{k=0}^{N-1}H(k)X(k)\frac{sin(\pi (k-m+\varepsilon))}{sin(\pi (k-m+\varepsilon)/N)}e^{j\pi (N-1)(k-m+\varepsilon)/N} \displaystyle\sum\limits_{n=0}^{N-1}H(n)^*X(n)^*\frac{sin(\pi (n-m+\varepsilon))}{sin(\pi (n-m+\varepsilon)/N)}e^{-j\pi (N-1)(n-m+\varepsilon)/N})+ |W(m)|^2 \nonumber \\
&=\frac{1}{N^2}\displaystyle\sum\limits_{k=0}^{N-1}E(|H(k)X(k)|^2)(\frac{sin(\pi (k-m+\varepsilon))}{sin(\pi (k-m+\varepsilon)/N)})^2 + |W(m)|^2 \nonumber \\
&=\frac{C}{N^2}\displaystyle\sum\limits_{k=0}^{N-1}(\frac{sin(\pi \varepsilon)}{sin(\pi (k-m+\varepsilon)/N)})^2 + |W(m)|^2 \\

\end{align}
$$

根据PARSEVAL定理，$\displaystyle\sum\limits_{n=0}^{N-1}|x(n)|^2=\frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1}|X(k)|^2$

where: $X(k)$ is the DFT of $x(n)$

for $x(n)=e^{j2\pi (m-\varepsilon)n/N}$

$X(k)=\displaystyle\sum\limits_{n=0}^{N-1}x(n)e^{-j2\pi kn/N}=
\displaystyle\sum\limits_{n=0}^{N-1}e^{j2\pi (m-k-\varepsilon)n/N}=
\frac{sin(\pi \varepsilon)}{sin(\pi (k-m+\varepsilon)/N)}e^{j\pi (N-1)(m-k-\varepsilon)/N}$

from $\displaystyle\sum\limits_{n=0}^{N-1}|x(n)|^2=\displaystyle\sum\limits_{n=0}^{N-1}|e^{j2\pi (m-\varepsilon)n/N}|^2=N$

get $\displaystyle\sum\limits_{k=0}^{N-1}|X(k)|^2=\displaystyle\sum\limits_{k=0}^{N-1}|\frac{sin(\pi \varepsilon)}{sin(\pi (k-m+\varepsilon)/N)}|^2=N^2$

公式$(7)$:
$|Y(m)|^2=C+ |W(m)|^2$

其他载波对载波$m$的干扰：$ICI=|Y(m)|^2-S_m=C+ |W(m)|^2-C(1-\frac{1}{3}(\pi\varepsilon)^2)=\frac{1}{3}(\pi\varepsilon)^2+ |W(m)|^2$

忽略噪声$W(m)^2$，频偏干扰导致的信噪比
$SNR= \frac{S_m}{ICI}=\frac{C(1-\frac{1}{3}(\pi\varepsilon)^2)}{\frac{1}{3}(\pi\varepsilon)^2} \approx 3(\pi\varepsilon)^{-2}$

$SNR_{dB} \approx -5.17-20log10(\varepsilon)$

## 多普勒频偏推导
无线信号都是光速传播，对接收机来说，信号频率可以认为是一秒钟内接收的整周期信号个数。

假设发送机和接收机距离为$\lambda=\frac{C}{f}$

如果发送机和接收机都不运动，发送机发出信号，接收机收到时间为$T=\lambda/C$

如果发送机静止，接收机径向运动速率为$v$,发送机发出信号，接收机收到时间为$T=\frac{\lambda+vT}{C} =>T=\frac{\lambda}{C-V}$

从接收机角度，收到信号频率为$fs=\frac{1}{T}=\frac{C-v}{\lambda}=f-\frac{v}{\lambda}=f-\frac{vf}{C}$

$-\frac{vf}{C}$就是多普勒频率

如果接收机远离发送机运动，多普勒频率为负数。反之为正。

## 载波频偏（CFO）数学模型
载波频偏指的是发送机和接收机之间的本振频率偏差，与多普勒频偏不同。多普勒频偏是通过发送机和接收机间相对运动产生，载波频偏是由于发送机和接收机间晶体振荡题频率偏差导致。

晶体振荡器频偏带来几个影响。

1. 载波频率偏差，比如对3GHz载波，相对频偏0.1ppm的晶体振荡器频偏导致$3^9*0.1*10^-6=300Hz$频偏
2. 采样时钟偏差，比如期望采样时钟32.76Mhz，实际得到$32.76MHz*(1+\rho)$,$\rho$是相对频偏
3. 定时偏差，比如一秒钟定时偏差为$\rho$，1ms定时偏差为$\rho10^{-3}$

考虑一个OFDM符号，载波k的时域连续接收信号为：
$$
\begin{align}
x(t)&=d_ke^{j2\pi(k+\varepsilon)f_s(t-t_0)}
\end{align}
$$ 
其中$\varepsilon$为相对载波频偏。比如子载波带宽30kHz,频偏300Hz，相对载波频偏$\varepsilon=300/30K=0.01$

$\rho$为载波频率相对偏差,采样时钟偏差为$T_c(1-\rho)$

$T_0$为定时偏差, $\delta= \frac{T_0}{T_c}$为相对定时偏差

$N=1/(f_sT_c)$

对于100MHz，30KHz SCS 5G载波，$f_s=30KHz$, $T_c=1/122.88MHz$,$N=4096$

对连续信号采样，得到的离散信号为：
$$
\begin{align}
x(n)&=d_ke^{j2\pi(k+\varepsilon)f_s(nT_c(1-\rho)-T_c\delta)}=d_ke^{j2\pi(k+\varepsilon)(n(1-\rho)-\delta)/N}
\end{align}
$$ 

对$x(n)$做DFT，得到：
$$
\begin{align}
x_m(K)&=\displaystyle\sum\limits_{n=0}^{N-1}d_ke^{j2\pi(k+\varepsilon)[n(1-\rho)-\delta]/N}e^{-2\pi nk/N} \nonumber \\
&=\displaystyle\sum\limits_{n=0}^{N-1}d_ke^{j2\pi[(-k\rho +\varepsilon-\rho\varepsilon)n-k\delta -\varepsilon\delta]/N} \nonumber \\
&=d_k e^{j2\pi(-k\delta -\varepsilon\delta)/N}\displaystyle\sum\limits_{n=0}^{N-1}d_ke^{j2\pi[(-k\rho +\varepsilon-\rho\varepsilon)n/N} \nonumber \\
&=d_k e^{j2\pi(-k\delta -\varepsilon\delta)/N}e^{j\pi(N-1)(-k\rho +\varepsilon-\rho\varepsilon)/N}\frac{sin(\pi(-k\rho +\varepsilon-\rho\varepsilon))}{sin(\pi(-k\rho +\varepsilon-\rho\varepsilon)/N)} \nonumber \\
&\approx d_ke^{j\pi(-2k\delta+(N-1)(-k\rho +\varepsilon))/N}\frac{sin(\pi(-k\rho +\varepsilon-\rho\varepsilon))}{sin(\pi(-k\rho +\varepsilon-\rho\varepsilon)/N)} \nonumber \\
&= d_ke^{j\pi(-2kL_m\rho+(N-1)(-k\rho +\varepsilon))/N}\frac{sin(\pi(-k\rho +\varepsilon-\rho\varepsilon))}{sin(\pi(-k\rho +\varepsilon-\rho\varepsilon)/N)}
\end{align}
$$ 

其中$L_m$为符号$m$相对于slot的相对时间偏差。

比如对于100MHz，30KHz SCS载波，symbol 0 长度为352CP+4096 sample, symbol 1 长度为288CP+4096sample, symbol2 CP = 288,$m=2$符号距离slot起始位置有$L_m=(352+4096+288+4096+200)\rho=9120\rho$


