function [filtsig] = filterBW(sig, percToKeep)

    filt = zeros(length(sig), 1);
    filt(1:ceil(length(sig) * percToKeep / 2)) = 1;
    filt(floor(length(sig) * 1 - (percToKeep / 2)):end) = 1;

    figure()
    plot(abs(fft(sig)))
    hold on
    plot(1:length(filt), filt, '--', 'color', 'black')
    title('Freq domain and filter')

    filtsig = fft(sig) .* filt;

    hold off
    figure()
    plot(abs(filtsig))
    filtsig = ifft(filtsig);
    title('filtered freq domain')
end