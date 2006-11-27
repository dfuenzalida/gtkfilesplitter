#!/usr/bin/env python
""" GtkFileSplitter - A simple graphical interface to a split/contact module
    Author: Denis Fuenzalida, based on code by Anand Pillai
    Licence: GPL - See the 'license.txt' file
"""

import sys

# Version con soporte para i10n :-)
# http://www.async.com.br/faq/pygtk/index.py?req=show&file=faq22.002.htp

import locale, gettext, os, sys

APP = 'filesplitter'
DIR = 'locale'

locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

try:
 	import pygtk
  	pygtk.require("2.0")
except:
  	pass
try:
	import gtk
  	import gtk.glade
except:
	sys.exit(1)


class FileSplitterException(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return str(self.value)

class FileSplitter:
	""" File splitter class """

	def __init__(self):

		# cache filename
		self.__filename = ''
		# number of equal sized chunks
		self.__numchunks = 5
		# Size of each chunk
		self.__chunksize = 0
		# Optional postfix string for the chunk filename
		self.__postfix = ''
		# Program name
		self.__progname = "FileSplitter.py"
		# Action
		self.__action = 0 # split

	def parseOptions(self, args):

		import getopt

		try:
			optlist, arglist = getopt.getopt(args, 'sji:n:', ["split=", "join="])
		except getopt.GetoptError, e:
			print e
			return None

		# Parse cmdline options
		for option, value in optlist:
			if option.lower() in ('-i', ):
				self.__filename = value
			elif option.lower() in ('-n', ):
				# self.__numchunks = int(value)
				self.__chunksize = int(value)
			elif option.lower() in ('-s', '--split'):
				self.__action = 0 # split
			elif option.lower() in ('-j', '--join'):
				self.__action = 1 # combine

		if not self.__filename:
			sys.exit("Error: filename not given")
		
	def do_work(self):
		if self.__action==0:
			self.split()
		elif self.__action==1:
			self.combine()
		else:
			return None
		
	def split(self, display):
		""" Split the file and save chunks
		to separate files """

		print 'Splitting file', self.__filename
		# print 'Number of chunks', self.__numchunks, '\n'
		print 'Chunksize', self.__chunksize
		print '\n'
		
		try:
			f = open(self.__filename, 'rb')
		except (OSError, IOError), e:
			raise FileSplitterException, str(e)

		# bname = (os.path.split(self.__filename))[1]
		bname = self.__filename # Use the same path to put the file pieces
		# Get the file size
		fsize = os.path.getsize(self.__filename)
		# Get size of each chunk
		#self.__chunksize = int(float(fsize)/float(self.__numchunks))
		self.__numchunks = 1 + int(float(fsize)/float(self.__chunksize))

		chunksz = self.__chunksize
		total_bytes = 0

		for x in range(self.__numchunks):
			chunkfilename = bname + '.' + str(x+1) + self.__postfix

			if (display != None):
				display.show_progress((1.0*x)/self.__numchunks)

			# if reading the last section, calculate correct
			# chunk size.
			if x == self.__numchunks - 1:
				chunksz = fsize - total_bytes

			try:
				print 'Writing file',chunkfilename

				# FIX THIS - Use a small buffer to complete chunksz of data!
				data = f.read(chunksz)
				total_bytes += len(data)
				chunkf = file(chunkfilename, 'wb')
				chunkf.write(data)
				chunkf.close()
			except (OSError, IOError), e:
				print e
				continue
			except EOFError, e:
				print e
				break

		if (display != None):
			display.show_progress(1)

		print 'Done.'

	def sort_index(self, f1, f2):

		index1 = f1.rfind('-')
		index2 = f2.rfind('-')
		
		if index1 != -1 and index2 != -1:
			i1 = int(f1[index1:len(f1)])
			i2 = int(f2[index2:len(f2)])
			return i2 - i1
		
	def combine(self):
		""" Combine existing chunks to recreate the file.
		The chunks must be present in the cwd. The new file
		will be written to cwd. """

		import re
		
		print 'Creating file', self.__filename
		
		bname = (os.path.split(self.__filename))[1]
		bname2 = bname
		
		# bugfix: if file contains characters like +,.,[]
		# properly escape them, otherwise re will fail to match.
		for a, b in zip(['+', '.', '[', ']','$', '(', ')'],
						['\+','\.','\[','\]','\$', '\(', '\)']):
			bname2 = bname2.replace(a, b)
			
		# Replaced the '-' with '.' as separator
		chunkre = re.compile(bname2 + '.' + '[0-9]+')
		
		chunkfiles = []
		for f in os.listdir("."):
			print f
			if chunkre.match(f):
				chunkfiles.append(f)


		print 'Number of chunks', len(chunkfiles), '\n'
		chunkfiles.sort(self.sort_index)

		data=''
		for f in chunkfiles:

			try:
				print 'Appending chunk', os.path.join(".", f)
				data += open(f, 'rb').read()
			except (OSError, IOError, EOFError), e:
				print e
				continue

		try:
			f = open(bname, 'wb')
			f.write(data)
			f.close()
		except (OSError, IOError, EOFError), e:
			raise FileSplitterException, str(e)

		print 'Wrote file', bname


#############################################################################

class GtkFileSplitter:
	"""GTK/Glade User interface to FileSplitter"""

	def __init__(self):
		
		#Set the Glade file
		self.gladefile = "gtkfilesplitter.glade"  
	        self.wTree = gtk.glade.XML(self.gladefile) 
		
		#Create our dictionay and connect it
		dic = { "on_fileToSplitButton_clicked" : self.on_fileToSplitButton_clicked,
			"on_cancelButton_clicked"      : self.on_cancelButton_clicked,
			"on_splitFileButton_clicked"   : self.on_splitFileButton_clicked,
			"on_FileSplitGui_destroy"      : gtk.main_quit }
		self.wTree.signal_autoconnect(dic)

		# select the first element in the 'chunksizeComboBox'
		self.wTree.get_widget("chunksizeComboBox").set_active(0)

	def on_cancelButton_clicked(self, widget):

		# Recupero el estado del checkbox 'deleteOriginalFileCheckButton' -- Cambiar nombre!
		self.deleteOriginalFileCheckButton = self.wTree.get_widget("deleteOriginalFileCheckButton")
		print _("Delete orig file: "), self.deleteOriginalFileCheckButton.get_active()
		confirmed = self.confirm(_("you wanna fries with that?"))
		if (confirmed):
			print "confirmed ok"
		else:
			print "not confirmed"
		self.alert(_("cancel pressed"))
		self.info(_("info works ok"))

	def on_fileToSplitButton_clicked(self, widget):
		chooser = gtk.FileChooserDialog(title=_("Select a file to split"), \
				action=gtk.FILE_CHOOSER_ACTION_OPEN,  \
				buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,\
					gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		response = chooser.run()

		if response == gtk.RESPONSE_OK:
			self.fileToSplit = chooser.get_filename()
			print _("file selected: "), chooser.get_filename()
			self.fileToSplitEntry = self.wTree.get_widget("fileToSplitEntry")
			self.fileToSplitEntry.set_text(self.fileToSplit)

		elif response == gtk.RESPONSE_CANCEL:
			print _("no files selected")

		chooser.destroy()

	def on_splitFileButton_clicked(self, widget):

			# chunksizeSpinButton check
			self.chunksizeSpinButton = self.widget("chunksizeSpinButton")
			self.baseChunkSize = int(self.chunksizeSpinButton.get_value())
			print "chunksize 1", self.baseChunkSize

			# ChunksizeComboBox check
			self.chunksizeComboBox = self.widget("chunksizeComboBox")
			self.comboboxMult = (1,1024,1048576)[self.chunksizeComboBox.get_active()]
			print "combobox mult:", self.comboboxMult

			# fileToSplitEntry check
			self.fileToSplitEntry = self.widget("fileToSplitEntry")
			filename = self.fileToSplitEntry.get_text()
			if (len(filename) < 3):
				self.error("Please select a file")
				return
			try:
				fileToSplit = file(filename, "rwb")
				fileToSplit.close()
			except:
				print _("Couldn't open the file '") , filename , _("'")
				self.error (_("Couldn't open the file '") + filename + _("'"))
				return

			# deleteOriginalFileCheckButton check
			self.deleteOriginalFileCheckButton = self.widget("deleteOriginalFileCheckButton")
			print _("Delete orig file: "), self.deleteOriginalFileCheckButton.get_active()

			# md5CheckButton check
			self.md5CheckButton = self.widget("md5CheckButton")
			print _("Generate MD5: "), self.md5CheckButton.get_active()
			
			# All ok, will split the file
			print "all ok"

			# create a FileSplitter and send args to the splitter class
			fileSplitter = FileSplitter()
			splitArgs = ["-i", filename, "-n", self.baseChunkSize * self.comboboxMult, "-s"]
			fileSplitter.parseOptions(splitArgs)

			fileSplitter.split(self) # use self as a display of the task status
			self.info(_("Done"))
			# self.show_progress(0.4)

	def show_progress(self, value):
		# import time
		# time.sleep(0.1)
		print "progress", value
		fr = self.widget("progressBar").get_fraction()
		self.widget("progressBar").set_fraction(value)

		# Fix to the update of a progressbar seen here:
		# http://www.daa.com.au/pipermail/pygtk/2004-December/009318.html
		while gtk.events_pending():
			gtk.main_iteration(gtk.FALSE)

	def widget(self, widgetName):
		return self.wTree.get_widget(widgetName)

	def info(self, message):
		md = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
				gtk.MESSAGE_INFO, gtk.BUTTONS_OK, message)
		md.set_title("Information")
		md.run()
		md.destroy()

	def alert(self, message):
		md = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
				gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, message)
		md.set_title("Alert")
		md.run()
		md.destroy()

	def error(self, message):
		md = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
				gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, message)
		md.set_title("Error")
		md.run()
		md.destroy()

	def confirm(self, message):
		md = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
				gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL, message)
		md.set_title("Please confirm")
		val = md.run()
		print "val", val
		md.destroy()
		if (val == gtk.RESPONSE_OK):
			return True
		else:
			return False

if __name__ == "__main__":
	gtkfilesplitter = GtkFileSplitter()
	gtk.main()
