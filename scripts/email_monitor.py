"""Read-only paper fill and market-hours outage email monitor. No trading API keys."""
import datetime as dt
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import time
import urllib.request

BASE='https://hermestradingsystem.onrender.com'


def instant(value):
    return dt.datetime.fromisoformat(value.replace('Z','+00:00'))


def email(subject,body,key,env=None,opener=None):
    env=os.environ if env is None else env
    payload={'from':'Daytrader <onboarding@resend.dev>','to':[env['ALERT_EMAIL']],
             'subject':subject,'text':body+'\n\nPaper trading only. '+BASE}
    request=urllib.request.Request('https://api.resend.com/emails',method='POST',
        data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+env['RESEND_API_KEY'],
        'Content-Type':'application/json','User-Agent':'Daytrader-Alerts/1.0','Idempotency-Key':'daytrader/'+key})
    with (opener or urllib.request.urlopen)(request,timeout=20) as response:
        result=json.load(response)
    if not result.get('id'):raise RuntimeError('Email sender did not acknowledge the alert')


def read_dashboard():
    client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    request=urllib.request.Request(BASE+'/login',method='POST',
        data=json.dumps({'password':os.environ['DAYTRADER_DASHBOARD_PASSWORD']}).encode(),
        headers={'Content-Type':'application/json','X-Daytrader':'dashboard'})
    with client.open(request,timeout=20) as response:
        if response.status!=200:raise RuntimeError('Dashboard login failed')
    with client.open(BASE+'/api/state',timeout=20) as response:return json.load(response)


def in_session(state,now):
    # Clock is obtained from Alpaca on a previous successful check. No guessed
    # weekday-only calendar: holidays and shortened sessions retain their dates.
    try:return instant(state['session_open'])<=now<instant(state['session_close'])
    except (KeyError,TypeError,ValueError):return False


def remember_clock(state,data,now):
    clock=data['market']
    state['session_open']=(now-dt.timedelta(minutes=5)).isoformat() if clock['is_open'] else clock['next_open']
    state['session_close']=clock['next_close']


def process(state,data,now,send=email):
    if data is not None:
        remember_clock(state,data,now)
        runner=data.get('runner',{})
        stamp=runner.get('updated_at')
        healthy=bool(stamp) and 0<=(now-instant(stamp)).total_seconds()<180 and not runner.get('needs_attention')
        notify_fills(state,data,now,send)
    else:healthy=False
    if not healthy:
        if in_session(state,now) and not state.get('incident'):
            incident=now.isoformat()
            send('Daytrader: offline or unhealthy during market hours',
                 'The external monitor could not confirm a healthy paper runner.\n'
                 'Detected at '+incident+' UTC.\n'
                 'The service, dashboard, or broker connection may be unavailable.\n'
                 'Check Render logs and Alpaca. Broker-held protective orders remain at Alpaca.',
                 'offline-'+hashlib.sha256(incident.encode()).hexdigest())
            state['incident']=incident
        return False
    if state.get('incident'):
        incident=state['incident']
        send('Daytrader: connection recovered','The external monitor can read the paper broker and a fresh runner heartbeat again.\n'
             'Previous incident started at '+incident+' UTC.',
             'recovered-'+hashlib.sha256(incident.encode()).hexdigest())
        state.pop('incident')
    return True


def notify_fills(state,data,now,send=email):
    day=now.date().isoformat()
    if state.get('day')!=day:state.update(day=day,sent=[])
    sent=set(state.get('sent',[]))
    for event in reversed(data.get('events',[])):
        if event.get('kind') not in ('buy','sell') or not event.get('time'):continue
        # Do not replay old sessions after a cache loss. Stable provider keys
        # suppress the same observed cumulative fill for 24 hours.
        if instant(event['time']).date().isoformat()!=day:continue
        key=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest()
        if key in sent:continue
        if len(sent)>=20:raise RuntimeError('Daily trade-alert safety cap reached')
        send('Daytrader PAPER '+event['kind'].upper()+': '+event['symbol'],
             event['text']+'\nRole: '+event['role']+'\nBroker time: '+event['time']+
             '\nThis is a confirmed cumulative fill, not a submitted-order signal.', 'fill-'+key)
        sent.add(key)
        state['sent']=sorted(sent)


def main():
    path=Path('.monitor-state/state.json')
    path.parent.mkdir(exist_ok=True)
    state=json.loads(path.read_text()) if path.exists() else {}
    configured=all(os.environ.get(k) for k in ('ALERT_EMAIL','RESEND_API_KEY','DAYTRADER_DASHBOARD_PASSWORD'))
    if not configured:
        print('Email alerts are not configured; no emails sent.')
        return
    data=None
    for attempt in range(2):
        try:
            data=read_dashboard()
            break
        except Exception:
            if attempt==0:time.sleep(10)
    try:
        healthy=process(state,data,dt.datetime.now(dt.timezone.utc))
        print('Email monitor finished. Runner healthy:',healthy)
        if not healthy:raise SystemExit('Paper runner unavailable or unhealthy; notification evaluated against cached exchange session.')
    except Exception:
        raise SystemExit('Email monitor failed. Check sender setup; private response details suppressed.')
    finally:
        tmp=path.with_suffix('.tmp')
        tmp.write_text(json.dumps(state))
        tmp.replace(path)


if __name__=='__main__':main()
