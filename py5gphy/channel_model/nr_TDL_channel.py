# -*- coding:utf-8 -*-
import numpy as np

def get_TDL_model_config(model,DSdesired,fm_inHz):
    """ return tapsm normalized delay, power in db, fading distribution
    
    refer to TR 38.901 Tapped Delay Line (TDL) channel from table 7.7.2-1 to table 7.7.2-5
    following aspects of TR 38.901 are implemented:
   * Section 7.7.2 Tapped Delay Line (TDL) models
   * Section 7.7.3 Scaling of delays 
   input:
   model: TDL model in ['TDL-A','TDL-B','TDL-C','TDL-D','TDL-E']
   DSdesired: 7.7.3 Scaling of delays in ns
   DS_desired_in_ns_Table_7_7_3_1 = {
        "Very short":10, "Short":30, "Nominal":100, "Long":300, "Very long":1000 
        }
   fm_inHz: maximum doppler frequency
   output:
   multi-path list,
   each multipath include:
   delay in ns, power in dB, Rayleigh or Rician, K in dB for Rician， fDo(doppler freq in hz) for Rician"
    """
    if model == 'TDL-A':
        tap_config = [
            [0.0000,	-13.4   ], 
            [0.3819,	0       ],
            [0.4025,	-2.2    ],
            [0.5868,	-4      ],
            [0.4610,	-6      ],
            [0.5375,	-8.2    ],
            [0.6708,	-9.9    ],
            [0.5750,	-10.5   ],
            [0.7618,	-7.5    ],
            [1.5375,	-15.9   ],
            [1.8978,	-6.6    ],
            [2.2242,	-16.7   ],
            [2.1718,	-12.4   ],
            [2.4942,	-15.2   ],
            [2.5119,	-10.8   ],
            [3.0582,	-11.3   ],
            [4.0810,	-12.7   ],
            [4.4579,	-16.2   ],
            [4.5695,	-18.3   ],
            [4.7966,	-18.9   ],
            [5.0066,	-16.6   ],
            [5.3043,	-19.9   ],
            [9.6586,	-29.7   ],
        ]
        for x in tap_config:
            x.extend(["Rayleigh",0,0]) 
        
    elif model == 'TDL-B':
        tap_config = [
            [0.0000,  0       ],
            [0.1072,  -2.2    ],
            [0.2155,  -4      ],
            [0.2095,  -3.2    ],
            [0.2870,  -9.8    ],
            [0.2986,  -1.2    ],
            [0.3752,  -3.4    ],
            [0.5055,  -5.2    ],
            [0.3681,  -7.6    ],
            [0.3697,  -3      ],
            [0.5700,  -8.9    ],
            [0.5283,  -9      ],
            [1.1021,  -4.8    ],
            [1.2756,  -5.7    ],
            [1.5474,  -7.5    ],
            [1.7842,  -1.9    ],
            [2.0169,  -7.6    ],
            [2.8294,  -12.2   ],
            [3.0219,  -9.8    ],
            [3.6187,  -11.4   ],
            [4.1067,  -14.9   ],
            [4.2790,  -9.2    ],
            [4.7834,  -11.3   ],
        ]
        for x in tap_config:
            x.extend(["Rayleigh",0,0]) 
    elif model == 'TDL-C':
        tap_config = [
            [0	   ,    -4.4   ],
            [0.2099,	-1.2   ],
            [0.2219,	-3.5   ],
            [0.2329,	-5.2   ],
            [0.2176,	-2.5   ],
            [0.6366,	0      ],
            [0.6448,	-2.2   ],
            [0.6560,	-3.9   ],
            [0.6584,	-7.4   ],
            [0.7935,	-7.1   ],
            [0.8213,	-10.7  ],
            [0.9336,	-11.1  ],
            [1.2285,	-5.1   ],
            [1.3083,	-6.8   ],
            [2.1704,	-8.7   ],
            [2.7105,	-13.2  ],
            [4.2589,	-13.9  ],
            [4.6003,	-13.9  ],
            [5.4902,	-15.8  ],
            [5.6077,	-17.1  ],
            [6.3065,	-16    ],
            [6.6374,	-15.7  ],
            [7.0427,	-21.6  ],
            [8.6523,	-22.8  ],
        ]
        for x in tap_config:
            x.extend(["Rayleigh",0,0]) 
    elif model == 'TDL-D':
        tap_config = [
            [0	    ,  -13.5 ],
            [0.035	,  -18.8 ],
            [0.612	,  -21   ],
            [1.363	,  -22.8 ],
            [1.405	,  -17.9 ],
            [1.804	,  -20.1 ],
            [2.596	,  -21.9 ],
            [1.775	,  -22.9 ],
            [4.042	,  -27.8 ],
            [7.937	,  -23.6 ],
            [9.424	,  -24.8 ],
            [12.525 ,  -27.7 ],
        ]
        #tap0 is Rician, other taps are Rayleigh
        #refer to 7.7.2 Tapped Delay Line (TDL) models, fDo for Rician = 0.7*fm(maxumim doppler freq)
        tap_config[0].extend(["Rician",13.3,fm_inHz*0.7])
        for x in tap_config[1:]:
            x.extend(["Rayleigh",0,0]) 
                
    elif model == 'TDL-E':
        tap_config = [
            [0	    ,  -22.03 ],
            [0.5133 ,  -15.8  ],
            [0.5440	,  -18.1  ],
            [0.5630	,  -19.8  ],
            [0.5440	,  -22.9  ],
            [0.7112	,  -22.4  ],
            [1.9092	,  -18.6  ],
            [1.9293	,  -20.8  ],
            [1.9589	,  -22.6  ],
            [2.6426	,  -22.3  ],
            [3.7136	,  -25.6  ],
            [5.4524	,  -20.2  ],
            [12.0034,  -29.8  ],
            [20.6519,  -29.2  ],
        ]
        #tap0 is Rician, other taps are Rayleigh
        #refer to 7.7.2 Tapped Delay Line (TDL) models, fDo for Rician = 0.7*fm(maxumim doppler freq)
        tap_config[0].extend(["Rician",22,fm_inHz*0.7])
        for x in tap_config[1:]:
            x.extend(["Rayleigh",0,0]) 

    #38.901 7.7.3 Scaling of delays
    for tap in tap_config:
        tap[0] *= DSdesired
    return tap_config


if __name__ == "__main__":

    pass