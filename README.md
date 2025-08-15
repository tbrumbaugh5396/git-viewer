# Git Repository Viewer

A comprehensive Git and Meta repository management tool built with wxPython. This application provides a graphical interface for all Git operations plus support for meta repositories using the [meta package](https://www.npmjs.com/package/meta).

## Features

### Git Repository Management
- **Timeline View**: Visual timeline of commits with branch visualization and TLOC tracking
- **Enhanced Repository Browser**: Improved views for branches, remotes, files, and commit history
- **Advanced File Operations**: Enhanced file browsing with icons, sizes, and smart content viewing
- **Smart Branch Management**: Create, checkout, delete branches with visual indicators
- **Commit Operations**: Stage files, create commits with advanced options
- **Merge Operations**: Merge branches with customizable options
- **Remote Management**: Add, remove, and manage remote repositories with status indicators  
- **Git Commands**: Pull, push, fetch, and other Git operations
- **Configuration**: Manage Git configuration (global, repository, system)

### Meta Repository Support
- **Meta Repository Detection**: Automatically detects and loads meta repositories
- **Project Management**: Add, import, and remove projects from meta repositories
- **Meta Commands**: Execute meta commands like `git status`, `npm install` across all projects
- **Project Browser**: View and manage individual projects within meta repositories
- **Seamless Integration**: Switch between Git and Meta views seamlessly

### User Interface
- **Tabbed Interface**: Separate tabs for Git and Meta repository management
- **Multi-Panel Layout**: Organized panels for different aspects of repository management
- **Real-time Updates**: Live status updates and command output
- **Context Menus**: Right-click operations for common tasks
- **Keyboard Shortcuts**: Efficient keyboard navigation and operations

## Installation

### Prerequisites

1. **Python 3.7+**: Make sure you have Python 3.7 or newer installed
2. **Git**: Git must be installed and accessible from the command line
3. **Node.js and npm** (optional): Required for meta repository support

### Install Python Dependencies

1. Clone or download this repository
2. Navigate to the project directory
3. Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Install Meta CLI (Optional)

For meta repository support, install the meta package globally:

```bash
npm install -g meta
```

## Usage

### Starting the Application

Run the application using one of these methods:

**Method 1 (Main launcher):**
```bash
python3 git_viewer.py
```

**Method 2 (Package module):**
```bash
python3 -m src.git_viewer
```

**Method 3 (From package directory):**
```bash
cd src/git_viewer && python3 run.py
```

**Method 4 (After installation):**
```bash
# First install: pip install -e .
git-viewer
```

**Note for macOS/Linux users:** Use `python3` instead of `python` as shown above.

### Git Repository Operations

#### Opening a Repository
1. **File → Open Repository** or `Ctrl+O`
2. Select the root directory of your Git repository
3. The application will load repository information automatically

#### Cloning a Repository
1. **File → Clone Repository** or `Ctrl+N`
2. Enter the repository URL and destination path
3. Configure clone options (recursive, shallow, bare)
4. Click "Clone" to start the process

#### Branch Management
- **View Branches**: Use the "Branches" tab to see all local and remote branches
- **Checkout Branch**: Double-click a branch or select and click "Checkout"
- **Create Branch**: Click "New Branch" and enter the branch name
- **Delete Branch**: Select a branch and click "Delete" (cannot delete current branch)

#### Making Commits
1. **Git → Commit** or `Ctrl+M`
2. Stage files by selecting them in the "Unstaged Files" tab and clicking "Stage"
3. Enter a commit message
4. Configure commit options (amend, sign-off)
5. Click "Commit"

#### Timeline View (New!)
The Timeline view provides a comprehensive visual representation of your repository's history:

**Features:**
- **Visual Commit Timeline**: See commits in chronological order with branch visualization
- **Branch Visualization**: Different colored lines show how branches diverge and merge
- **TLOC Tracking**: Total Lines of Code (TLOC) calculated for each commit and the entire project
- **File Impact Analysis**: See which files were changed in each commit with line count changes
- **Interactive Selection**: Click commits to see detailed information

**Using the Timeline:**
1. Open a repository and click the "Timeline" tab
2. Select branch filtering options (All Branches, Current Branch, or specific branch)
3. Adjust commit limit for performance (10-1000 commits)
4. Click commits in the timeline to see details:
   - Commit information (SHA, author, date, message)
   - TLOC statistics at that point in time
   - Files impacted with before/after line counts
5. Export timeline data to CSV for analysis

**TLOC Calculation:**
- Tracks Total Lines of Code for supported file extensions
- Shows code lines vs. blank lines
- Calculates net changes per commit
- Supports 60+ programming languages and file types

#### Enhanced View Panels (Updated!)

**🎯 Commits Panel**
- Color-coded commits based on number of files changed (green/orange/red)
- Truncated commit messages and author names for better readability
- Improved date formatting
- Better error handling for edge cases

**📄 File Content Panel**
- Toggle line numbers on/off
- Text wrapping control
- File statistics display (lines, characters, file size)
- Performance optimizations for large files
- Enhanced file viewing experience

**🎨 Diff Panel**
- Color-coded diff output (green for additions, red for deletions)
- File headers highlighted in blue
- Hunk headers in purple
- Summary statistics (files changed, lines added/deleted)
- Better formatting and readability

**📁 Files Panel**
- File type icons (💻 for code, 📄 for docs, 🖼️ for images, etc.)
- File size display for each file
- Color coding by file type
- Smart sorting (directories first, then files alphabetically)
- Enhanced visual presentation

**🌿 Branches Panel**
- Visual indicators for current branch
- Color coding for local vs remote branches
- Last commit information for each branch
- Enhanced branch creation and deletion

**🔗 Remotes Panel**
- Remote URL display and management
- Connection status indicators
- Enhanced remote operations

#### File Operations
- **Browse Files**: Use the enhanced "Files" tab with icons and file info
- **View File Content**: Double-click files for improved content viewing with line numbers
- **View Diffs**: Select commits to see colorized, formatted diffs

#### Remote Operations
- **View Remotes**: Use the "Remotes" tab to see configured remotes
- **Add Remote**: Click "Add Remote" and enter name and URL
- **Git Operations**: Use **Git** menu for pull, push, fetch operations

### Meta Repository Operations

#### Working with Meta Repositories
1. Open a directory containing a `.meta` file, or
2. Initialize a new meta repository with **Meta → Init Meta**
3. The Meta tab will automatically activate and show project information

#### Managing Projects
- **Add Project**: Click "Add Project" to create a new project
- **Import Project**: Click "Import Project" to import an existing repository
- **Remove Project**: Select a project and click "Remove Project"
- **Clone Projects**: Use "Git Update" to clone missing projects

#### Meta Commands
Use the Commands panel to execute meta operations:
- **Git Status**: See status across all projects
- **Git Pull/Push**: Perform Git operations on all projects
- **NPM Install**: Install dependencies for all Node.js projects
- **Custom Commands**: Execute any meta command

### Configuration

#### Git Configuration
1. **Tools → Configuration** or `Ctrl+,`
2. Configure user name, email, and default editor
3. Choose scope: Global, Repository, or System
4. Modify advanced settings in the Advanced tab

#### Application Preferences
- **Terminal Integration**: Open terminal in repository directory
- **Keyboard Shortcuts**: Use built-in shortcuts for common operations

## Project Structure

```
Git Viewer/
├── src/git_viewer/           # Main package directory
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Package entry point
│   ├── git_viewer.py        # Main application file
│   ├── git_panels.py        # Git-specific panel implementations
│   ├── git_dialogs.py       # Dialog boxes for Git operations
│   ├── timeline_panel.py    # Timeline view with TLOC tracking
│   ├── meta_panel.py        # Meta repository support
│   └── run.py              # Direct launcher script
├── scripts/                  # Utility scripts
│   ├── create_app_bundle.py # macOS app bundle creator
│   └── create_icon.py       # Icon generation script
├── examples/                 # Example repositories (if any)
├── tests/                   # Test files
├── git_viewer.py            # Main launcher script
├── setup.py                # Package installation script
├── requirements.txt         # Python dependencies
├── Pipfile                  # Pipenv dependencies
└── README.md               # This file
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open Repository |
| `Ctrl+N` | Clone Repository |
| `Ctrl+Q` | Exit Application |
| `Ctrl+P` | Git Pull |
| `Ctrl+Shift+P` | Git Push |
| `Ctrl+F` | Git Fetch |
| `Ctrl+M` | Commit Changes |
| `Ctrl+Shift+M` | Merge Branch |
| `Ctrl+,` | Configuration |
| `Ctrl+T` | Open Terminal |

## Tips and Best Practices

### Git Workflow
1. **Always fetch before starting work**: Use `Ctrl+F` to fetch latest changes
2. **Create feature branches**: Use "New Branch" for new features
3. **Review changes before committing**: Use the Diff panel to review changes
4. **Write meaningful commit messages**: Include context and reasoning

### Meta Repository Workflow
1. **Initialize carefully**: Make sure your directory structure is ready before running `meta init`
2. **Keep projects updated**: Regularly run "Git Update" to sync all projects
3. **Use consistent naming**: Use clear, consistent names for projects
4. **Leverage meta commands**: Use meta commands to perform operations across all projects

### Performance Tips
1. **Large repositories**: For very large repositories, some operations may take time
2. **File viewing**: Large files are truncated for performance
3. **Background operations**: Long-running commands execute in background threads

## Troubleshooting

### Common Issues

#### "Git not found" Error
- Ensure Git is installed and in your system PATH
- Restart the application after installing Git

#### "Meta CLI not available"
- Install the meta package: `npm install -g meta`
- Ensure Node.js and npm are properly installed

#### Repository Loading Issues
- Verify the directory is a valid Git repository
- Check file permissions
- Ensure you're not in a subdirectory of the repository

#### Performance Issues
- Close unnecessary applications
- Limit the number of commits displayed in large repositories
- Use the refresh button if data seems stale

### Getting Help

1. **Check Git Status**: Use Git status to understand repository state
2. **View Output**: Check the Output tab for detailed error messages
3. **Terminal Access**: Use "Open Terminal" to run commands manually
4. **Git Documentation**: Refer to official Git documentation for Git-specific issues

## Contributing

This is a comprehensive Git and Meta repository viewer built to provide a complete GUI solution for repository management. Feel free to extend the functionality or adapt it for your specific needs.

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python git_viewer.py`
4. Make changes and test thoroughly

### Code Organization

- **src/git_viewer/**: Main package directory with all source code
  - **__init__.py**: Package initialization and version info
  - **__main__.py**: Package entry point for `python -m` execution
  - **git_viewer.py**: Main application window and core functionality
  - **git_panels.py**: Individual panels for different Git views
  - **git_dialogs.py**: Dialog boxes for user input and operations
  - **timeline_panel.py**: Timeline visualization with TLOC tracking and branch analysis
  - **meta_panel.py**: Complete meta repository support
  - **run.py**: Direct launcher script
- **scripts/**: Utility scripts for building and deployment
- **setup.py**: Package installation configuration

## License

This project is released under the MIT License. Feel free to use, modify, and distribute as needed.

## Acknowledgments

- Built with [wxPython](https://wxpython.org/) for the GUI framework
- Uses [GitPython](https://gitpython.readthedocs.io/) for Git operations
- Integrates with [meta](https://www.npmjs.com/package/meta) for meta repository support 