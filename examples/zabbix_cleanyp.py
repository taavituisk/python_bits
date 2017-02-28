#!/usr/bin/env python

import pyzabbix
import requests
import signal

exit_received = False

def signal_handler(signal, frame):
  print('signal \'{signal}\' received'.format(signal = signal))
  global exit_received
  exit_received = True

def main():
  user = 'maumau'
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  session = requests.Session()
  session.auth = (user, 'password')
  zapi = pyzabbix.ZabbixAPI('https://monitor.grabcad.net/zabbix', session)
  print('Logging in to zabbix as user \'{user}\''.format(user = user))
  zapi.login(user)

  hostlist = zapi.host.get(output = 'extend', filter = { 'status': 1 })
  print('Got {amount} hosts from zabbix'.format(amount = len(hostlist)))

  for host in hostlist:
    if exit_received:
      raise SystemExit('quitting')

    if ('lin64-api-' in host['name']) and host['hostid']:
      print(host['hostid'] + ' ' + host['name'])
      res = zapi.host.delete(hostid = host['hostid'])

if __name__ == '__main__':
  main()
