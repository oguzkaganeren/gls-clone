#!/usr/bin/python
import os
import sys
from pathlib import Path
import subprocess
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

###############################
### system backend
###############################

class Backend:
    admin = True
    asynchro = False

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
    def execute(command: str, shell: bool = False):
        """ generic shell call
            :return tuple (code, stdout, stderr)
        """
        print(" :: exec :", command)
        proc = subprocess.run(command.split(), shell=shell, universal_newlines=True, capture_output=True)
        print("\n :: execute returncode:", proc.returncode)
        print(" :: execute out:", proc.stdout)
        print(" :: execute err:", proc.stderr, "\n")
        return proc.returncode, proc.stdout, proc.stderr

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
        # else
        # actual sync
        print("as Admin, run:", f"pkexec {fileexe} --admin --{self.sign} -{params}")
        proc = subprocess.run(f"pkexec {fileexe} --admin --{self.sign} {params}", shell=True)
        return proc.returncode

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
            print("   -> return code is:", err_code)
            exit(err_code)
        else:
            print("debug info: Not admin, we use gui ...")


class BackendTheme(Backend):
    def apply(self, **kwargs):
        """ make nothing """
        name = kwargs.get('theme')
        print("Apply new theme : ", self.__class__.__name__, "switch to:", name, "\n\n")
        code, _, _ = self.execute('ls -l | cat', shell=True)
        code, out, err = self.execute('/usr/bin/stat /root/.', shell=False)
        return code


class BackendCups(Backend):
    service = 'cups'
    def apply(self, **kwargs):
        activate = kwargs.get('active', "False")

        if activate == 'start': # example method
            return self.start()
        cmd = "disable"
        if activate == "True":
            cmd = "enable"
        code, _, _ = self.execute(f"systemctl {cmd} {self.service}")
        return code

    @classmethod
    def check(cls, **kwargs):
        """ example test if service exists, can use in gui for show/hide btn """
        code, _, _ = cls.execute("systemctl cat {self.service}")
        return code == 0

    def start(self):
        """ exemple we can create methods for actions call in apply()"""
        code, _, _ = self.execute("systemctl start {self.service}", shell=False)
        return code


class BackendUnit(Backend):
    def apply(self, **kwargs):
        unit = kwargs.get('unit')
        verb = kwargs.get('verb')
        verb = 'cat' # override for demo
        code = 99
        if unit:
            code, _, _ = self.execute(f"systemctl {verb} {unit}")
        return code

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

        self.set_size_request(300, 100)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.show_all()

    def on_apply(self, button, data_call):
        """ run actions as root with pkexec
                - for compact demo : only one on_apply() for all btns
        """
        if data_call == 'xxx':
            action = BackendUnit()
            err_code = action.load(unit='sddm', verb='edit')
            self.display_msg(str(err_code))
            return

        if data_call == 'theme':
            action = BackendTheme()
            err_code = action.load(theme='TheBestTheme')
            self.display_msg(str(err_code))
            return

        action = BackendCups()
        err_code = action.load(active=data_call)
        self.display_msg(str(err_code))

    def display_msg(self, msg: str, ico=Gtk.MessageType.INFO):
        print("GUI INFO dialog return:", msg)
        if msg == "0":  # show dialog only if error
            return
        dialog = Gtk.MessageDialog(parent=self, flags=0, message_type=ico, buttons=Gtk.ButtonsType.OK, text="function return code:")
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

    Backend.mainConsole()   # only if call from pkexex (or sudo --admin)

    main()    # gui
