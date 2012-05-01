import argparse
import logging
import threading
from pprint import pformat

import sarah.coloredLogging

import mirte
import mirte.main
import mirte.mirteFile

class Listener(object):
    """ Used by listen command """
    def __init__(self, program):
        self.program = program
        self.c = program.client
    def listen(self):
        self.c.on_occupation_changed.register(self._on_occupation_changed)
        self.c.on_roomMap_changed.register(self._on_roomMap_changed)
        self.c.on_schedule_changed.register(self._on_schedule_changed)
        self.c.on_tags_changed.register(self._on_tags_changed)
        tags = (None if self.program.args.tags == ['all']
                    else self.program.args.tags)
        self.c.set_msgFilter(tags)
        self.program.mirte_manager.sleep_event.wait()
    def _on_occupation_changed(self, occ, occVer, old_occ, old_occVer):
        print 'Occupation changed:'
        unaccounted = set(old_occ)
        for pc in occ:
            print ' %-20s %-2s (was %-2s)' % (pc, occ[pc],
                            old_occ[pc] if pc in old_occ else '-')
            if pc in unaccounted:
                unaccounted.remove(pc)
        for pc in unaccounted:
            print ' %-10s %-2s (was %-2s)' % (pc, ' ',
                            old_occ[pc] if pc in old_occ else '-')
    def _on_roomMap_changed(self, rm, rmVer, old_rm, old_rmVer):
        print 'Roommap changed:'
        removed_rooms = set(old_rm)
        for room in rm:
            if not room in removed_rooms:
                print ' %s is added' % rm[room].name
                print '  with pcs:   %s' % ' '.join(rm[room].pcs)
                continue
            if room in removed_romos:
                removed_rooms.remove(room)
            added = []
            removed = set(old_rm[room].pcs)
            for pc in rm[room].pcs:
                if pc in removed:
                    removed.remove(pc)
                added.append(pc)
            if added or removed:
                print ' %s' % rm[room].name
                if added:
                    print '  pcs added:    %s' % ' '.join(added)
                if removed:
                    print '  pcs removed:  %s' % ' '.join(removed)
        for room in removed_rooms:
            print ' %s is removed' % old_rm[room].name
            print '  with pcs:   %s ' % ' '.join(old_rm[room].pcs)

    def _on_schedule_changed(self, sched, schedVer, old_sched, old_schedVer):
        print 'Schedule changed:'
        def roomName(key):
            if key in self.c.roomMap:
                return self.c.roomMap[key].name
            return key
        removed_rooms = set(old_sched)
        for room in sched:
            if not room in removed_rooms:
                print ' %s is added' % roomName(room)
                print '  with events:'
                for e in sched[room]:
                    print '   %s' % e
                continue
            if room in removed_rooms:
                removed_rooms.remove(room)
            added = []
            removed = set(old_sched[room])
            for pc in sched[room]:
                if pc in removed:
                    removed.remove(pc)
                added.append(pc)
            if added or removed:
                print ' %s' % roomName(room)
                if added:
                    print '  events added:'
                    for e in added:
                        print '   %s' % e
                if removed:
                    print '  events removed:'
                    for e in removed:
                        print '   %s' % e
        for room in removed_rooms:
            print ' %s is removed' % roomName(room)
            print '  with events:'
            for e in old_sched[room]:
                print '   %s' % e

    def _on_tags_changed(self, tags, old_tags):
        print 'Tags changed:'
        old = set(old_tags)
        new = set(tags)
        if new - old:
            print ' added:       %s' % ' '.join(new - old)
        if old - new:
            print ' removed:     %s' % ' '.join(old - new)

class Program(object):
    def cmd_listen(self, args):
        Listener(self).listen()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--verbose', '-v', action='count', dest='verbosity')
        parser.add_argument('--host', '-H', type=str, default='welke.tk')
        parser.add_argument('--port', '-p', type=int, default=8080)
        parser.add_argument('--path', '-P', type=str, default='/')
        subparsers = parser.add_subparsers()
        parser_listen = subparsers.add_parser('listen')
        parser_listen.add_argument('--tags', '-t', type=str, default=['all'],
                                nargs='?')
        parser_listen.set_defaults(func=self.cmd_listen)
        self.args = parser.parse_args()
        return self.args

    def main(self):
        args = self.parse_args()
        if args.verbosity >= 1:
            sarah.coloredLogging.basicConfig(level=logging.DEBUG,
                                    formatter=mirte.main.MirteFormatter())
        self.mirte_manager = m = mirte.get_a_manager()
        mirte.mirteFile.load_mirteFile('tkb/client', m)
        mirte.mirteFile.load_mirteFile('joyce/comet', m)
        self.joyceClient = m.create_instance('joyceClient', 'cometJoyceClient',
                                            {'host': args.host,
                                             'port': args.port,
                                             'path': args.path})
        self.client = m.create_instance('tkbClient', 'tkbClient',
                                            {'joyceClient': 'joyceClient'})
        args.func(args)
        m.stop()

if __name__ == '__main__':
    Program().main()

# vim: et:sta:bs=2:sw=4:
