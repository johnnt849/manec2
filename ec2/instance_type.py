import os
import manec2

class Instance:
	"""
	Class for an AWS EC2 node.
	"""
	def __init__(self, id='', inst_type='', placement='', pr_ip='', pub_ip='0', dns='0',
		last_state='', user='', key=''):
		self.id = id
		self.type = inst_type
		self.placement = placement
		self.pr_ip = pr_ip
		self.pub_ip = pub_ip
		self.dns = dns
		self.last_observed_state = last_state
		self.user = user
		self.key = key

	def set_user_key(self, user_key_tuple):
		"""
		Set the user and key field.
		"""
		self.user, self.key = user_key_tuple

	def serialize(self):
		json_rep = {}
		json_rep['id'] = self.id
		json_rep['type'] = self.type
		json_rep['placement'] = self.placement
		json_rep['pr_ip'] = self.pr_ip
		json_rep['pub_ip'] = self.pub_ip
		json_rep['dns'] = self.dns
		json_rep['last_observed_state'] = self.last_observed_state
		json_rep['user'] = self.user if self.user != None else ''
		json_rep['key'] = self.key if self.key != None else ''

		return json_rep


def deserialize(json_rep):
	inst = Instance(json_rep['id'], json_rep['type'], json_rep['placement'],
		json_rep['pr_ip'], json_rep['pub_ip'], json_rep['dns'],
		json_rep['last_observed_state'], json_rep['user'], json_rep['key'])

	return inst