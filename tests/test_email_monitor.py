import datetime as dt
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('email_monitor',Path(__file__).resolve().parents[1]/'scripts/email_monitor.py')
monitor=importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)
NOW=dt.datetime(2026,10,26,14,tzinfo=dt.timezone.utc)


def data():
    return {'market':{'is_open':True,'next_close':'2026-10-26T20:00:00Z'},
            'runner':{'updated_at':NOW.isoformat(),'needs_attention':False},
            'events':[{'id':'buy-fill','time':NOW.isoformat(),'kind':'buy','symbol':'MSFT',
                       'text':'BUY 2 MSFT at $500','role':'Entry'}]}


class EmailMonitorTests(unittest.TestCase):
    def test_fill_email_is_deduplicated_and_partial_change_is_new(self):
        state={};sent=[];payload=data()
        send=lambda *args:sent.append(args)
        self.assertTrue(monitor.process(state,payload,NOW,send))
        monitor.process(state,payload,NOW,send)
        self.assertEqual(len(sent),1)
        payload['events'][0]['text']='BUY 3 MSFT at $500'
        monitor.process(state,payload,NOW,send)
        self.assertEqual(len(sent),2)
        self.assertNotEqual(sent[0][2],sent[1][2])

    def test_outage_once_recovery_once_and_no_weekend_alert(self):
        state={'session_open':'2026-10-26T13:30:00Z','session_close':'2026-10-26T20:00:00Z'}
        sent=[];send=lambda *args:sent.append(args)
        monitor.process(state,None,NOW,send)
        monitor.process(state,None,NOW+dt.timedelta(minutes=5),send)
        self.assertEqual(len(sent),1)
        payload=data();payload['events']=[]
        monitor.process(state,payload,NOW,send)
        self.assertEqual(len(sent),2)
        self.assertIn('recovered',sent[-1][0])
        monitor.process(state,None,NOW+dt.timedelta(days=5),send)
        self.assertEqual(len(sent),2)

    def test_failed_email_is_not_marked_sent(self):
        state={}
        def failed(*args):raise RuntimeError('sender unavailable')
        with self.assertRaises(RuntimeError):monitor.process(state,data(),NOW,failed)
        self.assertFalse(state.get('sent'))

    def test_old_fills_not_replayed_and_short_session_respected(self):
        state={};payload=data();sent=[]
        payload['events'][0]['time']='2026-10-23T15:00:00Z'
        monitor.process(state,payload,NOW,lambda *a:sent.append(a))
        self.assertEqual(sent,[])
        state.update(session_close='2026-10-26T14:00:00Z')
        self.assertFalse(monitor.in_session(state,NOW))

    def test_fill_still_alerts_if_runner_requires_attention(self):
        state={};payload=data();sent=[]
        payload['runner']['needs_attention']=True
        self.assertFalse(monitor.process(state,payload,NOW,lambda *a:sent.append(a)))
        self.assertEqual(len(sent),2)
        self.assertIn('BUY',sent[0][0])
        self.assertIn('unhealthy',sent[1][0])


if __name__=='__main__':unittest.main()
