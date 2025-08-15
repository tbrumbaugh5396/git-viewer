#!/usr/bin/env python3
"""
Git Operation Dialogs for Git Repository Viewer
Contains dialog implementations for various Git operations
"""

import wx
import wx.lib.scrolledpanel as scrolled
import os
import subprocess
import threading
from typing import Optional, List, Dict, Any
import git
from git import Repo


class CloneDialog(wx.Dialog):
    """Dialog for cloning a repository"""

    def __init__(self, parent):
        super().__init__(parent, title="Clone Repository", size=(500, 250))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # URL field
        url_sizer = wx.BoxSizer(wx.HORIZONTAL)
        url_sizer.Add(wx.StaticText(panel, label="Repository URL:"), 0,
                      wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.url_text = wx.TextCtrl(panel, size=(350, -1))
        url_sizer.Add(self.url_text, 1, wx.ALL, 5)

        # Directory field
        dir_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dir_sizer.Add(wx.StaticText(panel, label="Local Directory:"), 0,
                      wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.dir_text = wx.TextCtrl(panel, size=(250, -1))
        self.browse_btn = wx.Button(panel, label="Browse...")
        dir_sizer.Add(self.dir_text, 1, wx.ALL, 5)
        dir_sizer.Add(self.browse_btn, 0, wx.ALL, 5)

        # Options
        options_box = wx.StaticBox(panel, label="Options")
        options_sizer = wx.StaticBoxSizer(options_box, wx.VERTICAL)

        self.recursive_cb = wx.CheckBox(panel,
                                        label="Recursive (clone submodules)")
        self.shallow_cb = wx.CheckBox(panel, label="Shallow clone (depth 1)")
        self.bare_cb = wx.CheckBox(panel, label="Bare repository")

        options_sizer.Add(self.recursive_cb, 0, wx.ALL, 2)
        options_sizer.Add(self.shallow_cb, 0, wx.ALL, 2)
        options_sizer.Add(self.bare_cb, 0, wx.ALL, 2)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "Clone")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        sizer.Add(url_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(dir_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(options_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(sizer)

        # Bind events
        self.browse_btn.Bind(wx.EVT_BUTTON, self.on_browse)
        self.url_text.Bind(wx.EVT_TEXT, self.on_url_changed)

        # Set default directory
        self.dir_text.SetValue(os.path.expanduser("~/"))

    def on_browse(self, event):
        """Handle browse button"""
        with wx.DirDialog(self, "Choose clone directory") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.dir_text.SetValue(dialog.GetPath())

    def on_url_changed(self, event):
        """Handle URL text change to auto-suggest directory name"""
        url = self.url_text.GetValue().strip()
        if url:
            # Extract repository name from URL
            if url.endswith('.git'):
                repo_name = os.path.basename(url)[:-4]
            else:
                repo_name = os.path.basename(url)

            if repo_name:
                base_dir = os.path.dirname(
                    self.dir_text.GetValue()) or os.path.expanduser("~/")
                suggested_path = os.path.join(base_dir, repo_name)
                self.dir_text.SetValue(suggested_path)

    def get_values(self):
        """Get the entered values"""
        return self.url_text.GetValue(), self.dir_text.GetValue()

    def get_options(self):
        """Get the selected options"""
        return {
            'recursive': self.recursive_cb.GetValue(),
            'shallow': self.shallow_cb.GetValue(),
            'bare': self.bare_cb.GetValue()
        }


class CommitDialog(wx.Dialog):
    """Dialog for committing changes"""

    def __init__(self, parent, repo: Repo):
        super().__init__(parent, title="Commit Changes", size=(600, 500))

        self.repo = repo
        self.staged_files = []
        self.unstaged_files = []

        self.create_ui()
        self.load_status()

    def create_ui(self):
        """Create the commit dialog UI"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Files section
        files_notebook = wx.Notebook(panel)

        # Staged files
        self.staged_panel = wx.Panel(files_notebook)
        staged_sizer = wx.BoxSizer(wx.VERTICAL)

        staged_toolbar = wx.Panel(self.staged_panel)
        staged_toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.unstage_btn = wx.Button(staged_toolbar, label="Unstage")
        staged_toolbar_sizer.Add(self.unstage_btn, 0, wx.ALL, 2)
        staged_toolbar.SetSizer(staged_toolbar_sizer)

        self.staged_list = wx.ListBox(self.staged_panel)

        staged_sizer.Add(staged_toolbar, 0, wx.EXPAND | wx.ALL, 2)
        staged_sizer.Add(self.staged_list, 1, wx.EXPAND | wx.ALL, 2)
        self.staged_panel.SetSizer(staged_sizer)

        # Unstaged files
        self.unstaged_panel = wx.Panel(files_notebook)
        unstaged_sizer = wx.BoxSizer(wx.VERTICAL)

        unstaged_toolbar = wx.Panel(self.unstaged_panel)
        unstaged_toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.stage_btn = wx.Button(unstaged_toolbar, label="Stage")
        self.stage_all_btn = wx.Button(unstaged_toolbar, label="Stage All")
        unstaged_toolbar_sizer.Add(self.stage_btn, 0, wx.ALL, 2)
        unstaged_toolbar_sizer.Add(self.stage_all_btn, 0, wx.ALL, 2)
        unstaged_toolbar.SetSizer(unstaged_toolbar_sizer)

        self.unstaged_list = wx.ListBox(self.unstaged_panel)

        unstaged_sizer.Add(unstaged_toolbar, 0, wx.EXPAND | wx.ALL, 2)
        unstaged_sizer.Add(self.unstaged_list, 1, wx.EXPAND | wx.ALL, 2)
        self.unstaged_panel.SetSizer(unstaged_sizer)

        files_notebook.AddPage(self.staged_panel, "Staged Files")
        files_notebook.AddPage(self.unstaged_panel, "Unstaged Files")

        # Commit message section
        msg_box = wx.StaticBox(panel, label="Commit Message")
        msg_sizer = wx.StaticBoxSizer(msg_box, wx.VERTICAL)

        self.message_text = wx.TextCtrl(panel,
                                        style=wx.TE_MULTILINE,
                                        size=(-1, 100))
        msg_sizer.Add(self.message_text, 1, wx.EXPAND | wx.ALL, 5)

        # Options
        options_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.amend_cb = wx.CheckBox(panel, label="Amend last commit")
        self.sign_off_cb = wx.CheckBox(panel, label="Add Signed-off-by line")
        options_sizer.Add(self.amend_cb, 0, wx.ALL, 5)
        options_sizer.Add(self.sign_off_cb, 0, wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.commit_btn = wx.Button(panel, wx.ID_OK, "Commit")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        refresh_btn = wx.Button(panel, label="Refresh")
        btn_sizer.Add(self.commit_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        btn_sizer.Add(refresh_btn, 0, wx.ALL, 5)

        sizer.Add(files_notebook, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(msg_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(options_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        panel.SetSizer(sizer)

        # Bind events
        self.stage_btn.Bind(wx.EVT_BUTTON, self.on_stage)
        self.stage_all_btn.Bind(wx.EVT_BUTTON, self.on_stage_all)
        self.unstage_btn.Bind(wx.EVT_BUTTON, self.on_unstage)
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        self.commit_btn.Bind(wx.EVT_BUTTON, self.on_commit)

        # Initially disable commit button
        self.commit_btn.Enable(False)

    def load_status(self):
        """Load the repository status"""
        try:
            # Get staged and unstaged files
            self.staged_files = []
            self.unstaged_files = []

            # Check for changes
            diff_staged = self.repo.index.diff("HEAD")
            diff_unstaged = self.repo.index.diff(None)
            untracked = self.repo.untracked_files

            # Staged files
            for item in diff_staged:
                status = "M" if item.change_type == "M" else item.change_type
                self.staged_files.append(f"{status} {item.a_path}")

            # Unstaged files
            for item in diff_unstaged:
                status = "M" if item.change_type == "M" else item.change_type
                self.unstaged_files.append(f"{status} {item.a_path}")

            # Untracked files
            for file_path in untracked:
                self.unstaged_files.append(f"? {file_path}")

            self.update_file_lists()

        except Exception as e:
            wx.MessageBox(f"Error loading status: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)

    def update_file_lists(self):
        """Update the file list controls"""
        self.staged_list.Clear()
        self.unstaged_list.Clear()

        for file_entry in self.staged_files:
            self.staged_list.Append(file_entry)

        for file_entry in self.unstaged_files:
            self.unstaged_list.Append(file_entry)

        # Enable/disable commit button
        self.commit_btn.Enable(len(self.staged_files) > 0)

    def on_stage(self, event):
        """Stage selected files"""
        selected = self.unstaged_list.GetSelection()
        if selected != wx.NOT_FOUND:
            file_entry = self.unstaged_files[selected]
            file_path = file_entry[2:]  # Remove status prefix

            try:
                self.repo.index.add([file_path])
                self.load_status()
            except Exception as e:
                wx.MessageBox(f"Error staging file: {str(e)}", "Error",
                              wx.OK | wx.ICON_ERROR)

    def on_stage_all(self, event):
        """Stage all unstaged files"""
        try:
            file_paths = [entry[2:] for entry in self.unstaged_files]
            if file_paths:
                self.repo.index.add(file_paths)
                self.load_status()
        except Exception as e:
            wx.MessageBox(f"Error staging files: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)

    def on_unstage(self, event):
        """Unstage selected files"""
        selected = self.staged_list.GetSelection()
        if selected != wx.NOT_FOUND:
            file_entry = self.staged_files[selected]
            file_path = file_entry[2:]  # Remove status prefix

            try:
                self.repo.index.reset([file_path])
                self.load_status()
            except Exception as e:
                wx.MessageBox(f"Error unstaging file: {str(e)}", "Error",
                              wx.OK | wx.ICON_ERROR)

    def on_refresh(self, event):
        """Refresh the status"""
        self.load_status()

    def on_commit(self, event):
        """Perform the commit"""
        message = self.message_text.GetValue().strip()
        if not message:
            wx.MessageBox("Please enter a commit message.", "Missing Message",
                          wx.OK | wx.ICON_WARNING)
            return

        try:
            # Add sign-off if requested
            if self.sign_off_cb.GetValue():
                config = self.repo.config_reader()
                try:
                    name = config.get_value("user", "name")
                    email = config.get_value("user", "email")
                    message += f"\n\nSigned-off-by: {name} <{email}>"
                except:
                    pass

            # Commit
            if self.amend_cb.GetValue():
                self.repo.index.commit(message, amend=True)
            else:
                self.repo.index.commit(message)

            self.EndModal(wx.ID_OK)

        except Exception as e:
            wx.MessageBox(f"Error committing: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)


class MergeDialog(wx.Dialog):
    """Dialog for merging branches"""

    def __init__(self, parent, repo: Repo):
        super().__init__(parent, title="Merge Branch", size=(400, 300))

        self.repo = repo

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Current branch info
        try:
            current_branch = repo.active_branch.name
            current_label = wx.StaticText(
                panel, label=f"Current branch: {current_branch}")
        except:
            current_label = wx.StaticText(
                panel, label="Current branch: Detached HEAD")

        # Branch selection
        branch_sizer = wx.BoxSizer(wx.HORIZONTAL)
        branch_sizer.Add(wx.StaticText(panel, label="Merge branch:"), 0,
                         wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.branch_choice = wx.Choice(panel)
        branch_sizer.Add(self.branch_choice, 1, wx.ALL, 5)

        # Options
        options_box = wx.StaticBox(panel, label="Options")
        options_sizer = wx.StaticBoxSizer(options_box, wx.VERTICAL)

        self.no_ff_cb = wx.CheckBox(panel, label="No fast-forward (--no-ff)")
        self.squash_cb = wx.CheckBox(panel, label="Squash commits (--squash)")

        options_sizer.Add(self.no_ff_cb, 0, wx.ALL, 2)
        options_sizer.Add(self.squash_cb, 0, wx.ALL, 2)

        # Message
        msg_sizer = wx.BoxSizer(wx.HORIZONTAL)
        msg_sizer.Add(wx.StaticText(panel, label="Merge message:"), 0,
                      wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.message_text = wx.TextCtrl(panel, size=(200, -1))
        msg_sizer.Add(self.message_text, 1, wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        merge_btn = wx.Button(panel, wx.ID_OK, "Merge")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(merge_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        sizer.Add(current_label, 0, wx.ALL, 10)
        sizer.Add(branch_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(options_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(msg_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(sizer)

        # Populate branches
        self.populate_branches()

        # Bind events
        merge_btn.Bind(wx.EVT_BUTTON, self.on_merge)

    def populate_branches(self):
        """Populate the branch choice"""
        try:
            current_branch = self.repo.active_branch.name
        except:
            current_branch = None

        for branch in self.repo.heads:
            if branch.name != current_branch:
                self.branch_choice.Append(branch.name)

        if self.branch_choice.GetCount() > 0:
            self.branch_choice.SetSelection(0)

    def on_merge(self, event):
        """Perform the merge"""
        branch_name = self.branch_choice.GetStringSelection()
        if not branch_name:
            wx.MessageBox("Please select a branch to merge.",
                          "No Branch Selected", wx.OK | wx.ICON_WARNING)
            return

        try:
            branch = self.repo.heads[branch_name]

            # Prepare merge arguments
            merge_args = []
            if self.no_ff_cb.GetValue():
                merge_args.append("--no-ff")
            if self.squash_cb.GetValue():
                merge_args.append("--squash")

            message = self.message_text.GetValue().strip()
            if message:
                merge_args.extend(["-m", message])

            # Perform merge
            self.repo.git.merge(branch.name, *merge_args)

            self.EndModal(wx.ID_OK)

        except Exception as e:
            wx.MessageBox(f"Error merging: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)


class ConfigDialog(wx.Dialog):
    """Dialog for Git configuration"""

    def __init__(self, parent, repo: Optional[Repo]):
        super().__init__(parent, title="Git Configuration", size=(600, 500))

        self.repo = repo
        self.config_data = {}

        self.create_ui()
        self.load_config()

    def create_ui(self):
        """Create the configuration dialog UI"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Scope selection
        scope_sizer = wx.BoxSizer(wx.HORIZONTAL)
        scope_sizer.Add(wx.StaticText(panel, label="Scope:"), 0,
                        wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.scope_choice = wx.Choice(
            panel, choices=["Global", "Repository", "System"])
        self.scope_choice.SetSelection(0 if not self.repo else 1)
        scope_sizer.Add(self.scope_choice, 0, wx.ALL, 5)

        # Configuration notebook
        self.config_notebook = wx.Notebook(panel)

        # User settings
        self.user_panel = self.create_user_panel()
        self.config_notebook.AddPage(self.user_panel, "User")

        # Advanced settings
        self.advanced_panel = self.create_advanced_panel()
        self.config_notebook.AddPage(self.advanced_panel, "Advanced")

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_btn = wx.Button(panel, wx.ID_OK, "Save")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        refresh_btn = wx.Button(panel, label="Refresh")
        btn_sizer.Add(save_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        btn_sizer.Add(refresh_btn, 0, wx.ALL, 5)

        sizer.Add(scope_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.config_notebook, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        panel.SetSizer(sizer)

        # Bind events
        self.scope_choice.Bind(wx.EVT_CHOICE, self.on_scope_changed)
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)

    def create_user_panel(self):
        """Create the user settings panel"""
        panel = wx.Panel(self.config_notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # User name
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(wx.StaticText(panel, label="Name:"), 0,
                       wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.name_text = wx.TextCtrl(panel, size=(300, -1))
        name_sizer.Add(self.name_text, 1, wx.ALL, 5)

        # User email
        email_sizer = wx.BoxSizer(wx.HORIZONTAL)
        email_sizer.Add(wx.StaticText(panel, label="Email:"), 0,
                        wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.email_text = wx.TextCtrl(panel, size=(300, -1))
        email_sizer.Add(self.email_text, 1, wx.ALL, 5)

        # Default editor
        editor_sizer = wx.BoxSizer(wx.HORIZONTAL)
        editor_sizer.Add(wx.StaticText(panel, label="Editor:"), 0,
                         wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.editor_text = wx.TextCtrl(panel, size=(300, -1))
        editor_sizer.Add(self.editor_text, 1, wx.ALL, 5)

        sizer.Add(name_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(email_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(editor_sizer, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def create_advanced_panel(self):
        """Create the advanced settings panel"""
        panel = scrolled.ScrolledPanel(self.config_notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Configuration list
        self.config_list = wx.ListCtrl(panel,
                                       style=wx.LC_REPORT | wx.LC_EDIT_LABELS)
        self.config_list.AppendColumn("Key", width=200)
        self.config_list.AppendColumn("Value", width=300)

        # Add/remove buttons
        btn_panel = wx.Panel(panel)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        add_btn = wx.Button(btn_panel, label="Add")
        remove_btn = wx.Button(btn_panel, label="Remove")

        btn_sizer.Add(add_btn, 0, wx.ALL, 2)
        btn_sizer.Add(remove_btn, 0, wx.ALL, 2)
        btn_panel.SetSizer(btn_sizer)

        sizer.Add(self.config_list, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btn_panel, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)
        panel.SetupScrolling()

        # Bind events
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_config)
        remove_btn.Bind(wx.EVT_BUTTON, self.on_remove_config)

        return panel

    def load_config(self):
        """Load Git configuration"""
        try:
            scope = self.scope_choice.GetSelection()

            if scope == 0:  # Global
                config_reader = git.GitConfigParser(
                    [git.config.get_config_path("global")], read_only=True)
            elif scope == 1 and self.repo:  # Repository
                config_reader = self.repo.config_reader()
            else:  # System
                config_reader = git.GitConfigParser(
                    [git.config.get_config_path("system")], read_only=True)

            # Load user settings
            try:
                self.name_text.SetValue(
                    config_reader.get_value("user", "name", ""))
            except:
                self.name_text.SetValue("")

            try:
                self.email_text.SetValue(
                    config_reader.get_value("user", "email", ""))
            except:
                self.email_text.SetValue("")

            try:
                self.editor_text.SetValue(
                    config_reader.get_value("core", "editor", ""))
            except:
                self.editor_text.SetValue("")

            # Load advanced settings
            self.config_list.DeleteAllItems()
            self.config_data = {}

            for section_name in config_reader.sections():
                for option in config_reader.options(section_name):
                    key = f"{section_name}.{option}"
                    value = config_reader.get_value(section_name, option)

                    index = self.config_list.InsertItem(
                        self.config_list.GetItemCount(), key)
                    self.config_list.SetItem(index, 1, str(value))
                    self.config_data[key] = value

        except Exception as e:
            wx.MessageBox(f"Error loading configuration: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)

    def on_scope_changed(self, event):
        """Handle scope change"""
        self.load_config()

    def on_save(self, event):
        """Save configuration changes"""
        try:
            scope = self.scope_choice.GetSelection()

            if scope == 0:  # Global
                config_writer = git.GitConfigParser(
                    [git.config.get_config_path("global")], read_only=False)
            elif scope == 1 and self.repo:  # Repository
                config_writer = self.repo.config_writer()
            else:
                wx.MessageBox("System configuration editing not supported.",
                              "Not Supported", wx.OK | wx.ICON_WARNING)
                return

            # Save user settings
            name = self.name_text.GetValue().strip()
            email = self.email_text.GetValue().strip()
            editor = self.editor_text.GetValue().strip()

            if name:
                config_writer.set_value("user", "name", name)
            if email:
                config_writer.set_value("user", "email", email)
            if editor:
                config_writer.set_value("core", "editor", editor)

            config_writer.write()
            config_writer.release()

            self.EndModal(wx.ID_OK)

        except Exception as e:
            wx.MessageBox(f"Error saving configuration: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)

    def on_refresh(self, event):
        """Refresh configuration"""
        self.load_config()

    def on_add_config(self, event):
        """Add new configuration item"""
        dialog = wx.TextEntryDialog(
            self, "Enter configuration key (e.g., section.option):",
            "Add Configuration")
        if dialog.ShowModal() == wx.ID_OK:
            key = dialog.GetValue().strip()
            if key and '.' in key:
                value_dialog = wx.TextEntryDialog(self,
                                                  f"Enter value for '{key}':",
                                                  "Configuration Value")
                if value_dialog.ShowModal() == wx.ID_OK:
                    value = value_dialog.GetValue()

                    index = self.config_list.InsertItem(
                        self.config_list.GetItemCount(), key)
                    self.config_list.SetItem(index, 1, value)
                    self.config_data[key] = value

                value_dialog.Destroy()
        dialog.Destroy()

    def on_remove_config(self, event):
        """Remove selected configuration item"""
        selected = self.config_list.GetFirstSelected()
        if selected != -1:
            key = self.config_list.GetItemText(selected, 0)
            self.config_list.DeleteItem(selected)
            if key in self.config_data:
                del self.config_data[key]
