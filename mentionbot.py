import datetime
import sys
import copy
import time
import re
import os
import random

import discord # pip install --upgrade git+https://github.com/Rapptz/discord.py@legacy

import utils # TODO: Figure out how to just import individual things...
import clientextended
import mentions.mentionsummarycache
import helpmessages.helpmessages

LOGIN_DETAILS_FILENAME = "login_details" # This file is used to login. Only contains two lines. Line 1 is email, line 2 is password.
MESSAGE_MAX_LEN = 2000
BOTOWNER_ID = str(119384097473822727) # User ID of the owner of this bot
INITIAL_GAME_STATUS = "hello thar"

INITIAL_GLOBALENABLED_MENTIONS_NOTIFY = False

def initialize_global_variables():

   global re_alldigits
   global re_mentionstr
   global re_chmentionstr
   re_alldigits = re.compile("\d+")
   re_mentionstr = re.compile("<@\d+>")
   re_chmentionstr = re.compile("<#\d+>")

   # For matching command options.
   global re_option_ch
   global re_option_m
   global re_option_r
   re_option_ch = re.compile("ch=[\w\W]+") # e.g. "ch=<#124672134>"
   re_option_m = re.compile("m=\d+") # e.g. "m=100"
   re_option_r = re.compile("r=\d+") # e.g. "m=1000"

   # Global enabled/disabled
   global globalenabled_mentions_notify
   globalenabled_mentions_notify = INITIAL_GLOBALENABLED_MENTIONS_NOTIFY

   # The others
   global mentionSummaryCache
   global help_messages
   global bot_mention
   global bot_name
   global botowner_mention
   global botowner
   global initialization_timestamp
   mentionSummaryCache = mentions.mentionsummarycache.MentionSummaryCache()
   help_messages = helpmessages.helpmessages.HelpMessages()
   bot_mention = "<@{}>".format(client.user.id)
   bot_name = client.user.name
   botowner_mention = "<@{}>".format(BOTOWNER_ID)
   botowner = client.search_for_user(BOTOWNER_ID)
   initialization_timestamp = datetime.datetime.now()
   
   return

###########################################################################################


# Log in to discord
print("\nAttempting to log in using file '" + LOGIN_DETAILS_FILENAME + "'.")
if not os.path.isfile(LOGIN_DETAILS_FILENAME):
   print("File does not exist. Terminating.")
   sys.exit()
login_file = open(LOGIN_DETAILS_FILENAME, "r")
email = login_file.readline().strip()
password = login_file.readline().strip()
login_file.close()
print("Email: " + email)
print("Password: " + len(password) * "*")
print("Logging in...", end="")
client = clientextended.ClientExtended()
client.login(email, password)
print(" success.")


@client.event
def on_ready():
   initialize_global_variables()
   client.set_game_status(INITIAL_GAME_STATUS)
   print("")
   print("LOGIN_DETAILS_FILENAME = '{}'".format(LOGIN_DETAILS_FILENAME))
   print("MESSAGE_MAX_LEN = '{}'".format(MESSAGE_MAX_LEN))
   print("BOTOWNER_ID = '{}'".format(BOTOWNER_ID))
   print("INITIAL_GAME_STATUS = '{}'".format(INITIAL_GAME_STATUS))
   print("")
   print("INITIAL_GLOBALENABLED_MENTIONS_NOTIFY = '{}'".format(INITIAL_GLOBALENABLED_MENTIONS_NOTIFY))
   print("")
   print("Bot owner: " + botowner.name)
   print("Bot name: " + bot_name)
   print("")
   print("Initialization complete.")
   print("")

   
@client.event
def on_message(msg):
   global bot_mention

   if msg.author == client.user:
      return # never process own messages.

   text = msg.content.strip()
   (left, right) = utils.separate_left_word(text)
   if msg.channel.__class__.__name__ is "Channel":
      try:
         print("msg rcv #" + msg.channel.name + ": " + str(text.encode("unicode_escape")))
      except Exception:
         print("msg rcv (UNKNOWN DISPLAY ERROR)")

      if text.startswith("/"): 
         cmd1(text[1:].strip(), msg, no_default=True)

      elif left == "$mb":
         cmd1_mentions(right, msg, no_default=False)

      # EASTER EGG REPLY.
      elif (left == "$blame") and (bot_mention in text):
         client.send_msg(msg, "no fk u")

      elif (bot_mention in text or text == client.user.name + " pls"):
         cmd1_mentions_summary("", msg, add_extra_help=True)
      
      else:
         mentionSummaryCache.add_message(msg)
         simple_easter_egg_replies(msg)

   else:
      client.send_msg(msg, "sry m8 im not programmed to do anything fancy with pms yet")
      print("private msg rcv from" + msg.author.name + ": " + text)
   return


