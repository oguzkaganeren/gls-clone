import sys
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject
import subprocess
import shutil
from pathlib import Path
import re
import os
import tempfile
import atexit
from .config import UserConf

# Define the path to css file
css_file = Path("~/.config/gtk-3.0/gtk.css").expanduser()

# Define a temp folder to store preview
temp_dir = tempfile.mkdtemp()

# Define asset in use
asset = ["manjaro-gnome-assets-19.0", "manjaro-gdm-branding"]


class Opacity:
    TOP = 1
    MIDDLE = 0.9
    LOW = 0.7


def rm_tmp_dir():
    shutil.rmtree(temp_dir, ignore_errors=True)


atexit.register(rm_tmp_dir)


def get_layouts():
    return ({"id": "manjaro", "label": "Manjaro", "x": 1, "y": 0},
            {"id": "classic", "label": "Classic", "x": 2, "y": 0},
            {"id": "modern", "label": " Modern", "x": 1, "y": 3},
            {"id": "gnome", "label": "Gnome", "x": 2, "y": 3},)


def replace_in_file(file_name: str, regex: str, value: str):
    """ replace all word in file """
    pattern = re.compile(regex)
    file_old = f"{file_name}~"
    shutil.copy(file_name, file_old)
    with open(file_old, "tr") as file_read, open(file_name, "tw") as file_write:
        # reading lines takes less ram that reading the entire file, but is also slower.
        for line in file_read:
            file_write.write(re.sub(pattern, value, line))
    Path(file_old).unlink()


def shell(commands) -> tuple:
    """return true if command return 0 AND error message"""
    if "--dev" in sys.argv:
        print("Debug mode on:")
        print("Simulating shell commands:")
        print(f"{commands}")
    else:
        try:
            # only run if not in dev mode
            if isinstance(commands, str):
                # if is string then we only have one shell command
                subprocess.run(commands, text=True, shell=True, check=True)
            else:
                # is a tuple or list
                for cmd in commands:
                    subprocess.run(cmd, text=True, shell=True, check=True)
        except subprocess.CalledProcessError as err:
            return False, str(err)
    return True, ""


def enable_wayland():
    # commands = string
    commands = "pkexec sed -i 's/^WaylandEnable=false/#WaylandEnable=false/' /etc/gdm/custom.conf"
    shell(commands)


def disable_wayland():
    commands = "pkexec sed -i 's/^#WaylandEnable=false/WaylandEnable=false/' /etc/gdm/custom.conf"
    shell(commands)


def get_extensions(chosen_layout):
    # List needed extensions
    extensions = {
        "manjaro": (
            "dash-to-dock@micxgx.gmail.com",
            "user-theme@gnome-shell-extensions.gcampax.github.com",
            "drive-menu@gnome-shell-extensions.gcampax.github.com",
            "appindicatorsupport@rgcjonas.gmail.com",
        ),
        "classic": (
            "dash-to-panel@jderose9.github.com",
            "user-theme@gnome-shell-extensions.gcampax.github.com",
            "appindicatorsupport@rgcjonas.gmail.com",
            "arc-menu@linxgem33.com"
        ),
        "modern": (
            "dash-to-dock@micxgx.gmail.com",
            "user-theme@gnome-shell-extensions.gcampax.github.com",
            "unite@hardpixel.eu"
        ),
        "gnome": (
            "user-theme@gnome-shell-extensions.gcampax.github.com",
        )
    }
    # List needed extension packages
    ext_pkgs = {
        "manjaro": ["gnome-shell-extension-dash-to-dock",
                    "gnome-shell-extensions",
                    "gnome-shell-extension-appindicator",],
        "classic": ["gnome-shell-extension-dash-to-panel",
                    "gnome-shell-extensions",
                    "gnome-shell-extension-appindicator",
                    "gnome-shell-extension-arc-menu"],
        "modern": ["gnome-shell-extension-dash-to-dock",
                   "gnome-shell-extensions",
                   "gnome-shell-extension-unite"],
        "gnome": ["gnome-shell-extensions"]
    }

    # Check if extensions are missing
    pkgs_missing = False
    try:
        for ext in extensions.get(chosen_layout):
            user_path = Path(f"~/.local/share/gnome-shell/extensions/{ext}").expanduser()
            sys_path = Path(f"/usr/share/gnome-shell/extensions/{ext}")
            if not Path.is_dir(sys_path) and not Path.is_dir(Path(user_path).expanduser()):
                pkgs_missing = True
            else:
                print("Already installed", ext)
    except (TypeError, AttributeError) as e:
        print(e)
        pass

    # Install missing packages with pamac
    if pkgs_missing:
        pkg_list = []
        for pkg in ext_pkgs.get(chosen_layout):
            pkg_installed = subprocess.run(f"pacman -Qq {pkg}&>/dev/null", shell=True)
            if pkg_installed.returncode == 1:
                pkg_list.append(pkg)
        print(f"Needed packages: {' '.join(pkg_list)}")
        shell(f"pamac-installer {' '.join(pkg_list)}")


