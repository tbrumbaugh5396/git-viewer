#!/usr/bin/env python3
"""
Meta Repository Panel for Git Repository Viewer
Provides support for meta repositories using the meta package
"""

import wx
import wx.lib.agw.aui as aui
import os
import json
import subprocess
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class MetaPanel(wx.Panel):
    """Panel for Meta repository operations and management"""

    def __init__(self, parent, main_frame):
        super().__init__(parent)
        self.main_frame = main_frame
        self.meta_path = None
        self.meta_config = None
        self.projects = []

        self.create_ui()
        self.check_meta_availability()

    def create_ui(self):
        """Create the Meta panel UI"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left panel - meta info and projects
        left_panel = wx.Panel(self)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # Meta repository info
        meta_info_box = wx.StaticBox(left_panel, label="Meta Repository")
        meta_info_sizer = wx.StaticBoxSizer(meta_info_box, wx.VERTICAL)

        self.meta_path_text = wx.StaticText(
            left_panel, label="No meta repository detected")
        self.meta_status_text = wx.StaticText(left_panel, label="")
        self.projects_count_text = wx.StaticText(left_panel, label="")

        meta_info_sizer.Add(self.meta_path_text, 0, wx.EXPAND | wx.ALL, 5)
        meta_info_sizer.Add(self.meta_status_text, 0, wx.EXPAND | wx.ALL, 5)
        meta_info_sizer.Add(self.projects_count_text, 0, wx.EXPAND | wx.ALL, 5)

        # Meta operations toolbar
        meta_toolbar = wx.Panel(left_panel)
        meta_toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.init_meta_btn = wx.Button(meta_toolbar, label="Init Meta")
        self.clone_meta_btn = wx.Button(meta_toolbar, label="Clone Meta")
        self.refresh_meta_btn = wx.Button(meta_toolbar, label="Refresh")

        meta_toolbar_sizer.Add(self.init_meta_btn, 0, wx.ALL, 2)
        meta_toolbar_sizer.Add(self.clone_meta_btn, 0, wx.ALL, 2)
        meta_toolbar_sizer.Add(self.refresh_meta_btn, 0, wx.ALL, 2)
        meta_toolbar.SetSizer(meta_toolbar_sizer)

        # Projects list
        projects_box = wx.StaticBox(left_panel, label="Projects")
        projects_sizer = wx.StaticBoxSizer(projects_box, wx.VERTICAL)

        # Projects toolbar
        projects_toolbar = wx.Panel(left_panel)
        projects_toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.add_project_btn = wx.Button(projects_toolbar, label="Add Project")
        self.import_project_btn = wx.Button(projects_toolbar,
                                            label="Import Project")
        self.remove_project_btn = wx.Button(projects_toolbar,
                                            label="Remove Project")

        projects_toolbar_sizer.Add(self.add_project_btn, 0, wx.ALL, 2)
        projects_toolbar_sizer.Add(self.import_project_btn, 0, wx.ALL, 2)
        projects_toolbar_sizer.Add(self.remove_project_btn, 0, wx.ALL, 2)
        projects_toolbar.SetSizer(projects_toolbar_sizer)

        # Projects list control
        self.projects_list = wx.ListCtrl(left_panel,
                                         style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.projects_list.AppendColumn("Project", width=150)
        self.projects_list.AppendColumn("Path", width=200)
        self.projects_list.AppendColumn("URL", width=250)
        self.projects_list.AppendColumn("Status", width=80)

        projects_sizer.Add(projects_toolbar, 0, wx.EXPAND | wx.ALL, 2)
        projects_sizer.Add(self.projects_list, 1, wx.EXPAND | wx.ALL, 2)

        left_sizer.Add(meta_info_sizer, 0, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(meta_toolbar, 0, wx.EXPAND | wx.ALL, 2)
        left_sizer.Add(projects_sizer, 1, wx.EXPAND | wx.ALL, 5)
        left_panel.SetSizer(left_sizer)

        # Right panel - meta operations and output
        right_panel = wx.Panel(self)
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        # Meta operations notebook
        self.meta_notebook = wx.Notebook(right_panel)

        # Commands panel
        self.commands_panel = MetaCommandsPanel(self.meta_notebook, self)
        self.meta_notebook.AddPage(self.commands_panel, "Commands")

        # Project details panel
        self.project_details_panel = ProjectDetailsPanel(
            self.meta_notebook, self)
        self.meta_notebook.AddPage(self.project_details_panel,
                                   "Project Details")

        # Output panel
        self.output_panel = MetaOutputPanel(self.meta_notebook, self)
        self.meta_notebook.AddPage(self.output_panel, "Output")

        right_sizer.Add(self.meta_notebook, 1, wx.EXPAND | wx.ALL, 5)
        right_panel.SetSizer(right_sizer)

        # Add panels to main sizer
        sizer.Add(left_panel, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(right_panel, 2, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

        # Bind events
        self.init_meta_btn.Bind(wx.EVT_BUTTON, self.on_init_meta)
        self.clone_meta_btn.Bind(wx.EVT_BUTTON, self.on_clone_meta)
        self.refresh_meta_btn.Bind(wx.EVT_BUTTON, self.on_refresh_meta)
        self.add_project_btn.Bind(wx.EVT_BUTTON, self.on_add_project)
        self.import_project_btn.Bind(wx.EVT_BUTTON, self.on_import_project)
        self.remove_project_btn.Bind(wx.EVT_BUTTON, self.on_remove_project)
        self.projects_list.Bind(wx.EVT_LIST_ITEM_SELECTED,
                                self.on_project_selected)
        self.projects_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
                                self.on_project_activated)

        # Initially disable meta-specific buttons
        self.enable_meta_buttons(False)

    def check_meta_availability(self):
        """Check if meta CLI is available"""
        try:
            result = subprocess.run(['meta', '--version'],
                                    capture_output=True,
                                    text=True,
                                    timeout=5)
            if result.returncode == 0:
                self.meta_status_text.SetLabel("Meta CLI: Available")
                return True
            else:
                self.meta_status_text.SetLabel("Meta CLI: Not available")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.meta_status_text.SetLabel(
                "Meta CLI: Not available (install with: npm install -g meta)")
            return False

    def enable_meta_buttons(self, enable: bool):
        """Enable or disable meta-specific buttons"""
        buttons = [
            self.add_project_btn, self.import_project_btn,
            self.remove_project_btn
        ]
        for button in buttons:
            button.Enable(enable)

    def check_meta_repository(self, path: str):
        """Check if the given path is a meta repository"""
        meta_file = os.path.join(path, '.meta')
        if os.path.exists(meta_file):
            self.meta_path = path
            self.load_meta_config()
            self.enable_meta_buttons(True)
            return True
        else:
            self.meta_path = None
            self.meta_config = None
            self.projects = []
            self.enable_meta_buttons(False)
            self.update_display()
            return False

    def load_meta_config(self):
        """Load the .meta configuration file"""
        if not self.meta_path:
            return

        meta_file = os.path.join(self.meta_path, '.meta')
        try:
            with open(meta_file, 'r') as f:
                self.meta_config = json.load(f)

            self.projects = self.meta_config.get('projects', [])
            self.update_display()

        except Exception as e:
            self.output_panel.add_output(f"Error loading .meta file: {str(e)}")
            self.meta_config = None
            self.projects = []

    def update_display(self):
        """Update the display with current meta repository info"""
        if self.meta_path and self.meta_config:
            self.meta_path_text.SetLabel(f"Path: {self.meta_path}")
            self.projects_count_text.SetLabel(
                f"Projects: {len(self.projects)}")

            # Update projects list
            self.projects_list.DeleteAllItems()
            for i, project in enumerate(self.projects):
                project_name = list(project.keys())[0]
                project_info = project[project_name]
                project_path = os.path.join(self.meta_path, project_name)

                index = self.projects_list.InsertItem(i, project_name)
                self.projects_list.SetItem(index, 1, project_name)
                self.projects_list.SetItem(index, 2, project_info)

                # Check if project is cloned
                if os.path.exists(project_path):
                    self.projects_list.SetItem(index, 3, "Cloned")
                    self.projects_list.SetItemTextColour(
                        index, wx.Colour(0, 150, 0))
                else:
                    self.projects_list.SetItem(index, 3, "Missing")
                    self.projects_list.SetItemTextColour(
                        index, wx.Colour(150, 0, 0))

                self.projects_list.SetItemData(index, i)
        else:
            self.meta_path_text.SetLabel("No meta repository detected")
            self.projects_count_text.SetLabel("")
            self.projects_list.DeleteAllItems()

    def execute_meta_command(self,
                             command: str,
                             *args,
                             cwd: Optional[str] = None):
        """Execute a meta command"""
        if not self.check_meta_availability():
            wx.MessageBox(
                "Meta CLI is not available. Please install it with: npm install -g meta",
                "Meta Not Available", wx.OK | wx.ICON_ERROR)
            return

        def worker():
            try:
                work_dir = cwd or self.meta_path or os.getcwd()
                self.main_frame.update_status(f"Executing meta {command}...")

                result = subprocess.run(
                    ['meta'] + [command] + list(args),
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )

                output = result.stdout + result.stderr
                wx.CallAfter(self.on_meta_command_complete, command, output,
                             result.returncode)

            except subprocess.TimeoutExpired:
                wx.CallAfter(self.on_meta_command_complete, command,
                             "Command timed out", 1)
            except Exception as e:
                wx.CallAfter(self.on_meta_command_complete, command, str(e), 1)

        threading.Thread(target=worker, daemon=True).start()

    def on_meta_command_complete(self, command: str, output: str,
                                 return_code: int):
        """Handle meta command completion"""
        self.main_frame.update_status("Ready")

        if return_code == 0:
            self.output_panel.add_output(
                f"Meta {command} completed successfully:\n{output}")

            # Refresh if needed
            if command in ['init', 'project', 'git']:
                self.on_refresh_meta(None)
        else:
            self.output_panel.add_output(f"Meta {command} failed:\n{output}")

        # Switch to output tab
        self.meta_notebook.SetSelection(2)

    # Event handlers
    def on_init_meta(self, event):
        """Initialize a new meta repository"""
        if self.main_frame.current_repo_path:
            # Initialize in current repository directory
            path = self.main_frame.current_repo_path
        else:
            # Ask user to select directory
            with wx.DirDialog(
                    self, "Choose directory for meta repository") as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                path = dialog.GetPath()

        self.execute_meta_command('init', cwd=path)

    def on_clone_meta(self, event):
        """Clone a meta repository"""
        dialog = MetaCloneDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            url, path = dialog.get_values()
            self.execute_meta_command('git', 'clone', url, cwd=path)
        dialog.Destroy()

    def on_refresh_meta(self, event):
        """Refresh meta repository information"""
        if self.meta_path:
            self.load_meta_config()
        elif self.main_frame.current_repo_path:
            self.check_meta_repository(self.main_frame.current_repo_path)

    def on_add_project(self, event):
        """Add a new project to meta repository"""
        dialog = AddProjectDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            folder, url = dialog.get_values()
            self.execute_meta_command('project', 'create', folder, url)
        dialog.Destroy()

    def on_import_project(self, event):
        """Import an existing project to meta repository"""
        dialog = AddProjectDialog(self, title="Import Project")
        if dialog.ShowModal() == wx.ID_OK:
            folder, url = dialog.get_values()
            self.execute_meta_command('project', 'import', folder, url)
        dialog.Destroy()

    def on_remove_project(self, event):
        """Remove a project from meta repository"""
        selected = self.projects_list.GetFirstSelected()
        if selected == -1:
            return

        project_name = self.projects_list.GetItemText(selected, 0)

        if wx.MessageBox(
                f"Remove project '{project_name}' from meta repository?",
                "Confirm Remove", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            # Remove from .meta file manually since meta CLI doesn't have a remove command
            try:
                self.projects = [
                    p for p in self.projects if project_name not in p
                ]
                self.meta_config['projects'] = self.projects

                meta_file = os.path.join(self.meta_path, '.meta')
                with open(meta_file, 'w') as f:
                    json.dump(self.meta_config, f, indent=2)

                self.update_display()
                self.output_panel.add_output(
                    f"Removed project '{project_name}' from meta repository")

            except Exception as e:
                wx.MessageBox(f"Error removing project: {str(e)}", "Error",
                              wx.OK | wx.ICON_ERROR)

    def on_project_selected(self, event):
        """Handle project selection"""
        selected = self.projects_list.GetFirstSelected()
        if selected != -1:
            project_index = self.projects_list.GetItemData(selected)
            project = self.projects[project_index]
            project_name = list(project.keys())[0]

            # Update project details panel
            self.project_details_panel.show_project(project_name,
                                                    project[project_name])

    def on_project_activated(self, event):
        """Handle project double-click - open in Git viewer"""
        selected = self.projects_list.GetFirstSelected()
        if selected != -1:
            project_name = self.projects_list.GetItemText(selected, 0)
            project_path = os.path.join(self.meta_path, project_name)

            if os.path.exists(project_path):
                # Load this project as a Git repository
                if self.main_frame.load_repository(project_path):
                    # Switch to Git tab
                    self.main_frame.notebook.SetSelection(0)
            else:
                # Ask if user wants to clone the project
                if wx.MessageBox(
                        f"Project '{project_name}' is not cloned. Clone it now?",
                        "Clone Project",
                        wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
                    self.execute_meta_command('git', 'update')


class MetaCommandsPanel(wx.Panel):
    """Panel for executing meta commands"""

    def __init__(self, parent, meta_panel):
        super().__init__(parent)
        self.meta_panel = meta_panel

        self.create_ui()

    def create_ui(self):
        """Create the meta commands UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Common commands section
        common_box = wx.StaticBox(self, label="Common Commands")
        common_sizer = wx.StaticBoxSizer(common_box, wx.VERTICAL)

        # Git operations
        git_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.git_status_btn = wx.Button(self, label="Git Status")
        self.git_pull_btn = wx.Button(self, label="Git Pull")
        self.git_push_btn = wx.Button(self, label="Git Push")
        self.git_update_btn = wx.Button(self, label="Git Update")

        git_sizer.Add(self.git_status_btn, 0, wx.ALL, 2)
        git_sizer.Add(self.git_pull_btn, 0, wx.ALL, 2)
        git_sizer.Add(self.git_push_btn, 0, wx.ALL, 2)
        git_sizer.Add(self.git_update_btn, 0, wx.ALL, 2)

        # NPM operations
        npm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.npm_install_btn = wx.Button(self, label="NPM Install")
        self.npm_update_btn = wx.Button(self, label="NPM Update")
        self.npm_link_btn = wx.Button(self, label="NPM Link")

        npm_sizer.Add(self.npm_install_btn, 0, wx.ALL, 2)
        npm_sizer.Add(self.npm_update_btn, 0, wx.ALL, 2)
        npm_sizer.Add(self.npm_link_btn, 0, wx.ALL, 2)

        common_sizer.Add(git_sizer, 0, wx.EXPAND | wx.ALL, 5)
        common_sizer.Add(npm_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Custom command section
        custom_box = wx.StaticBox(self, label="Custom Command")
        custom_sizer = wx.StaticBoxSizer(custom_box, wx.VERTICAL)

        cmd_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cmd_sizer.Add(wx.StaticText(self, label="meta"), 0,
                      wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.custom_cmd_text = wx.TextCtrl(self, size=(300, -1), style=wx.TE_PROCESS_ENTER)
        self.execute_btn = wx.Button(self, label="Execute")

        cmd_sizer.Add(self.custom_cmd_text, 1, wx.ALL, 5)
        cmd_sizer.Add(self.execute_btn, 0, wx.ALL, 5)

        custom_sizer.Add(cmd_sizer, 0, wx.EXPAND | wx.ALL, 5)

        sizer.Add(common_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(custom_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

        # Bind events
        self.git_status_btn.Bind(
            wx.EVT_BUTTON,
            lambda e: self.meta_panel.execute_meta_command('git', 'status'))
        self.git_pull_btn.Bind(
            wx.EVT_BUTTON,
            lambda e: self.meta_panel.execute_meta_command('git', 'pull'))
        self.git_push_btn.Bind(
            wx.EVT_BUTTON,
            lambda e: self.meta_panel.execute_meta_command('git', 'push'))
        self.git_update_btn.Bind(
            wx.EVT_BUTTON,
            lambda e: self.meta_panel.execute_meta_command('git', 'update'))
        self.npm_install_btn.Bind(
            wx.EVT_BUTTON,
            lambda e: self.meta_panel.execute_meta_command('npm', 'install'))
        self.npm_update_btn.Bind(
            wx.EVT_BUTTON,
            lambda e: self.meta_panel.execute_meta_command('npm', 'update'))
        self.npm_link_btn.Bind(
            wx.EVT_BUTTON, lambda e: self.meta_panel.execute_meta_command(
                'npm', 'link', '--all'))
        self.execute_btn.Bind(wx.EVT_BUTTON, self.on_execute_custom)
        self.custom_cmd_text.Bind(wx.EVT_TEXT_ENTER, self.on_execute_custom)

    def on_execute_custom(self, event):
        """Execute custom command"""
        command = self.custom_cmd_text.GetValue().strip()
        if command:
            # Split command into parts
            parts = command.split()
            if parts:
                self.meta_panel.execute_meta_command(*parts)
            self.custom_cmd_text.Clear()


class ProjectDetailsPanel(wx.Panel):
    """Panel for showing project details"""

    def __init__(self, parent, meta_panel):
        super().__init__(parent)
        self.meta_panel = meta_panel

        self.create_ui()

    def create_ui(self):
        """Create the project details UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Project info
        self.project_name_text = wx.StaticText(self,
                                               label="No project selected")
        self.project_url_text = wx.StaticText(self, label="")
        self.project_path_text = wx.StaticText(self, label="")
        self.project_status_text = wx.StaticText(self, label="")

        # Project operations
        operations_box = wx.StaticBox(self, label="Project Operations")
        operations_sizer = wx.StaticBoxSizer(operations_box, wx.VERTICAL)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.clone_project_btn = wx.Button(self, label="Clone Project")
        self.open_project_btn = wx.Button(self, label="Open in Git Viewer")
        self.terminal_project_btn = wx.Button(self, label="Open Terminal")

        btn_sizer.Add(self.clone_project_btn, 0, wx.ALL, 2)
        btn_sizer.Add(self.open_project_btn, 0, wx.ALL, 2)
        btn_sizer.Add(self.terminal_project_btn, 0, wx.ALL, 2)

        operations_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)

        sizer.Add(self.project_name_text, 0, wx.ALL, 10)
        sizer.Add(self.project_url_text, 0, wx.ALL, 5)
        sizer.Add(self.project_path_text, 0, wx.ALL, 5)
        sizer.Add(self.project_status_text, 0, wx.ALL, 5)
        sizer.Add(operations_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

        # Bind events
        self.clone_project_btn.Bind(wx.EVT_BUTTON, self.on_clone_project)
        self.open_project_btn.Bind(wx.EVT_BUTTON, self.on_open_project)
        self.terminal_project_btn.Bind(wx.EVT_BUTTON, self.on_terminal_project)

        # Initially disable buttons
        self.enable_buttons(False)

    def enable_buttons(self, enable: bool):
        """Enable or disable project buttons"""
        self.clone_project_btn.Enable(enable)
        self.open_project_btn.Enable(enable)
        self.terminal_project_btn.Enable(enable)

    def show_project(self, project_name: str, project_url: str):
        """Show project details"""
        self.current_project = project_name
        self.current_url = project_url

        self.project_name_text.SetLabel(f"Project: {project_name}")
        self.project_url_text.SetLabel(f"URL: {project_url}")

        project_path = os.path.join(self.meta_panel.meta_path, project_name)
        self.project_path_text.SetLabel(f"Path: {project_path}")

        if os.path.exists(project_path):
            self.project_status_text.SetLabel("Status: Cloned")
            self.project_status_text.SetForegroundColour(wx.Colour(0, 150, 0))
        else:
            self.project_status_text.SetLabel("Status: Not cloned")
            self.project_status_text.SetForegroundColour(wx.Colour(150, 0, 0))

        self.enable_buttons(True)

    def on_clone_project(self, event):
        """Clone the selected project"""
        if hasattr(self, 'current_project'):
            self.meta_panel.execute_meta_command('git', 'update')

    def on_open_project(self, event):
        """Open project in Git viewer"""
        if hasattr(self, 'current_project'):
            project_path = os.path.join(self.meta_panel.meta_path,
                                        self.current_project)
            if os.path.exists(project_path):
                self.meta_panel.main_frame.load_repository(project_path)
                self.meta_panel.main_frame.notebook.SetSelection(0)

    def on_terminal_project(self, event):
        """Open terminal in project directory"""
        if hasattr(self, 'current_project'):
            project_path = os.path.join(self.meta_panel.meta_path,
                                        self.current_project)
            if os.path.exists(project_path):
                self.meta_panel.main_frame.current_repo_path = project_path
                self.meta_panel.main_frame.on_terminal(event)


class MetaOutputPanel(wx.Panel):
    """Panel for displaying meta command output"""

    def __init__(self, parent, meta_panel):
        super().__init__(parent)
        self.meta_panel = meta_panel

        self.create_ui()

    def create_ui(self):
        """Create the output panel UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Toolbar
        toolbar_panel = wx.Panel(self)
        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.clear_btn = wx.Button(toolbar_panel, label="Clear")
        toolbar_sizer.Add(self.clear_btn, 0, wx.ALL, 2)
        toolbar_panel.SetSizer(toolbar_sizer)

        # Output text control
        self.output_text = wx.TextCtrl(self,
                                       style=wx.TE_MULTILINE | wx.TE_READONLY
                                       | wx.TE_RICH2)
        self.output_text.SetFont(
            wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL))

        sizer.Add(toolbar_panel, 0, wx.EXPAND | wx.ALL, 2)
        sizer.Add(self.output_text, 1, wx.EXPAND | wx.ALL, 2)
        self.SetSizer(sizer)

        # Bind events
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)

    def add_output(self, text: str):
        """Add output text"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.output_text.AppendText(f"[{timestamp}] {text}\n\n")

    def on_clear(self, event):
        """Handle clear button"""
        self.output_text.Clear()


# Dialog classes for meta operations
class MetaCloneDialog(wx.Dialog):
    """Dialog for cloning a meta repository"""

    def __init__(self, parent):
        super().__init__(parent,
                         title="Clone Meta Repository",
                         size=(500, 200))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # URL field
        url_sizer = wx.BoxSizer(wx.HORIZONTAL)
        url_sizer.Add(wx.StaticText(panel, label="Meta Repository URL:"), 0,
                      wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.url_text = wx.TextCtrl(panel, size=(350, -1))
        url_sizer.Add(self.url_text, 1, wx.ALL, 5)

        # Directory field
        dir_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dir_sizer.Add(wx.StaticText(panel, label="Clone Directory:"), 0,
                      wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.dir_text = wx.TextCtrl(panel, size=(250, -1))
        self.browse_btn = wx.Button(panel, label="Browse...")
        dir_sizer.Add(self.dir_text, 1, wx.ALL, 5)
        dir_sizer.Add(self.browse_btn, 0, wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "Clone")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        sizer.Add(url_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(dir_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(sizer)

        # Bind events
        self.browse_btn.Bind(wx.EVT_BUTTON, self.on_browse)

        # Set default directory
        self.dir_text.SetValue(os.path.expanduser("~/"))

    def on_browse(self, event):
        """Handle browse button"""
        with wx.DirDialog(self, "Choose clone directory") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.dir_text.SetValue(dialog.GetPath())

    def get_values(self):
        """Get the entered values"""
        return self.url_text.GetValue(), self.dir_text.GetValue()


class AddProjectDialog(wx.Dialog):
    """Dialog for adding/importing a project"""

    def __init__(self, parent, title="Add Project"):
        super().__init__(parent, title=title, size=(500, 200))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Folder field
        folder_sizer = wx.BoxSizer(wx.HORIZONTAL)
        folder_sizer.Add(wx.StaticText(panel, label="Project Folder:"), 0,
                         wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.folder_text = wx.TextCtrl(panel, size=(200, -1))
        folder_sizer.Add(self.folder_text, 1, wx.ALL, 5)

        # URL field
        url_sizer = wx.BoxSizer(wx.HORIZONTAL)
        url_sizer.Add(wx.StaticText(panel, label="Repository URL:"), 0,
                      wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.url_text = wx.TextCtrl(panel, size=(350, -1))
        url_sizer.Add(self.url_text, 1, wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "Add")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        sizer.Add(folder_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(url_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(sizer)

    def get_values(self):
        """Get the entered values"""
        return self.folder_text.GetValue(), self.url_text.GetValue()
