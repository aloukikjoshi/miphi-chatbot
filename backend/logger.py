import logging, logging.handlers, os, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from pythonjsonlogger import jsonlogger

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_DIR = Path(os.getenv('LOG_DIR', 'logs'))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / 'app.log'

class MiphiJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        log_record['level'] = record.levelname
        log_record['module'] = record.module
        log_record.pop('levelname', None)
        log_record.pop('asctime', None)

_fmt = '%(message)s %(user_id)s %(session_id)s %(latency_ms)s %(status_code)s'

def _file_handler():
    h = logging.handlers.TimedRotatingFileHandler(str(LOG_FILE), when='midnight', interval=1, backupCount=30, encoding='utf-8', utc=True)
    h.suffix = '%Y-%m-%d'
    h.setFormatter(MiphiJsonFormatter(_fmt))
    return h

def _stream_handler():
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(MiphiJsonFormatter(_fmt))
    return h

_logger = logging.getLogger('miphi')
_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
if not _logger.handlers:
    _logger.addHandler(_file_handler())
    _logger.addHandler(_stream_handler())
_logger.propagate = False

_EXTRA = {'user_id': None, 'session_id': None, 'latency_ms': None, 'status_code': None}

def get_logger(name='miphi'):
    return logging.LoggerAdapter(logging.getLogger(name), extra=dict(_EXTRA))

def log_startup():
    get_logger().info('STARTUP: MiPhi API server started', extra={**_EXTRA, 'event': 'STARTUP'})

def log_crash(exc):
    get_logger().critical('CRASH: Unhandled exception', extra={**_EXTRA, 'event': 'CRASH', 'error_trace': traceback.format_exc(), 'error_type': type(exc).__name__})
