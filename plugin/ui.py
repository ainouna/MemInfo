# for localized messages  	 
from . import _
#################################################################################
#
#    Plugin for Dreambox-Enigma2
#    version:
VERSION = "1.01"
#    ims (c)2018 as MemInfo
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#################################################################################
from Screens.Screen import Screen
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigYesNo, ConfigSelection, ConfigInteger, config, getConfigListEntry
from Components.ActionMap import ActionMap
from Components.Label import Label
from os import system
from enigma import eTimer, getDesktop
from Components.ProgressBar import ProgressBar
from time import localtime

HD = False
if getDesktop(0).size().width() >= 1280:
	HD = True

config.plugins.MemInfo.enable = ConfigYesNo(default = False)

STARTMEM = []
MAXIMUM = []
MINIMUM = []
START = True

NGETTEXT = False
try:	# can be used ngettext ?
	ngettext("%d minute", "%d minutes", 5)
	NGETTEXT = True
except Exception, e:
	print "[MemInfo] ngettext is not supported:", e

choicelist = []
for i in range(1, 5, 1):
	if NGETTEXT:
		choicelist.append(("%d" % i, ngettext("%d minute", "%d minutes", i) % i))
	else:
		choicelist.append(("%d" % i))
for i in range(5, 61, 5):
	if NGETTEXT:
		choicelist.append(("%d" % i, ngettext("%d minute", "%d minutes", i) % i))
	else:
		choicelist.append(("%d" % i))
config.plugins.MemInfo.repeat_timeout = ConfigSelection(default = "5", choices = choicelist)
config.plugins.MemInfo.screen_info = ConfigYesNo(default = True)
choicelist = []
for i in range(1, 11):
	if NGETTEXT:
		choicelist.append(("%d" % i, ngettext("%d second", "%d seconds", i) % i))
	else:
		choicelist.append(("%d" % i))
config.plugins.MemInfo.timescreen_info = ConfigSelection(default = "5", choices = choicelist)
choicelist = [("0",_("Default")),]
cfg = config.plugins.MemInfo

# display mem, used, free and progressbar
ALL = 0x17

def getMinMax():
	global START
	current = []
	for i, line in enumerate(open('/proc/meminfo','r')):
		s = line.strip().split(None, 2)
		if len(s) == 3:
			name, size, units = s
		elif len(s) == 2:
			name, size = s
			units = ""
		else:
			continue
		current.append((name,size,units))
		if START:
			STARTMEM.append((name,size,units))
			MINIMUM.append((name,size,units))
			MAXIMUM.append((name,size,units))
		else:
			if int(MINIMUM[i][1]) > int(size):
				MINIMUM[i] = (name,size,units)
			if int(MAXIMUM[i][1]) < int(size):
				MAXIMUM[i] = (name,size,units)

	fo = open("/var/log/meminfo.log", "w")
	t = localtime()
	fo.write("Time: %2d:%02d:%02d\n" % (t.tm_hour, t.tm_min, t.tm_sec))
	fo.write("Parameter\t\tStart\tMinimum\tCurrent\tMaximum\n")
	fo.write("---------------------------------------------------------\n")
	for i, x in enumerate(current):
		fo.write("%s%s\t\t%s\t%s\t%s\t%s\t%s\n" % (MINIMUM[i][0], '\t' if len(MINIMUM[i][0])< 8 else '', STARTMEM[i][1], MINIMUM[i][1], x[1], MAXIMUM[i][1], x[2]))
	fo.close()
	START = False

