function [sig, wfm] = plotIQ(file,type)
fid = fopen(file);

raw = fread(fid, type);

rpt = raw(1:2:length(raw));
ipt = raw(2:2:length(raw));

sig = rpt + ipt*1j;

% % create a filter to restrict our band of interest to 200khz around center
n = 50;
Wn = 0.1;
b = fir1(n,Wn);

sig = conv(sig, b);

plot(1:length(sig), abs(fftshift(fft(sig))))

% figure()
% plot(1:length(sig), abs(fftshift(fft(sig))))
% title("Filtered signal")

figure()
window   = 1024; 
noverlap = 512;
nfft     = 1024;

spectrogram(sig, window, noverlap, nfft, 1e6, 'centered')

colormap winter;

% find the phase over time
phase = atan(imag(sig) ./ real(sig));

wfm = diff(phase);

% wfm = wfm ./ max(abs(wfm));

% go through and remove any spikes
ii = 2;
while ii < length(wfm) - 1
    jj = ii;
    if abs(wfm(jj)) > 1
        while and((jj < length(wfm)),(abs(wfm(jj)) > 1))
            % go until we find next point less than 1
            jj = jj + 1;
        end 
        wfm(ii:jj) = 0.5 * (wfm(ii - 1) + wfm(jj));
        ii = jj;
    end
    ii = ii + 1;
end
audiowrite("testaudio.wav", wfm, 1e6);

fclose(fid);

end