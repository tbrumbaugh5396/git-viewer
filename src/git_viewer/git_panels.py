#!/usr/bin/env python3
"""
Git Panel Implementations for Git Repository Viewer
Contains detailed implementations of all Git-related panels and dialogs
"""

import wx
import wx.lib.agw.aui as aui
import wx.lib.mixins.listctrl as listmix
import os
import subprocess
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any
import git
from git import Repo


class BranchesPanel(wx.Panel):
    """Panel for viewing and managing branches"""

    def __init__(self, parent, git_panel):
        super().__init__(parent)
        self.git_panel = git_panel
        self.repo = None

        self.create_ui()

    def create_ui(self):
        """Create the branches panel UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Toolbar
        toolbar_panel = wx.Panel(self)
        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.refresh_btn = wx.Button(toolbar_panel, label="Refresh")
        self.checkout_btn = wx.Button(toolbar_panel, label="Checkout")
        self.new_branch_btn = wx.Button(toolbar_panel, label="New Branch")
        self.delete_branch_btn = wx.Button(toolbar_panel, label="Delete")

        toolbar_sizer.Add(self.refresh_btn, 0, wx.ALL, 2)
        toolbar_sizer.Add(self.checkout_btn, 0, wx.ALL, 2)
        toolbar_sizer.Add(self.new_branch_btn, 0, wx.ALL, 2)
        toolbar_sizer.Add(self.delete_branch_btn, 0, wx.ALL, 2)
        toolbar_panel.SetSizer(toolbar_sizer)

        # Branches list
        self.branches_list = wx.ListCtrl(self,
                                         style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.branches_list.AppendColumn("Branch", width=200)
        self.branches_list.AppendColumn("Last Commit", width=300)
        self.branches_list.AppendColumn("Author", width=150)
        self.branches_list.AppendColumn("Date", width=100)

        sizer.Add(toolbar_panel, 0, wx.EXPAND | wx.ALL, 2)
        sizer.Add(self.branches_list, 1, wx.EXPAND | wx.ALL, 2)
        self.SetSizer(sizer)

        # Bind events
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        self.checkout_btn.Bind(wx.EVT_BUTTON, self.on_checkout)
        self.new_branch_btn.Bind(wx.EVT_BUTTON, self.on_new_branch)
        self.delete_branch_btn.Bind(wx.EVT_BUTTON, self.on_delete_branch)
        self.branches_list.Bind(wx.EVT_LIST_ITEM_SELECTED,
                                self.on_branch_selected)
        self.branches_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_checkout)

    def load_branches(self, repo: Repo):
        """Load branches from repository"""
        self.repo = repo
        self.refresh_branches()

    def refresh_branches(self):
        """Refresh the branches list"""
        if not self.repo:
            return

        self.branches_list.DeleteAllItems()

        try:
            # Get all branches (local and remote)
            branches = []

            # Local branches
            for branch in self.repo.heads:
                try:
                    last_commit = branch.commit
                    branches.append({
                        'name':
                        branch.name,
                        'type':
                        'local',
                        'current':
                        branch == self.repo.active_branch,
                        'commit':
                        last_commit,
                        'message':
                        last_commit.message.strip().split('\n')[0],
                        'author':
                        last_commit.author.name,
                        'date':
                        datetime.fromtimestamp(
                            last_commit.committed_date).strftime('%Y-%m-%d')
                    })
                except:
                    branches.append({
                        'name': branch.name,
                        'type': 'local',
                        'current': False,
                        'commit': None,
                        'message': 'No commits',
                        'author': '',
                        'date': ''
                    })

            # Remote branches
            for remote in self.repo.remotes:
                for ref in remote.refs:
                    if ref.name.endswith('/HEAD'):
                        continue

                    branch_name = f"{remote.name}/{ref.name.split('/')[-1]}"
                    try:
                        last_commit = ref.commit
                        branches.append({
                            'name':
                            branch_name,
                            'type':
                            'remote',
                            'current':
                            False,
                            'commit':
                            last_commit,
                            'message':
                            last_commit.message.strip().split('\n')[0],
                            'author':
                            last_commit.author.name,
                            'date':
                            datetime.fromtimestamp(
                                last_commit.committed_date).strftime(
                                    '%Y-%m-%d')
                        })
                    except:
                        branches.append({
                            'name': branch_name,
                            'type': 'remote',
                            'current': False,
                            'commit': None,
                            'message': 'No commits',
                            'author': '',
                            'date': ''
                        })

            # Sort branches
            branches.sort(key=lambda x: (x['type'], x['name']))

            # Add to list
            for i, branch in enumerate(branches):
                index = self.branches_list.InsertItem(i, branch['name'])

                # Mark current branch
                if branch['current']:
                    self.branches_list.SetItem(index, 0, f"* {branch['name']}")
                    self.branches_list.SetItemTextColour(
                        index, wx.Colour(0, 150, 0))

                # Set other columns
                self.branches_list.SetItem(index, 1, branch['message'])
                self.branches_list.SetItem(index, 2, branch['author'])
                self.branches_list.SetItem(index, 3, branch['date'])

                # Store branch data
                self.branches_list.SetItemData(index, i)

                # Different color for remote branches
                if branch['type'] == 'remote':
                    self.branches_list.SetItemTextColour(
                        index, wx.Colour(100, 100, 150))

            self.branches_data = branches

        except Exception as e:
            wx.MessageBox(f"Error loading branches: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)

    def on_refresh(self, event):
        """Handle refresh button"""
        self.refresh_branches()

    def on_checkout(self, event):
        """Handle checkout button or double-click"""
        selected = self.branches_list.GetFirstSelected()
        if selected == -1:
            return

        branch_data = self.branches_data[self.branches_list.GetItemData(
            selected)]
        branch_name = branch_data['name']

        # Remove remote prefix for checkout
        if branch_data['type'] == 'remote':
            local_name = branch_name.split('/')[-1]
            # Check if local branch already exists
            if local_name in [b.name for b in self.repo.heads]:
                branch_name = local_name

        try:
            if branch_data['type'] == 'remote' and '/' in branch_name:
                # Create and checkout tracking branch
                remote_name, local_name = branch_name.split('/', 1)
                self.repo.git.checkout('-b', local_name, branch_name)
            else:
                self.repo.git.checkout(branch_name)

            self.git_panel.main_frame.update_status(
                f"Checked out branch: {branch_name}")
            self.refresh_branches()
            self.git_panel.load_repository(self.repo)  # Refresh main view

        except Exception as e:
            wx.MessageBox(f"Error checking out branch: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)

    def on_new_branch(self, event):
        """Handle new branch button"""
        dialog = wx.TextEntryDialog(self, "Enter new branch name:",
                                    "New Branch")
        if dialog.ShowModal() == wx.ID_OK:
            branch_name = dialog.GetValue().strip()
            if branch_name:
                try:
                    new_branch = self.repo.create_head(branch_name)
                    new_branch.checkout()
                    self.git_panel.main_frame.update_status(
                        f"Created and checked out branch: {branch_name}")
                    self.refresh_branches()
                    self.git_panel.load_repository(self.repo)
                except Exception as e:
                    wx.MessageBox(f"Error creating branch: {str(e)}", "Error",
                                  wx.OK | wx.ICON_ERROR)
        dialog.Destroy()

    def on_delete_branch(self, event):
        """Handle delete branch button"""
        selected = self.branches_list.GetFirstSelected()
        if selected == -1:
            return

        branch_data = self.branches_data[self.branches_list.GetItemData(
            selected)]
        branch_name = branch_data['name']

        if branch_data['current']:
            wx.MessageBox("Cannot delete the current branch.", "Error",
                          wx.OK | wx.ICON_ERROR)
            return

        if branch_data['type'] == 'remote':
            wx.MessageBox("Cannot delete remote branches from here.", "Error",
                          wx.OK | wx.ICON_ERROR)
            return

        if wx.MessageBox(
                f"Are you sure you want to delete branch '{branch_name}'?",
                "Confirm Delete", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            try:
                self.repo.delete_head(branch_name)
                self.git_panel.main_frame.update_status(
                    f"Deleted branch: {branch_name}")
                self.refresh_branches()
            except Exception as e:
                wx.MessageBox(f"Error deleting branch: {str(e)}", "Error",
                              wx.OK | wx.ICON_ERROR)

    def on_branch_selected(self, event):
        """Handle branch selection"""
        # Enable/disable buttons based on selection
        selected = self.branches_list.GetFirstSelected()
        self.checkout_btn.Enable(selected != -1)
        self.delete_branch_btn.Enable(selected != -1)


class RemotesPanel(wx.Panel):
    """Panel for viewing and managing remotes"""

    def __init__(self, parent, git_panel):
        super().__init__(parent)
        self.git_panel = git_panel
        self.repo = None

        self.create_ui()

    def create_ui(self):
        """Create the remotes panel UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Toolbar
        toolbar_panel = wx.Panel(self)
        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.refresh_btn = wx.Button(toolbar_panel, label="Refresh")
        self.add_remote_btn = wx.Button(toolbar_panel, label="Add Remote")
        self.remove_remote_btn = wx.Button(toolbar_panel, label="Remove")
        self.fetch_btn = wx.Button(toolbar_panel, label="Fetch")

        toolbar_sizer.Add(self.refresh_btn, 0, wx.ALL, 2)
        toolbar_sizer.Add(self.add_remote_btn, 0, wx.ALL, 2)
        toolbar_sizer.Add(self.remove_remote_btn, 0, wx.ALL, 2)
        toolbar_sizer.Add(self.fetch_btn, 0, wx.ALL, 2)
        toolbar_panel.SetSizer(toolbar_sizer)

        # Remotes list
        self.remotes_list = wx.ListCtrl(self,
                                        style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.remotes_list.AppendColumn("Name", width=100)
        self.remotes_list.AppendColumn("URL", width=400)
        self.remotes_list.AppendColumn("Type", width=80)

        sizer.Add(toolbar_panel, 0, wx.EXPAND | wx.ALL, 2)
        sizer.Add(self.remotes_list, 1, wx.EXPAND | wx.ALL, 2)
        self.SetSizer(sizer)

        # Bind events
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        self.add_remote_btn.Bind(wx.EVT_BUTTON, self.on_add_remote)
        self.remove_remote_btn.Bind(wx.EVT_BUTTON, self.on_remove_remote)
        self.fetch_btn.Bind(wx.EVT_BUTTON, self.on_fetch)

    def load_remotes(self, repo: Repo):
        """Load remotes from repository"""
        self.repo = repo
        self.refresh_remotes()

    def refresh_remotes(self):
        """Refresh the remotes list"""
        if not self.repo:
            return

        self.remotes_list.DeleteAllItems()

        try:
            for i, remote in enumerate(self.repo.remotes):
                # Add fetch URL
                index = self.remotes_list.InsertItem(i * 2, remote.name)
                self.remotes_list.SetItem(index, 1, remote.url)
                self.remotes_list.SetItem(index, 2, "fetch")

                # Add push URL if different
                try:
                    push_urls = remote.urls
                    if len(list(push_urls)) > 1:
                        push_url = list(remote.urls)[1]
                        if push_url != remote.url:
                            index = self.remotes_list.InsertItem(
                                i * 2 + 1, remote.name)
                            self.remotes_list.SetItem(index, 1, push_url)
                            self.remotes_list.SetItem(index, 2, "push")
                except:
                    pass

        except Exception as e:
            wx.MessageBox(f"Error loading remotes: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)

    def on_refresh(self, event):
        """Handle refresh button"""
        self.refresh_remotes()

    def on_add_remote(self, event):
        """Handle add remote button"""
        dialog = AddRemoteDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            name, url = dialog.get_values()
            try:
                self.repo.create_remote(name, url)
                self.git_panel.main_frame.update_status(
                    f"Added remote: {name}")
                self.refresh_remotes()
            except Exception as e:
                wx.MessageBox(f"Error adding remote: {str(e)}", "Error",
                              wx.OK | wx.ICON_ERROR)
        dialog.Destroy()

    def on_remove_remote(self, event):
        """Handle remove remote button"""
        selected = self.remotes_list.GetFirstSelected()
        if selected == -1:
            return

        remote_name = self.remotes_list.GetItemText(selected, 0)

        if wx.MessageBox(
                f"Are you sure you want to remove remote '{remote_name}'?",
                "Confirm Remove", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            try:
                self.repo.delete_remote(remote_name)
                self.git_panel.main_frame.update_status(
                    f"Removed remote: {remote_name}")
                self.refresh_remotes()
            except Exception as e:
                wx.MessageBox(f"Error removing remote: {str(e)}", "Error",
                              wx.OK | wx.ICON_ERROR)

    def on_fetch(self, event):
        """Handle fetch button"""
        selected = self.remotes_list.GetFirstSelected()
        if selected != -1:
            remote_name = self.remotes_list.GetItemText(selected, 0)
            self.git_panel.execute_git_command("fetch", remote_name)
        else:
            self.git_panel.execute_git_command("fetch")


class FilesPanel(wx.Panel):
    """Panel for browsing repository files"""

    def __init__(self, parent, git_panel):
        super().__init__(parent)
        self.git_panel = git_panel
        self.repo = None

        self.create_ui()

    def create_ui(self):
        """Create the files panel UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Toolbar
        toolbar_panel = wx.Panel(self)
        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.refresh_btn = wx.Button(toolbar_panel, label="Refresh")
        self.view_file_btn = wx.Button(toolbar_panel, label="View File")

        toolbar_sizer.Add(self.refresh_btn, 0, wx.ALL, 2)
        toolbar_sizer.Add(self.view_file_btn, 0, wx.ALL, 2)
        toolbar_panel.SetSizer(toolbar_sizer)

        # File tree
        self.file_tree = wx.TreeCtrl(self,
                                     style=wx.TR_DEFAULT_STYLE
                                     | wx.TR_HIDE_ROOT)

        sizer.Add(toolbar_panel, 0, wx.EXPAND | wx.ALL, 2)
        sizer.Add(self.file_tree, 1, wx.EXPAND | wx.ALL, 2)
        self.SetSizer(sizer)

        # Bind events
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        self.view_file_btn.Bind(wx.EVT_BUTTON, self.on_view_file)
        self.file_tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_view_file)

    def load_files(self, repo: Repo):
        """Load files from repository"""
        self.repo = repo
        self.refresh_files()

    def refresh_files(self):
        """Refresh the file tree"""
        if not self.repo:
            return

        self.file_tree.DeleteAllItems()
        root = self.file_tree.AddRoot("Repository")

        try:
            self.populate_tree(root, self.repo.working_dir)
            self.file_tree.ExpandAll()
        except Exception as e:
            wx.MessageBox(f"Error loading files: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)

    def populate_tree(self, parent_item, path):
        """Recursively populate the file tree"""
        try:
            items = []
            for item in os.listdir(path):
                if item.startswith('.git'):
                    continue
                
                item_path = os.path.join(path, item)
                items.append((item, item_path, os.path.isdir(item_path)))
            
            # Sort: directories first, then files, both alphabetically
            items.sort(key=lambda x: (not x[2], x[0].lower()))

            for item_name, item_path, is_dir in items:
                try:
                    if is_dir:
                        # Directory - use folder icon and different color
                        dir_item = self.file_tree.AppendItem(parent_item, f"📁 {item_name}")
                        self.file_tree.SetItemData(dir_item, item_path)
                        self.file_tree.SetItemTextColour(dir_item, wx.Colour(0, 0, 150))

                        # Add subdirectories and files
                        try:
                            self.populate_tree(dir_item, item_path)
                        except PermissionError:
                            pass  # Skip directories we can't read
                    else:
                        # File - add file icon and size info
                        try:
                            file_size = os.path.getsize(item_path)
                            if file_size < 1024:
                                size_str = f" ({file_size}B)"
                            elif file_size < 1024 * 1024:
                                size_str = f" ({file_size/1024:.1f}KB)"
                            else:
                                size_str = f" ({file_size/(1024*1024):.1f}MB)"
                        except:
                            size_str = ""
                        
                        # Get file extension for icon
                        file_ext = os.path.splitext(item_name)[1].lower()
                        if file_ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h']:
                            icon = "💻"
                        elif file_ext in ['.txt', '.md', '.rst']:
                            icon = "📄"
                        elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                            icon = "🖼️"
                        elif file_ext in ['.zip', '.tar', '.gz', '.rar']:
                            icon = "📦"
                        else:
                            icon = "📄"
                        
                        file_item = self.file_tree.AppendItem(parent_item, f"{icon} {item_name}{size_str}")
                        self.file_tree.SetItemData(file_item, item_path)
                        
                        # Color code by file type
                        if file_ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h']:
                            self.file_tree.SetItemTextColour(file_item, wx.Colour(0, 100, 0))
                        elif file_ext in ['.md', '.txt', '.rst']:
                            self.file_tree.SetItemTextColour(file_item, wx.Colour(100, 100, 0))
                            
                except PermissionError:
                    pass  # Skip files we can't read

        except PermissionError:
            pass  # Skip directories we can't read

    def on_refresh(self, event):
        """Handle refresh button"""
        self.refresh_files()

    def on_view_file(self, event):
        """Handle view file button or double-click"""
        selected = self.file_tree.GetSelection()
        if not selected.IsOk():
            return

        file_path = self.file_tree.GetItemData(selected)
        if file_path and os.path.isfile(file_path):
            # Show file content in the file content panel
            rel_path = os.path.relpath(file_path, self.repo.working_dir)
            self.git_panel.file_content_panel.show_file(rel_path, file_path)
            self.git_panel.content_notebook.SetSelection(
                1)  # Switch to file content tab


class CommitsPanel(wx.Panel):
    """Panel for viewing commit history"""

    def __init__(self, parent, git_panel):
        super().__init__(parent)
        self.git_panel = git_panel
        self.repo = None

        self.create_ui()

    def create_ui(self):
        """Create the commits panel UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Toolbar
        toolbar_panel = wx.Panel(self)
        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.refresh_btn = wx.Button(toolbar_panel, label="Refresh")
        self.view_commit_btn = wx.Button(toolbar_panel, label="View Commit")
        self.checkout_commit_btn = wx.Button(toolbar_panel, label="Checkout")

        # Branch selector
        wx.StaticText(toolbar_panel, label="Branch:")
        self.branch_choice = wx.Choice(toolbar_panel)

        toolbar_sizer.Add(self.refresh_btn, 0, wx.ALL, 2)
        toolbar_sizer.Add(self.view_commit_btn, 0, wx.ALL, 2)
        toolbar_sizer.Add(self.checkout_commit_btn, 0, wx.ALL, 2)
        toolbar_sizer.AddStretchSpacer()
        toolbar_sizer.Add(wx.StaticText(toolbar_panel, label="Branch:"), 0,
                          wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        toolbar_sizer.Add(self.branch_choice, 0, wx.ALL, 2)
        toolbar_panel.SetSizer(toolbar_sizer)

        # Commits list
        self.commits_list = wx.ListCtrl(self,
                                        style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.commits_list.AppendColumn("Hash", width=80)
        self.commits_list.AppendColumn("Message", width=300)
        self.commits_list.AppendColumn("Author", width=150)
        self.commits_list.AppendColumn("Date", width=150)
        self.commits_list.AppendColumn("Files", width=60)

        sizer.Add(toolbar_panel, 0, wx.EXPAND | wx.ALL, 2)
        sizer.Add(self.commits_list, 1, wx.EXPAND | wx.ALL, 2)
        self.SetSizer(sizer)

        # Bind events
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        self.view_commit_btn.Bind(wx.EVT_BUTTON, self.on_view_commit)
        self.checkout_commit_btn.Bind(wx.EVT_BUTTON, self.on_checkout_commit)
        self.branch_choice.Bind(wx.EVT_CHOICE, self.on_branch_changed)
        self.commits_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_view_commit)

    def load_commits(self, repo: Repo):
        """Load commits from repository"""
        self.repo = repo
        self.populate_branch_choice()
        self.refresh_commits()

    def populate_branch_choice(self):
        """Populate the branch choice control"""
        if not self.repo:
            return

        self.branch_choice.Clear()

        # Add current branch first
        try:
            current_branch = self.repo.active_branch.name
            self.branch_choice.Append(current_branch)
            self.branch_choice.SetSelection(0)
        except:
            pass

        # Add other branches
        for branch in self.repo.heads:
            if branch.name != current_branch:
                self.branch_choice.Append(branch.name)

    def refresh_commits(self):
        """Refresh the commits list"""
        if not self.repo:
            return

        self.commits_list.DeleteAllItems()

        try:
            # Get selected branch
            branch_name = self.branch_choice.GetStringSelection()
            if not branch_name:
                return

            if branch_name in [b.name for b in self.repo.heads]:
                branch = self.repo.heads[branch_name]
                commits = list(self.repo.iter_commits(branch.name, max_count=100))
            else:
                # Fallback to current branch
                commits = list(self.repo.iter_commits('HEAD', max_count=100))

            for i, commit in enumerate(commits):
                index = self.commits_list.InsertItem(i, commit.hexsha[:8])

                # Message (first line only)
                message = commit.message.strip().split('\n')[0]
                if len(message) > 60:
                    message = message[:57] + "..."
                self.commits_list.SetItem(index, 1, message)

                # Author
                author_name = commit.author.name
                if len(author_name) > 20:
                    author_name = author_name[:17] + "..."
                self.commits_list.SetItem(index, 2, author_name)

                # Date
                date_str = datetime.fromtimestamp(
                    commit.committed_date).strftime('%Y-%m-%d %H:%M')
                self.commits_list.SetItem(index, 3, date_str)

                # Number of files changed with color coding
                try:
                    file_count = len(commit.stats.files)
                    self.commits_list.SetItem(index, 4, str(file_count))
                    
                    # Color code based on number of files changed
                    if file_count > 10:
                        self.commits_list.SetItemTextColour(index, wx.Colour(200, 0, 0))  # Red for large changes
                    elif file_count > 5:
                        self.commits_list.SetItemTextColour(index, wx.Colour(200, 100, 0))  # Orange for medium changes
                    else:
                        self.commits_list.SetItemTextColour(index, wx.Colour(0, 100, 0))  # Green for small changes
                except:
                    self.commits_list.SetItem(index, 4, "?")

                # Store commit object
                self.commits_list.SetItemData(index, i)

            self.commits_data = commits

        except Exception as e:
            wx.MessageBox(f"Error loading commits: {str(e)}", "Error",
                          wx.OK | wx.ICON_ERROR)

    def on_refresh(self, event):
        """Handle refresh button"""
        self.refresh_commits()

    def on_branch_changed(self, event):
        """Handle branch selection change"""
        self.refresh_commits()

    def on_view_commit(self, event):
        """Handle view commit button or double-click"""
        selected = self.commits_list.GetFirstSelected()
        if selected == -1:
            return

        commit = self.commits_data[self.commits_list.GetItemData(selected)]

        # Show commit diff in diff panel
        self.git_panel.diff_panel.show_commit_diff(commit)
        self.git_panel.content_notebook.SetSelection(2)  # Switch to diff tab

    def on_checkout_commit(self, event):
        """Handle checkout commit button"""
        selected = self.commits_list.GetFirstSelected()
        if selected == -1:
            return

        commit = self.commits_data[self.commits_list.GetItemData(selected)]

        if wx.MessageBox(
                f"Checkout commit {commit.hexsha[:8]}? This will put you in detached HEAD state.",
                "Confirm Checkout", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            try:
                self.repo.git.checkout(commit.hexsha)
                self.git_panel.main_frame.update_status(
                    f"Checked out commit: {commit.hexsha[:8]}")
                self.git_panel.load_repository(self.repo)
            except Exception as e:
                wx.MessageBox(f"Error checking out commit: {str(e)}", "Error",
                              wx.OK | wx.ICON_ERROR)


class FileContentPanel(wx.Panel):
    """Panel for displaying file content"""

    def __init__(self, parent, git_panel):
        super().__init__(parent)
        self.git_panel = git_panel

        self.create_ui()

    def create_ui(self):
        """Create the file content panel UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # File info panel with stats
        info_panel = wx.Panel(self)
        info_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.file_label = wx.StaticText(info_panel, label="No file selected")
        self.file_stats = wx.StaticText(info_panel, label="")
        
        info_sizer.Add(self.file_label, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        info_sizer.Add(self.file_stats, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        info_panel.SetSizer(info_sizer)

        # Toolbar for file operations
        toolbar_panel = wx.Panel(self)
        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.wrap_text_cb = wx.CheckBox(toolbar_panel, label="Wrap text")
        self.show_line_numbers_cb = wx.CheckBox(toolbar_panel, label="Line numbers")
        self.show_line_numbers_cb.SetValue(True)
        
        toolbar_sizer.Add(self.wrap_text_cb, 0, wx.ALL, 2)
        toolbar_sizer.Add(self.show_line_numbers_cb, 0, wx.ALL, 2)
        toolbar_panel.SetSizer(toolbar_sizer)

        # Content text control
        self.content_text = wx.TextCtrl(self,
                                        style=wx.TE_MULTILINE | wx.TE_READONLY
                                        | wx.TE_RICH2)
        self.content_text.SetFont(
            wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL))

        sizer.Add(info_panel, 0, wx.EXPAND | wx.ALL, 2)
        sizer.Add(toolbar_panel, 0, wx.EXPAND | wx.ALL, 2)
        sizer.Add(self.content_text, 1, wx.EXPAND | wx.ALL, 2)
        self.SetSizer(sizer)
        
        # Bind events
        self.wrap_text_cb.Bind(wx.EVT_CHECKBOX, self.on_wrap_changed)
        self.show_line_numbers_cb.Bind(wx.EVT_CHECKBOX, self.on_line_numbers_changed)

    def show_file(self, rel_path: str, file_path: str):
        """Show file content"""
        self.current_file_path = file_path
        self.current_rel_path = rel_path
        self.file_label.SetLabel(f"File: {rel_path}")

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            # Calculate file statistics
            lines = content.splitlines()
            line_count = len(lines)
            char_count = len(content)
            
            # Get file size
            import os
            file_size = os.path.getsize(file_path)
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            self.file_stats.SetLabel(f"Lines: {line_count:,} | Chars: {char_count:,} | Size: {size_str}")

            # Limit content size for performance
            truncated = False
            if len(content) > 100000:  # 100KB limit
                content = content[:100000]
                truncated = True

            # Add line numbers if enabled
            if self.show_line_numbers_cb.GetValue():
                content = self._add_line_numbers(content)
            
            if truncated:
                content += "\n\n... (file truncated for performance)"

            self.content_text.SetValue(content)
            
            # Apply text wrapping
            self._update_text_wrapping()

        except Exception as e:
            self.content_text.SetValue(f"Error reading file: {str(e)}")
            self.file_stats.SetLabel("Error loading file")
    
    def _add_line_numbers(self, content: str) -> str:
        """Add line numbers to content"""
        lines = content.splitlines()
        max_digits = len(str(len(lines)))
        
        numbered_lines = []
        for i, line in enumerate(lines, 1):
            line_num = str(i).rjust(max_digits)
            numbered_lines.append(f"{line_num}: {line}")
        
        return '\n'.join(numbered_lines)
    
    def _update_text_wrapping(self):
        """Update text wrapping based on checkbox"""
        if hasattr(self, 'content_text'):
            if self.wrap_text_cb.GetValue():
                # Enable word wrap
                style = self.content_text.GetWindowStyle()
                style &= ~wx.TE_DONTWRAP
                self.content_text.SetWindowStyle(style)
            else:
                # Disable word wrap
                style = self.content_text.GetWindowStyle()
                style |= wx.TE_DONTWRAP
                self.content_text.SetWindowStyle(style)
    
    def on_wrap_changed(self, event):
        """Handle wrap text checkbox change"""
        self._update_text_wrapping()
    
    def on_line_numbers_changed(self, event):
        """Handle line numbers checkbox change"""
        if hasattr(self, 'current_file_path'):
            self.show_file(self.current_rel_path, self.current_file_path)


class DiffPanel(wx.Panel):
    """Panel for displaying diffs"""

    def __init__(self, parent, git_panel):
        super().__init__(parent)
        self.git_panel = git_panel

        self.create_ui()

    def create_ui(self):
        """Create the diff panel UI"""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Diff info
        info_panel = wx.Panel(self)
        info_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.diff_label = wx.StaticText(info_panel, label="No diff selected")
        info_sizer.Add(self.diff_label, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                       5)
        info_panel.SetSizer(info_sizer)

        # Diff text control
        self.diff_text = wx.TextCtrl(self,
                                     style=wx.TE_MULTILINE | wx.TE_READONLY
                                     | wx.TE_RICH2)
        self.diff_text.SetFont(
            wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                    wx.FONTWEIGHT_NORMAL))

        sizer.Add(info_panel, 0, wx.EXPAND | wx.ALL, 2)
        sizer.Add(self.diff_text, 1, wx.EXPAND | wx.ALL, 2)
        self.SetSizer(sizer)

    def show_commit_diff(self, commit):
        """Show diff for a commit"""
        try:
            # Update label with commit info
            commit_msg = commit.message.strip().split('\n')[0]
            if len(commit_msg) > 50:
                commit_msg = commit_msg[:47] + "..."
            
            self.diff_label.SetLabel(
                f"Commit: {commit.hexsha[:8]} - {commit_msg}"
            )

            # Get diff
            if commit.parents:
                diff = commit.parents[0].diff(commit, create_patch=True)
            else:
                # Initial commit
                diff = commit.diff(git.NULL_TREE, create_patch=True)

            diff_text = ""
            files_changed = 0
            lines_added = 0
            lines_deleted = 0
            
            for item in diff:
                if item.diff:
                    files_changed += 1
                    diff_content = item.diff.decode('utf-8', errors='replace')
                    diff_text += diff_content + "\n"
                    
                    # Count line changes
                    for line in diff_content.split('\n'):
                        if line.startswith('+') and not line.startswith('+++'):
                            lines_added += 1
                        elif line.startswith('-') and not line.startswith('---'):
                            lines_deleted += 1

            if not diff_text:
                diff_text = "No changes in this commit"
            else:
                # Add summary header
                summary = f"Files changed: {files_changed} | Lines added: +{lines_added} | Lines deleted: -{lines_deleted}\n"
                summary += "=" * 80 + "\n\n"
                diff_text = summary + diff_text

            # Apply diff coloring
            self._apply_diff_coloring(diff_text)

        except Exception as e:
            self.diff_text.SetValue(f"Error getting diff: {str(e)}")
    
    def _apply_diff_coloring(self, diff_text: str):
        """Apply color coding to diff text"""
        self.diff_text.SetValue(diff_text)
        
        # Apply styling to different types of lines
        lines = diff_text.split('\n')
        start_pos = 0
        
        for line in lines:
            line_len = len(line) + 1  # +1 for newline
            
            if line.startswith('+++') or line.startswith('---'):
                # File headers - blue
                self.diff_text.SetStyle(start_pos, start_pos + len(line), 
                                       wx.TextAttr(wx.Colour(0, 0, 200)))
            elif line.startswith('@@'):
                # Hunk headers - purple
                self.diff_text.SetStyle(start_pos, start_pos + len(line),
                                       wx.TextAttr(wx.Colour(128, 0, 128)))
            elif line.startswith('+') and not line.startswith('+++'):
                # Added lines - green
                self.diff_text.SetStyle(start_pos, start_pos + len(line),
                                       wx.TextAttr(wx.Colour(0, 150, 0)))
            elif line.startswith('-') and not line.startswith('---'):
                # Deleted lines - red
                self.diff_text.SetStyle(start_pos, start_pos + len(line),
                                       wx.TextAttr(wx.Colour(150, 0, 0)))
            elif line.startswith('diff --git') or line.startswith('index'):
                # Git metadata - gray
                self.diff_text.SetStyle(start_pos, start_pos + len(line),
                                       wx.TextAttr(wx.Colour(100, 100, 100)))
            
            start_pos += line_len


class OutputPanel(wx.Panel):
    """Panel for displaying command output"""

    def __init__(self, parent, git_panel):
        super().__init__(parent)
        self.git_panel = git_panel

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


# Dialog classes for various operations
class AddRemoteDialog(wx.Dialog):
    """Dialog for adding a remote repository"""

    def __init__(self, parent):
        super().__init__(parent, title="Add Remote", size=(400, 150))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Name field
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(wx.StaticText(panel, label="Name:"), 0,
                       wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.name_text = wx.TextCtrl(panel, size=(200, -1))
        name_sizer.Add(self.name_text, 1, wx.ALL, 5)

        # URL field
        url_sizer = wx.BoxSizer(wx.HORIZONTAL)
        url_sizer.Add(wx.StaticText(panel, label="URL:"), 0,
                      wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.url_text = wx.TextCtrl(panel, size=(200, -1))
        url_sizer.Add(self.url_text, 1, wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        sizer.Add(name_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(url_sizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        panel.SetSizer(sizer)

        # Set default values
        self.name_text.SetValue("origin")

    def get_values(self):
        """Get the entered values"""
        return self.name_text.GetValue(), self.url_text.GetValue()
