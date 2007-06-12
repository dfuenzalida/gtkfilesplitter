#!/usr/bin/env python
# $Id$
#
# GtkFileSplitter - A simple graphical interface to a split/contact module
# Author: Denis Fuenzalida <denis.fuenzalida@gmail.com>, 
# based on code by Anand Pillai, see
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/224800
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os
import sys
import md5

# for i10n support see
# http://www.async.com.br/faq/pygtk/index.py?req=show&file=faq22.002.htp

import locale, gettext

APP = 'gtkfilesplitter'
DIR = '/usr/share/locale'

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

gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
gtk.glade.bindtextdomain(APP, DIR)
gtk.glade.textdomain(APP)


class FileSplitterException(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return str(self.value)

class FileSplitter:
  """ File splitter class """

  def __init__(self):

    # TODO remove some obsolete code from here
    # cache filename
    self.__filename = ''
    # number of equal sized chunks
    self.__numchunks = 5
    # Size of each chunk
    self.__chunksize = 0
    # Optional postfix string for the chunk filename
    self.__postfix = ''
    # Program name
    self.__progname = "gtkfilesplitter.py"
    # Action
    self.__action = 0 # split

    # md5 checksum
    self.__md5 = 0
    # delete original
    self.__delete_original = 0

  def parseOptions(self, args):

    import getopt
    try:
      optlist, arglist = getopt.getopt(args, 'sji:n:m:d:', ["split=", "join="])
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

      # New options - MD5 checksum and remove original file
      elif option.lower() in ('-m'):
        self.__md5 = int(value)    # md5 checksum
      elif option.lower() in ('-d'):
        self.__delete_original = int(value) # delete original

      elif option.lower() in ('-s', '--split'):
        self.__action = 0 # split
      elif option.lower() in ('-j', '--join'):
        self.__action = 1 # combine

    if not self.__filename:
      sys.exit(_("Error: filename not given"))
    
  def do_work(self):
    if self.__action==0:
      self.split()
    elif self.__action==1:
      self.combine()
    else:
      return None
    
  def split(self, display):
    """ Split the file and save chunks to separate files """

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
    import os
    fsize = os.path.getsize(self.__filename)
    # Get size of each chunk
    #self.__chunksize = int(float(fsize)/float(self.__numchunks))
    self.__numchunks = 1 + int(float(fsize)/float(self.__chunksize))

    chunksz = self.__chunksize
    total_bytes = 0
    self.__hash = md5.new()

    # Insane number of chunks? ask the user
    if (self.__numchunks > 100):
      if (display.confirm(_("You're about to create %d files. Are you sure?" \
        % self.__numchunks )) == False):
        return

    for x in range(self.__numchunks):
      chunkfilename = bname + '.' + str(x+1) + self.__postfix

      #if (display != None):
      #  display.show_progress((1.0*x)/self.__numchunks)

      # if reading the last section, calculate correct
      # chunk size.
      if x == self.__numchunks - 1:
        chunksz = fsize - total_bytes

      try:
        print 'Writing file', chunkfilename

	buffersize = 4096 # 4-kilobyte buffer - nice to the md5 buffer too?
	left = chunksz

        chunkf = file(chunkfilename, 'wb')

        # while working
        while (left > 0):
          if (left > buffersize):
            current = buffersize
          else:
            current = left

	  # FIX this hack to cancel an action
	  if (display.splitActionCanceled != False):
            display.splitActionCanceled = False
            display.set_sensitive(True)
	    return

          left = left - current
          data = f.read(current)
          total_bytes += len(data)
          chunkf.write(data)

          if (display != None):
            display.show_progress("progressBar", (1.0*total_bytes)/fsize)

          # update md5 hash if requested
	  if (self.__md5 == 1):
            self.__hash.update(data)

        #data = f.read(chunksz)
        #total_bytes += len(data)
        #chunkf = file(chunkfilename, 'wb')
        #chunkf.write(data)
        chunkf.close()

      except (OSError, IOError), e:
        print e
        continue
      except EOFError, e:
        print e
        break

    if (display != None):
      display.show_progress("progressBar", 1)

    # Try to remove the original file if requested
    if (self.__delete_original == 1):
      try:
        import os
        os.remove(self.__filename)
      except:
        display.alert(_("Could't remove original file"))

    # Try to create a md5 hashfile if requested
    if (self.__md5 == 1):
      try:
        import os
        hashfile = file("%s.md5" % self.__filename, "w")
        bname = (os.path.split(self.__filename))[1]
        hashfile.write("%s  %s" % (self.__hash.hexdigest(), bname))
	hashfile.close()
      except:
        display.alert(_("Could't create md5 hashfile"))

    print 'Done.'

  # Used to sort files while joining file parts
  def sort_index(self, f1, f2):

    print "sorting: %s %s" % (f1, f2)

    index1 = f1.rfind('.') + 1
    index2 = f2.rfind('.') + 1
    
    if index1 != -1 and index2 != -1:
      i1 = int(f1[index1:len(f1)])
      i2 = int(f2[index2:len(f2)])
      # return i2 - i1
      return i1 - i2
    
  def combine(self, display):
    """ Combine existing chunks to recreate the file.
    The chunks must be present in the cwd. The new file
    will be written to cwd. """

    import re
    import os
    
    # remove the last dot and number (/foo/bar.baz.1 -> /foo/bar.baz)
    self.__filename = self.__filename.rsplit(".", 1)[0]
    print 'Creating file', self.__filename
    
    bname = (os.path.split(self.__filename))[1]
    destdir = (os.path.split(self.__filename))[0]
    print "destdir", destdir

    #bname = self.__filename
    bname2 = bname
    
    # bugfix: if file contains characters like +,.,[]
    # properly escape them, otherwise re will fail to match.
    for a, b in zip(['+', '.', '[', ']','$', '(', ')'],
            ['\+','\.','\[','\]','\$', '\(', '\)']):
      bname2 = bname2.replace(a, b)
      
    print "bname2 =", bname2

    # Replaced the '-' with '.' as separator
    chunkre = re.compile(bname2 + '\.' + '[0-9]+')
    
    chunkfiles = []
    #for f in os.listdir((os.path.split(bname2))[0]):
    for f in os.listdir(destdir):
      if chunkre.match(f):
        print "Using file", f
        chunkfiles.append(f)


    print 'Number of chunks', len(chunkfiles), '\n'
    chunkfiles.sort(self.sort_index)

    data=''
    original = open(destdir + os.path.sep + bname, "wb")
    i = 0
    self.__hash = md5.new()

    for f in chunkfiles:

      # open part, read chunks up to 4k, write to original file
      i = i + 1
      print "joining part", (destdir + os.path.sep + f)
      part = open(destdir + os.path.sep + f, "rb")
      reading = True

      while reading:

        # check if join files is cancelled
        if (display.joinActionCanceled != False):
          display.joinActionCanceled = False
          display.set_sensitive(True)
	  return

        data = part.read(4096)
        #print "writing %d bytes" % len(data)
	if (len(data) > 0):
          original.write(data)

          # update md5 hash if requested
	  if (self.__md5 == 1):
            self.__hash.update(data)
        else:
          reading = False

      part.close()
      # update join progressBar status
      display.show_progress("joinProgressBar", float(i)/len(chunkfiles))

    original.close()

    display.show_progress("joinProgressBar", 0)
    print 'Wrote file', bname

    # Verify MD5 checksum against .md5 file
    if (self.__md5 == 1):

      print "opening checksum file", self.__filename + ".md5"
      md5file = open(self.__filename + ".md5", "rb")
      md5text = md5file.readline().rstrip("\n\r")
      md5file.close()
      md5check = "%s  %s" % (self.__hash.hexdigest(), bname)

      if (md5check == md5text):
        display.info(_("Checksum verified OK"))
        
	# try to delete part files if requested and verified ok
        if (self.__delete_original == 1):
          import os
	  for f in chunkfiles:
            try:
              os.remove(f)
            except:
              display.alert(_("Could't remove file part\n'%s'") % f)

      else:
        display.alert(_("Checksum couldn't be verified"))
        print "e '%s'\nf '%s'" % (md5text, md5check)
        return

    # we're done? tell the user
    display.info(_("Done"))

#############################################################################

class GtkFileSplitter:
  """GTK/Glade User interface to FileSplitter"""

  def __init__(self):
    
    #Set the Glade file
    try:
      self.gladefile = "gtkfilesplitter.glade"  
      self.wTree = gtk.glade.XML(self.gladefile, "GtkFileSplitter", APP) 
    except:
      print "glade file not found in current dir, trying installed glade file."
      self.gladefile = "/usr/share/gtkfilesplitter/gtkfilesplitter.glade"  
      self.wTree = gtk.glade.XML(self.gladefile, "GtkFileSplitter", APP) 

    
    #Create our dictionay and connect it
    dic = {
      "on_fileToSplitButton_clicked" : self.on_fileToSplitButton_clicked,
      "on_cancelButton_clicked"      : self.on_cancelButton_clicked,
      "on_splitFileButton_clicked"   : self.on_splitFileButton_clicked,
      "on_split_file_into_parts_activate"   : self.show_split_file_screen,
      "on_join_file_parts_activate"  : self.show_join_parts_screen,
      "on_fileToJoinButton_clicked"  : self.on_fileToJoinButton_clicked,
      "on_cancelJoinButton_clicked"  : self.on_cancelJoinButton_clicked,
      "on_joinButton_clicked"        : self.on_joinButton_clicked,
      "on_about_activate"            : self.show_about_screen,
      "on_FileSplitGui_destroy"      : gtk.main_quit }
    self.wTree.signal_autoconnect(dic)

    # select the first element in the 'chunksizeComboBox'
    self.widget("chunksizeComboBox").set_active(0)
    # deactivate the 'cancel' buttons
    self.widget("cancelButton").set_sensitive(False)
    self.widget("cancelJoinButton").set_sensitive(False)

    # splitActionCanceled
    self.splitRunning = False
    self.splitActionCanceled = False
    self.joinActionCanceled = False

    self.widget("vbox3").hide()

  def on_cancelButton_clicked(self, widget):
    if (self.splitRunning and self.confirm(_("Do you want to cancel?"))):
      self.splitActionCanceled = True
      self.alert(_("Action canceled by user"))

  def on_fileToSplitButton_clicked(self, widget):
    # TODO Set home folder as start folder for this dialog
    chooser = gtk.FileChooserDialog(title=_("Select a file to split"), \
        action=gtk.FILE_CHOOSER_ACTION_OPEN,  \
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,\
          gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    response = chooser.run()

    if response == gtk.RESPONSE_OK:
      self.fileToSplit = chooser.get_filename()
      print _("file selected: "), chooser.get_filename()
      self.fileToSplitEntry = self.widget("fileToSplitEntry")
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
      self.comboboxMult = (1,1024,1024*1024)[self.chunksizeComboBox.get_active()]
      print "combobox mult:", self.comboboxMult

      # fileToSplitEntry check
      self.fileToSplitEntry = self.widget("fileToSplitEntry")
      filename = self.fileToSplitEntry.get_text()
      if (len(filename) < 3):
        self.error(_("Please select a file"))
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
      delete_original = self.deleteOriginalFileCheckButton.get_active()
      print _("Delete orig file: "), delete_original

      # md5CheckButton check
      self.md5CheckButton = self.widget("md5CheckButton")
      md5 = self.md5CheckButton.get_active()
      print _("Generate MD5: "), md5
      
      # All ok, will split the file
      print "all ok"

      # create a FileSplitter and send args to the splitter class
      fileSplitter = FileSplitter()
      splitArgs = ["-i", filename, "-n", self.baseChunkSize * self.comboboxMult, \
		   "-m", md5, "-d", delete_original, "-s" ]
      fileSplitter.parseOptions(splitArgs)

      # Deactivate controls while working
      self.set_sensitive(False)

      # delegate splits the file
      self.splitRunning = True
      fileSplitter.split(self) # use self as a display of the task status
      self.splitRunning = False
      self.info(_("Done"))

      # Activate Controls and reset progress
      self.set_sensitive(True)
      self.show_progress("progressBar", 0)

  def on_fileToJoinButton_clicked(self, widget):
    # TODO Set home folder as start folder for this dialog
    chooser = gtk.FileChooserDialog(title=_("Select the first file to join"), \
        action=gtk.FILE_CHOOSER_ACTION_OPEN,  \
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,\
          gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    response = chooser.run()

    if response == gtk.RESPONSE_OK:
      self.fileToJoin = chooser.get_filename()
      self.fileToJoinEntry = self.widget("fileToJoinEntry")
      self.fileToJoinEntry.set_text(self.fileToJoin)

    elif response == gtk.RESPONSE_CANCEL:
      print _("no files selected")

    chooser.destroy()

  def on_joinButton_clicked(self, widget):
    # TODO check join options
    self.fileToJoinEntry = self.widget("fileToJoinEntry")
    filename = self.fileToJoinEntry.get_text()

    if (len(filename) < 3):
      self.error(_("Please select a file"))
      return
    try:
      fileToSplit = file(filename, "rb")
      fileToSplit.close()
    except:
      self.error (_("Couldn't open the file '%s'") % filename )
      return

    # Check verifyMD5Button
    md5 = self.widget("verifyMD5Button").get_active()

    # Check deletePartsButton
    delete_original = self.widget("deletePartsButton").get_active()

    fileSplitter = FileSplitter()
    splitArgs = ["-i", filename, "-m", md5, "-d", delete_original, "-j" ]
    fileSplitter.parseOptions(splitArgs)
    fileSplitter.combine(self)

  def on_cancelJoinButton_clicked(self, widget):
    if (self.joinRunning and self.confirm(_("Do you want to cancel?"))):
      self.joinActionCanceled = True
      self.alert(_("Action canceled by user"))

  def show_about_screen(self, value):
    self.info(_("Simple File Splitter/Joiner version 0.1\nby Denis Fuenzalida <denis.fuenzalida@gmail.com>\n\nhttp://code.google.com/p/gtkfilesplitter"))

  def show_split_file_screen(self, value):
    self.widget("vbox2").show()
    self.widget("vbox3").hide()

  def show_join_parts_screen(self, value):
    if (self.splitRunning == False):
      self.widget("vbox2").hide()
      self.widget("vbox3").show()

  def set_sensitive(self, value):
    # split file widgets
    self.widget("chunksizeSpinButton").set_sensitive(value)
    self.widget("chunksizeComboBox").set_sensitive(value)
    self.widget("fileToSplitButton").set_sensitive(value)
    self.widget("fileToSplitEntry").set_sensitive(value)
    self.widget("deleteOriginalFileCheckButton").set_sensitive(value)
    self.widget("md5CheckButton").set_sensitive(value)
    self.widget("splitFileButton").set_sensitive(value)

    # join file widgets
    self.widget("fileToJoinEntry").set_sensitive(value)
    self.widget("fileToJoinButton").set_sensitive(value)
    self.widget("verifyMD5Button").set_sensitive(value)
    self.widget("deletePartsButton").set_sensitive(value)
    self.widget("joinButton").set_sensitive(value)

    # Cancelbutton == !value
    self.widget("cancelButton").set_sensitive(not value)
    self.widget("cancelJoinButton").set_sensitive(not value)

  def show_progress(self, progressBarName, value):
    self.widget(progressBarName).set_fraction(value)
    if (value > 0):
      text = _("Working ... %d%c done") % ( int(100*value), '%')
      self.widget(progressBarName).set_text(text)
    else:
      self.widget(progressBarName).set_text('')

    # Fix to the update of a progressbar as seen here:
    # http://www.daa.com.au/pipermail/pygtk/2004-December/009318.html
    while gtk.events_pending():
      gtk.main_iteration(gtk.FALSE)

  def widget(self, widgetName):
    return self.wTree.get_widget(widgetName)

  def info(self, message):
    md = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
        gtk.MESSAGE_INFO, gtk.BUTTONS_OK, message)
    md.set_title(_("Information"))
    md.run()
    md.destroy()

  def alert(self, message):
    md = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
        gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, message)
    md.set_title(_("Alert"))
    md.run()
    md.destroy()

  def error(self, message):
    md = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
        gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, message)
    md.set_title(_("Error"))
    md.run()
    md.destroy()

  def confirm(self, message):
    md = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
        gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL, message)
    md.set_title(_("Please confirm"))
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
