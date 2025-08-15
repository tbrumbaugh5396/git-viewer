#!/usr/bin/env python3
"""
Git Repository Viewer GUI Application
A comprehensive Git and Metarepo management tool using wxPython
"""

import wx
import os
import sys
import subprocess
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import git
    from git import Repo, InvalidGitRepositoryError
except ImportError:
    print("GitPython not found. Please install: pip install GitPython")
    sys.exit(1)

# Import timeline panel - handle both package and script execution
try:
    # Try relative import first (for package execution)
    from .timeline_panel import TimelinePanel
    from .git_panels import (
        BranchesPanel, RemotesPanel, FilesPanel, CommitsPanel,
        FileContentPanel, DiffPanel, OutputPanel
    )
    from .git_dialogs import CloneDialog, CommitDialog, MergeDialog, ConfigDialog
    from .meta_panel import MetaPanel
except ImportError:
    # Fall back to absolute import (for script execution)
    from timeline_panel import TimelinePanel
    from git_panels import (
        BranchesPanel, RemotesPanel, FilesPanel, CommitsPanel,
        FileContentPanel, DiffPanel, OutputPanel
    )
    from git_dialogs import CloneDialog, CommitDialog, MergeDialog, ConfigDialog
    from meta_panel import MetaPanel


class GitViewerApp(wx.App):
    """Main application class"""

    def OnInit(self):
        self.frame = MainFrame()
        self.frame.Show()
        return True


