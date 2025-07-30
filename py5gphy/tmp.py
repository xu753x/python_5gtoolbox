class MIMO_FadingChannel():
    """ MIMO fading channel
    """
    def __init__(self,num_taps, tap_config_list,samplerate_in_hz,R_spat=np.array([1]),Nt=1,Nr=1):
        """
        input:
            R_spat: spatial_correlation_matrix
            Nt: number of Tx antenna
            Nr: number of Rx antenna
        """
        self.num_taps = num_taps
        self.tap_config_list = tap_config_list
        self.samplerate_in_hz = samplerate_in_hz

        self.R_spat = R_spat
        self.Nt = Nt
        self.Nr = Nr
    
    def gen_mimo_tap_filters(self, num_of_sample):
        """generate num_of_sample of Nt X Nr MIMO matrix * """
        num_taps = self.num_taps 
        tap_config_list = self.tap_config_list 
        samplerate_in_hz = self.samplerate_in_hz 

        R_spat = self.R_spat
        L = np.linalg.cholesky(R_spat)
        Nt = self.Nt 
        Nr = self.Nr 
        
        #first generate SISO fading channel
        siso_FadingChannel = SISO_fading_channel.SISO_FadingChannel(num_taps, tap_config_list,samplerate_in_hz)

        #generate Nt*Nr tap filters 
        siso_FadingChannel_filters_list = []
        for _ in range(Nt*Nr):
            tap_filters_list,tap_delay_in_sample_list = siso_FadingChannel.gen_tap_filters(num_of_sample)
            siso_FadingChannel_filters_list.append(tap_filters_list)
        
        #generate MIMO matrix 
        MIMO_tap_filters_list = []
        for tap in range(num_taps):
            MIMO_tap_filter = np.zeros((num_of_sample,Nr, Nt),'c8')
            for sample in range(num_of_sample):
                #get Nt*Nr uncorrelated filter coeff from each SISO
                coeffs = np.zeros((Nt*Nr,1),'c8')
                
                #get tap filter for each siso_FadingChannel
                for m in range(Nt*Nr):
                    tap_filters_list = siso_FadingChannel_filters_list[m]
                    coeffs[m] = tap_filters_list[tap,sample]
                
                vec_H = L @ coeffs
                # reshape vec_H to Nr X Nt matrix
                H = vec_H.reshape((Nr, Nt), order='F')
                MIMO_tap_filter[sample] = H
            
            MIMO_tap_filters_list.append(MIMO_tap_filter)
        
        return MIMO_tap_filters_list, tap_delay_in_sample_list
    
    def filter(self, signal_in):
        """signal_in go through fading channel
        """
        Nr = self.Nr 

        assert signal_in.shape[0] == self.Nt
        num_of_sample = signal_in.shape[1]

        MIMO_tap_filters_list, tap_delay_in_sample_list = self.gen_mimo_tap_filters(num_of_sample)

        #MIMO filter
        signal_out = np.zeros((Nr,num_of_sample), 'c8')
        for tap in range(self.num_taps):
            tap_delay_in_sample = tap_delay_in_sample_list[tap]
            MIMO_tap_filters = MIMO_tap_filters_list[tap]

            tap_out = np.zeros((Nr,num_of_sample), 'c8')
            for sample in range(num_of_sample):
                H = MIMO_tap_filters[sample]
                tap_out[:,sample] = H @ signal_in[:,sample]
            
            #tap shift
            signal_out[:,tap_delay_in_sample:] += tap_out[:,0:num_of_sample-tap_delay_in_sample]
        
        return signal_out, MIMO_tap_filters_list, tap_delay_in_sample_list
    