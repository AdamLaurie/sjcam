# sjcam

A python CLI tool for controlling SJCAM WiFi Sports Cameras

# installation

As far as I know, the only dependancy not catered for by the installation script is VideoLAN, used for viewing a live stream from the camera. To install under Ubuntu:

  sudo apt-get install vlc

For other ditros, visit the home page for more info:

  http://www.videolan.org/

To install sjcam:

  sudo python ./setup.py install

# usage

Running the script with no arguments will show a help screen:

  sjcam

  Usage: /usr/local/bin/sjcam &gt;COMMAND&lt; [ARG(s)] [&gt;COMMAND&lt [ARG(s)] ...]

    Commands:

       CONFIG                                 Show camera config and status
       DATE <YYYY-MM-DD>                      Set camera date
       DIR                                    Show PHOTO and MOVIE directory listing
       GET <FILE>                             Copy file from camera to local storage
       IP <ADDRESS>                           Set IP address (default 192.168.1.254)
       MODE <[T]MOVIE | [T]PHOTO>             Set camera to [TIMED] MOVIE or PHOTO mode
       PASS <PASSWORD>                        Set WiFi PASSWORD (will not take effect until disconnect/reconnect)
       PATH <FILE PATH>                       Set PATH for saving snapshots (default ./)
       PING                                   Check camera is visible and connectable on network
       SET <PARAMETER> <VALUE>                Set camera config ('?' to list parameters and/or values)
       SYNC                                   Synchronise camera clock & date with host
       [G|V]SNAP                              Take a snapshot and optionally [V]iew and/or [G]et it (auto switch to PHOTO mode)
       SSID <SSID>                            Set WiFi SSID (will not take effect until disconnect/reconnect)
       STREAM                                 View live video stream (auto switch to MOVIE mode)
       TIME <HH:MM:SS>                        Set camera clock

    Commands will be executed sequentially and must be combined as appropriate.

Most commands are self explanatory.

# viewing camera config settings

  sjcam config

    Camera config:

      Movie_Resolution: 720P_1280x720_60fps
      Cyclic_Record: Off
      HDR/WDR: On
      1012: 0
      Motion_Detection: On
      Audio: Off
      Date_Stamping: On
      2010: 3
      Videolapse: Off
      Photo_Image_Size: 8M_3264x2448
      1005: 0
      Sharpness: Strong
      White_Balance: Auto
      Colour: Colour
      ISO: 100
      Exposure: +0.0
      Anti_Shaking: On
      Frequency: 60Hz
      Rotate: Off
      Default_Setting: Cancel
      Format: Cancel
      Auto_Power_Off: Off
      3003: 0
      3004: 0
      Language: English

Parameter names and values are translated to a keyword format that is easy to cut & paste for SET commands. Parameters that have not yet been reverse engineered or cannot be changed using the SET command are shown as their original numeric value.

# setting camera parameters

Changeable parameters can be set using the SET command, followed by parameter name and value. To get a full list of paramaters and values, use:

  sjcam set ? ?

    SET config help:

      Default_Setting: Cancel, OK
      HDR/WDR: Off, On
      Language: English, French, Spanish, Polish, German, Italian, Unknown_1, Unknown_2, Russian, Unknown_3, Unknown_4, Unknown_5, Portugese
      Rotate: Off, On
      Format: Cancel, OK
      Exposure: +2.0, +5/3, +4/3, +1.0, +2/3, +1/3, +0.0, -1/3, -2/3, -1.0, -4/3, -5/3, -2.0
      Frequency: 50Hz, 60Hz
      Auto_Power_Off: Off, 3_Minutes, 5_Minutes, 10_Minutes
      Anti_Shaking: Off, On
      Movie_Resolution: 1080FHD_1920x1080, 720P_1280x720_60fps, 720P_1280x720_30fps, WVGA_848x480, VGA_640x480
      Cyclic_Record: Off, 3_Minutes, 5_Minutes, 10_Minutes
      Videolapse: Off, 1_Second, 2_Seconds, 5_Seconds, 10_Seconds, 30_Seconds, 1_Minute
      Motion_Detection: Off, On
      Audio: Off, On
      ISO: Auto, 100, 200, 400
      Colour: Colour, B/W, Sepia
      White_Balance: Auto, Daylight, Cloudy, Tungsten, Flourescent
      Sharpness: Strong, Normal, Soft
      Date_Stamping: Off, On
      Photo_Image_Size: 12M_4032x3024, 10M_3648x2736, 8M_3264x2448, 5M_2592x1944, 3M_2048x1536, 2MHD_1920x1080, VGA_640x480, 1.3M_1280x960

To get the list of values for a specific parameter, use e.g.:

  sjcam set Photo_Image_Size ?

    SET config help:

      Photo_Image_Size: 12M_4032x3024, 10M_3648x2736, 8M_3264x2448, 5M_2592x1944, 3M_2048x1536, 2MHD_1920x1080, VGA_640x480, 1.3M_1280x960

To change a parameter, specify the parameter name and new value:

  sjcam set Photo_Image_Size 2MHD_1920x1080

    Setting Photo_Image_Size to 2MHD_1920x1080
      OK

# known issues / further development

Since there is no published API for this type of camera, it was reverse engineered by sniffing packets from the Android app. Not all settings visible on the camera can be changed from the app, so some things are still unknown or may be incorrect.

There are several tools out there for doing this, and I used one that allows sniffing of only the local network traffic without rooting the phone:

  https://play.google.com/store/apps/details?id=app.greyshirts.sslcapture&hl=en_GB

It's a bit clunky and doesn't have any kind of filtering support, so you have to wade through a lot of irrelevant data to find the packet you're looking for, but it was easy to install and run and got the ball rolling, so I stuck with it.

I only have access to the SJ4000 camera, so it's possible other cameras behave completely differently - please let me know your experiences!

Commands can be tested by sending them directly to the camera using a browser. For example, to change the WiFi name:

  http://192.168.1.254/?custom=1&cmd=3003&str=%22MyShinySJ4000%22

If you find any new or useful commands, please email me datails, or send me a pull request. I have commented some as yet unexplored options in sj4000.py

At some point, it would be nice to have a GUI.

Need to add GET option to video start/stop...

Need to fix camera directory to show file sizes, dates etc. (strange problem with BS4)