class MainFrame(wx.Frame):
    """Main application window"""

    def __init__(self):
        super().__init__(None, title="Git Repository Viewer", size=(1400, 900))

        # Initialize variables
        self.current_repo_path = None
        self.current_repo = None

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.create_status_bar()

        # Create main panel with notebook for tabs
        self.create_main_panel()

        # Center the window
        self.Center()

    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        open_repo_item = file_menu.Append(wx.ID_OPEN,
                                          "&Open Repository...\tCtrl+O")
        clone_repo_item = file_menu.Append(wx.ID_ANY,
                                           "&Clone Repository...\tCtrl+N")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q")

        # Git menu
        git_menu = wx.Menu()
        self.pull_item = git_menu.Append(wx.ID_ANY, "&Pull\tCtrl+P")
        self.push_item = git_menu.Append(wx.ID_ANY, "P&ush\tCtrl+Shift+P")
        self.fetch_item = git_menu.Append(wx.ID_ANY, "&Fetch\tCtrl+F")
        git_menu.AppendSeparator()
        self.commit_item = git_menu.Append(wx.ID_ANY, "&Commit...\tCtrl+M")
        self.merge_item = git_menu.Append(wx.ID_ANY, "M&erge...\tCtrl+Shift+M")

        # Tools menu
        tools_menu = wx.Menu()
        config_item = tools_menu.Append(wx.ID_ANY, "&Configuration...\tCtrl+,")
        terminal_item = tools_menu.Append(wx.ID_ANY, "Open &Terminal\tCtrl+T")

        # Help menu
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "&About")

        # Add menus to menubar
        menubar.Append(file_menu, "&File")
        menubar.Append(git_menu, "&Git")
        menubar.Append(tools_menu, "&Tools")
        menubar.Append(help_menu, "&Help")

        self.SetMenuBar(menubar)

        # Bind menu events
        self.Bind(wx.EVT_MENU, self.on_open_repo, open_repo_item)
        self.Bind(wx.EVT_MENU, self.on_clone_repo, clone_repo_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_pull, self.pull_item)
        self.Bind(wx.EVT_MENU, self.on_push, self.push_item)
        self.Bind(wx.EVT_MENU, self.on_fetch, self.fetch_item)
        self.Bind(wx.EVT_MENU, self.on_commit, self.commit_item)
        self.Bind(wx.EVT_MENU, self.on_merge, self.merge_item)
        self.Bind(wx.EVT_MENU, self.on_config, config_item)
        self.Bind(wx.EVT_MENU, self.on_terminal, terminal_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

        # Initially disable git-specific menu items
        self.enable_git_menus(False)

    def create_status_bar(self):
        """Create the status bar"""
        self.statusbar = self.CreateStatusBar(3)
        self.statusbar.SetStatusWidths([-1, 200, 150])
        self.statusbar.SetStatusText("No repository loaded", 0)
        self.statusbar.SetStatusText("", 1)
        self.statusbar.SetStatusText("Ready", 2)

    def create_main_panel(self):
        """Create the main panel with notebook tabs"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Create notebook for tabs
        self.notebook = wx.Notebook(panel)

        # Create tabs
        self.git_panel = GitPanel(self.notebook, self)
        self.meta_panel = MetaPanel(self.notebook, self)

        self.notebook.AddPage(self.git_panel, "Git Repository")
        self.notebook.AddPage(self.meta_panel, "Meta Repository")

        sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)

    def enable_git_menus(self, enable: bool):
        """Enable or disable git-specific menu items"""
        items = [
            self.pull_item, self.push_item, self.fetch_item, self.commit_item,
            self.merge_item
        ]
        for item in items:
            item.Enable(enable)

    def load_repository(self, repo_path: str):
        """Load a Git repository"""
        try:
            self.current_repo = Repo(repo_path)
            self.current_repo_path = repo_path

            # Update status bar
            repo_name = os.path.basename(repo_path)
            branch_name = self.current_repo.active_branch.name
            self.statusbar.SetStatusText(f"Repository: {repo_name}", 0)
            self.statusbar.SetStatusText(f"Branch: {branch_name}", 1)

            # Enable git menus
            self.enable_git_menus(True)

            # Update git panel
            self.git_panel.load_repository(self.current_repo)

            # Check if it's also a meta repository
            self.meta_panel.check_meta_repository(repo_path)

            return True

        except InvalidGitRepositoryError:
            wx.MessageBox(f"'{repo_path}' is not a valid Git repository.",
                          "Invalid Repository", wx.OK | wx.ICON_ERROR)
            return False
        except Exception as e:
            wx.MessageBox(f"Error loading repository: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)
            return False

    def update_status(self, message: str, field: int = 2):
        """Update status bar message"""
        self.statusbar.SetStatusText(message, field)

    # Menu event handlers
    def on_open_repo(self, event):
        """Handle open repository menu item"""
        with wx.DirDialog(self, "Choose repository directory") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.load_repository(dialog.GetPath())

    def on_clone_repo(self, event):
        """Handle clone repository menu item"""
        dialog = CloneDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            url, path = dialog.get_values()
            self.clone_repository(url, path)
        dialog.Destroy()

    def on_exit(self, event):
        """Handle exit menu item"""
        self.Close()

    def on_pull(self, event):
        """Handle pull menu item"""
        if self.current_repo:
            self.git_panel.execute_git_command("pull")

    def on_push(self, event):
        """Handle push menu item"""
        if self.current_repo:
            self.git_panel.execute_git_command("push")

    def on_fetch(self, event):
        """Handle fetch menu item"""
        if self.current_repo:
            self.git_panel.execute_git_command("fetch")

    def on_commit(self, event):
        """Handle commit menu item"""
        if self.current_repo:
            dialog = CommitDialog(self, self.current_repo)
            dialog.ShowModal()
            dialog.Destroy()

    def on_merge(self, event):
        """Handle merge menu item"""
        if self.current_repo:
            dialog = MergeDialog(self, self.current_repo)
            dialog.ShowModal()
            dialog.Destroy()

    def on_config(self, event):
        """Handle configuration menu item"""
        dialog = ConfigDialog(self, self.current_repo)
        dialog.ShowModal()
        dialog.Destroy()

    def on_terminal(self, event):
        """Handle open terminal menu item"""
        if self.current_repo_path:
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.Popen(
                    ['open', '-a', 'Terminal', self.current_repo_path])
            elif sys.platform.startswith('win'):  # Windows
                subprocess.Popen(['cmd'],
                                 cwd=self.current_repo_path,
                                 creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:  # Linux and other Unix-like systems
                subprocess.Popen(['gnome-terminal'],
                                 cwd=self.current_repo_path)

    def on_about(self, event):
        """Handle about menu item"""
        info = wx.adv.AboutDialogInfo()
        info.SetName("Git Repository Viewer")
        info.SetVersion("1.0.0")
        info.SetDescription(
            "A comprehensive Git and Meta repository management tool")
        info.SetCopyright("(C) 2024")
        info.AddDeveloper("Git Viewer Team")

        wx.adv.AboutBox(info)

    def clone_repository(self, url: str, path: str):
        """Clone a repository in a separate thread"""

        def clone_worker():
            try:
                self.update_status("Cloning repository...")
                repo = Repo.clone_from(url, path)
                wx.CallAfter(self.on_clone_complete, path, None)
            except Exception as e:
                wx.CallAfter(self.on_clone_complete, None, str(e))

        threading.Thread(target=clone_worker, daemon=True).start()

    def on_clone_complete(self, path: Optional[str], error: Optional[str]):
        """Handle clone completion"""
        if error:
            self.update_status("Ready")
            wx.MessageBox(f"Clone failed: {error}", "Error",
                          wx.OK | wx.ICON_ERROR)
        else:
            self.update_status("Clone completed")
            self.load_repository(path)


class GitPanel(wx.Panel):
    """Panel for Git repository operations and browsing"""

    def __init__(self, parent, main_frame):
        super().__init__(parent)
        self.main_frame = main_frame
        self.repo = None

        self.create_ui()

    def create_ui(self):
        """Create the Git panel UI"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Left panel - repository browser
        left_panel = wx.Panel(self)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # Repository info
        repo_info_box = wx.StaticBox(left_panel, label="Repository")
        repo_info_sizer = wx.StaticBoxSizer(repo_info_box, wx.VERTICAL)

        self.repo_path_text = wx.StaticText(left_panel,
                                            label="No repository loaded")
        self.repo_url_text = wx.StaticText(left_panel, label="")
        self.current_branch_text = wx.StaticText(left_panel, label="")

        repo_info_sizer.Add(self.repo_path_text, 0, wx.EXPAND | wx.ALL, 5)
        repo_info_sizer.Add(self.repo_url_text, 0, wx.EXPAND | wx.ALL, 5)
        repo_info_sizer.Add(self.current_branch_text, 0, wx.EXPAND | wx.ALL, 5)

        # Navigation notebook
        self.nav_notebook = wx.Notebook(left_panel)

        # Branches tab
        self.branches_panel = BranchesPanel(self.nav_notebook, self)
        self.nav_notebook.AddPage(self.branches_panel, "Branches")

        # Remotes tab
        self.remotes_panel = RemotesPanel(self.nav_notebook, self)
        self.nav_notebook.AddPage(self.remotes_panel, "Remotes")

        # Files tab
        self.files_panel = FilesPanel(self.nav_notebook, self)
        self.nav_notebook.AddPage(self.files_panel, "Files")

        left_sizer.Add(repo_info_sizer, 0, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(self.nav_notebook, 1, wx.EXPAND | wx.ALL, 5)
        left_panel.SetSizer(left_sizer)

        # Right panel - content viewer
        right_panel = wx.Panel(self)
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        # Content notebook
        self.content_notebook = wx.Notebook(right_panel)

        # Timeline tab
        self.timeline_panel = TimelinePanel(self.content_notebook, self)
        self.content_notebook.AddPage(self.timeline_panel, "Timeline")

        # Commits tab
        self.commits_panel = CommitsPanel(self.content_notebook, self)
        self.content_notebook.AddPage(self.commits_panel, "Commits")

        # File content tab
        self.file_content_panel = FileContentPanel(self.content_notebook, self)
        self.content_notebook.AddPage(self.file_content_panel, "File Content")

        # Diff tab
        self.diff_panel = DiffPanel(self.content_notebook, self)
        self.content_notebook.AddPage(self.diff_panel, "Diff")

        # Output tab for git commands
        self.output_panel = OutputPanel(self.content_notebook, self)
        self.content_notebook.AddPage(self.output_panel, "Output")

        right_sizer.Add(self.content_notebook, 1, wx.EXPAND | wx.ALL, 5)
        right_panel.SetSizer(right_sizer)

        # Add panels to main sizer
        sizer.Add(left_panel, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(right_panel, 2, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

    def load_repository(self, repo: Repo):
        """Load repository data into the panel"""
        self.repo = repo

        # Update repository info
        self.repo_path_text.SetLabel(f"Path: {repo.working_dir}")

        # Get remote URL if available
        try:
            origin = repo.remote('origin')
            self.repo_url_text.SetLabel(f"URL: {origin.url}")
        except:
            self.repo_url_text.SetLabel("URL: No remote configured")

        # Get current branch
        try:
            branch_name = repo.active_branch.name
            self.current_branch_text.SetLabel(f"Branch: {branch_name}")
        except:
            self.current_branch_text.SetLabel("Branch: Detached HEAD")

        # Load data into sub-panels
        self.timeline_panel.load_timeline(repo)
        self.branches_panel.load_branches(repo)
        self.remotes_panel.load_remotes(repo)
        self.files_panel.load_files(repo)
        self.commits_panel.load_commits(repo)

        self.Layout()

    def execute_git_command(self, command: str, *args):
        """Execute a git command and show output"""
        if not self.repo:
            return

        def worker():
            try:
                self.main_frame.update_status(f"Executing git {command}...")

                # Execute the git command
                if command == "pull":
                    result = self.repo.remote().pull()
                    output = "Pull completed successfully"
                elif command == "push":
                    result = self.repo.remote().push()
                    output = "Push completed successfully"
                elif command == "fetch":
                    result = self.repo.remote().fetch()
                    output = "Fetch completed successfully"
                else:
                    # For other commands, use subprocess
                    result = subprocess.run(['git', command] + list(args),
                                            cwd=self.repo.working_dir,
                                            capture_output=True,
                                            text=True)
                    output = result.stdout + result.stderr

                wx.CallAfter(self.on_command_complete, command, output, None)

            except Exception as e:
                wx.CallAfter(self.on_command_complete, command, "", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def on_command_complete(self, command: str, output: str,
                            error: Optional[str]):
        """Handle git command completion"""
        self.main_frame.update_status("Ready")

        if error:
            self.output_panel.add_output(f"Error executing {command}: {error}")
        else:
            self.output_panel.add_output(f"Git {command} output:\n{output}")

            # Refresh repository data
            if self.repo:
                self.load_repository(self.repo)

        # Switch to output tab
        self.content_notebook.SetSelection(4)





if __name__ == '__main__':
    app = GitViewerApp()
    app.MainLoop()
