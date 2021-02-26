import sublime
import sublime_plugin
import uuid
import random
import datetime
from os import path as pt

class misc_async(sublime_plugin.TextCommand):
    def run(self, edit, command, args):
        sublime.set_timeout(lambda: self.view.run_command(command, args), 0)

# Similar to ChainOfCommand, but generates a single undo rather than multiple.
class misc_chain(sublime_plugin.TextCommand):
    def run(self, edit, commands):
        for command in commands:
            self.view.window().run_command(*command)

class misc_gen_uuid(sublime_plugin.TextCommand):
    def run(self, edit):
        for region in self.view.sel():
            self.view.replace(edit, region, str(uuid.uuid4()))

class misc_gen_uuid_no_dashes(sublime_plugin.TextCommand):
    def run(self, edit):
        for region in self.view.sel():
            self.view.replace(edit, region, uuid.uuid4().hex)

# TODO: option to pad seq with zeros.
class misc_gen_seq(sublime_plugin.TextCommand):
    def run(self, edit, start = 0):
        num = start
        for region in self.view.sel():
            self.view.replace(edit, region, str(num))
            num += 1

hex_chars = '0123456789abcdef'

class misc_gen_hex(sublime_plugin.TextCommand):
    def run(self, edit):
        for region in self.view.sel():
            start = min(region.a, region.b)
            end = max(region.a, region.b)
            text = ''.join(random.choice(hex_chars) for _ in range(end - start))
            self.view.replace(edit, region, text)

class misc_gen_datetime(sublime_plugin.TextCommand):
    def run(self, edit):
        text = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M%:%SZ')
        for region in self.view.sel():
            self.view.replace(edit, region, text)

class misc_context_selectors(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key == 'misc_selector_prev_line_eol':
            index = prev_eol(view)
            return index >= 0 and view.match_selector(index, operand)
        if key == 'misc_selector_next_line_eol':
            return view.match_selector(next_eol(view), operand)
        return None

def bol(view):
    return view.line(first_sel(view)).begin()

def eol(view):
    return view.line(first_sel(view)).end()

def prev_eol(view):
    index = bol(view) - 1
    return view.line(index).end() if index >= 0 else -1

def next_eol(view):
    return view.line(eol(view) + 1).end()

def first_sel(view):
    return view.sel()[0]

class misc_prompt_select_recent_folder(sublime_plugin.WindowCommand):
    def run(self):
        path = session_path()
        if not path:
            self.window.status_message('session file not found')
            return

        with open(path, 'r', encoding='UTF-8') as file:
            session = sublime.decode_value(file.read())

        folders = session['folder_history'] or []

        def select(index):
            if index >= 0:
                switch_to_folder(folders[index])

        self.window.show_quick_panel(
            list(unexpand_paths(folders)),
            select,
            flags=sublime.MONOSPACE_FONT,
            placeholder='select folder',
        )

def switch_to_folder(folder):
    window = sublime.active_window()
    if window and folder in window.folders():
        return

    for window in sublime.windows():
        if folder in window.folders():
            window.bring_to_front()
            return

    window = sublime.active_window()
    if not window or len(window.folders()):
        sublime.run_command('new_window')
    sublime.active_window().set_project_data({'folders': [{'path': folder}]})

def session_path():
    session_dir = pt.join(pt.dirname(sublime.packages_path()), 'Local')

    auto_session_path = pt.join(session_dir, 'Auto Save Session.sublime_session')
    if pt.isfile(auto_session_path):
        return auto_session_path

    session_path = pt.join(session_dir, 'Session.sublime_session')
    if pt.isfile(session_path):
        return session_path

    return None

def unexpand_paths(paths):
    home = pt.expanduser('~')

    for path in paths:
        if path.startswith(home):
            yield pt.join('~', pt.relpath(path, home))
        else:
            yield path
