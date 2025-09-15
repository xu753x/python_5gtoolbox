# 前言
本文介绍下面几个基本的MIMO信道均衡算法：
1. ZF and ZF-IRC
2. MMSE and MMSE-IRC
4. ML

其中MMSE-IRC是产品中最常用的算法。此外还有一些sphere, QRM等算法，算法性能近似ML，但是似乎很少在产品中实现。

## 一些矩阵知识
$\frac{\partial a^Hxb}{\partial x}=ab^H$

$\frac{\partial a^Hx^Hxb}{\partial x}=x(ab^H +  ba^H)$

# 信道模型
MIMO信道： $Y_{N_r,1}=H_{N_r,N_L}s_{N_L,1}+v_{N_r,1}$

where:
* $N_L$为发送信道number of layer
* $N_r$为Y为接收天线个数
* $Y_{N_r,1}$为接收列向量，长度为$N_r$
* $H_{N_r,N_L}$为 $N_r$ by $N_L$信道矩阵
* $s_{N_L,1}$为发送列向量，长度为$N_L$
* $v_{N_r,1}$为接收干扰和噪声，$E(vv^H)=\Sigma_v$

5G系统中，DMRS和数据部分共用相同的precoding matrix，信道估计得到的是无线信道和precoding matrix的组合，所以接收机不需要知道发送的precoding matrix，这一点与LTE不同。

# ZF(Zero Forcing) and ZF-IRC 信道均衡算法

 * ZF-IRC 信道均衡

$
E(s-\hat s)=E(s-W_{ZF}Y)=E(s-W_{ZF}Hs-W_{ZF}v)=E(s-W_{ZF}Hs)=0 \\
$
we get ZF equalizer: 

$W_{ZF}=(H^HH)^{-1}H^H$

and signal estimation:

$\hat s = WY=(H^HH)^{-1}H^HHs+(H^HH)^{-1}H^Hv=s+(H^HH)^{-1}H^Hv$

get:
$$
\begin{align}
E(\hat s \hat s^H)&=E(ss^H)+(H^HH)^{-1}H^H\Sigma_vH(H^HH)^{-1} \nonumber \\
&=I+(H^HH)^{-1}H^H\Sigma_vH(H^HH)^{-1}
\end{align}
$$ 

$k_{th}$ layer SNR:

$SNR_k= \frac{1}{((H^HH)^{-1}H^H\Sigma_vH(H^HH)^{-1})_{k,k}}$

it should be way to simplify this SNR formula....

* ZF 信道均衡

假设MIMO信道为纯噪声信道，并且每一层的噪声方差相同，则 $\Sigma_v=\sigma^2I$，ZF-IRC算法简化为ZF算法。

则 $E(\hat s \hat s^H)=I+\sigma^2(H^HH)^{-1}$

$k_{th}$ layer SNR:

$SNR_k= \frac{1}{\sigma^2(H^HH)^{-1}_{k,k}}$

# MMSE-IRC and MMSE信道均衡算法
## MMSE-IRC 公式推导
MMSE-IRC算法：

assume $\hat s = WY$

$\hat s = argmin(E(\vert s-\hat s \vert^2))=argmin(E((s-WY)^H(s-WY)))$

it need solve:

$\frac{\partial E((s-WY)^H(s-WY))}{\partial W}=0$

from
$$
\begin{align}
\frac{\partial (s-WY)^H(s-WY)}{\partial W}&=\frac{\partial(s-WY)^H(s-WY)}{\partial (s-WY)}\frac{\partial (s-WY)}{\partial W} \nonumber \\
&=(s-WY)Y^H
\end{align}
$$

get:
$$
\begin{align}
\frac{\partial E((s-WY)^H(s-WY))}{\partial W}=E((s-WY)Y^H)=E(sY^H-WYY^H)=0
\end{align}
$$

with: $E(ss^H)=I$, $E(sv^H)=0$

get:

$E(sY^H)=E(s(s^HH^H+v^H))=E(ss^H)H^H=H^H$

