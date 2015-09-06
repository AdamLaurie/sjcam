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
import sys
import requests
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import subprocess
import math

# todo:
# command 3027 gets random number? - e.g. returns <Value>89770999</Value>
# 3002 lists what appears to be a bunch of other commands - need to explore!
# http://192.168.1.254/?custom=1&cmd=1003 - returns number -e.g. 4694 - what is it?
# find a way to read current wifi name and password
# what does camera mode 2 do?
# what is data from cmd 3019?

class camera:
	DEBUG= False
	ip= '192.168.1.254'
	DEVNULL= None
	MODE_PHOTO= '0'
	MODE_MOVIE= '1'
	MODE_TPHOTO= '4'
	MODE_TMOVIE= '3'
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
			'DISK_SPACE':'3017',
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

	def get_disk_space(self):
		ret, info= self.send_command('DISK_SPACE')
		if not ret:
			return ret, info
		space= self.get_element(info, 'Value')
		if space:
			return True, int(space)
		return False, 0

	# extract a single element from response to 'send_command'
	def get_element(self, response, element):
		tree= ElementTree.fromstring(response.text)
		try:
			return tree.find(element).text
		except:
			return None

	def get_file(self, path, f):
		ret, flen= self.print_directory(quiet= True, find= f)
		if not ret:
			return False, "Could not read directory"
		if not flen:
			return False, "Could not get file length"
		r= requests.get("http://" + self.ip + f, stream=True)
		fname= f.split('/')[-1:][0]
		outfile= open(path + fname, "wb")
		gotlen= 0
		for chunk in r.iter_content(chunk_size= 2048 * 1024):
			if chunk: # filter out keep-alive new chunks
				gotlen += len(chunk)
				print '    %s of %s    \r' % (self.human_readable(gotlen), flen),
				sys.stdout.flush()
				outfile.write(chunk)
		outfile.close()
		r.close()
		return True, fname

	# return file length and creation date/time from html table
	def get_file_details(self, cells, filename):
		for x in range(len(cells)):
			try:
				entry= cells[x].findChildren('a')[0].get('href')
			except:
				continue
			if entry == filename:
				return cells[x+1].string.strip(), cells[x+2].string.strip().split(' ')[0], cells[x+2].string.strip().split(' ')[1]
		return None, None, None

	def get_mode(self):
		ret, info= self.send_command('STATUS_MODE')
		if ret:
			return True, self.get_element(info, 'Status')
		else:
			return False, info

	# not sure what's going on here, but we seem to be able to grab a low res image
	# when in PHOTO mode
	def get_preview(self):
		r= requests.get('http://' + self.ip + ':8192/', stream=True)
		if not r.raw.readline().strip() == "--arflebarfle":
			return False, 'Preview image not found!'
		size= 0
		# 4 lines of header including blank
		for x in range(3):
			header= r.raw.readline()
			if header.startswith('Content-length:'):
				size= int(header.split(' ')[1])
		if not size:
			return False, 'Could not determine image size!'
		data= r.raw.read(size)
		r.close()
		return True, data

	def http_test(self):
		try:
			resp= requests.get('http://' + self.ip, timeout= 1)
		except:
			return 'HTTP socket CLOSED'
		if resp.status_code == 200:
			return 'HTTP socket OPEN'
		return 'HTTP socket open but returned: %d' % resp.status_code

	def human_readable(self, num):
		units= ['B','KB','MB','GB','TB','PB','EB','ZB','YB']
		p= math.floor(math.log(num, 2)/10)
		return "%.2f %s" % (num / math.pow(1024, p), units[int(p)])

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
			return False, "Couldn't read config!"
		return True, None

	def print_directory(self, quiet= False, find= None):
		for thing in "PHOTO", "MOVIE":
			if not quiet:
				print
				print '    %s:' % thing
				print
			try:
				resp= requests.get("http://" + self.ip + "/DCIM/%s" % thing, timeout= 5)
			except:
				return False, 'Timeout!'
			if resp.status_code != 200:
				return False, resp
			soup= BeautifulSoup(resp.text)
			try:
				table= soup.findChildren('table')[0]
			except:
				break
			rows= table.findChildren(['tr'])
			for row in rows:
				cells= row.findChildren('td')
				for cell in cells:
					if cell.findChildren('a'):
						entry= cell.findChildren('a')[0].get('href')
						if entry.find('del') > 0:
							continue
						fsize, fdate, ftime= self.get_file_details(cells, entry)
						if find == entry:
							return True, fsize
						if not quiet:
							print '      %s    % 10.10s    %s    %s' % (entry, fsize, fdate, ftime)
		if not quiet:
			print
			print '    SD Card space remaining:',
			ret, sd= self.get_disk_space()
			if not ret:
				return ret, sd
			if sd == 0:
				print 'None!'
			else:
				print self.human_readable(sd)

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
			ret, info= self.send_command('MODE_PHOTO_MOVIE', param= self.MODE_TPHOTO)
			if not ret:
				return ret, info
			switch= self.MODE_TPHOTO
		elif mode == 'MOVIE':
			ret, info= self.send_command('MODE_PHOTO_MOVIE', param= self.MODE_MOVIE)
			if not ret:
				return ret, info
			switch= self.MODE_MOVIE
		elif mode == 'TMOVIE':
			ret, info= self.send_command('MODE_PHOTO_MOVIE', param= self.MODE_TMOVIE)
			if not ret:
				return ret, info
			switch= self.MODE_TMOVIE
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

