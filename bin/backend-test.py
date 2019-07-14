#!/usr/bin/python
import os
import sys
from pathlib import Path
import subprocess
import asyncio
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

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

    async def execute(self, command: str):
        """ generic shell async call """
        self.stdout = ""
        self.stderr = ""
        print(" :: exec :", command)
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self.stdout, self.stderr = await proc.communicate()
        self.stdout = self.stdout.decode()
        self.stderr = self.stderr.decode()
        #proc = subprocess.run(command.split(), shell=shell, universal_newlines=True, capture_output=True)

        print("\n :: execute returncode:", proc.returncode)
        print(" :: execute out:", self.stdout)
        print(" :: execute err:", self.stderr, "\n")
        self.err_code = proc.returncode
        if '--admin' in sys.argv:
            exit(self.err_code)
        #return proc.returncode, self.stdout, self.stderr

    async def _execute_pkexec(self, command: str):
        """ run self script async call"""
        self.stdout = ""
        self.stderr = ""
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self.stdout, self.stderr = await proc.communicate()
        self.stdout = self.stdout.decode()
        self.stderr = self.stderr.decode()
        self.err_code = proc.returncode
        print("\n :: pkexec execute returncode:", proc.returncode)
        print(" :: pkexec execute out:", self.stdout)
        print(" :: pkexec execute err:", self.stderr, "\n")
        self._on_end_process()


    def run(self, **kwargs):
        """ subprocess.run() """
        #name=kwargs.get('name', None)
        err_code = self.check(**kwargs)
        print("err_code check() =", err_code)
        if err_code > 0:
            return err_code
        return self.apply(**kwargs)

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

        # TODO if self.asynchro : GLib.spawn_async (..., self.callback)
        #https://gist.github.com/fabrixxm/8deb791ad0930fa209be
        # else
        # actual sync
        print("as Admin, run:", f"pkexec {fileexe} --admin --{self.sign} -{params}")
        return asyncio.run(self._execute_pkexec(f"pkexec {fileexe} --admin --{self.sign} {params}"))
        print("end asyncio.run()")
        #proc = subprocess.run(f"pkexec {fileexe} --admin --{self.sign} {params}", shell=True)

    def _on_end_process(self):
        """ async callback function from process """
        print("DEBUG _on_end_process() async: END process", self.sign, self.err_code)
        if '--admin' in sys.argv:
            exit(self.err_code)
        if self.on_end:
            self.on_end(self.sign, self.err_code, self.stdout, self.stderr)

    def on_end(self, action:str, code:int, stdout: str, stderr: str):
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
            args = {x[1:]: args[args.index(x)+1] for x in args if args.index(x) % 2 == 0}
            print("params pass to run(): ", args)
            action_class = globals()[sign]      # param to Class
            action = action_class()             # create object from second console parameter
            err_code = action.run(**args)
            return True
        else:
            print("debug info: Not admin, we use gui ...")
            return False


class BackendTheme(Backend):
    def apply(self, **kwargs):
        """ make nothing """
        name = kwargs.get('theme')
        print("Apply new theme : ", self.__class__.__name__, "switch to:", name, "\n\n")
        '''
        # if we not want async :
        proc = subprocess.run('/usr/bin/statERR /root/.', shell=True, text=True, capture_output=True)
        exit(proc.returncode)
        # or want async :
        '''
        asyncio.run(self.execute('ls -l | cat'))
        asyncio.run(self.execute('/usr/bin/stat /root/.'))



class BackendCups(Backend):
    service = 'cups'
    def apply(self, **kwargs):
        activate = kwargs.get('active', "False")

        if activate == 'start': # example method
            return self.start()
        cmd = "disable"
        if activate == "True":
            cmd = "enable"
        asyncio.run(self.execute(f"systemctl {cmd} {self.service}"))

    @classmethod
    def check(cls, **kwargs):
        """ example test if service exists, can use in gui for show/hide btn """
        # test if file or service exists
        return 0

    def start(self):
        """ exemple we can create methods for actions call in apply()"""
        asyncio.run(self.execute("systemctl start {self.service}"))


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


        btn = Gtk.Button.new_with_label("ls /root/")
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
        self.btn.set_sensitive(False) # demo : not always this btn
        if data_call == 'xxx':
            action = BackendUnit(callback_func=self.on_end_process)
            action.load(unit='sddm', verb='edit')
            return

        if data_call == 'theme':
            action = BackendTheme()
            action.on_end = self.on_end_process # pass by init or after
            action.load(theme='TheBestTheme')
            return

        action = BackendCups(callback_func=self.on_end_process)
        action.on_end = self.on_end_process
        action.load(active=data_call)


    def on_end_process(self, action, code, stdout, stderr):
        self.btn.set_sensitive(True)  # demo : not always this btn
        self.display_msg(f"End process: {action}:{code}\n\n{stdout}\n\nSTDERR:\n{stderr}")

    def display_msg(self, msg: str, ico=Gtk.MessageType.INFO):
        print("GUI INFO dialog return")
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