def cmd1(substr, msg, no_default=False):
   substr = substr.strip()
   if substr == "" and not no_default:
      cmd1_mentions_summary("", msg, add_extra_help=False)
   else:
      (left, right) = utils.separate_left_word(substr)

      if left == "help":
         global help_messages
         if is_privileged_user(msg.author.id):
            privilege_level = 1
         else:
            privilege_level = 0
         buf = help_messages.get_message(right, privilegelevel=privilege_level)
         if buf == None:
            cmd_invalidcmd(msg)
         else:
            client.send_msg(msg, buf)

      elif (left == "mentions") or (left == "mb") or (left == "mentionbot"):
         cmd1_mentions(right, msg)

      elif left == "avatar":
         cmd1_avatar(right, msg)

      elif (left == "randomcolour") or (left == "randomcolor"):
         # TODO: THIS IS TEMPORARY!!!
         rand_int = random.randint(0,(16**6)-1)
         rand = hex(rand_int)[2:] # Convert to hex
         rand = rand.zfill(6)
         buf = "{}, your random colour is {} (decimal: {})".format(msg.author.name, rand, rand_int)
         buf += "\nhttp://www.colorhexa.com/{}.png".format(rand)
         client.send_msg(msg, buf)

      elif left == "source":
         cmd_source(msg)

      elif left == "rip":
         client.send_msg(msg, "doesnt even deserve a funeral")

      elif left == "status":
         buf = "**Status:**"
         buf += "\nBot current uptime: {}. ".format(utils.seconds_to_string(get_bot_uptime()))
         buf += "\nNotification system enabled = " + str(globalenabled_mentions_notify)
         client.send_msg(msg, buf)

      elif (left == "admin") or (left == "a"):
         cmd_admin(right, msg)
      
      # else:
      #    cmd_invalidcmd(msg)
   
   return


def cmd1_mentions(substr, msg, no_default=False):
   substr = substr.strip()
   if substr == "" and not no_default:
      cmd1_mentions_summary("", msg, add_extra_help=False)
   else:
      (left, right) = utils.separate_left_word(substr)

      if left == "summary":
         cmd1_mentions_summary(right, msg)

      elif (left == "search") or (left == "s"):
         cmd1_mentions_search(right, msg)

      elif (left == "notify") or (left == "n"):
         cmd1_mentions_notify(right, msg)
      
      else:
         cmd_invalidcmd(msg)
   
   return


def cmd1_mentions_summary(substr, msg, add_extra_help=False):
   send_as_pm = False
   preserve_data = False
   verbose = False

   # Parse substring for options. Return on invalid option.
   flags = utils.parse_flags(substr)
   for flag in flags:
      if (send_as_pm == False) and ((flag == "p") or (flag == "privmsg")):
         send_as_pm = True
         add_extra_help = False # Never attach extra help message if sent via PM.
      elif (preserve_data == False) and ((flag == "k") or (flag == "preservedata")):
         preserve_data = True
      elif (verbose == False) and ((flag == "v") or (flag == "verbose")):
         verbose = True
      else: # Invalid flag!
         return cmd_badargs(msg)

   if mentionSummaryCache.user_has_mentions(msg.author.id):
      buf = "Here's a summary of your recent mentions."
      buf += "\nBot current uptime: {}. ".format(utils.seconds_to_string(get_bot_uptime()))
      if add_extra_help:
         buf += " (`/help` for more commands.)".format(bot_name)
      buf += "\n\n" + msg_list_to_string(mentionSummaryCache.get_user_latest(msg.author.id), verbose=verbose)
      if not preserve_data:
         mentionSummaryCache.delete_user_data(msg.author.id)
   else:
      buf = "sry m8 no mentions to see"
      buf += "\nBot current uptime: {}".format(utils.seconds_to_string(get_bot_uptime()))
      if add_extra_help:
         buf += " (`/help` for more commands.)".format(bot_name)
   
   if send_as_pm:
      client.send_msg(msg.author, buf)
      client.send_msg(msg, "List of mentions sent via PM.")
   else:
      client.send_msg(msg, buf)
   return


