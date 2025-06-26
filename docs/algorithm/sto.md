# 前言
无线系统发送和接收时间不可避免存在定时偏差，频率不一致，以及运动场景下多普勒频移。

本文内容包括：
1. 定时偏差接收机的数学模型，时偏估计和补偿
2. 接收机频率偏差数学模型，SINR分析
3. 频率偏差估计和补偿
4. 如何区分频偏是多普勒频移导致还是接收机频率偏差导致

# 载波频偏和多普勒频偏下接收信号数学模型
载波频偏指的是发送机和接收机之间的本振频率偏差，与多普勒频偏不同。多普勒频偏是通过发送机和接收机间相对运动产生，载波频偏是由于发送机和接收机间晶体振荡题频率偏差导致。

晶体振荡器频偏带来几个影响。

1. 载波频率偏差，比如对3GHz载波，相对频偏0.1ppm的晶体振荡器频偏导致$3^9*0.1*10^-6=300Hz$频偏
2. 采样时钟偏差，比如期望采样时钟32.76Mhz，实际得到$32.76MHz*(1+\rho)$,$\rho$是相对频偏
3. 定时偏差，比如一秒钟定时偏差为$\rho$，1ms定时偏差为$\rho10^{-3}$

多普勒频偏：$\frac{vf_c}{C}$,其中 $v$为发送和接收机互相靠近的相对速度。

如果接收机远离发送机运动，多普勒频率为负数。反之为正。

## 数学模型
DFT公式为：$x(n)=\frac{1}{N}\displaystyle\sum\limits_{k=0}^{N-1} X[k]e^{j2\pi kn/N}$

只考虑一个子载波$k$,其他$X(k)=0$, 则OFDM符号的时域离散接收信号为：
$$
\begin{align}
x(n)&=\frac{1}{N}d_ke^{j2\pi(k+\frac{f_i}{f_c}\rho+\frac{f_d}{f_c})(n(1+\rho)+L_m\rho-\delta)/N} \nonumber \\
&=\frac{1}{N}d_ke^{j2\pi(k+M\rho+\varepsilon)(n(1+\rho)+L_m\rho-\delta)/N}
\end{align}
$$ 

其中：
* $\frac{f_i}{f_c}\rho=M\rho$为相对于子载波频率的载波频偏, $M$为载波频率和子载波带宽比值
* $\frac{f_d}{f_c}$为相对于子载波频率的多普勒频偏
* $(1+\rho)$为相对采样时钟
* $L_m\rho$为晶体振荡器相对频偏导致的符号$m$的采样定时偏差
* $\delta$为发送机和接收机间符号定时偏差
* 晶体振荡器相对频偏$\rho$
* 载波频率$f_i$
* 子载波带宽$f_c$
* 采样时钟带宽$T_C$
* 多普勒频移$f_d$

假设一个5G载波频率3GHz，带宽100MHz，子载波带宽30KHz，采样时钟带宽$T_C=1/122.88MHz$,晶体振荡器相对频偏$\rho=0.1ppm$，移动速度$v=216km/hour=60m/s$，$\delta=2.5$

symbol 0 长度为352CP+4096 sample, symbol 1 长度为288CP+4096sample, symbol2 CP = 288,$m=2$符号距离slot起始位置有$L_m=(352+4096+288+4096+200)\rho=9120\rho$

根据上面公式可以得到：
1. 多普勒频移$f_d=\frac{vf_c}{C}=600Hz$
2. $\frac{f_i}{f_c}\rho=0.01$
3. $\frac{f_d}{f_c}=0.02$
3. 符号2 $L_2\rho=9120*10^{-7}$
4. FFT size $N=1/(f_csT_c)=4096$


对$x(n)$做DFT，得到：
$$
\begin{align}
X_m(K)&=\displaystyle\sum\limits_{n=0}^{N-1}\frac{1}{N}d_ke^{j2\pi(k+M\rho+\varepsilon)(n(1+\rho)+L_m\rho-\delta)/N}e^{-2\pi nk/N} \nonumber \\
&\approx \frac{1}{N}d_ke^{j2\pi[k(L_m\rho-\delta)+(M\rho+\varepsilon)(L_m\rho-\delta)]/N}\displaystyle\sum\limits_{n=0}^{N-1}e^{j2\pi(k\rho+M\rho+\varepsilon)n/N} \nonumber \\
&= \frac{1}{N}d_ke^{j2\pi[k(L_m\rho-\delta)+(M\rho+\varepsilon)(L_m\rho-\delta)]/N}e^{j\pi(N-1)(k\rho+M\rho+\varepsilon)/N} \frac{sin(\pi(k\rho+M\rho+\varepsilon))}{sin(\pi(k\rho+M\rho+\varepsilon)/N)} \nonumber \\
&\approx \frac{1}{N}d_ke^{j\pi [k(2((L_m\rho-\delta))+\rho)+(M\rho+\varepsilon)(2(L_m\rho-\delta)+1))]/N}\frac{sin(\pi(k\rho+M\rho+\varepsilon))}{sin(\pi(k\rho+M\rho+\varepsilon)/N)}
\end{align}
$$ 

## SINR 分析
假设发送的子载波$k$信号功率为$|d_k|^2=1$，如果不考虑路损，接收信号总功率也是$1$

接收信号子载波$k$功率为：
$$
\begin{align}
|X_m(K)|^2 &=\frac{1}{N^2}|d_k|^2(\frac{sin(\pi(k\rho+M\rho+\varepsilon))}{sin(\pi(k\rho+M\rho+\varepsilon)/N)})^2  \nonumber \\
& \approx \frac{1}{N^2}(\frac{sin(\pi(M\rho+\varepsilon))}{sin(\pi(M\rho+\varepsilon)/N)})^2 \nonumber \\
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

## 时偏估计
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