def set_highlight_color(new_color):
    """ set highlight color in user file gtk.css """
    # If not present, copy the file from default
    # TODO re-write : line by line or user Path().read/write
    try:
        if not Path.is_file(css_file):
            shutil.copyfile("/usr/share/gtk-3.0/gtk.css", css_file)
        # Find the current highlight color
        with open(css_file) as f:
            file = f.read()
            current_color = re.search("^@define-color.*theme_selected_bg_color.*#(.*)", file)
            # TODO use group(1)
            try:
                current_color = current_color.group(1)
                # Replace the old color with new one
                with open(css_file) as f:
                    new_text = f.read().replace(current_color, new_color, 2)
                # Write the changes
                with open(css_file, "w") as f:
                    f.write(new_text)
            except AttributeError:
                print("Cannot set color. Copy /usr/share/gtk-3.0/gtk.css to ~/.config/gtk-3.0/gtk.css to continue")

    except FileNotFoundError:
        print("Cannot set color, gtk.css not found")


# def rgba_to_hex(col):
#     col.to_string()[4:-1:]
#     col = self.default_color.split(",")
#     col = (int(x) for x in col)
#     col = "#%02x%02x%02x" % tuple(col)
#     return col

# ----------------- branding functions --------------------------
def do_branding(remove: bool) -> tuple:
    arguments = asset
    if not isinstance(asset, str):
        arguments = " ".join(asset)
    if remove:
        commands = f"pkexec pamac remove --no-confirm {arguments}"
    else:
        commands = f"pkexec pamac install --no-confirm {arguments}"
    return shell(commands)


def get_asset_state() -> bool:
    arguments = asset
    if not isinstance(asset, str):
        arguments = " ".join(asset)
    asset_state = subprocess.run(f"pacman -Qq {arguments} > /dev/null 2>&1", shell=True)
    if asset_state.returncode == 0:
        return True
    return False
# ----------------- end branding functions ----------------------


