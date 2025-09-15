# introduction
ML MIMO channel equalization algorithm complexity is O($N^2$) for rank 2 case, where N is number of constellation points.
This method is to reduce the complexity from $N^2$ to $2N$ 

I found this method for LTE DL processing in 2009 when I worked for Huawei in Beijing China.

# ML detection system model

rank 2 MIMO Rx system model: $Y=Hs+n$

where:
* $Y$ is $NrX1$ vector
* $H$ is $NrX2$ matrix
* $s=[s_0,s_1]^T=[x_0+jy_0,x_1+jy_1]^T$

ML detection:
$$
\hat s=argmin((Y-Hs)^H(Y-Hs))
$$
Let 
$$
\begin{align}
L = (Y-Hs)^H(Y-Hs)=Y^HY-2RE(Y^HHs)+s^H(H^HH)s
\end{align}
$$

omit $Y^HY$,and with:
* $Y^HH=[a_{0i}+ja_{0q},a_{1i}+ja_{1q}]$ is 1 by 2 vector

* $H^HH=\begin{bmatrix}a_2 & a_{4i}+ja_{4q} \\a_{4i}-ja_{4q} & a_3 \end{bmatrix}$

get:
$$
\begin{align}
L&=-2(a_{0i}x_0-a_{0q}y_0+a_{1i}x_1-a_{1q}y_1) \nonumber \\
& \quad \: +[s_0^*a2+s_1^*(a_{4i}-ja_{4q}),s_0^*(a_{4i}+ja_{4q})+s_1^*a3]\begin{bmatrix}s_0  \\s_1 \end{bmatrix} \nonumber \\
&=-2(a_{0i}x_0-a_{0q}y_0+a_{1i}x_1-a_{1q}y_1) \nonumber \\ 
&\quad \: +a_2x_0^2+a_2y_0^2+a_3x_1^2+a_3y_1^2+2[a_{4i}x_0x_1+a_{4i}y_0y_1+a_{4q}x_1y_0-a_{4q}x_0y_1] \nonumber \\ \nonumber \\
&=a_2x_0^2+a_2y_0^2-2a_{0i}x_0+2a_{0q}y_0  \tag{2.1} \\
&\quad \:+a_3x_1^2+2(-a_{1i}+a_{4i}x_0+a_{4q}y_0)x_1 \tag{2.2} \\
&\quad \:+a_3y_1^2+2(a_{1q}+a_{4i}y_0-a_{4q}x_0)y_1 \tag{2.3} \\ \nonumber \\
&=a_3x_1^2+a_3y_1^2-2a_{1i}x_1+2a_{1q}y_1 \tag{3.1} \\ 
&\quad \:+a_2x_0^2+2(-a_{0i}+a_{4i}x_1-a_{4q}y_1)x_0 \tag{3.2} \\
&\quad \:+a_2y_0^2+2(a_{0q}+a_{4i}y_1+a_{4q}x_1)y_0 \tag{3.3} 

\end{align}
$$


# optimized ML detection algorithm
let's focus on equation (2.1),(2.2),(2.3) to show how to do optimized ML

$$
\begin{align}
L21&=a_2x_0^2+a_2y_0^2-2a_{0i}x_0+2a_{0q}y_0  \tag{2.1} \\
L22&=a_3x_1^2+2(-a_{1i}+a_{4i}x_0+a_{4q}y_0)x_1 \tag{2.2} \\
L23&=a_3y_1^2+2(a_{1q}+a_{4i}y_0-a_{4q}x_0)y_1 \tag{2.3} 

\end{align}
$$

for any $[x_0,y_0]$ pair:

$L22=L22_{min} $ when $\large \hat x_1=-\frac{-a_{1i}+a_{4i}x_0+a_{4q}y_0}{a_3}$

$L23=L23_{min} $ when $\large \hat y_1=-\frac{a_{1q}+a_{4i}y_0-a_{4q}x_0}{a_3}$

$x_1$ and $y_1$ are the real part and imag part of QAM points, we can separately search $x_1$ and $y_1$ that are cloest to $\hat x_1$ and $\hat y_1$ to get $L22_{min}$, $L23_{min}$

