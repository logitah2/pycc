class Plugin(object):
	'''This class is the base of all Plugins
	
	It defines methods that all plugins need and use
	Every plugin will be derived from this class

PluginClass.registeredName 
	is the string all commands for the plugin start with.
PluginClass.priority 
	is the priority relative to other plugins.
	PluginClass.recvCommand is called first for Plugins with 
	higher priority.
'''
	#names under which the plugins wants to be registered
	registeredCommands=None
	priority=0


	#any plugin will be bound to a PyCCManager at its initialisation
	def __init__(self, manager, backend, config):
		'''all Plugins are initialized with a manager class'''
		self.backend = backend
		self.manager = manager
		self.PyCCManager = manager
		self.config = config


	def init(self):
		pass


	#This method sends a command to the PyCCManager
	def sendCommand(self, command, data):
		'''send a command to the PyCCManager - not yet ready for use'''
		self.PyCCManager.send(command, data)

	#Any command send from the PyCCManager will be here
	def recvCommand(self, con):
		'''all commands for this plugin are passed to this function

con is of type backend.connection.PyCCPackage
'''
		raise NotImplementedError('if you see this you forgot to implement \
recvComment(self, con) in your Plugin.')

	#tell the register that you want be registered with it
	def registerInManager(self):
		'''register this Plugin in the manager

this method should not be overwritten'''
		comm= self.registeredCommands
		if type(comm) is str:
			self.PyCCManager.registerPlugin(comm, self,\
							self.priority)
		elif hasattr(comm, '__iter__'):
			reg = self.PyCCManager.registerPlugin
			for comm in comm:
				reg(comm, self, self.priority)
		elif comm is None:
			pass		
		else:
			raise ValueError('invalid value for attribute registeredCommands {0}'.format(comm))

	def startup(self):
		pass

	def shutdown(self):
		'''this method shuts down the Plugin

It is called after all commands are handled.
The Plugin will not be used afterwards.
'''
		pass

class EasyPlugin(Plugin):
	'''This class is an advanced Plugin class for easier plugins

	Every command_* will be used as a registered command
	Every plugin will be derived from this class

'''

	#any plugin will be bound to a PyCCManager at its initialisation
	def __init__(self, manager, backend, config):
		'''all Plugins are initialized with a manager class'''
		Plugin.__init__(self, manager, backend, config)
		self._simplePlugin_commands = {}

	#tell the register that you want be registered with it
	def registerInManager(self):
		'''register this Plugin in the manager

this method should not be overwritten'''
		if type(self) == EasyPlugin: # don't register yourself
			return

		for element in dir(self):
			if not element.startswith('command'):
				continue
			command, name = element.split('_',1)
			command = list(command[7:]) # get attributes
			self.manager.registerPlugin(name, self, self.priority)
			self._simplePlugin_commands[name] = (element, command)


	#Any command send from the PyCCManager will be here
	def recvCommand(self, package):
		'''all commands for this plugin are passed to this function

con is of type backend.connection.PyCCPackage
'''
		for command in self._simplePlugin_commands:
			if package.command.startswith(command):
				call, flags =self._simplePlugin_commands[command]
				if 'U' in flags: # data must be unicode
					try:
						package.data = package.data.decode('utf8')
					except UnicodeError:
						package.data = 'data have to be utf8'
						package.connection.sendError(package)
				if 'A' in flags: # parse attributes
					callargs = [package]
					args = package.command.split(' ')
					package.command = args[0]
					callargs = [package] + args[1:]
					try:
						result=getattr(self,call)(*callargs)
					except TypeError: # wrong arguments
						package.data = 'wrong arguments'
						package.connection.sendError(package)
				else:
					result=getattr(self,call)(package)
				if 'R' in flags:
					if type(result) is str or type(result) is bytearray:
						package.data = result
						package.connection.sendResponse(package)





class PyCCPluginToBackendInterface(object):
	
	def __init__(self,manager,server):
		self._manager = manager
		self._server = server

	def getNodeIdForUser(self):
		pass

	def getNodeConnections(self,nodeId):
		for connection in self._server.getConnectionList(nodeId):
			yield connection

	def getNodeId(self):
		return self._server.getNodeId()
