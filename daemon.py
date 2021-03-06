# -*- coding: utf-8 -*-
import MySQLdb
import sys
import time
import functions
from PIL import ImageFont

import configuration

# Luma.LED_Matrix requirements
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.led_matrix.device import max7219
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT

# LED Matrix Setup
serial = spi(port=0, device=0, gpio=noop())
device = max7219(serial, cascaded=configuration.LED['CASCADED'], block_orientation=configuration.LED['ORIENTATION'])

device.contrast(configuration.LED['CONTRAST'])
device.clear()

# Show IP Adress
show_message(device, functions.cleanMessage(functions.getIP()), fill="white", font=proportional(CP437_FONT),scroll_delay=0.02)
# Show Startup Messages
if len(configuration.STARTUP_MESSAGE):
	for m in configuration.STARTUP_MESSAGE:
		show_message(device, functions.cleanMessage(m), fill="white", font=proportional(CP437_FONT),scroll_delay=0.02)

# Setup DB connection
SQLcon = MySQLdb.connect(configuration.DATABASE['HOST'], configuration.DATABASE['USER'], configuration.DATABASE['PASSWORD'], configuration.DATABASE['NAME'])
SQLcon.set_character_set('utf8')

with SQLcon:
	while(1):
		# Setup DB cursor
		SQLcur = SQLcon.cursor()
		SQLcur.execute('SET NAMES utf8;')
		SQLcur.execute('SET CHARACTER SET utf8;')
		SQLcur.execute('SET character_set_connection=utf8;')

		# Grab unshown messages from DB
		SQLcur.execute("SELECT `message_id`, `provider_name`, `message_text`, `message_from`, `message_speed` FROM `message` JOIN `provider` ON `message`.`provider_id` = `provider`.`provider_id` WHERE `message_shown` = 0 ORDER BY `message_id` ASC;")

		# Grab one message after another
		for i in range(SQLcur.rowcount):
			# Fetch and prepare date
			SQLrow = SQLcur.fetchone()
			if SQLrow:
				for i in range(0, len(SQLrow)):
					if type(SQLrow[i]) is str:
						SQLrow[i].decode("utf-8")

				# Prepare device + message
				device.show()
				message = configuration.LED['MESSAGE_FORMAT']
				message = message.replace('[message]', SQLrow[2])
				if SQLrow[3] != None:
					message = message.replace('[user]', SQLrow[3])
				else:
					message = message.replace('[user]', '')
				message = message.replace('[provider]', SQLrow[1])

				message_device = functions.cleanMessage(message)

				print "Started showing message id=" + str(SQLrow[0]) + ", time=" + str(SQLrow[3]) + ", message=" + message

				# Show message
				show_message(device, message_device, fill="white", font=proportional(CP437_FONT), scroll_delay=SQLrow[4])

				# Turn Off and clear device
				device.hide()
				device.clear()
				print "Stopped showing message id=" + str(SQLrow[0]) + ", time=" + str(SQLrow[3]) + ", message=" + message

				# Set state of message to shown
				SQLcur.execute("UPDATE `message` SET `message_shown` = 1 WHERE `message_id` = '" + str(SQLrow[0]) + "';")

		# Commit to DB and prepare to restart
		SQLcon.commit()
		time.sleep(1)
