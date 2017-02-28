import signal

class InterruptableRegion(object):
    def __init__(self, sig=signal.SIGINT):
        self.sig = sig
        self.interrupted = False
        self.released = False
        self.original_handler = None

    def __enter__(self):
        self._validate_region_start()
        self._store_signal_default_handler()

        def _signal_invoked_new_handler(signum, frame):
            self._release()
            self.interrupted = True

        signal.signal(self.sig, _signal_invoked_new_handler)

        return self

    def __exit__(self, type, value, tb):
        self._release()

    def _validate_region_start(self):
        if self.interrupted or self.released or self.original_handler:
            raise RuntimeError("An interruptable region can only be used once")

    def _release(self):
        if not self.released:
            self._reset_signal_default_handler()
            self.released = True

    def _store_signal_default_handler(self):
        self.original_handler = signal.getsignal(self.sig)

    def _reset_signal_default_handler(self):
        signal.signal(self.sig, self.original_handler)


if __name__ == '__main__':

    import unittest
    import time
                
    class InterruptableRegionTestCase(unittest.TestCase):
        
        def test_simple(self):
            with InterruptableRegion() as h:
                while True:
                    print "..."
                    time.sleep(1)
                    if h.interrupted:
                        print "interrupted!"
                        time.sleep(5)
                        break
                    
        def test_nested(self):
            with InterruptableRegion() as h1:
                while True:
                    print "(1)..."
                    time.sleep(1)
                    with InterruptableRegion() as h2:
                        while True:
                            print "\t(2)..."
                            time.sleep(1)
                            if h2.interrupted:
                                print "\t(2) interrupted!"
                                time.sleep(2)
                                break
                    if h1.interrupted:
                        print "(1) interrupted!"
                        time.sleep(2)
                        break
                        
    unittest.main()