$E(WYY^H)=E(W(Hs+v)(s^HH^H+v^H)=W(HH^H+\Sigma_v)$

from:

$H^H=W(HH^H+\Sigma_v)$

get MMSE equalizer: $W=H^H(HH^H+\Sigma_v)^{-1}$ 

usually we use another format of MMSE equalizer:

$W=(H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}$

we can prove two equations are equal:

$$
\begin{align}
(H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}(HH^H+\Sigma_v) 
&=(H^H\Sigma_v^{-1}H+I)^{-1}(H^H\Sigma_v^{-1}HH^H+H^H) \nonumber \\
&=(H^H\Sigma_v^{-1}H+I)^{-1}(H^H\Sigma_v^{-1}H+I)H^H \nonumber \\
&=H^H
\end{align}
$$

## MMSE-IRC signal power, noise power and SNR
$\hat s = WY=(H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}(Hs+v)$

from:

$(H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}Hs=(H^H\Sigma_v^{-1}H+I)^{-1}(H^H\Sigma_v^{-1}H+I-I)s=(I-(H^H\Sigma_v^{-1}H+I)^{-1})s$

get:

$\hat s =(I-(H^H\Sigma_v^{-1}H+I)^{-1})s+(H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}v$

$k^{th}$ layer estimated signal:

$\hat s_k=(1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k})s_k+\sum_{j\neq k}(1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,j})s_j) +((H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}v)_k$

first item is signal power, second item is interference from other layers, third item is noise and external interference.

$k^{th}$ layer estimated signal power:

$Es_k=(1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k})s_k(1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k})s_k^*=(1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k})^2$

to calculate $k^{th}$ layer noise and interference power, first get;

$$
\begin{align}
&E(\hat s \hat s^H) \nonumber \\
&=(I-(H^H\Sigma_v^{-1}H+I)^{-1})s((I-(H^H\Sigma_v^{-1}H+I)^{-1})s)^H+(H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}v((H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}v)^H \nonumber \\
&=(I-(H^H\Sigma_v^{-1}H+I)^{-1})^2+(I-(H^H\Sigma_v^{-1}H+I)^{-1})(H^H\Sigma_v^{-1}H+I)^{-1} \nonumber \\
&=I-(H^H\Sigma_v^{-1}H+I)^{-1}
\end{align}
$$

with:
$$
\begin{align}
&(H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}v((H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}v)^H \nonumber \\
&=(H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}\Sigma_v\Sigma_v^{-1}H(H^H\Sigma_v^{-1}H+I)^{-1} \nonumber \\
&=(H^H\Sigma_v^{-1}H+I)^{-1}(H^H\Sigma_v^{-1}H+I-I)(H^H\Sigma_v^{-1}H+I)^{-1} \nonumber \\
&=(I-(H^H\Sigma_v^{-1}H+I)^{-1})(H^H\Sigma_v^{-1}H+I)^{-1}
\end{align}
$$

from above equation we get $k^{th}$ layer signal and noise power summation:

$E_k=E(\hat s \hat s^H)_{k,k}= 1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k}$

$k^{th}$ layer signal noise power :

$En_k=E_k-Es_k=1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k}-(1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k})^2$

$k^{th}$ layer $SNR$:

$SNR_k=\frac{Es_k}{En_k}=\frac{(1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k})^2}{1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k}-(1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k})^2}=\frac{1}{(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k}}-1$

## MMSE-IRC result compensation for LLR demodulation
LLR demodulation input requrest input signal power  = 1, while MMSE estimated signal power is not 1 and need compensaition by:

$LLR_k=\frac{\hat s_k}{sqrt(Es_k)}=\frac{\hat s_k}{1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k}}$

noise variance after compensation is:

$var_k=\frac{En_k}{(1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k})^2}=\frac{1}{1-(H^H\Sigma_v^{-1}H+I)^{-1}_{k,k}}-1$

## MMSE
if assuming $\Sigma_v=\sigma^2I$, MMSE-IRC can simplify to MMSE

$W=(H^H\Sigma_v^{-1}H+I)^{-1}H^H\Sigma_v^{-1}=(H^HH+\sigma^2I)H^H$

# ML 信道均衡算法
