
import array
from time import ticks_us
from pyb import Pin, ExtInt
from utime import sleep_ms, sleep_us

# The GPIO input pin is fed with a 1KHz pulse train. We keep 1 sec worth of
# timestamps.
GPIO_CB_TS_ARRAY_LEN = const(1000)

# Ignore initial timestamps as 1ms may not be enough time to do the processing
# and a pending callback will write wrong values as soon as interrupts are
# enabled.
GPIO_CB_IGNORED_TIMESTAMPS = const(80)

# Histogram length in usec bins.
GPIO_HIST_ARRAY_LEN = const(20)

# Remove this line to test the bytecode emitter, or change it to
# @micropython.viper in order to test the viper emitter
@micropython.native
def gpio_callback(e):
    global cb_timestamp
    global cb_timestamp_index
    cb_timestamp[cb_timestamp_index] = ticks_us()
    p_out(1)
    p_out(0)
    cb_timestamp_index += 1
    if cb_timestamp_index > GPIO_CB_TS_ARRAY_LEN:
        # should not happen
        raise BoundsException('CB timestamp array bounds exceeded')

cb_timestamp_index = 0
cb_timestamp = array.array('L', 0 for x in range(GPIO_CB_TS_ARRAY_LEN))
cb_timestamp_jitter = array.array('L', 0 for x in range(GPIO_CB_TS_ARRAY_LEN))
hist = array.array('L', 0 for x in range(GPIO_HIST_ARRAY_LEN))

# Configure GPIO output pin (PyBoard v1.0).
p_out = Pin('X3', mode = Pin.OUT_PP, pull = Pin.PULL_DOWN)

# Configure GPIO input pin to trigger an interrupt (PyBoard v1.0).
ExtInt(Pin('X4'), ExtInt.IRQ_RISING, Pin.PULL_DOWN, gpio_callback)

while True:
    # Wait for callback timestamp array to fill up in ISR.
    while cb_timestamp_index < GPIO_CB_TS_ARRAY_LEN:
        sleep_us(100)

    # Start of critical section.
    irq_state = pyb.disable_irq()

    cb_captured_time_span = cb_timestamp[GPIO_CB_TS_ARRAY_LEN - 1] - cb_timestamp[GPIO_CB_IGNORED_TIMESTAMPS]
    # Protect against ticks_us wrap-around.
    if cb_captured_time_span > 0:

        time_per_bin = float(cb_captured_time_span) / (GPIO_CB_TS_ARRAY_LEN - 1 - GPIO_CB_IGNORED_TIMESTAMPS)

        # Build latency jitter array.
        for i in range(GPIO_CB_IGNORED_TIMESTAMPS, GPIO_CB_TS_ARRAY_LEN):
            cb_timestamp_jitter[i] = cb_timestamp[i] - int(time_per_bin * i)
        timestamp_min = min(cb_timestamp_jitter[GPIO_CB_IGNORED_TIMESTAMPS:])
        for i in range(GPIO_CB_IGNORED_TIMESTAMPS, GPIO_CB_TS_ARRAY_LEN):
            cb_timestamp_jitter[i] -= timestamp_min

        # Build latency jitter histogram.
        for i in range(GPIO_CB_IGNORED_TIMESTAMPS + 1, GPIO_CB_TS_ARRAY_LEN):
            if cb_timestamp_jitter[i] < GPIO_HIST_ARRAY_LEN:
                hist[cb_timestamp_jitter[i]] += 1
            else:
                # Outliers, we do not update corresponding bin as it does not
                # fit the predefined histogram array.
                hist[GPIO_HIST_ARRAY_LEN - 1] += 1

        # Output latency histogram.
        for i in range(GPIO_HIST_ARRAY_LEN):
            print('i: {0:3d}     acc: {1:d}'.format(i, hist[i]))
        str_back_up = (GPIO_HIST_ARRAY_LEN + 1) * '\033[F'
        print(str_back_up)

    cb_timestamp_index = 0

    # End of critical section
    pyb.enable_irq(irq_state)
