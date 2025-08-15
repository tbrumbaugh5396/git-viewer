#!/usr/bin/env python3
"""
Create macOS Application Bundle for Git Repository Viewer
Generates a complete .app bundle that can be double-clicked to launch
"""

import os
import shutil
import stat
import plistlib
from pathlib import Path
import sys


def create_app_bundle():
	"""Create a complete macOS application bundle"""

	app_name = "Git Repository Viewer"
	bundle_name = f"{app_name}.app"

	# Remove existing bundle if it exists
	if os.path.exists(bundle_name):
		shutil.rmtree(bundle_name)

	# Create bundle directory structure
	bundle_path = Path(bundle_name)
	contents_path = bundle_path / "Contents"
	macos_path = contents_path / "MacOS"
	resources_path = contents_path / "Resources"

	# Create directories
	macos_path.mkdir(parents=True, exist_ok=True)
	resources_path.mkdir(parents=True, exist_ok=True)

	# Copy application files into Resources
	# - Include the source package so we can import `git_viewer`
	root = Path.cwd()
	src_dir = root / "src"
	if src_dir.exists():
		# Copy the entire src tree (contains `git_viewer` package)
		shutil.copytree(src_dir, resources_path / "src")
	else:
		print("⚠️  src directory not found; the app may not launch.")

	# Always include helpful files
	for file in ["requirements.txt", "README.md"]:
		if (root / file).exists():
			shutil.copy2(root / file, resources_path)

	# Copy any data files if they exist
	# (Git repositories will be opened through the app, no specific data file needed)

	# Copy icons
	icons_src = root / "icons"
	if icons_src.exists():
		shutil.copytree(icons_src, resources_path / "icons")

	# Use the current Python interpreter for the shebang so Finder can launch it
	python_exec = sys.executable
	if not python_exec:
		python_exec = "/usr/bin/env python3"

	# Create the main executable launcher script (Python)
	launcher_body = """import sys
import os

# Paths inside the .app bundle
app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
resources_path = os.path.join(app_path, "Resources")
src_path = os.path.join(resources_path, "src")

# Ensure we can import the `git_viewer` package from Resources/src
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Change to Resources so relative files (configs, icons) resolve
os.chdir(resources_path)

try:
    # Prefer running the package entrypoint
    from git_viewer.__main__ import main as run_main
    run_main()
except Exception as e:
    # Show a simple GUI error dialog using tkinter (no terminal when double-clicking)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"Failed to start application:\\n{e}")
        root.destroy()
    except Exception:
        # Last resort: write to a log file in Resources
        try:
            with open(os.path.join(resources_path, "launch_error.log"), "a") as f:
                f.write(str(e) + "\\n")
        except Exception:
            pass
"""
	launcher_script = f"#!{python_exec}\n" + launcher_body

	# Write the launcher script
	launcher_path = macos_path / app_name.replace(" ", "")
	with open(launcher_path, 'w') as f:
		f.write(launcher_script)

	# Make the launcher executable
	st = os.stat(launcher_path)
	os.chmod(launcher_path, st.st_mode | stat.S_IEXEC)

	# Create Info.plist
	plist_data = {
		'CFBundleName': app_name,
		'CFBundleDisplayName': app_name,
		'CFBundleIdentifier': 'com.gitviewer.repositoryviewer',
		'CFBundleVersion': '1.0.0',
		'CFBundleShortVersionString': '1.0.0',
		'CFBundleExecutable': app_name.replace(" ", ""),
		'CFBundleIconFile': 'git_viewer_icon.icns',
		'CFBundlePackageType': 'APPL',
		'CFBundleSignature': '????',
		'LSMinimumSystemVersion': '10.13.0',
		'NSHighResolutionCapable': True,
		'NSSupportsAutomaticGraphicsSwitching': True,
		'NSRequiresAquaSystemAppearance': False,
		'LSApplicationCategoryType': 'public.app-category.developer-tools',
		'CFBundleDocumentTypes': [{
			'CFBundleTypeName': 'Git Repository',
			'CFBundleTypeExtensions': ['git'],
			'CFBundleTypeRole': 'Viewer',
			'CFBundleTypeDescription': 'Git Repository Directory'
		}]
	}

	# Write Info.plist
	with open(contents_path / "Info.plist", 'wb') as f:
		plistlib.dump(plist_data, f)

	# Convert PNG icon to ICNS if possible
	create_icns_icon(resources_path)

	print(f"✅ Created {bundle_name}")
	print(f"📁 Bundle location: {os.path.abspath(bundle_name)}")
	print(f"🚀 Double-click {bundle_name} to launch the application")
	print(f"📋 You can drag {bundle_name} to Applications folder or Dock")

	return bundle_name


