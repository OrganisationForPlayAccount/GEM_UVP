"""
repos
"""

import os, sys, optparse, json
from subprocess import call

# command-line usage
__version__ = "None"
__copyright__ = "None"
__description__ = "Managing multiple Git repos and its submodules"
__requirements__ = "Requires Python 2.5 or higher"

def parseOptions():
	usage = """
  %prog add <name> <path> - to add repo at <path> under <name> to the list
  %prog add all <path> - to add all repos in subdirectories of <path> to the list
  %prog rm <name> - to remove repo with <name> from the list
  %prog pull <name> - to pull updates for repo <name> (git pull)
  %prog sub_pull <name> - to pull updates for submodules in repo <name> (git submodule update --remote --merge)
  %prog up <name> - to pull updates for repo <name>
  %prog push <name> - to push updates for repo <name> (git push origin master)
  %prog show <name> - show repo details
  %prog list - to list tracked repos

  You can use special name "all" to work on all repos (e.g. %prog pull all)
  """
	parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(), usage=usage, version=__version__, description="%prog " + "version %s. %s. %s" % (__version__, __copyright__, __description__), epilog=__requirements__)

	return parser.parse_args()

ERROR = "ERROR"
REPORT = "REPORT"

def logger(message, mode="INFO"):
	"""
	Simple logger.
	"""

	if mode == ERROR:
		message = "ERROR: " + message
	print(message)

class repos(object):
	"""
	Class to manage list of Git repos and pull changes.
	"""

	def __init__(self):
		super(repos, self).__init__()

		self.preferences = os.path.join(os.path.expanduser("~"), ".repos")
		self.repos = {}
		
		# set up preferences file if it does not exist
		if not os.path.exists(self.preferences):
			open(self.preferences, "a").close() # make an empty file

		# read repo dict
		s = open(self.preferences, "r").read()
		if s:
			self.repos = json.loads(s)

	def save(self):
		"""
		Save changes in JSON preferences.
		"""

		# save updated repo dict
		if self.repos:
			with open(self.preferences, "w") as outfile:
				output = json.dumps(self.repos, sort_keys=True, indent=4, separators=(',', ': '))
				outfile.write(output)

	def check(self, name, verbose=True):
		"""
		Check if record is active repo.
		"""

		if name != "all":
			if name.lower() in self.repos.keys():
				path = self.repos[name.lower()]["path"]
				if os.path.isdir(os.path.join(path, ".git")):
					try:
						start = os.getcwd()
						os.chdir(path)
						os.chdir(start)
						if verbose:
							logger("Repo record '%s' appears to be ok." % name, REPORT)
						return True
					except:
						logger("Repo record '%s' does not point to a valid git repo." % name, ERROR)
						return False
				else:
					logger("Repo record '%s' does not point to a folder." % name, ERROR)
					return False
			else:
				logger("Repo '%s' is not in the list of repos." % name, ERROR)
				return False
		else:
			for name in self.repos:
				self.check(name, verbose=verbose)

	def add(self, name = "", path = ""):
		"""
		Add repo path to list.
		Use name "all" to add all repos in subdirectories and use dictionary names in lowercase as names.
		"""
		
		# check if unique and if it is actual repo
		if name != "all":
			if not name in list(self.repos.keys())+["all"] and not path in self.repos.values():
				if os.path.isdir(os.path.join(path, ".git")):
					logger("Adding repo '%s' at path '%s'." % (name, path))
					self.repos[name.lower()] = {}
					self.repos[name.lower()]["path"] = os.path.abspath(path)
					self.repos[name.lower()]["enabled"] = True
				else:
					logger("There does not seem to be any Git repo at '%s'" % path, ERROR)
			else:
				logger("Repo with name '%s' or path '%s' already exist in the list." % (name, path), ERROR)
		else:
			# add recursively
			for (dirpath, dirnames, filenames) in os.walk(path):
				if ".git" in dirnames:
					name = dirpath.replace("./","").replace("/","_").lower()
					self.add(name, os.path.abspath(dirpath))

	def rm(self, name = ""):
		"""
		Remove repo from the list.
		"""
		
		# remove item(s)
		if name in self.repos:
			logger("Removing '%s' from the list." % name)
			self.repos = {key: value for key, value in self.repos.items() if key != name}
		else:
			logger("Repo '%s' is not in the list." % name, ERROR)

	def enable(self, name = ""):
		"""
		Set enabled status for repo.
		"""

		if self.check(name, verbose=False):
			logger("Enabling '%s'." % name)
			self.repos[name.lower()]["enabled"] = True

	def disable(self, name = ""):
		"""
		Set disabled status for repo.
		"""

		if self.check(name, verbose=False):
			logger("Disabling '%s'." % name)
			self.repos[name.lower()]["enabled"] = False

	def pull(self, name = ""):
		"""
		Pull changes for repo with given name.
		"""

		if self.check(name, verbose=False):
			logger("Updating '%s'." % name)
			self.git("git pull", name)

	def sub_pull(self, name=""):
		"""
		Pull changes for submodules in repo with given name.
		"""

		if self.check(name, verbose=False):
			logger("Updating '%s'." % name)
			self.git("git submodule update --remote --merge", name)

	def up(self, name = ""):
		self.pull(name)

	def push(self, name = ""):
		"""
		Pushing repo with given name.
		"""

		if self.check(name, verbose=False):
			logger("Pushing '%s'." % name)
			self.git("git push origin master", name)

	def show(self, name = ""):
		"""
		Show repo details.
		"""

		if self.check(name, verbose=False):
			enabled = "enabled" if self.repos[name.lower()]["enabled"] else "disabled"
			logger("%s %s (%s):\n  %s" % (name, enabled, self.repos[name.lower()]["path"]))

	def list(self):
		"""
		List of repos with +/- to signify if it is enabled/disabled.
		"""

		for name in self.repos:
			bullet = "+ " if self.repos[name]["enabled"] else "- " # sorry!
			logger(bullet + name)
			print(bullet + name)

	def git(self, command = "git pull", name = ""):
		"""
		Run git command for repo.
		"""

		if self.check(name, verbose=False):
			start = os.getcwd()
			# start = 'https://github.com/OrganisationForPlayAccount/GEM_UVP'
			os.chdir(self.repos[name.lower()]["path"])
			call(command, shell=True)
			os.chdir(start)

	def all(self, func="show"):
		"""
		Call method for all repos.
		"""

		if func in ["pull", "up", "push", "sub_pull"]:
			for repo in [name for name, details in self.repos.items() if details["enabled"]]:
				getattr(self, func)(repo)
		else:
			for repo in self.repos:
				getattr(self, func)(repo)


def main():
	(options, args) = parseOptions()

	if args:
		r = repos()
		try:
			if args[0] in ["check", "rm", "enable", "disable", "push", "up", "pull", "show", "sub_pull"]:
				if (len(args) > 1 and args[1] == "all"):
					r.all(args[0])
				else:
					# run method of this name with args[1] as an attribute
					# getattr(r, args[1],args[0])
					try:
						getattr(r, args[0])(args[1])
					except Exception as exc:
						# getattr(r, args[0])(args[1].replace('\\','/').lower())
						getattr(r, args[0],args[1])
			elif args[0] == "list":
				r.list()
			elif args[0] == "add":
				r.add(args[1], args[2])
			else:
				logger("Unknown argument(s). Add -h for help.", ERROR)
		except Exception as e:
			logger("Bad argument(s). Add -h for help.", ERROR)
		r.save()
	else:
		logger("Add -h for help")

if __name__ == "__main__":
	sys.exit(main())