def cmd1_mentions_search(substr, msg):
   # return client.send_msg(msg, "This command is temporarily unavailable due to possible abuse.") # TEMPORARY.
   send_as_pm = False # TYPE: Boolean
   verbose = False # TYPE: Boolean
   ch = None # TYPE: String, or None. This is a channel name, channel mention, or channel ID.
   mentions_to_get = None # TYPE: Int, or None. This is the number of mentions this function will try to fetch.
   search_range = None # TYPE: Int, or None. This is the number of messages the function will search through.

   flags = utils.parse_flags(substr)
   for flag in flags:
      if (send_as_pm == False) and ((flag == "p") or (flag == "privmsg")):
         send_as_pm = True
      elif (verbose == False) and ((flag == "v") or (flag == "verbose")):
         verbose = True
      elif (ch is None) and re_option_ch.fullmatch(flag):
         ch = flag[3:]
      elif (mentions_to_get == None) and re_option_m.fullmatch(flag):
         mentions_to_get = int(flag[2:])
      elif (search_range == None) and re_option_r.fullmatch(flag):
         search_range = int(flag[2:])
      else: # Invalid flag!
         return cmd_badargs(msg)

   # Get channel object from ch (and handle the default value)
   if ch is None:
      channel = msg.channel
   else:
      server_to_search = msg.server
      if server_to_search == None:
         return client.send_msg(msg, "Sorry, the --ch option is unusable in private channels.")
      channel = client.search_for_channel(ch, enablenamesearch=True, serverrestriction=server_to_search)
      if channel is None:
         return client.send_msg(msg, "Channel not found. Search failed.")
   # Handle other default values or invalid inputs.
   if mentions_to_get == None:
      mentions_to_get = 3
   elif mentions_to_get == 0:
      return cmd_badargs(msg)
   if search_range == None:
      search_range = 2000
   elif search_range == 0:
      return cmd_badargs(msg)

   # Search
   search_results = []
   searched = 0 # Used for feedback on how many messages were searched.
   mentions_left = mentions_to_get
   search_before = None # Used for generating more logs after the limit is reached.
   while True:
      print("RETRIEVING 100 MESSAGES FROM " + channel.name + "...")
      client.send_typing(msg.channel) # Feedback that the bot is still running.
      more_left_to_search = False
      for retrieved_msg in client.logs_from(channel, limit=search_range, before=search_before):
         if searched >= search_range:
            break
         searched += 1
         prev_retrieved_msg = retrieved_msg # Used for generating more logs after the limit is reached.
         more_left_to_search = True # Used for generating more logs after the limit is reached.
         if msg.author in retrieved_msg.mentions:
            search_results.append(retrieved_msg)
            mentions_left -= 1
            if mentions_left == 0:
               break
      if (searched >= search_range) or not (more_left_to_search and (mentions_left > 0)):
         break
      search_before = prev_retrieved_msg
   
   # Report search results
   if len(search_results) == 0:
      buf = "No results found."
      buf += "\nLooked through " + str(searched) + " messages in <#" + channel.id + ">."
      buf += "\n(mentions_to_get=" + str(mentions_to_get) + ", range=" + str(search_range) + ")"
   else:
      mentions_found = mentions_to_get - mentions_left
      buf = "Here are your " + str(mentions_found) + " latest mentions in <#" + channel.id + ">."
      buf += "\n(mentions_to_get=" + str(mentions_to_get) + ", range=" 
      buf += str(search_range) + ", searched=" + str(searched) + "):"
      buf += "\n\n"
      buf += msg_list_to_string(search_results, verbose=verbose)

   return client.send_msg(msg, buf)


def cmd1_mentions_notify(substr, msg):
   return client.send_msg(msg, "This feature has not yet been implemented.")


def cmd1_avatar(substr, msg):
   (left, right) = utils.separate_left_word(substr)
   user = None
   if len(left) > 0:
      user = client.search_for_user(left, enablenamesearch=True, serverrestriction=msg.server)
      if user is None:
         return client.send_msg(msg, left + " doesn't even exist m8")
   else:
      user = msg.author

   # Guaranteed to have a user.
   avatar = user.avatar_url()
   if avatar == "":
      return client.send_msg(msg, left + " m8 get an avatar")
   else:
      return client.send_msg(msg, avatar)


def cmd_source(msg):
   # buf = "https://github.com/simshadows/discord-mentionbot"
   buf = "idk, ask sim."
   return client.send_msg(msg, buf)