def create_icns_icon(resources_path):
	"""Create ICNS icon file from PNG icons"""

	icons_dir = resources_path / "icons"
	if not icons_dir.exists():
		print("⚠️  Icons directory not found, using default icon")
		return

	# Try to use iconutil (macOS built-in tool)
	try:
		import subprocess

		# Create iconset directory
		iconset_dir = resources_path / "git_viewer_icon.iconset"
		iconset_dir.mkdir(exist_ok=True)

		# Icon size mappings for macOS
		icon_mappings = {
			'icon_16x16.png': 'git_viewer_icon_16x16.png',
			'icon_16x16@2x.png': 'git_viewer_icon_32x32.png',
			'icon_32x32.png': 'git_viewer_icon_32x32.png',
			'icon_32x32@2x.png': 'git_viewer_icon_64x64.png',
			'icon_128x128.png': 'git_viewer_icon_128x128.png',
			'icon_128x128@2x.png': 'git_viewer_icon_256x256.png',
			'icon_256x256.png': 'git_viewer_icon_256x256.png',
			'icon_256x256@2x.png': 'git_viewer_icon_512x512.png',
			'icon_512x512.png': 'git_viewer_icon_512x512.png',
			'icon_512x512@2x.png': 'git_viewer_icon_1024x1024.png'
		}

		# Copy icons with correct names
		for iconset_name, source_name in icon_mappings.items():
			source_path = icons_dir / source_name
			if source_path.exists():
				shutil.copy2(source_path, iconset_dir / iconset_name)

		# Convert to ICNS using iconutil
		icns_path = resources_path / "git_viewer_icon.icns"
		result = subprocess.run(
			['iconutil', '-c', 'icns', str(iconset_dir), '-o', str(icns_path)],
			capture_output=True,
			text=True)

		if result.returncode == 0:
			print("✅ Created ICNS icon file")
			# Clean up iconset directory
			shutil.rmtree(iconset_dir)
		else:
			print("⚠️  Could not create ICNS file, using PNG icon")
			# Fallback: copy the largest PNG icon
			largest_icon = icons_dir / "git_viewer_icon_512x512.png"
			if largest_icon.exists():
				shutil.copy2(largest_icon, resources_path / "git_viewer_icon.icns")

	except Exception as e:
		print(f"⚠️  Could not create ICNS icon: {e}")
		# Copy any available icon as fallback
		if (icons_dir / "git_viewer_icon.png").exists():
			shutil.copy2(icons_dir / "git_viewer_icon.png", resources_path / "git_viewer_icon.icns")


def create_dmg_installer():
	"""Create a DMG installer (optional)"""
	app_name = "Git Repository Viewer"
	bundle_name = f"{app_name}.app"
	dmg_name = f"{app_name}.dmg"

	if not os.path.exists(bundle_name):
		print("❌ App bundle not found. Create the app bundle first.")
		return

	try:
		import subprocess

		# Remove existing DMG
		if os.path.exists(dmg_name):
			os.remove(dmg_name)

		# Create DMG
		subprocess.run([
			'hdiutil', 'create', '-volname', app_name, '-srcfolder', bundle_name, '-ov', '-format', 'UDZO', dmg_name
		], check=True)

		print(f"✅ Created installer: {dmg_name}")

	except subprocess.CalledProcessError:
		print("⚠️  Could not create DMG installer")
	except Exception as e:
		print(f"⚠️  DMG creation failed: {e}")


if __name__ == "__main__":
	print("🏗️  Creating macOS Application Bundle...")
	bundle_name = create_app_bundle()

	print("\n📦 Would you like to create a DMG installer? (y/n): ", end="")
	try:
		response = input().lower().strip()
		if response in ['y', 'yes']:
			create_dmg_installer()
	except (EOFError, KeyboardInterrupt):
		pass

	print("\n🎉 Application bundle creation complete!")
	print(f"🚀 Launch: Double-click {bundle_name}")
	print(f"📱 Install: Drag {bundle_name} to Applications folder")
