#! /usr/bin/env python

#  sj4000.py - SJCAM SJ4000 Camara support functions
# 
#  Adam Laurie <adam@algroup.co.uk>
# 
#  This code is copyright (c) Adam Laurie 2015, All rights reserved.
#
# note camera firmware seems to be very buggy!
# if you send an invalid command parameter, you will likely crash the camera
# and it will stop talking to you. power on/off is the only recourse!

import os
import requests
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import subprocess

# todo:
# command 3027 gets random number? - e.g. returns <Value>89770999</Value>
# 3002 lists what appears to be a bunch of other commands - need to explore!
# http://192.168.1.254/?custom=1&cmd=1003 - returns number -e.g. 4694 - what is it?
# find a way to read current wifi name and password

class camera:
	DEBUG= False
	ip= '192.168.1.254'
	DEVNULL= None
	MODE_PHOTO= '0'
	MODE_MOVIE= '1'
	START= '1'
	STOP= '0'
	# config commands with configurable parameters
	CONFIG=		{
			'1002':['Photo_Image_Size', '12M_4032x3024', '10M_3648x2736', '8M_3264x2448', '5M_2592x1944', '3M_2048x1536', '2MHD_1920x1080', 'VGA_640x480', '1.3M_1280x960'],
			'1006':['Sharpness', 'Strong', 'Normal', 'Soft'],
			'1007':['White_Balance', 'Auto', 'Daylight', 'Cloudy', 'Tungsten', 'Flourescent'],
			'1008':['Colour', 'Colour', 'B/W', 'Sepia'],
			'1009':['ISO', 'Auto', '100', '200', '400'],
			'1011':['Anti_Shaking', 'Off', 'On'],
			'2002':['Movie_Resolution', '1080FHD_1920x1080', '720P_1280x720_60fps', '720P_1280x720_30fps', 'WVGA_848x480', 'VGA_640x480'],
			'2003':['Cyclic_Record', 'Off', '3_Minutes', '5_Minutes', '10_Minutes'],
			'2004':['HDR/WDR', 'Off', 'On'],
			'2005':['Exposure', '+2.0', '+5/3', '+4/3', '+1.0', '+2/3', '+1/3', '+0.0', '-1/3', '-2/3', '-1.0', '-4/3', '-5/3', '-2.0'],
			'2006':['Motion_Detection', 'Off', 'On'],
			'2007':['Audio', 'Off', 'On'],
			'2008':['Date_Stamping', 'Off', 'On'],
			'2019':['Videolapse','Off', '1_Second', '2_Seconds', '5_Seconds', '10_Seconds', '30_Seconds', '1_Minute'],
			'3007':['Auto_Power_Off', 'Off', '3_Minutes', '5_Minutes', '10_Minutes'],
			'3008':['Language', 'English', 'French', 'Spanish', 'Polish', 'German', 'Italian', 'Unknown_1', 'Unknown_2', 'Russian', 'Unknown_3', 'Unknown_4', 'Unknown_5', 'Portugese'],
			'3010':['Format', 'Cancel', 'OK'],
			'3011':['Default_Setting', 'Cancel', 'OK'],
			'3025':['Frequency', '50Hz', '60Hz'],
			'3026':['Rotate', 'Off', 'On'],
			}
	# commands with no or free-form string parameters
	COMMANDS= 	{
			'CONFIG':'3014',
			'DATE':'3005',
			'MODE_PHOTO_MOVIE':'3001',
			'SNAP':'1001',
			'START_STOP':'2001',
			'STATUS_MODE':'3016',
			'TIME':'3006',
			'WIFI_NAME':'3003',
			'WIFI_PW':'3004',
			}

	def get_config_by_name(self, config):
		for conf in self.CONFIG:
			if self.CONFIG[conf][0].upper() == config.upper():
				return conf
		return None

	def get_file(self, path, f):
		r= requests.get("http://" + self.ip + f, stream=True)
		fname= f.split('/')[-1:][0]
		outfile= open(path + fname, "wb")
		outfile.write(r.content)
		outfile.close()
		r.close()
		return True, fname

	def get_mode(self):
		ret, info= self.send_command('STATUS_MODE')
		if ret:
			return True, self.get_status(info)
		else:
			return False, info

	# extract a single status value from response to 'send_command'
	def get_status(self, response):
		tree= ElementTree.fromstring(response.text)
		try:
			return tree.find('Status').text
		except:
			return None

	def http_test(self):
		try:
			resp= requests.get('http://' + self.ip, timeout= 1)
		except:
			return 'HTTP socket CLOSED'
		if resp.status_code == 200:
			return 'HTTP socket OPEN'
		return 'HTTP socket open but returned: %d' % resp.status_code

	def ping(self):
		ret= subprocess.Popen(["ping", "-c1", "-W 1", self.ip],stdout= subprocess.PIPE).communicate()[0]
		if ret.find(' 0%') >= 0:
			return 'Host is UP'
		return 'Host is DOWN'

	def print_config_help(self, parameter):
		if parameter:
			print '    %s:' % self.CONFIG[self.get_config_by_name(parameter)][0],
			print ', '.join([i for i in self.CONFIG[self.get_config_by_name(parameter)][1:]])
		else:
			for item in self.CONFIG:
				print '    %s:' % self.CONFIG[item][0],
				print ', '.join([i for i in self.CONFIG[item][1:]])

	def print_config(self):
		ret, info= self.send_command('CONFIG')
		if ret:
			tree= ElementTree.fromstring(info.text)
			# sj4000 XML is not properly nested, so we need to kludge it
			print
			for branch in tree:
				if branch.tag == 'Status':
					try:
						print self.CONFIG[current][int(branch.text) + 1]
					except:
						print branch.text
				else:
					current= branch.text
					try:
						print '    %s:' % self.CONFIG[branch.text][0],
					except:
						print '    %s:' % branch.text,
		else:
			print "    Couldn't read config!"
			return False
		return True

	def print_directory(self):
		for thing in "PHOTO", "MOVIE":
			try:
				resp= requests.get("http://" + self.ip + "/DCIM/%s" % thing, timeout= 5)
			except:
				return False, 'Timeout!'
			if resp.status_code != 200:
				return False, resp
			soup= BeautifulSoup(resp.text, 'html.parser')
			# fixme: we should be able to parse the directory listing better...
			#table= soup.find('table')
			#for row in table.find_all('tr'):
				#print row
			#	for cell in row.find_all('td'):
			#		print cell
			print
			print '    %s:' % thing
			print
			# every second link is a delete ref
			count= 0
			for f in soup.find_all('a'):
				count += 1
				if not count % 2:
					continue
				#print f
				print '     ', f.get('href')
		

	# send command by name or number
	def send_command(self, command, param= None, str_param= None):
		try:
			full_command= 'http://' + self.ip + '/?custom=1&cmd=' + self.COMMANDS[command]
		except:
			full_command= 'http://' + self.ip + '/?custom=1&cmd=' + command
		if param:
			full_command += '&par=' + param
		if str_param:
			full_command += '&str=' + str_param
		if self.DEBUG:
			print 'DEBUG: >>>', full_command
		try:
			resp= requests.get(full_command, timeout= 5)
			if self.DEBUG:
				print 'DEBUG: <<<', resp
		except:
			return False, 'Timeout!'
		if resp.status_code == 200:
			return True, resp
		else:
			return False, resp

	def set_config(self, param, val):
		config= self.get_config_by_name(param)
		if not config:
			return False, 'No such parameter'
		found= False
		for num, item in enumerate(self.CONFIG[config]):
			if item.upper() == val.upper():
				found= True
				num -= 1
				break
		if not found:
			return False, 'Invalid value for parameter'
		return self.send_command(config, param= str(num))

	def set_date(self, date):
		return self.send_command('DATE', str_param= date)

	def set_mode(self, mode):
		if mode == 'PHOTO':
			ret, info= self.send_command('MODE_PHOTO_MOVIE', param= self.MODE_PHOTO)
			if not ret:
				return ret, info
			switch= self.MODE_PHOTO
		elif mode == 'TPHOTO':
			return False, 'Not yet implemented'
		elif mode == 'MOVIE':
			ret, info= self.send_command('MODE_PHOTO_MOVIE', param= self.MODE_MOVIE)
			if not ret:
				return ret, info
			switch= self.MODE_MOVIE
		elif mode == 'TMOVIE':
			return False, 'Not yet implemented'
		else:
			return False, 'Unrecognised MODE'
		# wait for mode switch
		while 42:
			stat, mode= self.get_mode()
			if stat:
				if mode == switch:
					return True, None
			else:
				return False, mode

	def set_time(self, time):
		return self.send_command('TIME', str_param= time)

	def set_wifi_name(self, name):
		return self.send_command('WIFI_NAME', str_param= name)

	def set_wifi_pw(self, pw):
		return self.send_command('WIFI_PW', str_param= pw)

	# take a picture, optionally store it, and return the DCIM filename
	def snap(self, path):
		ret, info= self.send_command('SNAP')
		if not ret:
			return ret, info
		try:
			resp= requests.get("http://" + self.ip + "/DCIM/PHOTO", timeout= 5)
		except:
			return False, 'Timeout!'
		if resp.status_code != 200:
			return False, resp
		soup= BeautifulSoup(resp.text, 'html.parser')
		f= soup.find_all('a')[len(soup.find_all('a')) - 2].get('href')
		fname= f.split('/')[-1:][0]
		if path:
			return self.get_file(path, f)
		return True, fname

	def start_stop_movie(self, action):
		return self.send_command('START_STOP', param= action)

	def stream(self):
		if not self.DEVNULL:
			self.DEVNULL= open(os.devnull, 'wb')
		subprocess.Popen(['vlc', 'rtsp://' + self.ip + '/sjcam.mov'], stdout= self.DEVNULL, stderr= subprocess.STDOUT)

