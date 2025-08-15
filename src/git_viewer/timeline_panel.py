#!/usr/bin/env python3
"""
Timeline Panel for Git Repository Viewer
Provides a visual timeline of commits with branch information and TLOC tracking
"""

import wx
import wx.lib.agw.aui as aui
import wx.lib.scrolledpanel as scrolled
import os
import subprocess
import threading
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
import git
from git import Repo
from collections import defaultdict


class TlocCalculator:
    """Utility class for calculating Total Lines of Code"""
    
    # File extensions to consider for TLOC calculation
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.cc', '.cxx',
        '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.swift', '.m',
        '.mm', '.scala', '.clj', '.hs', '.ml', '.fs', '.vb', '.pas', '.d', '.nim',
        '.cr', '.jl', '.elm', '.dart', '.v', '.sv', '.vhd', '.vhdl', '.tcl', '.r',
        '.R', '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.pl', '.pm',
        '.lua', '.sql', '.html', '.htm', '.css', '.scss', '.sass', '.less', '.xml',
        '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.md', '.tex',
        '.makefile', '.cmake', '.gradle', '.maven', '.ant', '.sbt', '.mix', '.ex',
        '.exs', '.erl', '.hrl', '.proto', '.thrift', '.avro', '.capnp', '.fbs'
    }
    
    @classmethod
    def is_code_file(cls, filepath: str) -> bool:
        """Check if a file should be counted for TLOC"""
        _, ext = os.path.splitext(filepath.lower())
        filename = os.path.basename(filepath.lower())
        
        # Check by extension
        if ext in cls.CODE_EXTENSIONS:
            return True
            
        # Check by filename (for files without extensions)
        code_filenames = {
            'makefile', 'dockerfile', 'vagrantfile', 'gemfile', 'rakefile',
            'gruntfile', 'gulpfile', 'webpack', 'rollup', 'vite', 'jest',
            'babel', 'eslint', 'prettier', 'tsconfig', 'package', 'composer',
            'requirements', 'pipfile', 'poetry', 'cargo', 'go.mod', 'go.sum'
        }
        
        base_name = filename.split('.')[0]
        return base_name in code_filenames
    
    @classmethod
    def count_lines_in_file(cls, file_path: str) -> Tuple[int, int, int]:
        """
        Count lines in a file
        Returns: (total_lines, code_lines, blank_lines)
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            blank_lines = sum(1 for line in lines if line.strip() == '')
            code_lines = total_lines - blank_lines
            
            return total_lines, code_lines, blank_lines
        except Exception:
            return 0, 0, 0
    
    @classmethod
    def calculate_file_tloc_at_commit(cls, repo: Repo, commit, file_path: str) -> Tuple[int, int, int]:
        """
        Calculate TLOC for a specific file at a specific commit
        Returns: (total_lines, code_lines, blank_lines)
        """
        try:
            # Get file content at this commit using a more robust approach
            try:
                # Use git show command instead of blob stream to avoid stream issues
                content = repo.git.show(f"{commit.hexsha}:{file_path}")
            except Exception:
                # File doesn't exist at this commit or other error
                return 0, 0, 0
            
            lines = content.splitlines()
            total_lines = len(lines)
            blank_lines = sum(1 for line in lines if line.strip() == '')
            code_lines = total_lines - blank_lines
            
            return total_lines, code_lines, blank_lines
            
        except Exception:
            return 0, 0, 0
    
    @classmethod
    def calculate_project_tloc_at_commit(cls, repo: Repo, commit) -> Dict[str, Any]:
        """
        Calculate TLOC for entire project at a specific commit (lightweight version)
        Returns dict with totals only for performance
        """
        result = {
            'files': {},
            'totals': {'total_lines': 0, 'code_lines': 0, 'blank_lines': 0, 'file_count': 0}
        }
        
        try:
            # Use git ls-tree for better performance
            tree_output = repo.git.ls_tree('-r', '--name-only', commit.hexsha)
            files = tree_output.splitlines() if tree_output else []
            
            # Count only code files for performance
            code_files = [f for f in files if cls.is_code_file(f)]
            result['totals']['file_count'] = len(code_files)
            
            # For timeline display, we'll calculate a rough estimate
            # Only calculate actual TLOC for a sample of files to avoid performance issues
            sample_size = min(10, len(code_files))
            if sample_size > 0:
                sample_files = code_files[:sample_size]
                total_lines_sample = 0
                
                for file_path in sample_files:
                    try:
                        total, code, blank = cls.calculate_file_tloc_at_commit(repo, commit, file_path)
                        total_lines_sample += code
                    except Exception:
                        continue
                
                # Estimate total based on sample
                if total_lines_sample > 0:
                    avg_lines_per_file = total_lines_sample / sample_size
                    estimated_total = int(avg_lines_per_file * len(code_files))
                    result['totals']['code_lines'] = estimated_total
                    result['totals']['total_lines'] = int(estimated_total * 1.2)  # Rough estimate including blanks
                    result['totals']['blank_lines'] = result['totals']['total_lines'] - result['totals']['code_lines']
        
        except Exception as e:
            print(f"Error calculating TLOC at commit {commit.hexsha[:8]}: {e}")
        
        return result


class CommitTimelineData:
    """Data structure for timeline commit information"""
    
    def __init__(self, commit, repo: Repo):
        self.commit = commit
        self.repo = repo
        self.sha = commit.hexsha
        self.short_sha = commit.hexsha[:8]
        self.message = commit.message.strip()
        self.author = commit.author.name
        self.email = commit.author.email
        self.date = datetime.fromtimestamp(commit.committed_date)
        self.parents = [p.hexsha for p in commit.parents]
        
        # Calculate affected files and their changes
        self.affected_files = []
        self.files_added = []
        self.files_modified = []
        self.files_deleted = []
        self.tloc_changes = {}
        
        self._calculate_file_changes()
        
        # Calculate TLOC at this commit (with error handling)
        try:
            self.tloc_data = TlocCalculator.calculate_project_tloc_at_commit(repo, commit)
        except Exception as e:
            print(f"Warning: Could not calculate TLOC for commit {self.short_sha}: {e}")
            # Provide default TLOC data
            self.tloc_data = {
                'files': {},
                'totals': {'total_lines': 0, 'code_lines': 0, 'blank_lines': 0, 'file_count': 0}
            }
        
        # Branch information (to be set by timeline panel)
        self.branches = []
        self.is_merge = len(self.parents) > 1
        self.is_branch_point = False
    
    def _calculate_file_changes(self):
        """Calculate which files were changed in this commit"""
        try:
            if self.commit.parents:
                # Compare with first parent (get actual commit object)
                parent_commit = self.commit.parents[0]
                diff = parent_commit.diff(self.commit)
            else:
                # Initial commit - compare with empty tree
                diff = self.commit.diff(git.NULL_TREE)
            
            for change in diff:
                file_path = change.b_path or change.a_path
                
                if change.change_type == 'A':  # Added
                    self.files_added.append(file_path)
                elif change.change_type == 'M':  # Modified
                    self.files_modified.append(file_path)
                elif change.change_type == 'D':  # Deleted
                    self.files_deleted.append(file_path)
                
                if file_path:
                    self.affected_files.append(file_path)
                    
                    # Calculate TLOC changes for code files (simplified to avoid stream issues)
                    if TlocCalculator.is_code_file(file_path):
                        try:
                            if change.change_type != 'D':
                                # File exists after commit
                                after_tloc = TlocCalculator.calculate_file_tloc_at_commit(
                                    self.repo, self.commit, file_path)
                            else:
                                after_tloc = (0, 0, 0)
                            
                            if change.change_type != 'A' and self.commit.parents:
                                # File existed before commit
                                parent_commit = self.commit.parents[0]
                                before_tloc = TlocCalculator.calculate_file_tloc_at_commit(
                                    self.repo, parent_commit, file_path)
                            else:
                                before_tloc = (0, 0, 0)
                            
                            lines_changed = after_tloc[1] - before_tloc[1]  # code lines difference
                            self.tloc_changes[file_path] = {
                                'before': before_tloc,
                                'after': after_tloc,
                                'change': lines_changed
                            }
                        except Exception as tloc_error:
                            # Skip TLOC calculation for this file if it fails
                            print(f"Warning: Could not calculate TLOC for {file_path}: {tloc_error}")
                            continue
        
        except Exception as e:
            print(f"Error calculating file changes for commit {self.short_sha}: {e}")


class TimelinePanel(wx.Panel):
    """Panel for displaying commit timeline with branch visualization and TLOC tracking"""
    
    def __init__(self, parent, git_panel):
        super().__init__(parent)
        self.git_panel = git_panel
        self.repo = None
        self.timeline_data = []
        self.branch_colors = {}
        self.selected_commit = None
        
        self.create_ui()
    
    def create_ui(self):
        """Create the timeline panel UI"""
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Left panel - timeline controls and options
        left_panel = wx.Panel(self)
        left_panel.SetMinSize((250, -1))
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Controls
        controls_box = wx.StaticBox(left_panel, label="Timeline Controls")
        controls_sizer = wx.StaticBoxSizer(controls_box, wx.VERTICAL)
        
        # Branch selection
        branch_sizer = wx.BoxSizer(wx.HORIZONTAL)
        branch_sizer.Add(wx.StaticText(left_panel, label="Branches:"), 0,
                        wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        self.branch_choice = wx.Choice(left_panel)
        branch_sizer.Add(self.branch_choice, 1, wx.ALL, 2)
        
        # Limit controls
        limit_sizer = wx.BoxSizer(wx.HORIZONTAL)
        limit_sizer.Add(wx.StaticText(left_panel, label="Limit:"), 0,
                       wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        self.limit_spin = wx.SpinCtrl(left_panel, value="50", min=10, max=1000)
        limit_sizer.Add(self.limit_spin, 0, wx.ALL, 2)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.refresh_btn = wx.Button(left_panel, label="Refresh")
        self.export_btn = wx.Button(left_panel, label="Export")
        btn_sizer.Add(self.refresh_btn, 0, wx.ALL, 2)
        btn_sizer.Add(self.export_btn, 0, wx.ALL, 2)
        
        controls_sizer.Add(branch_sizer, 0, wx.EXPAND | wx.ALL, 2)
        controls_sizer.Add(limit_sizer, 0, wx.EXPAND | wx.ALL, 2)
        controls_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 2)
        
        # Statistics
        stats_box = wx.StaticBox(left_panel, label="Project Statistics")
        stats_sizer = wx.StaticBoxSizer(stats_box, wx.VERTICAL)
        
        self.stats_text = wx.StaticText(left_panel, label="No data loaded")
        stats_sizer.Add(self.stats_text, 1, wx.EXPAND | wx.ALL, 5)
        
        left_sizer.Add(controls_sizer, 0, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(stats_sizer, 1, wx.EXPAND | wx.ALL, 5)
        left_panel.SetSizer(left_sizer)
        
        # Right panel - timeline visualization and details
        right_panel = wx.Panel(self)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Timeline view (scrollable)
        self.timeline_scroll = scrolled.ScrolledPanel(right_panel)
        self.timeline_scroll.SetupScrolling(scroll_x=False, scroll_y=True)
        self.timeline_scroll.SetBackgroundColour(wx.Colour(250, 250, 250))
        
        # Details panel
        details_splitter = wx.SplitterWindow(right_panel, style=wx.SP_3D)
        
        # Commit details
        self.details_panel = wx.Panel(details_splitter)
        self.create_details_panel()
        
        # File impact details  
        self.files_panel = wx.Panel(details_splitter)
        self.create_files_panel()
        
        details_splitter.SplitHorizontally(self.details_panel, self.files_panel)
        details_splitter.SetSashGravity(0.3)
        details_splitter.SetMinimumPaneSize(100)
        
        right_sizer.Add(self.timeline_scroll, 2, wx.EXPAND | wx.ALL, 2)
        right_sizer.Add(details_splitter, 1, wx.EXPAND | wx.ALL, 2)
        right_panel.SetSizer(right_sizer)
        
        # Add panels to main sizer
        main_sizer.Add(left_panel, 0, wx.EXPAND | wx.ALL, 2)
        main_sizer.Add(right_panel, 1, wx.EXPAND | wx.ALL, 2)
        
        self.SetSizer(main_sizer)
        
        # Bind events
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export)
        self.branch_choice.Bind(wx.EVT_CHOICE, self.on_branch_changed)
        self.timeline_scroll.Bind(wx.EVT_PAINT, self.on_timeline_paint)
        self.timeline_scroll.Bind(wx.EVT_LEFT_DOWN, self.on_timeline_click)
    
    def create_details_panel(self):
        """Create the commit details panel"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Commit info
        info_box = wx.StaticBox(self.details_panel, label="Commit Details")
        info_sizer = wx.StaticBoxSizer(info_box, wx.VERTICAL)
        
        self.commit_sha_text = wx.StaticText(self.details_panel, label="")
        self.commit_author_text = wx.StaticText(self.details_panel, label="")
        self.commit_date_text = wx.StaticText(self.details_panel, label="")
        self.commit_message_text = wx.TextCtrl(self.details_panel, 
                                              style=wx.TE_MULTILINE | wx.TE_READONLY,
                                              size=(-1, 80))
        
        info_sizer.Add(self.commit_sha_text, 0, wx.ALL, 2)
        info_sizer.Add(self.commit_author_text, 0, wx.ALL, 2)
        info_sizer.Add(self.commit_date_text, 0, wx.ALL, 2)
        info_sizer.Add(wx.StaticText(self.details_panel, label="Message:"), 0, wx.ALL, 2)
        info_sizer.Add(self.commit_message_text, 1, wx.EXPAND | wx.ALL, 2)
        
        # TLOC info
        tloc_box = wx.StaticBox(self.details_panel, label="TLOC at this Commit")
        tloc_sizer = wx.StaticBoxSizer(tloc_box, wx.VERTICAL)
        
        self.tloc_summary_text = wx.StaticText(self.details_panel, label="")
        tloc_sizer.Add(self.tloc_summary_text, 0, wx.ALL, 2)
        
        sizer.Add(info_sizer, 1, wx.EXPAND | wx.ALL, 2)
        sizer.Add(tloc_sizer, 0, wx.EXPAND | wx.ALL, 2)
        
        self.details_panel.SetSizer(sizer)
    
    def create_files_panel(self):
        """Create the files impact panel"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # File list
        files_box = wx.StaticBox(self.files_panel, label="Files Impacted")
        files_sizer = wx.StaticBoxSizer(files_box, wx.VERTICAL)
        
        self.files_list = wx.ListCtrl(self.files_panel, style=wx.LC_REPORT)
        self.files_list.AppendColumn("File", width=250)
        self.files_list.AppendColumn("Change", width=80)
        self.files_list.AppendColumn("Lines Before", width=100)
        self.files_list.AppendColumn("Lines After", width=100)
        self.files_list.AppendColumn("Net Change", width=100)
        
        files_sizer.Add(self.files_list, 1, wx.EXPAND | wx.ALL, 2)
        
        sizer.Add(files_sizer, 1, wx.EXPAND | wx.ALL, 2)
        self.files_panel.SetSizer(sizer)
    
    def load_timeline(self, repo: Repo):
        """Load timeline data from repository"""
        self.repo = repo
        self.populate_branch_choice()
        self.refresh_timeline()
    
    def populate_branch_choice(self):
        """Populate branch selection"""
        if not self.repo:
            return
        
        self.branch_choice.Clear()
        self.branch_choice.Append("All Branches")
        
        try:
            current_branch = self.repo.active_branch.name
            self.branch_choice.Append(f"Current ({current_branch})")
            self.branch_choice.SetSelection(1)
        except:
            self.branch_choice.SetSelection(0)
        
        # Add other branches
        for branch in self.repo.heads:
            if hasattr(self.repo, 'active_branch'):
                try:
                    if branch.name != self.repo.active_branch.name:
                        self.branch_choice.Append(branch.name)
                except:
                    self.branch_choice.Append(branch.name)
            else:
                self.branch_choice.Append(branch.name)
    
    def refresh_timeline(self):
        """Refresh timeline data"""
        if not self.repo:
            return
        
        # Show loading message
        self.git_panel.main_frame.update_status("Loading timeline data...")
        
        def worker():
            try:
                self.timeline_data = []
                
                # Get commits based on branch selection
                selection = self.branch_choice.GetSelection()
                limit = self.limit_spin.GetValue()
                
                if selection == 0:  # All branches
                    commits = list(self.repo.iter_commits('--all', max_count=limit))
                elif selection == 1:  # Current branch
                    commits = list(self.repo.iter_commits('HEAD', max_count=limit))
                else:  # Specific branch
                    branch_name = self.branch_choice.GetStringSelection()
                    commits = list(self.repo.iter_commits(branch_name, max_count=limit))
                
                # Create timeline data
                for commit in commits:
                    commit_data = CommitTimelineData(commit, self.repo)
                    self.timeline_data.append(commit_data)
                
                # Calculate branch information
                self._calculate_branch_info()
                
                # Update UI on main thread
                wx.CallAfter(self._update_timeline_ui)
                
            except Exception as e:
                wx.CallAfter(self._on_timeline_error, str(e))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _calculate_branch_info(self):
        """Calculate branch information for timeline visualization"""
        # Assign colors to branches
        branch_names = set()
        for data in self.timeline_data:
            try:
                # Find which branches contain this commit
                branches = [branch.name for branch in self.repo.heads 
                           if self.repo.is_ancestor(data.commit, branch.commit)]
                data.branches = branches
                branch_names.update(branches)
            except:
                data.branches = []
        
        # Assign colors
        colors = [
            wx.Colour(255, 100, 100),  # Red
            wx.Colour(100, 255, 100),  # Green  
            wx.Colour(100, 100, 255),  # Blue
            wx.Colour(255, 255, 100),  # Yellow
            wx.Colour(255, 100, 255),  # Magenta
            wx.Colour(100, 255, 255),  # Cyan
            wx.Colour(255, 150, 100),  # Orange
            wx.Colour(150, 100, 255),  # Purple
        ]
        
        for i, branch in enumerate(sorted(branch_names)):
            self.branch_colors[branch] = colors[i % len(colors)]
    
    def _update_timeline_ui(self):
        """Update timeline UI after data loading"""
        # Update statistics
        if self.timeline_data:
            latest_data = self.timeline_data[0]
            tloc = latest_data.tloc_data['totals']
            
            stats_text = f"Files: {tloc['file_count']}\n"
            stats_text += f"Total Lines: {tloc['total_lines']:,}\n"
            stats_text += f"Code Lines: {tloc['code_lines']:,}\n"
            stats_text += f"Commits: {len(self.timeline_data)}"
            
            self.stats_text.SetLabel(stats_text)
        
        # Refresh timeline visualization
        self.timeline_scroll.Refresh()
        self.git_panel.main_frame.update_status("Timeline loaded")
    
    def _on_timeline_error(self, error_msg: str):
        """Handle timeline loading error"""
        wx.MessageBox(f"Error loading timeline: {error_msg}", "Error",
                     wx.OK | wx.ICON_ERROR)
        self.git_panel.main_frame.update_status("Ready")
    
    def on_timeline_paint(self, event):
        """Paint the timeline visualization"""
        if not self.timeline_data:
            event.Skip()
            return
        
        dc = wx.PaintDC(self.timeline_scroll)
        self.timeline_scroll.PrepareDC(dc)
        
        # Clear background
        size = self.timeline_scroll.GetSize()
        dc.SetBackground(wx.Brush(wx.Colour(250, 250, 250)))
        dc.Clear()
        
        # Timeline constants
        margin_left = 50
        margin_top = 20
        commit_height = 40
        branch_width = 20
        max_branches = 8
        
        # Calculate timeline dimensions
        timeline_height = len(self.timeline_data) * commit_height + margin_top * 2
        timeline_width = margin_left + max_branches * branch_width + 400
        
        # Set virtual size for scrolling
        self.timeline_scroll.SetVirtualSize((timeline_width, timeline_height))
        
        # Draw commits
        for i, commit_data in enumerate(self.timeline_data):
            y = margin_top + i * commit_height
            
            # Draw branch lines
            branch_x = margin_left
            for j, branch in enumerate(sorted(self.branch_colors.keys())):
                if j >= max_branches:
                    break
                    
                color = self.branch_colors[branch]
                dc.SetPen(wx.Pen(color, 3))
                
                x = branch_x + j * branch_width
                
                if branch in commit_data.branches:
                    # Draw commit point
                    dc.SetBrush(wx.Brush(color))
                    dc.DrawCircle(x, y + commit_height // 2, 6)
                    
                    # Draw line to next commit if it's also on this branch
                    if i < len(self.timeline_data) - 1:
                        next_commit = self.timeline_data[i + 1]
                        if branch in next_commit.branches:
                            dc.DrawLine(x, y + commit_height // 2 + 6,
                                      x, y + commit_height + commit_height // 2 - 6)
                else:
                    # Draw continuing line
                    if i < len(self.timeline_data) - 1:
                        next_commit = self.timeline_data[i + 1]
                        if (branch in [data.branches for data in self.timeline_data[i+1:] 
                                     if data.branches] and 
                            any(branch in data.branches for data in self.timeline_data[i+1:])):
                            dc.SetPen(wx.Pen(color, 1))
                            dc.DrawLine(x, y, x, y + commit_height)
            
            # Draw commit info
            info_x = margin_left + max_branches * branch_width + 20
            
            # Highlight selected commit
            if commit_data == self.selected_commit:
                dc.SetBrush(wx.Brush(wx.Colour(230, 230, 255)))
                dc.SetPen(wx.Pen(wx.Colour(100, 100, 200), 2))
                dc.DrawRectangle(info_x - 5, y - 2, 390, commit_height + 4)
            
            # Commit SHA and message
            dc.SetTextForeground(wx.Colour(0, 0, 0))
            dc.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            dc.DrawText(commit_data.short_sha, info_x, y + 2)
            
            dc.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            message = commit_data.message.split('\n')[0]
            if len(message) > 50:
                message = message[:47] + "..."
            dc.DrawText(message, info_x + 80, y + 2)
            
            # Author and date
            dc.SetTextForeground(wx.Colour(100, 100, 100))
            dc.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            dc.DrawText(f"{commit_data.author}", info_x, y + 18)
            dc.DrawText(commit_data.date.strftime('%Y-%m-%d %H:%M'), info_x + 150, y + 18)
            
            # TLOC info
            tloc = commit_data.tloc_data['totals']
            tloc_text = f"TLOC: {tloc['code_lines']:,} ({tloc['file_count']} files)"
            dc.DrawText(tloc_text, info_x + 250, y + 18)
        
        event.Skip()
    
    def on_timeline_click(self, event):
        """Handle timeline click to select commit"""
        if not self.timeline_data:
            return
        
        pos = event.GetPosition()
        commit_height = 40
        margin_top = 20
        
        # Convert click position to commit index
        y = pos.y + self.timeline_scroll.GetScrollPos(wx.VERTICAL)
        commit_index = (y - margin_top) // commit_height
        
        if 0 <= commit_index < len(self.timeline_data):
            self.selected_commit = self.timeline_data[commit_index]
            self.update_commit_details()
            self.timeline_scroll.Refresh()
    
    def update_commit_details(self):
        """Update commit details panel"""
        if not self.selected_commit:
            return
        
        commit = self.selected_commit
        
        # Update commit info
        self.commit_sha_text.SetLabel(f"SHA: {commit.sha}")
        self.commit_author_text.SetLabel(f"Author: {commit.author} <{commit.email}>")
        self.commit_date_text.SetLabel(f"Date: {commit.date.strftime('%Y-%m-%d %H:%M:%S')}")
        self.commit_message_text.SetValue(commit.message)
        
        # Update TLOC info
        tloc = commit.tloc_data['totals']
        tloc_text = f"Files: {tloc['file_count']:,}\n"
        tloc_text += f"Total Lines: {tloc['total_lines']:,}\n"
        tloc_text += f"Code Lines: {tloc['code_lines']:,}\n"
        tloc_text += f"Blank Lines: {tloc['blank_lines']:,}"
        self.tloc_summary_text.SetLabel(tloc_text)
        
        # Update files list
        self.files_list.DeleteAllItems()
        
        for i, file_path in enumerate(commit.affected_files):
            index = self.files_list.InsertItem(i, file_path)
            
            # Determine change type
            if file_path in commit.files_added:
                change_type = "Added"
                self.files_list.SetItemTextColour(index, wx.Colour(0, 150, 0))
            elif file_path in commit.files_modified:
                change_type = "Modified"
                self.files_list.SetItemTextColour(index, wx.Colour(100, 100, 0))
            elif file_path in commit.files_deleted:
                change_type = "Deleted"
                self.files_list.SetItemTextColour(index, wx.Colour(150, 0, 0))
            else:
                change_type = "Unknown"
            
            self.files_list.SetItem(index, 1, change_type)
            
            # TLOC information if available
            if file_path in commit.tloc_changes:
                tloc_info = commit.tloc_changes[file_path]
                before_lines = tloc_info['before'][1]  # code lines
                after_lines = tloc_info['after'][1]   # code lines
                net_change = tloc_info['change']
                
                self.files_list.SetItem(index, 2, str(before_lines))
                self.files_list.SetItem(index, 3, str(after_lines))
                
                change_str = f"{net_change:+d}" if net_change != 0 else "0"
                self.files_list.SetItem(index, 4, change_str)
    
    def on_refresh(self, event):
        """Handle refresh button"""
        self.refresh_timeline()
    
    def on_export(self, event):
        """Handle export button"""
        if not self.timeline_data:
            wx.MessageBox("No timeline data to export.", "No Data", wx.OK | wx.ICON_WARNING)
            return
        
        with wx.FileDialog(self, "Export Timeline Data",
                          defaultFile="timeline_data.csv",
                          wildcard="CSV files (*.csv)|*.csv",
                          style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dialog:
            
            if dialog.ShowModal() == wx.ID_OK:
                self.export_timeline_data(dialog.GetPath())
    
    def export_timeline_data(self, file_path: str):
        """Export timeline data to CSV"""
        try:
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'SHA', 'Short SHA', 'Author', 'Email', 'Date', 'Message',
                    'Branches', 'Files Changed', 'Files Added', 'Files Modified', 'Files Deleted',
                    'Total Files', 'Total Lines', 'Code Lines', 'Blank Lines'
                ])
                
                # Write commit data
                for commit_data in self.timeline_data:
                    tloc = commit_data.tloc_data['totals']
                    
                    writer.writerow([
                        commit_data.sha,
                        commit_data.short_sha,
                        commit_data.author,
                        commit_data.email,
                        commit_data.date.isoformat(),
                        commit_data.message.replace('\n', ' '),
                        ', '.join(commit_data.branches),
                        len(commit_data.affected_files),
                        len(commit_data.files_added),
                        len(commit_data.files_modified),
                        len(commit_data.files_deleted),
                        tloc['file_count'],
                        tloc['total_lines'],
                        tloc['code_lines'],
                        tloc['blank_lines']
                    ])
            
            wx.MessageBox(f"Timeline data exported to {file_path}", "Export Complete",
                         wx.OK | wx.ICON_INFORMATION)
            
        except Exception as e:
            wx.MessageBox(f"Error exporting data: {str(e)}", "Export Error",
                         wx.OK | wx.ICON_ERROR)
    
    def on_branch_changed(self, event):
        """Handle branch selection change"""
        self.refresh_timeline()