class LayoutBox(Gtk.Box):

    def __init__(self, window: Gtk.Window, orientation=Gtk.Orientation.VERTICAL, spacing=1, usehello=False):
        super().__init__(orientation=orientation, spacing=spacing, expand=True)
        self.set_margin_top(16)
        """ initialize main box """
        self.layout = "manjaro"
        self.window = window
        self.usehello = usehello  # if we want some diff in hello or standalone app...

        # PEP: no variable declaration outside __init__
        self.btn_layout_first = None
        self.branding_handler_id = None
        self.branding_active = None

        with UserConf() as conf:
            self.layout = conf.read("layout", "manjaro")
            print("current layout:", self.layout)

        self.previews = {}
        self.color_button = None
        self._current_color = None

        # self.set_default_size(300, 300)

        # Determine preview color and highllight color
        rgba = self.window.get_style_context().lookup_color("theme_fg_color").color
        self.default_color = "#{:02x}{:02x}{:02x}".format(*[int(c * 255) for c in rgba]).upper()

        rgba = self.window.get_style_context().lookup_color("theme_selected_bg_color").color
        self.highlight_color = "#{:02x}{:02x}{:02x}".format(*[int(c * 255) for c in rgba]).upper()

        # Stack settings
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(300)
        stack.set_hhomogeneous(False)
        stack.set_vhomogeneous(False)
        stack.set_vexpand(True)
        stack.props.valign = Gtk.Align.START
        self.create_page_layout(stack)
        self.create_page_theme(stack)
        self.current_color = ""  # set colors from .css
        self.show_all()
        self.previews[self.layout].get_parent().btn.set_active(True)

    def create_page_layout(self, stack):
        """ Layout menu """
        vbox = Gtk.Grid(row_homogeneous=False, column_homogeneous=False, row_spacing=0, margin_left=0, margin_right=0,
                        margin_bottom=1, margin_top=0)
        self.add(vbox)
        vbox.attach(stack, 1, 1, 1, 3)
        radiobox = Gtk.Grid(column_spacing=45, row_spacing=15, margin_left=10, margin_right=10, margin_bottom=0,
                            margin_top=15)
        radiobox.set_hexpand(True)
        radiobox.props.halign = Gtk.Align.CENTER
        for layout in get_layouts():
            self.create_layout_btn(layout=layout, the_grid=radiobox)

        applybutton = Gtk.Button.new_with_label("Apply")
        applybutton.connect("clicked", self.on_layoutapply_clicked)
        radiobox.attach(applybutton, 1, 6, 2, 1)
        applybutton.props.valign = Gtk.Align.END

        stack.add_titled(radiobox, "radiobox", "Layout")
        stack.props.margin_bottom = 0
        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)
        stack_switcher.set_hexpand(True)
        stack_switcher.props.halign = Gtk.Align.CENTER
        vbox.attach(stack_switcher, 1, 0, 1, 1)

    def create_page_theme(self, stack):
        """ The theme tab """
        theme_grid = Gtk.Grid(row_spacing=20, margin_left=40, margin_right=40, margin_bottom=0, margin_top=15)
        theme_grid.set_hexpand(False)
        theme_grid.props.valign = Gtk.Align.START
        theme_grid.set_vexpand(True)
        stack.add_titled(theme_grid, "theme_grid", "Settings")

        # ----------------------------------------------
        # Manjaro branding toggle
        manjaro_switch = Gtk.Switch()
        manjaro_switch.set_hexpand(False)

        # get branding state True/False
        self.branding_active = get_asset_state()
        manjaro_switch.set_active(self.branding_active)
        self.branding_handler_id = manjaro_switch.connect("notify::active", self.on_branding_activated)
        # --- branding initialize end
        # ----------------------------------------------

        manjaro_label = Gtk.Label()
        manjaro_label.set_markup("        Manjaro branding")
        manjaro_label.props.halign = Gtk.Align.START

        # wayland toggle
        wayland_switch = Gtk.Switch()
        wayland_switch.set_hexpand(False)
        wayland_enabled = subprocess.run("grep -q '^WaylandEnable=false' /etc/gdm/custom.conf", shell=True)
        if wayland_enabled.returncode == 1:
            wayland_switch.set_active(True)
        else:
            wayland_switch.set_active(False)
        wayland_switch.connect("notify::active", self.on_wayland_activated)
        wayland_label = Gtk.Label()
        wayland_label.set_markup("        Wayland session")
        wayland_label.props.halign = Gtk.Align.START

        # System tray 
        tray_switch = Gtk.Switch()
        tray_switch.set_hexpand(False)
        tray_enabled = subprocess.run(
            "gnome-extensions info appindicatorsupport@rgcjonas.gmail.com | grep -q ENABLED", shell=True)
        if tray_enabled.returncode == 0:
            tray_switch.set_active(True)
        else:
            tray_switch.set_active(False)
        tray_switch.connect("notify::active", self.on_tray_activated)
        tray_label = Gtk.Label()
        tray_label.set_markup("        System tray")
        tray_label.props.halign = Gtk.Align.START

        # Desktop icons
        desk_switch = Gtk.Switch()
        desk_switch.set_hexpand(False)
        desk_enabled = subprocess.run(
            "gnome-extensions info desktop-icons@csoriano | grep -q ENABLED", shell=True)
        if desk_enabled.returncode == 0:
            desk_switch.set_active(True)
        else:
            desk_switch.set_active(False)
        desk_switch.connect("notify::active", self.on_desk_activated)
        desk_label = Gtk.Label()
        desk_label.set_markup("        Desktop icons")
        desk_label.props.halign = Gtk.Align.START

        # Gnome Tweaks
        theme_button = Gtk.Button.new_with_label("Open")
        theme_button.connect("clicked", self.on_gnometweaks_activated)
        theme_label = Gtk.Label()
        theme_label.set_markup("        Gnome tweak tool")
        theme_label.props.halign = Gtk.Align.START

        # Dynamic wallpaper
        dynapaper_button = Gtk.Button.new_with_label("Open")
        dynapaper_button.connect("clicked", self.on_dynapaper_activated)
        dynapaper_label = Gtk.Label()
        dynapaper_label.set_markup("        Dynamic wallpaper settings")
        dynapaper_label.props.halign = Gtk.Align.START

        # Gnome Tweaks
        goa_button = Gtk.Button.new_with_label("Open")
        goa_button.connect("clicked", self.on_goa_activated)
        goa_label = Gtk.Label()
        goa_label.set_markup("        Online accounts")
        goa_label.props.halign = Gtk.Align.START

        # # Color picker
        # self.color_button = Gtk.ColorButton()
        # if Path.is_file(css_file):
        #     try:
        #         with open(css_file) as f:
        #             file = f.read()
        #             current_color = re.search("^@define-color.*theme_selected_bg_color.*#(.*)", file)
        #             current_color = current_color.group(1)
        #     except AttributeError:
        #         current_color = self.highlight_color    
        # else:
        #     current_color = self.highlight_color
        # color = Gdk.RGBA()
        # color.parse(current_color)
        # color.to_string()
        # self.color_button.set_rgba(color)

        # color_label = Gtk.Label()
        # color_label.set_markup("        Application highlight color")
        # color_label.props.halign = Gtk.Align.START
        # choosing a color in the dialogue window emits a signal
        # self.color_button.connect("color-set", self.on_color_chosen)

        # Theme tab layout
        theme_grid.attach(dynapaper_button, 1, 0, 1, 1)
        theme_grid.attach(dynapaper_label, 3, 0, 2, 1)
        theme_grid.attach(theme_button, 1, 1, 1, 1)
        theme_grid.attach(theme_label, 3, 1, 2, 1)
        theme_grid.attach(goa_button, 1, 2, 1, 1)
        theme_grid.attach(goa_label, 3, 2, 2, 1)
        theme_grid.attach(manjaro_switch, 1, 3, 1, 1)
        theme_grid.attach(manjaro_label, 3, 3, 2, 1)
        theme_grid.attach(wayland_switch, 1, 4, 1, 1)
        theme_grid.attach(wayland_label, 3, 4, 2, 1)
        theme_grid.attach(desk_switch, 1, 5, 1, 1)
        theme_grid.attach(desk_label, 3, 5, 2, 1)
        theme_grid.attach(tray_switch, 1, 6, 1, 1)
        theme_grid.attach(tray_label, 3, 6, 2, 1)
        # theme_grid.attach(self.color_button, 1, 3, 1, 1)
        # theme_grid.attach(color_label, 3, 3, 2, 1)

    def set_preview_colors(self, newcolor: str):
        """ load preview images """
        # TODO use property data_dir
        res_directory = Path(__file__).parent / "../../data"  # only if we use git, path exists
        if not res_directory.resolve().exists():
            res_directory = "/usr/share/gls"
        try:
            for key, img in self.previews.items():
                # Normal preview
                shutil.copyfile(f"{res_directory}/pictures/{key}preview.svg", f"{temp_dir}/{key}preview.svg")
                replace_in_file(f"{temp_dir}/{key}preview.svg", "#16a085", self.default_color)
                img.set_from_file(f"{temp_dir}/{key}preview.svg")
                # Selected preview
                shutil.copyfile(f"{res_directory}/pictures/{key}preview.svg", f"{temp_dir}/{key}preview_selected.svg")
                replace_in_file(f"{temp_dir}/{key}preview_selected.svg", "#16a085", newcolor)
        except FileNotFoundError:
            return False

    def create_layout_btn(self, layout, the_grid):
        """ Create desktop element in grid """
        btn = Gtk.RadioButton.new_with_label_from_widget(self.btn_layout_first, layout["label"])
        if not self.btn_layout_first:
            self.btn_layout_first = btn
        btn.connect("toggled", self.on_layout_toggled, layout["id"])
        the_grid.attach(btn, layout["x"], layout["y"], 1, 1)

        preview_img = Gtk.Image()
        self.previews[layout["id"]] = preview_img
        # preview loaded by set_preview_colors()
        btn.image = preview_img  # link img to checkbox for easy find
        # reduce opacity of de-selected previews
        if btn.get_active():
            preview_img.set_opacity(Opacity.TOP)
        else:
            preview_img.set_opacity(Opacity.MIDDLE)
        # make preview images clickable
        event_img = Gtk.EventBox()
        event_img.connect("button-release-event", self.on_click_img)  # click in box
        event_img.connect("enter-notify-event", self.on_over_img, True)  # mouse over box
        event_img.connect("leave-notify-event", self.on_over_img, False)  # mouse out box
        event_img.add(preview_img)  # add img in box
        event_img.btn = btn  # link btn to box for easy find
        the_grid.attach(event_img, layout["x"], layout["y"] + 1, 1, 1)  # add box and not img in grid

    @property
    def current_color(self):
        return self._current_color

    @current_color.setter
    def current_color(self, value):
        """ assign new curent color :
                change preview images
                change btn theme color
                not change file.css

            if not value then read value in file.css
        """
        if not value:
            value = "#16a085"
            try:
                with open(css_file) as fread:
                    file = fread.read()
                    value = re.search("^@define-color.*theme_selected_bg_color.*#(.*);", file)
                    value = f"#{value.group(1)}"
            except FileNotFoundError:
                value = self.highlight_color
            except AttributeError:
                value = self.highlight_color
        self._current_color = value
        self.set_preview_colors(self._current_color)
        # ??? and (re-)change btn theme color
        if self.color_button:
            color = Gdk.RGBA()
            color.parse(self._current_color)
            self.color_button.set_rgba(color)

    ###
    # event functions
    ###

    def on_layout_toggled(self, button, name):
        """ change defaut layout """
        state = Opacity.LOW
        if button.get_active():
            state = Opacity.TOP
            self.layout = name
            print("active layout:", self.layout)
            button.image.set_from_file(f"{temp_dir}/{self.layout}preview_selected.svg")
        else:
            button.image.set_from_file(f"{temp_dir}/{self.layout}preview.svg")
        button.image.set_opacity(state)  # change img opacity from state

    def on_over_img(self, box, event, is_over_image):
        """ on mouse over / out : change opacity """
        if box.btn.get_active():
            return
        if is_over_image:
            box.btn.image.set_opacity(Opacity.MIDDLE)
        else:
            box.btn.image.set_opacity(Opacity.LOW)

    def on_color_chosen(self, user_data):
        """ after chose a theme color """
        col = self.color_button.get_rgba().to_string()[4:-1:]
        # convert color to hexadecimal
        col = col.split(",")
        col = (int(x) for x in col)
        col = "#%02x%02x%02x" % tuple(col)
        set_highlight_color(col)
        self.current_color = col

    def on_wayland_activated(self, switch, gparam):
        if switch.get_active():
            state = "on"
            enable_wayland()
        else:
            state = "off"
            disable_wayland()
        print("Wayland was turned", state)

    def on_desk_activated(self, switch, gparam):
        if switch.get_active():
            state = "on"
            subprocess.run("gnome-extensions enable desktop-icons@csoriano", shell=True)
        else:
            state = "off"
            subprocess.run("gnome-extensions disable desktop-icons@csoriano", shell=True)
        print("Desktop icons was turned", state)

    def on_tray_activated(self, switch, gparam):
        if switch.get_active():
            state = "on"
            subprocess.run("gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com", shell=True)
        else:
            state = "off"
            subprocess.run("gnome-extensions disable appindicatorsupport@rgcjonas.gmail.com", shell=True)
        print("System tray was turned", state)

    # ------------- branding -------------------------------------------
    def on_branding_activated(self, switch, gparam):
        self.change_branding(switch)

    def change_branding(self, switch):
        # https://python-gtk-3-tutorial.readthedocs.io/en/latest/basics.html#main-loop-and-signals
        # disconnect the signal
        switch.disconnect(self.branding_handler_id)

        # print entry state aka the new state
        print(f"(ENTRY) switch.get_active() is {switch.get_active()} - new state")
        print(f"(ENTRY) switch.get_state() is {switch.get_state()} - new state")

        # switch branding
        if switch.get_active():
            result, _ = do_branding(False)
            if result:
                self.branding_active = True
        else:
            result, _ = do_branding(True)
            if result:
                self.branding_active = False
        if not result:
            self.branding_active = get_asset_state()
            switch.set_active(self.branding_active)

        # reconnect signal
        self.branding_handler_id = switch.connect("notify::active", self.on_branding_activated)

        # print the exit state
        print(f"(EXIT) switch.get_active() is {switch.get_active()} - final state")
        print(f"(EXIT) switch.get_state() is {switch.get_state()} - final state")
    # ------------- end branding ---------------------------------------

    def on_gnometweaks_activated(self, button):
        subprocess.Popen("gnome-tweaks", shell=True)

    def on_goa_activated(self, button):
        subprocess.Popen("gnome-control-center online-accounts", shell=True)

    def on_dynapaper_activated(self, button):
        subprocess.Popen("dynamic-wallpaper-editor", shell=True)

    def on_click_img(self, box, event):
        """Make images clickable
            change checkbox state and call on_layout_toggled()"""
        box.btn.set_active(True)

    def dialog_error(self, title: str, message: str):
        """display error modal dialog"""
        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            message_format=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def on_layoutapply_clicked(self, button):
        """ apply defaut layout to user """
        commands = {
            'manjaro': (
                'gsettings set org.gnome.shell enabled-extensions "[\'dash-to-dock@micxgx.gmail.com\', '
                '\'user-theme@gnome-shell-extensions.gcampax.github.com\', '
                '\'appindicatorsupport@rgcjonas.gmail.com\', \'pamac-updates@manjaro.org\']"',
                'gsettings set org.gnome.shell.extensions.dash-to-dock dock-position LEFT',
                'gsettings set org.gnome.shell.extensions.dash-to-dock extend-height false',
                'gsettings set org.gnome.shell.extensions.dash-to-dock dock-fixed false',
                'gsettings set org.gnome.shell.extensions.dash-to-dock intellihide true',
                'gsettings set org.gnome.desktop.wm.preferences button-layout ":minimize,maximize,close"',
            ),
            'classic': (
                'gsettings set org.gnome.shell enabled-extensions "[\'dash-to-panel@jderose9.github.com\', '
                '\'user-theme@gnome-shell-extensions.gcampax.github.com\', '
                '\'appindicatorsupport@rgcjonas.gmail.com\', \'pamac-updates@manjaro.org\', '
                '\'arc-menu@linxgem33.com\']"',
                'gsettings --schemadir /usr/share/gnome-shell/extensions/dash-to-panel@jderose9.github.com/schemas '
                'set org.gnome.shell.extensions.dash-to-panel show-show-apps-button false',
                'gsettings --schemadir /usr/share/gnome-shell/extensions/dash-to-panel@jderose9.github.com/schemas '
                'set org.gnome.shell.extensions.dash-to-panel panel-position BOTTOM',
                'gsettings --schemadir /usr/share/gnome-shell/extensions/arc-menu@linxgem33.com/schemas '
                'set org.gnome.shell.extensions.arc-menu custom-menu-button-icon-size 32.0',
                'gsettings set org.gnome.desktop.wm.preferences button-layout ":minimize,maximize,close"'
            ),
            'modern': (
                'gsettings set org.gnome.shell enabled-extensions "[\'dash-to-dock@micxgx.gmail.com\', '
                '\'user-theme@gnome-shell-extensions.gcampax.github.com\', \'unite@hardpixel.eu\', '
                '\'pamac-updates@manjaro.org\']"',
                'gsettings set org.gnome.shell.extensions.dash-to-dock dock-position BOTTOM',
                'gsettings set org.gnome.shell.extensions.dash-to-dock extend-height false',
                'gsettings set org.gnome.shell.extensions.dash-to-dock dock-fixed false',
                'gsettings set org.gnome.desktop.wm.preferences button-layout "close,minimize,maximize:"'
            ),
            'gnome': (
                'gsettings set org.gnome.shell enabled-extensions "[\'pamac-updates@manjaro.org\', '
                '\'user-theme@gnome-shell-extensions.gcampax.github.com\']"',
                'gsettings set org.gnome.desktop.wm.preferences button-layout ":minimize,maximize,close"'
            )

        }

        get_extensions(self.layout)
        ret = True
        good = True
        err = None
        for cmd in commands.get(self.layout, ""):
            good, err = shell(cmd)
        if not good:
            # here we continue commands ... good idea ??
            ret = False
        if not ret:
            self.dialog_error(f"Error for set layout \"{self.layout}\"", err)
        else:
            # save only if not one error
            with UserConf() as conf:
                self.layout = conf.write({"layout": self.layout})
                print("Layout applied")
