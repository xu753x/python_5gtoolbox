
``` mermaid
graph LR
A[DL-SCH] -->B(PDSCH and DMRS) --> C[Precoding] --> D[low-phy]-->D2[channel model]-->D3[low phy receiver]

-->D4[channel estimation]-->D5[PSCH decoding]-->D6[DL-SCH decoding]

```