class MemInfoSetupMenu(Screen, ConfigListScreen):
	skin = """
	<screen name="MemInfo" position="center,center" size="500,290" title="" backgroundColor="#31000000" >
		<widget name="config" position="10,10" size="480,200" zPosition="1" transparent="0" backgroundColor="#31000000" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="skin_default/div-h.png" position="0,223" zPosition="2" size="500,2" />
		<widget name="memory" position="10,225" zPosition="2" size="480,25" valign="center" halign="left" font="Regular;20" transparent="1" foregroundColor="white" />
		<widget name="slide" position="10,250" zPosition="2" borderWidth="1" size="480,8" backgroundColor="dark" />
		<ePixmap pixmap="skin_default/div-h.png" position="0,258" zPosition="2" size="500,2" />
		<widget name="key_red" position="0,260" zPosition="2" size="120,30" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="red" />
		<widget name="key_green" position="120,260" zPosition="2" size="120,30" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="green" />
		<widget name="key_yellow" position="240,260" zPosition="2" size="120,30" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="yellow" />
		<widget name="key_blue" position="360,260" zPosition="2" size="120,30" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="blue" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.onChangedEntry = [ ]
		self.list = [ ]
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)
		self.setup_title = _("Setup MemInfo")
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.keyCancel,
				"green": self.keySave,
				"ok": self.keySave,
				"red": self.keyCancel,
				"yellow": self.memoryInfo,
				"blue": self.restartMonitoring,
			}, -2)

		self["key_green"] = Label(_("Save"))
		self["key_red"] = Label(_("Cancel"))
		self["key_yellow"] = Label(_("Info"))
		self["key_blue"] = Label(_("Restart"))

		self["slide"] = ProgressBar()
		self["slide"].setValue(100)
		self["slide"].hide()
		self["memory"] = Label()

		self.runSetup()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("Setup MemInfo") + "  " + VERSION)
		self["memory"].setText(self.getMemory(ALL))

	def runSetup(self):
		self.list = [ getConfigListEntry(_("Enable MemInfo"), cfg.enable) ]
		if cfg.enable.value:
			autotext = _("Auto timeout")
			timetext = _("Time of info message")
			if not NGETTEXT:
				autotext = _("Auto timeout (1-50min)")
				timetext = _("Time of info message (1-10sec)")
			self.list.extend((
				getConfigListEntry(autotext, cfg.repeat_timeout),
				getConfigListEntry(_("Show info on screen"), cfg.screen_info),
				getConfigListEntry(timetext, cfg.timescreen_info),
				getConfigListEntry(_("Display plugin in"), cfg.where),
			))

		self["config"].list = self.list
		self["config"].setList(self.list)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		MemInfoAuto.startMemInfo(self.session)
		self.close()

	def keyCancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		if self["config"].getCurrent()[1] == cfg.enable:
			self.runSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self["config"].getCurrent()[1] == cfg.enable:
			self.runSetup()

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def restartMonitoring(self):
		global START
		START = True
		system("echo 3 > /proc/sys/vm/drop_caches")
		getMinMax()
		self.keySave()

	def getMemory(self, par=0x01):
		try:
			mm = mu = mf = 0
			for line in open('/proc/meminfo','r'):
				line = line.strip()
				if "MemTotal:" in line:
					line = line.split()
					mm = int(line[1])
				if "MemFree:" in line:
					line = line.split()
					mf = int(line[1])
					break
			mu = mm - mf
			self["memory"].setText("")
			self["slide"].hide()
			memory = ""
			if par&0x01:
				memory += "".join((_("Memory:")," %d " % (mm/1024),_("MB"),"  "))
			if par&0x02:
				memory += "".join((_("Used:")," %.2f%s" % (100.*mu/mm,'%'),"  "))
			if par&0x04:
				memory += "".join((_("Free:")," %.2f%s" % (100.*mf/mm,'%')))
			if par&0x10:
				self["slide"].setValue(int(100.0*mu/mm+0.25))
				self["slide"].show()
			return memory
		except Exception, e:
			print "[MemInfo] getMemory FAIL:", e
			return ""

	def memoryInfo(self):
		self.session.openWithCallback(self.afterInfo, MemInfoInfoScreen)

	def afterInfo(self, answer=False):
		self["memory"].setText(self.getMemory(ALL))

class MemInfoAutoMain():
	def __init__(self):
		self.dialog = None
		self.show = False

	def startMemInfo(self, session):
		if not self.dialog:
			self.dialog = session.instantiateDialog(MemInfoAutoScreen)
		self.showDialog()

	def showDialog(self):
		if cfg.screen_info.value:
			self.dialog.show()
			self.show = True
		else:
			self.dialog.hide()
			self.show = False

MemInfoAuto = MemInfoAutoMain()

class MemInfoAutoScreen(Screen):
	if HD:
		skin = """<screen name="MemInfoAutoScreen" position="830,130" zPosition="10" size="250,30" title="MemInfo Status" backgroundColor="#31000000" >
				<widget name="message_label" font="Regular;24" position="0,0" zPosition="2" valign="center" halign="center" size="250,30" backgroundColor="#31000000" transparent="1" />
			</screen>"""
	else:
		skin = """<screen name="MemInfoAutoScreen" position="550,50" zPosition="10" size="150,20" title="MemInfo Status" backgroundColor="#31000000" >
				<widget name="message_label" font="Regular;16" position="0,0" zPosition="2" valign="center" halign="center" size="150,20" backgroundColor="#31000000" transparent="1" />
			</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = MemInfoAutoScreen.skin
		self['message_label'] = Label(_("Starting"))

		self.MemInfoRepeatTimer = eTimer()
		self.MemInfoRepeatTimer.timeout.get().append(self.__run)

		self.showDialogTimer = eTimer()
		self.showDialogTimer.timeout.get().append(self.__endShow)

		self.state = None
		self.onLayoutFinish.append(self.__chckState)
		self.onShow.append(self.__onShowDialog)

	def __onShowDialog(self):
		self.setTitle(_("MemInfo Status"))
		self.showDialogTimer.start(int(cfg.timescreen_info.value) * 1000, True)

	def __chckState(self):
		if self.instance and self.state is None:
			if cfg.enable.value:
				self['message_label'].setText(_("Started"))
			else:
				self['message_label'].setText(_("Stopped"))
			self.state = cfg.enable.value
			if cfg.screen_info.value and MemInfoAuto.dialog:
				MemInfoAuto.dialog.show()
		self.MemInfoRepeatTimer.start(int(cfg.repeat_timeout.value)*60000, True)

	def __run(self):
		if cfg.enable.value:
			getMinMax()
			if self.instance:
				self['message_label'].setText(_("MemInfo saved"))
				if cfg.screen_info.value and MemInfoAuto.dialog:
					MemInfoAuto.dialog.show()
					MemInfoAuto.show = True
		t = localtime()
		print "[MemInfo]", "%2d:%02d:%02d" % (t.tm_hour, t.tm_min, t.tm_sec)
		self.MemInfoRepeatTimer.start(int(cfg.repeat_timeout.value)*60000, True)

	def __endShow(self):
		if MemInfoAuto.show:
			MemInfoAuto.dialog.hide()
			MemInfoAuto.show = False

