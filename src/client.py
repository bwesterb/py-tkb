import threading
import collections
from pprint import pformat

from mirte.core import Module

from joyce.base import JoyceChannel

from sarah.event import Event

roomMap_entry = collections.namedtuple('roomMap_entry', ('name', 'pcs'))

class TkbClientChannel(JoyceChannel):
    def __init__(self, server, *args, **kwargs):
        super(TkbClientChannel, self).__init__(*args, **kwargs)
        self.s = server
        self.l = self.s.l
        self.msg_map = {
                'occupation': self._msg_occupation,
                'occupation_update': self._msg_occupation_update,
                'schedule': self._msg_schedule,
                'welcome': self._msg_welcome,
                'tags': self._msg_tags,
                'roomMap': self._msg_roomMap }
    def handle_message(self, data):
        typ = data.get('type')
        if typ in self.msg_map:
            self.msg_map[typ](data)
        else:
            self.l.warn('Unknown message type: %s' % repr(typ))
    def _msg_welcome(self, data):
        self.l.info('Welcome %s' % pformat(data))
    def _msg_occupation(self, data):
        with self.s.lock:
            old_occupation = self.s.occupation
            old_occupationVersion = self.s.occupationVersion
            self.s.occupation = data['occupation']
            self.s.occupationVersion = data['version']
        self.s.on_occupation_changed(data['occupation'],
                data['version'], old_occupation,
                old_occupationVersion)
    def _msg_occupation_update(self, data):
        old_occupation = {}
        with self.s.lock:
            for pc in data['update']:
                old_occupation[pc] = self.s.occupation.get(pc)
            old_occupationVersion = self.s.occupationVersion
            self.s.occupation.update(data['update'])
            self.s.occupationVersion = data['version']
        self.s.on_occupation_changed(data['update'],
                data['version'], old_occupation,
                old_occupationVersion)
    def _msg_schedule(self, data):
        with self.s.lock:
            old_schedule = self.s.schedule
            old_scheduleVersion = self.s.scheduleVersion
            self.s.schedule = data['schedule']
            self.s.scheduleVersion = data['version']
        self.s.on_schedule_changed(data['schedule'], data['version'],
                old_schedule, old_scheduleVersion)
    def _msg_roomMap(self, data):
        roomMap = {}
        for room, pair in data['roomMap'].iteritems():
            roomMap[room] = roomMap_entry(*pair)
        with self.s.lock:
            old_roomMap = self.s.roomMap
            old_roomMapVersion = self.s.roomMapVersion
            self.s.roomMap = roomMap
            self.s.roomMapVersion = data['version']
        self.s.on_roomMap_changed(roomMap, data['version'],
                old_roomMap, old_roomMapVersion)
    def _msg_tags(self, data):
        with self.s.lock:
            old_tags = self.s.tags
            self.s.tags = data['tags']
        self.s.on_tags_changed(data['tags'], old_tags)

class TkbClient(Module):
    def __init__(self, settings, l):
        super(TkbClient, self).__init__(settings, l)
        def _channel_class(*args, **kwargs):
            return TkbClientChannel(self, *args, **kwargs)
        self.lock = threading.Lock()
        self.channel = self.joyceClient.create_channel(
                        channel_class=_channel_class)

        # State
        self.tags = []
        self.roomMap = {}
        self.roomMapVersion = None
        self.schedule = {}
        self.scheduleVersion = None
        self.occupation = {}
        self.occupationVersion = None

        # Events
        self.on_tags_changed = Event()
        self.on_occupation_changed = Event()
        self.on_roomMap_changed = Event()
        self.on_schedule_changed = Event()
    def set_msgFilter(self, tags):
        self.channel.send_message({'type': 'set_msgFilter',
                                   'occupation': tags,
                                   'schedule': tags,
                                   'roomMap': tags})
        self.channel.send_message({'type': 'get_occupation'})
        self.channel.send_message({'type': 'get_schedule'})
        self.channel.send_message({'type': 'get_roomMap'})

# vim: et:sta:bs=2:sw=4:
