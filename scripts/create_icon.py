#!/usr/bin/env python3
"""
Create macOS Application Icon for Git Repository Viewer
Generates a high-resolution icon with Git branch visualization design
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_icon():
    """Create a modern Git repository viewer icon"""

    # Create high-resolution image for icon (1024x1024 for macOS)
    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background with rounded corners
    margin = 80
    bg_rect = [margin, margin, size - margin, size - margin]

    # Draw rounded rectangle background (Git orange/dark theme)
    corner_radius = 120
    draw.rounded_rectangle(bg_rect, corner_radius,
                           fill=(24, 24, 27, 255))  # Dark gray

    # Add subtle border
    border_margin = margin - 10
    border_rect = [
        border_margin, border_margin, size - border_margin,
        size - border_margin
    ]
    draw.rounded_rectangle(border_rect,
                           corner_radius + 10,
                           outline=(249, 115, 22, 100),  # Git orange
                           width=8)

    # Draw Git branch visualization
    center_x = size // 2
    center_y = size // 2
    
    # Define branch colors
    main_color = (249, 115, 22, 255)    # Git orange
    branch1_color = (34, 197, 94, 255)  # Green  
    branch2_color = (59, 130, 246, 255) # Blue
    branch3_color = (168, 85, 247, 255) # Purple
    
    # Draw main branch (central vertical line)
    main_start_y = center_y - 250
    main_end_y = center_y + 250
    draw.line([(center_x, main_start_y), (center_x, main_end_y)], 
              fill=main_color, width=12)
    
    # Draw branch lines
    branch_offset = 120
    
    # Branch 1 (left side)
    branch1_start = (center_x, center_y - 100)
    branch1_mid = (center_x - branch_offset, center_y - 50)
    branch1_end = (center_x - branch_offset, center_y + 100)
    
    # Draw curved branch line
    draw.line([branch1_start, branch1_mid], fill=branch1_color, width=10)
    draw.line([branch1_mid, branch1_end], fill=branch1_color, width=10)
    
    # Merge back to main
    merge1_start = (center_x - branch_offset, center_y + 100)
    merge1_end = (center_x, center_y + 150)
    draw.line([merge1_start, merge1_end], fill=branch1_color, width=8)
    
    # Branch 2 (right side)
    branch2_start = (center_x, center_y - 50)
    branch2_mid = (center_x + branch_offset, center_y)
    branch2_end = (center_x + branch_offset, center_y + 150)
    
    draw.line([branch2_start, branch2_mid], fill=branch2_color, width=10)
    draw.line([branch2_mid, branch2_end], fill=branch2_color, width=10)
    
    # Branch 3 (shorter branch on left)
    branch3_start = (center_x, center_y + 50)
    branch3_end = (center_x - 80, center_y + 120)
    draw.line([branch3_start, branch3_end], fill=branch3_color, width=8)
    
    # Draw commit dots
    commit_radius = 20
    commits = [
        (center_x, center_y - 200, main_color),
        (center_x, center_y - 100, main_color),
        (center_x - branch_offset, center_y - 20, branch1_color),
        (center_x, center_y - 50, main_color),
        (center_x + branch_offset, center_y + 30, branch2_color),
        (center_x, center_y + 50, main_color),
        (center_x - 80, center_y + 120, branch3_color),
        (center_x, center_y + 150, main_color),
        (center_x, center_y + 200, main_color)
    ]
    
    for x, y, color in commits:
        # Draw commit circle with subtle shadow
        shadow_offset = 3
        draw.ellipse([x - commit_radius + shadow_offset, y - commit_radius + shadow_offset,
                     x + commit_radius + shadow_offset, y + commit_radius + shadow_offset],
                    fill=(0, 0, 0, 50))
        draw.ellipse([x - commit_radius, y - commit_radius,
                     x + commit_radius, y + commit_radius],
                    fill=color)
        # Inner circle for depth
        inner_radius = commit_radius - 6
        draw.ellipse([x - inner_radius, y - inner_radius,
                     x + inner_radius, y + inner_radius],
                    fill=(255, 255, 255, 200))

    # Add title text at the top
    try:
        # Try to use a nice font
        font_size = 80
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",
                                  font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    title = "Git"
    title_bbox = draw.textbbox((0, 0), title, font=font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (size - title_width) // 2
    title_y = 180

    # Draw title with shadow
    draw.text((title_x + 3, title_y + 3),
              title,
              font=font,
              fill=(0, 0, 0, 100))
    draw.text((title_x, title_y), title, font=font, fill=(249, 115, 22, 255))

    return img


def create_icon_set():
    """Create a complete icon set for macOS"""

    base_icon = create_icon()

    # Icon sizes for macOS
    sizes = [16, 32, 64, 128, 256, 512, 1024]

    # Create icons directory
    if not os.path.exists("icons"):
        os.makedirs("icons")

    for size in sizes:
        # Resize image with high quality
        resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)

        # Save as PNG
        filename = f"icons/git_viewer_icon_{size}x{size}.png"
        resized.save(filename, "PNG")
        print(f"Created {filename}")

    # Save the main icon
    base_icon.save("icons/git_viewer_icon.png", "PNG")
    print("Created icons/git_viewer_icon.png")

    # Create ICO file for cross-platform compatibility
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128),
                 (256, 256)]
    ico_images = []

    for size in ico_sizes:
        resized = base_icon.resize(size, Image.Resampling.LANCZOS)
        ico_images.append(resized)

    # Save as ICO
    ico_images[0].save("icons/git_viewer_icon.ico", format="ICO", sizes=ico_sizes)
    print("Created icons/git_viewer_icon.ico")

    print("\nIcon set created successfully!")
    print("For macOS app bundle, use the PNG files.")
    print("For cross-platform compatibility, use the ICO file.")
    print("Icons represent Git branch visualization with commits.")


if __name__ == "__main__":
    create_icon_set()
