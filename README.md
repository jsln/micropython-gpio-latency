# micropython-gpio-latency
Measure MicroPython GPIO interrupt latency stability

This code measures the GPIO interrupt latency jitter on a board running
MicroPython. A GPIO pin is configured as source of external interrupt, while
another GPIO pin is configured as output pin. A PyBoard v1.0 has been used.

An histogram of latency values is produced where each bin corresponds to 1
microsecond of jitter.

The tests are performed by connecting a 1KHz pulse train to X4 of the PyBoard
while the X3 pin is connected to an oscilloscope in order to visualize the
latency stability (oscilloscope display is set in persistent mode).

Similar tests have been run on a Nucleo F429ZI board, where PC8 is used as
output and PC9 as input.
