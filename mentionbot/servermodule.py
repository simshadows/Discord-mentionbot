# Abstract Class (would've been an interface...)
# All server modules are subclasses of ServerModule.
class ServerModule:
   
   RECOMMENDED_CMD_NAMES = NotImplemented

   MODULE_NAME = NotImplemented
   MODULE_SHORT_DESCRIPTION = NotImplemented

   # Defines a standard construction method.
   @classmethod
   def get_instance(cls, cmd_names, resources):
      raise NotImplementedError

   # Return a list of strings to be used to invoke a module command.
   # For example, if command_names=["foo","baz"], then subcommands
   # "foo example" or "baz example" SHOULD both cause the ServerModule
   # process_cmd() function to be called with substr="example".
   # TODO: Figure out a better way to define abstract attributes!!!
   @property
   def cmd_names(self):
      raise NotImplementedError

   # Every module has the opportunity to pre-process the contents of a message.
   # This is carried out after all modules have carried out their on_message()
   # methods.
   # The msg_preprocessor() methods for all installed server modules
   # are daisy-chained, i.e. the output from the first module.msg_preprocessor()
   # is the input into the next module.msg_preprocessor(). This means that
   # this method MAY receive an alread-processed command by another module!
   # Thus, it is important to ensure no preprocessor methods collide.
   # If you're not sure how to use this method, don't worry about implementing
   # it.
   #
   # This method is often used for processing command shortcuts.
   #     Example:
   #        Server module "Random" has the command "/rng choose [args]".
   #        invocation_shortcuts("something") -> returns -> "something"
   #        invocation_shortcuts("/choose A;B;C") -> returns -> "/rng choose A;B;C"
   # Some modules may even be entirely build around pre-processing.
   #     For example, a module may be a dedicated standin for another bot.
   #     That module may detect if that bot is offline or not responding,
   #     and if so, the module will process messages to redirect
   #     commands to itself to serve them.
   async def msg_preprocessor(self, content, msg, default_cmd_prefix):
      return content # THIS IS TO BE OVERWRITTEN!

   # Get a help-message string summarising the module functionality,
   # or at least directing the user to more detailed help.
   # Returned string has no leading/trailing whitespace.
   # NOTE: cmd_prefix is sensitive to leading/trailing whitespace.
   #       For example, cmd_prefix="/" will make module commands show
   #       up as "/examplecommand", while "$mb " will make the same
   #       module command show up as "$mb examplecommand".
   def get_help_summary(self, cmd_prefix, privilegelevel=0):
      raise NotImplementedError

   # Get a detailed help-message string about the module.
   # String has no leading/trailing whitespace.
   # NOTE: cmd_prefix works the same as in get_help_summary.
   def get_help_detail(self, substr, cmd_prefix, privilegelevel=0):
      raise NotImplementedError

   # This method is always called every time a message from the module's associated
   # server is received.
   async def on_message(self, msg):
      pass

   # This method is called if a command is to be handled by the module.
   async def process_cmd(self, substr, msg, privilegelevel=0):
      pass



