import time
import sys
import base64
from itertools import zip_longest
import contextlib
from tqdm import tqdm

def banner():
    banner = base64.b64decode(
        'IF9fX19fIF8gICBfX19fX19fX19fX19fX19fX19fIF9fX19fX19fX19fIAovICBfX198IHwgLyAvXyAgIF98IF9fXyBcIF9fXyBcICBfX198IF9fXyBcClwgYC0tLnwgfC8gLyAgfCB8IHwgfF8vIC8gfF8vIC8gfF9fIHwgfF8vIC8KIGAtLS4gXCAgICBcICB8IHwgfCAgX18vfCAgX18vfCAgX198fCAgICAvIAovXF9fLyAvIHxcICBcX3wgfF98IHwgICB8IHwgICB8IHxfX198IHxcIFwgClxfX19fL1xffCBcXy9cX19fL1xffCAgIFxffCAgIFxfX19fL1xffCBcX3wgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCg=='
    ).decode('utf-8')
    print(f'\n\033[91m{banner}\033[0m by \033[92m@NetD0G\033[0m\033[0m(B.M.W).\n\n')


def beep():
    print('\a')

def store(service_name, combo):
  filename = service_name + ".txt"
  print(f"email:{combo[0]} pass:{combo[1]} source:{combo[2]}", file=open(filename, "a+"))

def wait(t, step=1):
    pad_str = ' ' * len('%d' % step)
    for i in range(t, 0, -step):
        sys.stdout.write(f'Throttling for the next {i} seconds. {pad_str}\r'),
        sys.stdout.flush()
        time.sleep(step)
    print(f'Done throttling for {t} seconds! {pad_str}')


def failed(combo):
    print(f"\033[91m FAILED LOGIN \U0001F61E using email {combo[0]} and password {combo[1]} \033[0m")


def passed(service_name, combo):
    beep()
    print(f"\033[92m SUCCESS LOGIN {combo[0]}:{combo[1]} \033[0m")
    store(service_name, combo)

def passed_untrusted(service_name, combo):
    beep()
    print(f"\033[92m SUCCESS LOGIN {combo[0]}:{combo[1]}, But\033[0m \033[91mUntrusted!\033[0m")
    store(service_name, combo)

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

#https://github.com/tqdm/tqdm#redirecting-writing
class DummyTqdmFile(object):
    """Dummy file-like that will write to tqdm"""
    file = None
    def __init__(self, file):
        self.file = file

    def write(self, x):
        # Avoid print() second call (useless \n)
        if len(x.rstrip()) > 0:
            tqdm.write(x, file=self.file)

    def flush(self):
        return getattr(self.file, "flush", lambda: None)()
        
#https://github.com/tqdm/tqdm#redirecting-writing
@contextlib.contextmanager
def std_out_err_redirect_tqdm():
    orig_out_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = map(DummyTqdmFile, orig_out_err)
        yield orig_out_err[0]
    # Relay exceptions
    except Exception as exc:
        raise exc
    # Always restore sys.stdout/err if necessary
    finally:
        sys.stdout, sys.stderr = orig_out_err