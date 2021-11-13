# History

## Week 1
1. Download OS from ```https://www.ev3dev.org/downloads/```
2. Need to create a bootable SD card.
3. To install the OS I follow those instructions ```http://docs.ev3dev.org/en/ev3dev-stretch/getting-started/ev3.html#installing-ev3dev```
4. I flashed the .iso to SD card, then I insert the SD card and installation started.
5. Unfortunately we can't connect to the device via SSH (no Wi-Fi), but we can connect via Bluetooth ```https://www.ev3dev.org/docs/tutorials/```
6. Via the Bluetooth connection we can get Internet, then connect via SSH
```shell script
$ ssh robot@ev3dev.local # password: maker
```

7. Programming language available: ```https://www.ev3dev.org/docs/programming-languages/```
8. To send a file:
```shell script
$ scp Hello.class robot@ev3dev.local:res # res is a folder
```
9. Finally, I launch a Python script to print ```Hello World!```
10. <p>Commit <a href="https://gaufre.informatique.univ-paris-diderot.fr/petic/idjellidaine-petic-plong-2020/commit/148f5e3927685c535ca3d141ec44e79ef2ff4c8f" rel="nofollow">148f5e39</a></p>

## Week 2

1. Need to launch at less one engine and get RGB from camera
2. I suggest taking a look on:  ```https://github.com/ev3dev/ev3dev-lang-python```.
3. I created a Makefile to:
    - **send** - send all files
    - **con** - connect via ssh
    - **id** - to copy your keys to the target server and avoid typing password

## Week 4

At the moment we can launch engines.

1. Get color from the sensor
2. Docs is here ```https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/stable/sensors.html#ev3dev2.sensor.Sensor```
3. There are consts for color provides by EV3
4. I found a way to get closest tuple RGB from dict. Need to add another colors.


## Week 8

Added color learning and basic line following

1. Scan two colors from the sensor, the line and the floor
2. We can then control the motors and decide what to do based on the colors seen before and the color we see right now
3. Docs for the motors is here ```https://ev3dev-lang.readthedocs.io/projects/python-ev3dev/en/stable/motors.html```

## Week 12

Upgraded line following, now workd at a good pace

## Week 20

Upgraded to PID algorithm