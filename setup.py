from setuptools import setup

setup  (name        = 'sjcam',
        version     = '1.0',
        description = "SJCAM WiFi Camera CLI utility",
        author = 'Adam Laurie',
        author_email = 'adam@algroup.co.uk',
	url='https://github.com/AdamLaurie/sjcam',
        scripts = ['sjcam', 'sj4000.py'],
	install_requires = [ 'beautifulsoup4', 'requests', 'lxml' ]
       )