class MemInfoInfoScreen(Screen):
	if HD:
		skin = """<screen name="MemInfoInfoScreen" position="center,center" zPosition="2" size="620,550" title="MemInfo Info" backgroundColor="#31000000" >
				<widget name="lmemtext" font="Regular;16" position="10,10" size="140,504" zPosition="2" valign="top" halign="left" backgroundColor="#31000000" transparent="1" />
				<widget name="lmemvalue" font="Regular;16" position="150,10" size="100,504" zPosition="2" valign="top" halign="right" backgroundColor="#31000000" transparent="1" />
				<widget name="rmemtext" font="Regular;16" position="370,10" size="140,504" zPosition="2" valign="top" halign="left" backgroundColor="#31000000" transparent="1" />
				<widget name="rmemvalue" font="Regular;16" position="510,10" size="100,504" zPosition="2" valign="top" halign="right" backgroundColor="#31000000" transparent="1" />
				<widget name="pfree" position="240,115" size="70,20" font="Regular;14" zPosition="3" halign="right" backgroundColor="#31000000" transparent="1" />
				<widget name="pused" position="240,390" size="70,20" font="Regular;14" zPosition="3" halign="right" backgroundColor="#31000000" transparent="1" />
				<widget name="slide" position="320,10" size="18,500" render="Progress" zPosition="3" borderWidth="1" orientation="orBottomToTop" />
				<ePixmap pixmap="skin_default/div-h.png" position="0,519" zPosition="2" size="620,2" />
				<widget name="key_red" position="10,522" zPosition="2" size="130,28" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="red" />
				<widget name="key_green" position="130,522" zPosition="2" size="130,28" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="green" />
				<widget name="key_blue" position="390,522" zPosition="2" size="130,28" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="blue" />
			</screen>"""
	else:
		skin = """<screen name="MemInfoInfoScreen" position="center,50" zPosition="2" size="540,500" title="MemInfo Info" backgroundColor="#31000000" >
				<widget name="lmemtext" font="Regular;16" position="10,10" size="120,500" zPosition="2" valign="top" halign="left" backgroundColor="#31000000" transparent="1" />
				<widget name="lmemvalue" font="Regular;16" position="130,10" size="80,500" zPosition="2" valign="top" halign="right" backgroundColor="#31000000" transparent="1" />
				<widget name="rmemtext" font="Regular;16" position="330,10" size="120,500" zPosition="2" valign="top" halign="left" backgroundColor="#31000000" transparent="1" />
				<widget name="rmemvalue" font="Regular;16" position="450,10" size="80,500" zPosition="2" valign="top" halign="right" backgroundColor="#31000000" transparent="1" />
				<widget name="pfree" position="200,100" size="70,20" font="Regular;14" zPosition="3" halign="right" backgroundColor="#31000000" transparent="1" />
				<widget name="pused" position="200,370" size="70,20" font="Regular;14" zPosition="3" halign="right" backgroundColor="#31000000" transparent="1" />
				<widget name="slide" position="280,10" size="18,445" render="Progress" zPosition="3" borderWidth="1" orientation="orBottomToTop" />
				<ePixmap pixmap="skin_default/div-h.png" position="0,465" zPosition="2" size="540,2" />
				<widget name="key_red" position="10,472" zPosition="2" size="130,28" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="red" />
				<widget name="key_green" position="130,472" zPosition="2" size="130,28" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="green" />
				<widget name="key_blue" position="390,472" zPosition="2" size="130,28" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="blue" />
			</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _("MemInfo Info")
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"green": self.getMemInfo,
			}, -2)

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Refresh"))
		self["key_blue"] = Label()

		self['lmemtext'] = Label()
		self['lmemvalue'] = Label()
		self['rmemtext'] = Label()
		self['rmemvalue'] = Label()
		self['pfree'] = Label()
		self['pused'] = Label()

		self["slide"] = ProgressBar()
		self["slide"].setValue(100)

		self.setTitle(_("MemInfo Info") + "  " + VERSION)
		self.onLayoutFinish.append(self.getMemInfo)

	def getMemInfo(self):
		try:
			ltext = rtext = ""
			lvalue = rvalue = ""
			mem = 0
			free = 0
			for i, line in enumerate(open('/proc/meminfo','r')):
				s = line.strip().split(None, 2)
				if len(s) == 3:
					name, size, units = s
				elif len(s) == 2:
					name, size = s
					units = ""
				else:
					continue
				if name.startswith("MemTotal"):
					mem = int(size)
				if name.startswith("MemFree"):
					free = int(size)
				if i < 28:
					ltext += "".join((name,"\n"))
					lvalue += "".join((size," ",units,"\n"))
				else:
					rtext += "".join((name,"\n"))
					rvalue += "".join((size," ",units,"\n"))

			self['lmemtext'].setText(ltext)
			self['lmemvalue'].setText(lvalue)
			self['rmemtext'].setText(rtext)
			self['rmemvalue'].setText(rvalue)

			self["slide"].setValue(int(100.0*(mem-free)/mem+0.25))
			self['pfree'].setText("%.1f %s" % (100.*free/mem,'%'))
			self['pused'].setText("%.1f %s" % (100.*(mem-free)/mem,'%'))

		except Exception, e:
			print "[MemInfo] getMemory FAIL:", e

	def cancel(self):
		self.close()
