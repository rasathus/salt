import os
import threading

import salt.utils
import salt.payload

def running(opts):
    ret = []
    current_thread = threading.currentThread().name
    proc_dir = os.path.join(opts['cachedir'], 'proc')
    if not os.path.isdir(proc_dir):
        return []
    for fn_ in os.listdir(proc_dir):
        path = os.path.join(proc_dir, fn_)
        try:
            data = _read_proc_file(path, opts)
            if data is not None:
                ret.append(data)
        except IOError:
            # proc files may be removed at any time during this process by
            # the minion process that is executing the JID in question, so
            # we must ignore ENOENT during this process
            pass

    return ret

def _read_proc_file(path, opts):
    '''
    Return a dict of JID metadata, or None
    '''
    serial = salt.payload.Serial(opts)
    pid = os.getpid()
    with salt.utils.fopen(path, 'rb') as fp_:
        buf = fp_.read()
        fp_.close()
        if buf:
            data = serial.loads(buf)
        else:
            # Proc file is empty, remove
            os.remove(path)
            return None
    if not isinstance(data, dict):
        # Invalid serial object
        return None
    if not salt.utils.process.os_is_running(data['pid']):
        # The process is no longer running, clear out the file and
        # continue
        os.remove(path)
        return None
    if opts['multiprocessing']:
        if data.get('pid') == pid:
            return None
    else:
        if data.get('pid') != pid:
            os.remove(path)
            return None
        if data.get('jid') == current_thread:
            return None
        if not data.get('jid') in [x.name for x in threading.enumerate()]:
            os.remove(path)
            return None

    return data
