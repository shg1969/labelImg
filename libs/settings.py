import os
import pickle

try:
    from PyQt5.QtCore import QByteArray, QPoint, QSize
    from PyQt5.QtGui import QColor
except ImportError:
    from PyQt4.QtCore import QByteArray, QPoint, QSize
    from PyQt4.QtGui import QColor

from libs.constants import (SETTING_FILL_COLOR, SETTING_LABEL_FILE_FORMAT,
                            SETTING_LINE_COLOR, SETTING_WIN_POSE,
                            SETTING_WIN_SIZE, SETTING_WIN_STATE)

# Suffix of the backup that keeps an unreadable settings file from being
# silently overwritten by the next save.
BACKUP_SUFFIX = '.pkl.bak'


def encode_value(key, value):
    """Turn a setting value into a plain Python value.

    Older releases pickled QSize/QPoint/QColor/QByteArray instances and the
    LabelFileFormat enum directly. Such a file can only be unpickled by the
    very same PyQt/sip/Python build that wrote it, so any environment change
    (a different PyQt version, or another copy of labelImg) made it unreadable.
    Plain values keep the settings file portable.
    """
    if isinstance(value, QByteArray):
        return bytes(value)
    if isinstance(value, QSize):
        return [value.width(), value.height()]
    if isinstance(value, QPoint):
        return [value.x(), value.y()]
    if isinstance(value, QColor):
        return list(value.getRgb())
    if key == SETTING_LABEL_FILE_FORMAT and hasattr(value, 'value'):
        return value.value
    return value


def decode_value(key, value):
    """Rebuild the objects labelImg expects, accepting the legacy format too."""
    if key == SETTING_WIN_SIZE and not isinstance(value, QSize):
        return QSize(value[0], value[1])
    if key == SETTING_WIN_POSE and not isinstance(value, QPoint):
        return QPoint(value[0], value[1])
    if key == SETTING_WIN_STATE and not isinstance(value, QByteArray):
        return QByteArray(value)
    if key in (SETTING_LINE_COLOR, SETTING_FILL_COLOR) and not isinstance(value, QColor):
        return QColor(*value)
    if key == SETTING_LABEL_FILE_FORMAT and isinstance(value, int):
        from libs.labelFile import LabelFileFormat
        return LabelFileFormat(value)
    return value


class Settings(object):
    def __init__(self):
        # Be default, the home will be in the same folder as labelImg
        home = os.path.expanduser("~")
        self.data = {}
        self.path = os.path.join(home, '.labelImgSettings.pkl')

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        if key in self.data:
            return self.data[key]
        return default

    def save(self):
        if self.path:
            portable = dict((key, encode_value(key, value))
                            for key, value in self.data.items())
            with open(self.path, 'wb') as f:
                pickle.dump(portable, f, pickle.HIGHEST_PROTOCOL)
                return True
        return False

    def load(self):
        if not self.path or not os.path.exists(self.path):
            return False
        try:
            with open(self.path, 'rb') as f:
                stored = pickle.load(f)
            if not isinstance(stored, dict):
                raise ValueError('unexpected settings content: %s' % type(stored))
        except Exception as e:
            # Never swallow the reason, and never let the unreadable file be
            # overwritten by the next save().
            print('Loading setting failed: %s: %s' % (type(e).__name__, e))
            self._backup_unreadable_file()
            self.data = {}
            return False
        self.data = dict((key, decode_value(key, value))
                         for key, value in stored.items())
        return True

    def _backup_unreadable_file(self):
        backup_path = self.path + BACKUP_SUFFIX
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(self.path, backup_path)
            print('Unreadable setting file kept as %s' % backup_path)
        except OSError as e:
            print('Could not back up setting file: %s' % e)

    def reset(self):
        if os.path.exists(self.path):
            os.remove(self.path)
            print('Remove setting pkl file ${0}'.format(self.path))
        self.data = {}
        self.path = None
