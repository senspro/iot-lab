#!/usr/bin/env python

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

from simplejson import JSONEncoder, JSONDecoder
from subprocess import check_output
from urllib import unquote


class Reqs:

  def get_owned_nodes(self, site):
	res, err = call("experiment-cli get -l --state Running")
	if err: return err

	state = {}
	for experiment in res["items"]:
		nodes = experiment["resources"]
		if nodes[0].find("." + site + ".") == -1:
			continue
		for n in nodes:
			node_id = n.split('-')[1].split('.')[0]
			state[node_id] = "owned"
	return state

  def get_system_state(self, site, archi):
	res, err = call("experiment-cli info -li --site " + site)
	if err: return err

	state = res["items"][0][site][archi]
	return state

  def save_node_set(self, name, nodes):
	name = unquote(name)
	nodes = unquote(nodes)
	file_name = "nodes-sets.json"
	data = JSONDecoder().decode(file(file_name).read())
	data[name] = nodes
	open(file_name, "w").write(
		JSONEncoder(indent=4,sort_keys=1).encode(data))
	return {"name": name}

  def start_nodes(self, nodes, site, archi):
	return {}

  def stop_nodes(self, nodes, site, archi):
	return {}

  def reset_nodes(self, nodes, site, archi):
	return {}

  def update_nodes(self, firmware, nodes, site, archi):
	firmware = unquote(firmware)
	return {}

  def grab_nodes(self, nodes, site, archi, duration):
	res, err = call("experiment-cli submit -d " + duration
			+ " -l" + ",".join([site, archi, nodes]))
	if err: return err
	return res


class Handler(Reqs, SimpleHTTPRequestHandler):

  def do_GET(self):
	path, args = self.parse_req()
	if not hasattr(self, path):
		return SimpleHTTPRequestHandler.do_GET(self)
	res = eval("self." + path, {"self":self}, {})(**args)
	if type(res) == str:
		return self.error(res)
	self.send_response(200)
	self.send_header("Content-type", "text/plain")
	self.end_headers()
	self.wfile.write(JSONEncoder().encode(res))

  def do_POST(self):
	#print self.rfile.read()
	return self.do_GET()

  def parse_req(self):
	try:
		path, args = self.path.split('?')
		args = dict([kv.split('=')
			for kv in args.strip('&').split('&')])
	except:
		path = self.path
		args = {}
	return [path.strip('/'), args]

  def error(self, msg):
	self.send_response(500)
	self.end_headers()
	self.wfile.write(msg)

  def log_message(self, format, *args):
	pass
 
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	#address_family = socket.AF_INET6
	pass
 
def call(cmd):
	try:
		return JSONDecoder().decode(check_output(cmd.split(" "))), 0
	except ValueError:
		return 0, "invalid json returned by experiment-cli"
	except Exception:
		return 0, "error calling experiment-cli"
	
def main():
	server = ThreadedHTTPServer(('localhost', 8000), Handler)
	server.serve_forever()
 
if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		pass