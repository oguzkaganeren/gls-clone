#!/usr/bin/python
import os
import sys
from pathlib import Path
import subprocess
import threading
import gi
from userconf import UserConf
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject
from gi.overrides import GLib


class PopenWrapper(object):
    def __init__(self):
        self.process = None
        self.stdout_reader_thread = None
        self.stderr_reader_thread = None
        self.exit_watcher = None
        self.stdout = ''
        self.stderr = ''

    def run(self, command):
        self.process = subprocess.Popen(command,
                text=True, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL
        )
        self.stdout_reader_thread = threading.Thread(target=self._reader, args=(self.process.stdout,))
        self.stderr_reader_thread = threading.Thread(target=self._readererr, args=(self.process.stderr,))
        self.exit_watcher = threading.Thread(target=self._exit_watcher)

        self.stdout_reader_thread.start()
        self.stderr_reader_thread.start()
        self.exit_watcher.start()

    def _reader(self, fileobj):
        for line in fileobj:
            self.stdout = f"{self.stdout}{line}"
            self.on_data(line)

    def _readererr(self, fileobj):
        for line in fileobj:
            self.stderr = f"{self.stderr}{line}"
            self.on_data_err(line)

    def _exit_watcher(self):
        self.process.wait()
        self.stdout_reader_thread.join()
        self.stderr_reader_thread.join()
        self.on_exit(self.process.returncode, self.stdout, self.stderr)

    def on_data(self, line):
        print(f"\033[92m ::\033[0m {line}", end=" ")  #TODO comment for production

    def on_data_err(self, line):
        print(f"\033[91mSTDERR:\033[0m {line}", end="")  #TODO comment for production

    def on_exit(self, *data):
        return self.process.returncode

    def join(self):
        self.process.wait()


###############################
### system backend
###############################

