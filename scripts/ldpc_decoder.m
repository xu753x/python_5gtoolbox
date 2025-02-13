% test LDPC decoder performance
close all;clear;

bgn = 1;                    % Base graph number
Zc= 10;                   % Code block segment length
snr_db_range = -1:0.5:1;
algo_list = ["BP", "min-sum", "NMS", "OMS"];
%algo_list = ["min-sum"];
L_list = [32];
alpha_list = [0.8,0.5];
beta_list = [0.3, 0.1];
if bgn == 1
    K = Zc*22;

end

bler_list = [];
algo_flag = [];
for algo = algo_list
    if algo == "BP"
        test_num = 1;
    elseif algo == "min-sum"
        test_num = 1;
    elseif algo == "NMS"
        test_num = length(alpha_list);
    else
        test_num = length(beta_list);
    end

    for test_idx = 1:test_num
        if algo == "BP"
            algo_flag  = [algo_flag, "BP"];
        elseif algo == "min-sum"
            algo_flag  = [algo_flag, "min-sum"];
        elseif algo == "NMS"
            algo_flag  = [algo_flag, "NMS-alpha "+alpha_list(test_idx)];
        else
            algo_flag  = [algo_flag, "OMS-beta "+beta_list(test_idx)];
        end

        bler_result = [];
        for snr_db = snr_db_range
            tmp = 400;
            if snr_db < 0
                total_count = tmp;
            else
                total_count = tmp*10;
            end
            failed_count = 0;
            for count = 1:total_count

                txcbs = randi([0,1],K,1);
                txcodedcbs = nrLDPCEncode(txcbs,bgn);   % Encode

                rxcodedcbs = double(1-2*txcodedcbs);    % Convert to soft bits
                %LLR
                noise_linear = 10^(-snr_db/10);
                sigma = sqrt(noise_linear);
                y = rxcodedcbs + sigma*randn(size(rxcodedcbs)); % 

                % 
                LLR_y = 2*y/(noise_linear);

                % Decode with a maximum of 25 iterations
                if algo == "BP"
                    [rxcbs, actualniters] = nrLDPCDecode(LLR_y,bgn,L_list(1),'Algorithm','Belief propagation');
                elseif algo == "min-sum"
                    [rxcbs, actualniters] = nrLDPCDecode(LLR_y,bgn,L_list(1),'Algorithm','Normalized min-sum','ScalingFactor',1);
                elseif algo == "NMS"
                    [rxcbs, actualniters] = nrLDPCDecode(LLR_y,bgn,L_list(1),'Algorithm','Normalized min-sum','ScalingFactor',alpha_list(test_idx));
                else
                    [rxcbs, actualniters] = nrLDPCDecode(LLR_y,bgn,L_list(1),'Algorithm','Offset min-sum','Offset',beta_list(test_idx));
                end
                

                if sum(abs(int8(txcbs) - rxcbs)) > 0
                    failed_count = failed_count + 1;
                end
            end
            bler_result = [bler_result,failed_count/total_count];
        end
        bler_list = [bler_list;bler_result];
    end
end

%display
figure('numbertitle','off','name','BLER')
for idx = 1:length(algo_flag)
    semilogy(snr_db_range, bler_list(idx, :), 'LineWidth', 1.0, 'MarkerSize', 6); hold on;
end
xlabel('Eb/N0(dB)'); ylabel('FER');
legend(algo_flag)
grid on;


aaaa=1;