#!/usr/bin/python
import os
import sys
from pathlib import Path
import subprocess
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
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

class Backend:
    admin = True

    def __init__(self, callback_func=None):
        """ by defaut use async calls """
        self.asynchro = True
        self.code = -1    # not run
        self.stdout = ""
        self.stderr = ""
        if callback_func:
            self.on_end = callback_func

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
        """ run self script async call"""
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
        if self.on_end:
            self.on_end(self.sign, self.code, self.stdout, self.stderr)

    def on_end(self, action: str, code: int, stdout: str, stderr: str):
        """ callback for gui """
        pass

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
        self.execute("systemctl start {self.service}")


class BackendUnit(Backend):
    def apply(self, **kwargs):
        unit = kwargs.get('unit')
        verb = kwargs.get('verb')
        verb = 'cat' # override for demo
        code = 99
        if unit:
            asyncio.run(self.execute(f"systemctl {verb} {unit}"))

###############################
# GUI
###############################

class TestWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="pkAction test")
        self.action = None

        self.connect('delete-event', Gtk.main_quit)
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

        self.set_size_request(300, 100)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.show_all()

    def on_apply(self, button, data_call):
        """ run actions as root with pkexec
                - for compact demo : only one on_apply() for all btns
        """
        if self.action: # wait action end
            self.display_msg("wait end curent process", Gtk.MessageType.ERROR)
            return 
        self.btn.set_sensitive(False) # demo : not always this btn
        if data_call == 'xxx':
            self.action = BackendUnit(callback_func=self.on_end_process)
            self.action.load(unit='sddm', verb='edit')
            return

        if data_call == 'theme':
            self.action = BackendTheme()
            self.action.on_end = self.on_end_process # pass by init or after
            self.action.load(theme='TheBestTheme')
            print("not end pkexec action if async but begin ?") # ok
            return

        self.action = BackendCups()
        self.action.on_end = self.on_end_process
        self.action.load(active=data_call)

    def set_demo_btn(self, btn):
        self.btn.set_sensitive(True)  # demo : not always this btn

    def on_end_process(self, action, code, stdout, stderr):
        self.action = None
        print("gui.on_end_process", action, code)
        GLib.idle_add(self.set_demo_btn, action)
        GLib.idle_add(self.display_msg, f"End process: {action}:{code}\n\n{stdout}\n\nSTDERR:\n{stderr}")
        #self.display_msg(f"End process: {action}:{code}\n\n{stdout}\n\nSTDERR:\n{stderr}")

    def display_msg(self, msg: str, ico=Gtk.MessageType.INFO):
        print("display_msg() GUI INFO dialog return")
        if msg == "0":  # show dialog only if error
            return
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