class Backend(GObject.GObject):
    admin = True

    __gsignals__ = {
        'endprocess': (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self):
        """ by defaut use async calls """
        GObject.GObject.__init__(self)
        self.asynchro = True
        self.code = -1    # not run
        self.stdout = ""
        self.stderr = ""

    def __int__(self):
        return self.code

    def __call__(self):
        return self.code

    def __str__(self):
        return f"{{\n 'class:': {self.sign}\n 'return': {self.code}\n 'err': {self.stderr.strip()}\n}}"

    @classmethod
    def check(cls, **kwargs):
        """
        check sys.argv  or
        check if Admin  or
        check file exists  or
        check manjaro / good DE  or ...
        """
        if not cls.admin and os.geteuid() == 0:
            raise PermissionError(f"Never run this action {cls.__name__} as Admin")
        return 0

    def apply(self, **kwargs):
        raise RuntimeError("Backend not yet implemented")

    @staticmethod
    def log(*args):
        #print(args)
        print('\033[92m', *args, '\033[0m')

    def execute(self, command: str) -> bool:
        """ generic shell sync call """
        self.stdout = ""
        self.stderr = ""
        self.log(" :: exec cmd:", command)
        proc = subprocess.run(command, shell=True, text=True, capture_output=True)# universal_newlines=True, capture_output=True)
        self.stderr = proc.stderr
        self.stdout = proc.stdout
        self.code = proc.returncode
        self.log(" :: exec out:", self.stdout)
        self.log(" :: exec err:", self.code, self.stderr, "\n")

        if '--admin' in sys.argv:
            print(self.stderr, file=sys.stderr)
        return self.code == 0

    def _execute_pkexec(self, command: str):
        """
        run self script async call

        for wayland, run before ??? `xhost +si:localuser:root` if app is gtk gui
        """
        pkexec = PopenWrapper()
        pkexec.on_exit = self._on_end_process
        pkexec.run(command)

    def run(self, **kwargs):
        """ subprocess.run() """
        #name=kwargs.get('name', None)
        err_code = self.check(**kwargs)
        #self.log("err_code check() =", err_code)
        if err_code > 0:
            return err_code
        self.apply(**kwargs)
        if '--admin' in sys.argv:
            exit(self.code)

    def load(self, **kwargs):
        """ fonction for GUI """
        if not self.admin:
            # direct run
            return self.run(**kwargs)
        # else uses pkexec self app with same parameters
        params = ''
        for key, value in kwargs.items():
            params = f"{params} -{key} {str(value)}"
        fileexe = Path(sys.argv[0]).resolve()

        # actual async
        self.log("as Admin, run:", f"pkexec {fileexe} --admin --{self.sign} -{params}")
        self._execute_pkexec(f"pkexec {fileexe} --admin --{self.sign} {params}")
        #return await self._execute_pkexec(f"pkexec {fileexe} --admin --{self.sign} {params}")

    def _on_end_process(self, code, stdout, stderr):
        """ async callback function from process """
        self.code = code
        self.stderr = stderr
        self.stdout = stdout
        self.log("DEBUG _on_end_process() async: END process", self.sign, self.code, self.stderr)

        if '--admin' in sys.argv:
            exit(self.code)
        self.log("emit signal endprocess for gui...", self.code, self.stderr)
        self.emit('endprocess')

    def do_endprocess(self):
        """ recept emit signal endprocess """
        return

    @property
    def sign(self):
        return self.__class__.__name__

    @staticmethod
    def mainConsole():
        """ run as Admin in console """
        print("---mainConsole --- ? for ", sys.argv)
        if '--admin' in sys.argv:
            args = sys.argv[2:]
            sign = args.pop(0)[2:]
            print("want run action:", sign)
            if not str(sign).startswith('Backend'):
                raise RuntimeError(f"Action {sign} not implemented") # run only backend object
            if not sign in globals():
                raise RuntimeError(f"Action {sign} not exists")

            print('As admin, we run params:', sys.argv)
            print("ENV pkexec :", os.environ)
            args = {x[1:]: args[args.index(x)+1] for x in args if args.index(x) % 2 == 0}
            print("params pass to run(): ", args)
            action_class = globals()[sign]      # param to Class
            action = action_class()             # create object from second console parameter
            action.run(**args)
            return True
        else:
            print("debug info: Not admin, we use gui ...")
            return False

GObject.type_register(Backend)

###############################
# examples backend class
###############################

class BackendTheme(Backend):
    def apply(self, **kwargs):
        """ make nothing but good test """
        name = kwargs.get('theme')
        print("Apply new theme : ", self.sign, "switch for:", name, "\n\n")

        if not self.execute('/usr/bin/stat /root/. && env'):
            #pass
            pass
        if not self.execute('sleep 4'):
            print("ERROR:", self.code, "we can exit process, not run next")
            # return
            pass
        self.execute('echo "ok"')



class BackendCups(Backend):
    service = 'cups'
    def apply(self, **kwargs):
        activate = kwargs.get('active', "False")

        if activate == 'start': # example method
            return self.start()
        cmd = "disable"
        if activate == "True":
            cmd = "enable"
        self.execute(f"systemctl {cmd} {self.service}")

    @classmethod
    def check(cls, **kwargs):
        """ example test if service exists, can use in gui for show/hide btn """
        # test if file or service exists
        return 0

    def start(self):
        """ exemple we can create methods for actions call in apply()"""
        self.execute(f"systemctl start {self.service}")


class BackendUnit(Backend):
    def apply(self, **kwargs):
        unit = kwargs.get('unit')
        verb = kwargs.get('verb')
        verb = 'cat' # override for demo
        self.code = 99
        if unit:
            self.execute(f"systemctl {verb} {unit}")

###############################
# GUI
###############################

class TestWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="pkAction test")
        self.action = None

        self.connect('delete-event', self.on_exit)
        self.connect('destroy', self.on_main_window_destroy)

        box = Gtk.VBox(spacing=20)
        self.add(box)

        #if BackendCups.check():
        btn = Gtk.Button.new_with_label("Cups On")
        btn.connect("clicked", self.on_apply, True)
        box.pack_start(btn, expand=True, fill=True, padding=4)
        if BackendCups.check():
            btn = Gtk.Button.new_with_label("Cups Off")
            btn.connect("clicked", self.on_apply, False)
            box.pack_start(btn, expand=True, fill=True, padding=4)
        #if BackendCups.check():
        btn = Gtk.Button.new_with_label("Cups Start")
        btn.connect("clicked", self.on_apply, 'start')
        box.pack_start(btn, expand=True, fill=True, padding=4)

        btn = Gtk.Button.new_with_label("systemctl xxx unit")
        btn.connect("clicked", self.on_apply, 'xxx')
        box.pack_end(btn, expand=True, fill=True, padding=4)


        btn = Gtk.Button.new_with_label("ls /root/ && env")
        btn.connect("clicked", self.on_apply, 'theme')
        box.pack_end(btn, expand=True, fill=True, padding=4)
        self.btn = btn # for demo validate / unvalidate

        with UserConf('BACKEND-TEST') as conf:
            try:
                position = conf.reads('POSITION')
                self.set_size_request(position.w, position.h)
                self.move(position.x, position.y)
            except KeyError as err:
                self.set_default_size(400, 400)
                self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

        self.show_all()

    def on_exit(self, widget, event=None, data=None):
        with UserConf('BACKEND-TEST') as conf:
            conf.write({
                'w': self.get_size().width,
                'h': self.get_size().height,
                'x': self.get_position()[0],
                'y': self.get_position()[1],
                },
                'POSITION')
        Gtk.main_quit()

    def on_apply(self, button, data_call):
        """ run actions as root with pkexec
                - for compact demo : only one on_apply() for all btns
        """
        if self.action: # wait action end
            self.display_msg("wait end curent process", Gtk.MessageType.ERROR)
            return 
        self.btn.set_sensitive(False) # demo : not always this btn
        if data_call == 'xxx':
            self.action = BackendUnit()
            self.action.connect('endprocess', self.on_endprocess)
            self.action.load(unit='sddm', verb='edit')
            return

        if data_call == 'theme':
            self.action = BackendTheme()
            self.action.connect('endprocess', self.on_endprocess)
            self.action.load(theme='TheBestTheme')
            print("not end pkexec action if async but begin ?") # ok
            return

        self.action = BackendCups()
        self.action.connect('endprocess', self.on_endprocess)
        self.action.load(active=data_call)

    def set_demo_btn(self, btn):
        self.btn.set_sensitive(True)  # demo : not always this btn

    def on_endprocess(self, action):
        """ callback end pkexec process backend """
        self.action = None
        GLib.idle_add(self.set_demo_btn, action)
        if action:
            print("gui event on_endprocess()", action.sign, action.code, action.stderr)
            print(action)
            if action() > 0:
                print("return (int) code: ", int(action), action())
            #if action.code != 0 :    # show dialog only if error
            GLib.idle_add(self.display_msg, f"End process: {action.sign}:{action.code}\n\n{action.stdout}\n\nSTDERR:\n{action.stderr}")

    def display_msg(self, msg: str, ico=Gtk.MessageType.INFO):
        """ GUI INFO dialog """
        dialog = Gtk.MessageDialog(parent=self, flags=0, message_type=ico, buttons=Gtk.ButtonsType.OK, text="Action return:")
        dialog.format_secondary_text(msg)
        dialog.run()
        dialog.destroy()


    @staticmethod
    def on_main_window_destroy(widget):
        Gtk.main_quit()

    def main(self):
        Gtk.main()

###############################
# EXEC
###############################

def main():
    if os.geteuid() == 0:
        raise PermissionError("Not run Gui Application as Admin")
    app = TestWindow()
    app.main()

if __name__ == '__main__':

    print("\nDEBUG: os.geteuid() :", os.geteuid())

    if not Backend.mainConsole():   # only if call from pkexex (or sudo --admin)
        main()    # gui