def cmd_admin(substr, msg):
   if not is_privileged_user(msg.author.id):
      cmd_badprivileges(msg)
      return

   substr = substr.strip()
   if substr == "" and not no_default:
      cmd_invalidcmd(msg)
   else:
      (left1, right1) = utils.separate_left_word(substr)

      if left1 == "say":
         client.send_msg(msg, right1)

      elif left1 == "iam":
         cmd_admin_iam(right1, msg)

      elif left1 == "toggle":
         (left2, right2) = utils.separate_left_word(right1)
         if (left2 == "mentions") or (left2 == "mb") or (left2 == "mentionbot"):
            (left3, right3) = utils.separate_left_word(right2)
            if (left3 == "notify") or (left3 == "n"):
               global globalenabled_mentions_notify # TODO: Is this actually needed?
               globalenabled_mentions_notify = not globalenabled_mentions_notify
               client.send_msg(msg, "Notification system enabled = " + str(globalenabled_mentions_notify))
            else:
               cmd_invalidcmd(msg)
         else:
            cmd_invalidcmd(msg)

      elif left1 == "gettime":
         client.send_msg(msg, datetime.datetime.utcnow().strftime("My current system time: %c UTC"))

      elif left1 == "setgame":
         client.set_game_status(right1)
         client.send_msg(msg, "Game set to: " + right1)

      elif left1 == "setusername":
         client.edit_profile(password, username=right1)
         bot_name = right1 # TODO: Consider making this a function. Or stop using bot_name...
         client.send_msg(msg, "Username set to: " + right1)

      elif left1 == "getemail":
         client.send_msg(msg, "My email is: " + email)

      elif left1 == "joinserver":
         try:
            client.accept_invite(right1)
            client.send_msg(msg, "Successfully joined a new server.")
         except discord.InvalidArgument:
            client.send_msg(msg, "Failed to join a new server.")

      elif left1 == "leaveserver":
         client.send_msg(msg, "Bye!")
         client.leave_server(msg.channel.server)

      elif left1 == "throwexception":
         raise Exception
      
      else:
         cmd_invalidcmd(msg)
   return


def cmd_admin_iam(substr, msg):
   substr = substr.strip()
   (left, right) = utils.separate_left_word(substr)
   
   if re_mentionstr.fullmatch(left):
      user_to_pose_as = left[2:-1]
      replacement_msg = copy.deepcopy(msg)
      replacement_msg.author = client.search_for_user(user_to_pose_as)
      if replacement_msg.author == None:
         return client.send_msg(msg, "Unknown user.")
      replacement_msg.content = right
      client.send_msg(msg, "Executing command as {}: {}".format(replacement_msg.author, replacement_msg.content))
      client.send_msg(msg, "**WARNING: There are no guarantees of the safety of this operation.**")
      on_message(replacement_msg)
   return


# If bad arguments were entered for a command.
def cmd_badargs(msg):
   return client.send_msg(msg, "soz m8 one or more (or 8) arguments are invalid")


# For attempts to use commands without sufficient privileges
def cmd_badprivileges(msg):
   return client.send_msg(msg, "im afraid im not allowed to do that for you m8")


# For invalid commands.
def cmd_invalidcmd(msg):
   return client.send_msg(msg, "sry m8 idk what ur asking") # intentional typos. pls don't lynch me.


def simple_easter_egg_replies(msg):
   if msg.content.startswith("$blame " + botowner_mention) or msg.content.startswith("$blame " + botowner.name):
      client.send_msg(msg, "he didnt do shit m8")
   return


def is_privileged_user(user_ID):
   return user_ID == BOTOWNER_ID


# RETURNS: Bot's current uptime in seconds
def get_bot_uptime():
   timediff = datetime.datetime.now() - initialization_timestamp
   return timediff.seconds


# TODO: There already is a copy of this function in mentionbot.py...
def msg_list_to_string(mentions, verbose=False): # TYPE: String
   now = datetime.datetime.utcnow()
   buf = "" # FORMAT: String
   for i in mentions:
      timediff = now - i.timestamp
      if verbose:
         buf += "Message ID: " + i.id + "\n"
         # buf += "Timestamp: " + i.timestamp.strftime("%c UTC") + "\n" # Unnecessary
      buf += "By " + i.author.name + " in " + "<#{}>".format(i.channel.id) + ", " + utils.seconds_to_string(timediff.seconds) + " ago\n"
      buf += i.content + "\n\n"
   if buf != "":
      buf = buf[:-2]
   return buf


client.run() # let the games begin...
