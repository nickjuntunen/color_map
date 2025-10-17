"""
Interactive Colormap Creator with Brightness Control
Run this script to create custom colormaps with a color wheel picker
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle, Rectangle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import colorsys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, simpledialog
import pickle

class ColorMapCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Colormap Creator")
        self.root.geometry("1400x700")
        

        # Store colors as list of dictionaries with position and color
        # Add default colors at positions 0 and 1 to prevent preview error
        self.colors = [
            {'position': 0.0, 'color': (1.0, 1.0, 1.0)},  # White at start
            {'position': 1.0, 'color': (0.0, 0.0, 0.0)},  # Black at end
        ]
        self.replaced = False  # Flag to track if an initial color was replaced
        self.current_color = '#FF0000'
        self.current_rgb = (1.0, 0.0, 0.0)
        self.current_hue = 0.0
        self.current_saturation = 1.0
        self.current_value = 1.0
        self.custom_cmap = None
        
        self.setup_ui()
        self.draw_color_wheel()
        self.draw_value_bar()
        self.update_current_color_display()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Left panel - Color wheel and brightness
        left_frame = ttk.LabelFrame(main_frame, text="Color Selector", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Color wheel frame
        wheel_frame = ttk.Frame(left_frame)
        wheel_frame.pack(side=tk.LEFT, padx=5)
        
        # Create matplotlib figure for color wheel
        self.fig_wheel, self.ax_wheel = plt.subplots(figsize=(5, 5))
        self.canvas_wheel = FigureCanvasTkAgg(self.fig_wheel, master=wheel_frame)
        self.canvas_wheel.get_tk_widget().pack()
        
        # Bind click event
        self.canvas_wheel.mpl_connect('button_press_event', self.on_wheel_click)
        
        # Brightness/Value bar frame
        value_frame = ttk.Frame(left_frame)
        value_frame.pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        ttk.Label(value_frame, text="Brightness").pack(pady=5)
        
        # Create matplotlib figure for value bar
        self.fig_value, self.ax_value = plt.subplots(figsize=(1, 5))
        self.canvas_value = FigureCanvasTkAgg(self.fig_value, master=value_frame)
        self.canvas_value.get_tk_widget().pack()
        
        # Bind click event
        self.canvas_value.mpl_connect('button_press_event', self.on_value_click)
        
        # Value slider (alternative to clicking)
        # self.value_var = tk.DoubleVar(value=1.0)
        # value_slider = ttk.Scale(value_frame, from_=1.0, to=0.0, 
        #                         variable=self.value_var, orient=tk.VERTICAL,
        #                         command=self.on_value_slider_change)
        # value_slider.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.value_var = tk.DoubleVar(value=1.0)

        # Use tk.Scale instead of ttk.Scale
        value_slider = tk.Scale(value_frame, from_=1.0, to=0.0, 
                            variable=self.value_var, orient=tk.VERTICAL,
                            resolution=0.01, showvalue=0,
                            command=self.on_value_slider_change,
                            length=300, sliderlength=20, width=20)
        value_slider.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Current color display
        color_display_frame = ttk.Frame(left_frame)
        color_display_frame.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        
        ttk.Label(color_display_frame, text="Selected Color:", 
                 font=('TkDefaultFont', 10, 'bold')).pack(pady=5)
        
        self.color_canvas = tk.Canvas(color_display_frame, width=120, height=120, 
                                      bg=self.current_color, highlightthickness=2,
                                      highlightbackground='black')
        self.color_canvas.pack(pady=10)
        
        # Color info
        info_frame = ttk.Frame(color_display_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text="HEX:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.color_hex_var = tk.StringVar(value=self.current_color)
        ttk.Entry(info_frame, textvariable=self.color_hex_var, 
                 width=10, state='readonly').grid(row=0, column=1, padx=5)
        
        ttk.Label(info_frame, text="RGB:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.color_rgb_var = tk.StringVar(value="255, 0, 0")
        ttk.Entry(info_frame, textvariable=self.color_rgb_var, 
                 width=10, state='readonly').grid(row=1, column=1, padx=5)
        
        ttk.Label(info_frame, text="HSV:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.color_hsv_var = tk.StringVar(value="0°, 100%, 100%")
        ttk.Entry(info_frame, textvariable=self.color_hsv_var, 
                 width=10, state='readonly').grid(row=2, column=1, padx=5)
        
        # Right panel - Colormap builder
        right_frame = ttk.LabelFrame(main_frame, text="Colormap Builder", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Position slider
        # position_frame = ttk.Frame(right_frame)
        # position_frame.pack(fill=tk.X, pady=5)
        
        # ttk.Label(position_frame, text="Position in colormap:").pack(anchor=tk.W)
        # self.position_var = tk.DoubleVar(value=0.5)
        # self.position_slider = ttk.Scale(position_frame, from_=0.0, to=1.0, 
        #                                 variable=self.position_var, orient=tk.HORIZONTAL)
        # self.position_slider.pack(fill=tk.X, pady=5)
        
        # self.position_label = ttk.Label(position_frame, text="0.50")
        # self.position_label.pack(anchor=tk.W)
        
        # # Update position label
        # self.position_slider.configure(command=self.update_position_label)
        
        position_frame = ttk.Frame(right_frame)
        position_frame.pack(fill=tk.X, pady=5)

        ttk.Label(position_frame, text="Position in colormap:").pack(anchor=tk.W)
        self.position_var = tk.DoubleVar(value=0.5)

        # Use tk.Scale instead of ttk.Scale for better click behavior
        self.position_slider = tk.Scale(position_frame, from_=0.0, to=1.0, 
                                    variable=self.position_var, orient=tk.HORIZONTAL,
                                    resolution=0.01, showvalue=0, 
                                    command=self.update_position_label,
                                    length=400, sliderlength=20)
        self.position_slider.pack(fill=tk.X, pady=5)

        self.position_label = ttk.Label(position_frame, text="0.50")
        self.position_label.pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # First row of buttons
        button_row1 = ttk.Frame(button_frame)
        button_row1.pack(fill=tk.X, pady=2)

        ttk.Button(button_row1, text="➕ Add Color", 
                command=self.add_color).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row1, text="❌ Remove", 
                command=self.remove_color).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row1, text="🗑️ Clear All", 
                command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # Second row of buttons - for editing selected colors
        button_row2 = ttk.Frame(button_frame)
        button_row2.pack(fill=tk.X, pady=2)

        ttk.Label(button_row2, text="Edit selected:").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row2, text="✏️ Edit Position", 
                command=self.edit_color_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_row2, text="🎨 Edit Color", 
                command=self.edit_color_rgb).pack(side=tk.LEFT, padx=5)
        
        # Color list
        list_frame = ttk.Frame(right_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(list_frame, text="Colors in colormap:").pack(anchor=tk.W)
        
        # Listbox with scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.color_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=8)
        self.color_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.color_listbox.yview)
        
        # Colormap preview
        preview_frame = ttk.LabelFrame(right_frame, text="Colormap Preview", padding="5")
        preview_frame.pack(fill=tk.X, pady=10)
        
        self.fig_preview, self.ax_preview = plt.subplots(figsize=(6, 1))
        self.fig_preview.subplots_adjust(bottom=0.3, top=0.9)
        self.canvas_preview = FigureCanvasTkAgg(self.fig_preview, master=preview_frame)
        self.canvas_preview.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Save buttons
        save_frame = ttk.Frame(right_frame)
        save_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(save_frame, text="💾 Save Colormap (.npy)", 
                  command=self.save_colormap_npy).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_frame, text="📊 Save as Image", 
                  command=self.save_colormap_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_frame, text="🐍 Export Python Code", 
                  command=self.export_python_code).pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = """
INSTRUCTIONS:
1. Click color wheel to select hue & saturation
2. Click brightness bar (or slider) to adjust brightness
3. Set position slider (0.0 = start, 1.0 = end)
4. Click 'Add Color' to add to colormap
5. Add at least 2 colors, then save your colormap

TIP: Center of wheel = white, Edge = vivid colors
        """
        ttk.Label(right_frame, text=instructions, justify=tk.LEFT, 
                 font=('TkDefaultFont', 9)).pack(pady=5)
        
        self.update_colormap_preview()
    
    def draw_color_wheel(self):
        """Draw the color wheel with full spectrum (saturation based)"""
        self.ax_wheel.clear()
        self.ax_wheel.set_xlim(-1.2, 1.2)
        self.ax_wheel.set_ylim(-1.2, 1.2)
        self.ax_wheel.set_aspect('equal')
        self.ax_wheel.axis('off')
        
        # Create a higher resolution color wheel
        size = 500
        wheel_img = np.zeros((size, size, 3))
        center = size / 2
        
        for i in range(size):
            for j in range(size):
                # Calculate position relative to center
                x = j - center
                y = center - i  # Flip y-axis
                
                # Calculate radius and angle
                radius = np.sqrt(x**2 + y**2) / center
                
                if radius <= 1.0:
                    angle = np.arctan2(y, x)
                    if angle < 0:
                        angle += 2 * np.pi
                    
                    # Convert to HSV (using current value/brightness)
                    hue = angle / (2 * np.pi)
                    saturation = radius
                    value = 1.0  # Always show full brightness on wheel
                    
                    # Convert HSV to RGB
                    rgb = colorsys.hsv_to_rgb(hue, saturation, value)
                    wheel_img[i, j] = rgb
                else:
                    # White outside the circle
                    wheel_img[i, j] = [1, 1, 1]
        
        # Display the color wheel
        self.ax_wheel.imshow(wheel_img, extent=[-1, 1, -1, 1], origin='upper')
        self.ax_wheel.set_title('Hue & Saturation', fontsize=11, fontweight='bold')
        
        # Add a circle border
        circle = Circle((0, 0), 1.0, fill=False, edgecolor='black', linewidth=2)
        self.ax_wheel.add_patch(circle)
        
        self.canvas_wheel.draw()
    
    def draw_value_bar(self):
        """Draw the brightness/value bar"""
        self.ax_value.clear()
        self.ax_value.set_xlim(0, 1)
        self.ax_value.set_ylim(0, 1)
        self.ax_value.set_aspect('auto')
        self.ax_value.axis('off')
        
        # Create gradient from current color at full brightness to black
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        
        # Get current hue and saturation
        hue = self.current_hue
        saturation = self.current_saturation
        
        # Create color gradient
        colors = np.zeros((256, 1, 3))
        for i in range(256):
            value = gradient[i, 0]
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            colors[i, 0] = rgb
        
        self.ax_value.imshow(colors, extent=[0, 1, 0, 1], origin='lower', aspect='auto')
        
        # Add border
        rect = Rectangle((0, 0), 1, 1, fill=False, edgecolor='black', linewidth=2)
        self.ax_value.add_patch(rect)
        
        # Add marker for current value
        marker_y = self.current_value
        self.ax_value.plot([0, 1], [marker_y, marker_y], 'w-', linewidth=2)
        self.ax_value.plot([0, 1], [marker_y, marker_y], 'k--', linewidth=1)
        
        self.canvas_value.draw()

    def on_wheel_click(self, event):
        """Handle click on color wheel"""
        if event.inaxes == self.ax_wheel and event.xdata and event.ydata:
            x, y = event.xdata, event.ydata
            radius = np.sqrt(x**2 + y**2)
            
            if radius <= 1.0:
                angle = np.arctan2(y, x)
                if angle < 0:
                    angle += 2*np.pi
                
                self.current_hue = angle / (2*np.pi)
                self.current_saturation = radius
                # Keep current value/brightness
                
                self.update_color_from_hsv()
                
                # Visual feedback - add a small marker
                self.draw_color_wheel()
                marker = Circle((x, y), 0.05, color='black', fill=True)
                self.ax_wheel.add_patch(marker)
                marker2 = Circle((x, y), 0.03, color='white', fill=True)
                self.ax_wheel.add_patch(marker2)
                self.canvas_wheel.draw()
                self.draw_value_bar()
    
    def on_value_click(self, event):
        """Handle click on value bar"""
        if event.inaxes == self.ax_value and event.ydata:
            self.current_value = max(0.0, min(1.0, event.ydata))
            self.value_var.set(self.current_value)
            self.update_color_from_hsv()
            self.draw_value_bar()
    
    def on_value_slider_change(self, value):
        """Handle value slider change"""
        self.current_value = float(value)
        self.update_color_from_hsv()
        self.draw_value_bar()
    
    def update_color_from_hsv(self):
        """Update current color from HSV values"""
        self.current_rgb = colorsys.hsv_to_rgb(
            self.current_hue, 
            self.current_saturation, 
            self.current_value
        )
        self.current_color = '#{:02x}{:02x}{:02x}'.format(
            int(self.current_rgb[0]*255), 
            int(self.current_rgb[1]*255), 
            int(self.current_rgb[2]*255)
        )
        self.update_current_color_display()
    
    def update_current_color_display(self):
        """Update the current color display"""
        self.color_canvas.config(bg=self.current_color)
        self.color_hex_var.set(self.current_color)
        
        # Update RGB display
        rgb_text = f"{int(self.current_rgb[0]*255)}, {int(self.current_rgb[1]*255)}, {int(self.current_rgb[2]*255)}"
        self.color_rgb_var.set(rgb_text)
        
        # Update HSV display
        hsv_text = f"{int(self.current_hue*360)}°, {int(self.current_saturation*100)}%, {int(self.current_value*100)}%"
        self.color_hsv_var.set(hsv_text)
    
    def update_position_label(self, value):
        """Update position label"""
        self.position_label.config(text=f"{float(value):.2f}")
    
    # def add_color(self):
    #     """Add current color to colormap"""
    #     position = self.position_var.get()
        
    #     # Use the current color from the color wheel (normalized RGB)
    #     rgb_normalized = self.current_rgb
        
    #     self.colors.append({'position': position, 'color': rgb_normalized})
    #     self.colors.sort(key=lambda x: x['position'])
    #     self.update_color_list()
    #     self.update_colormap_preview()


    def add_color(self):
        """Add current color to colormap"""
        position = self.position_var.get()
        
        # Use the current color from the color wheel (normalized RGB)
        rgb_normalized = self.current_rgb
        
        # Check if a color already exists at this exact position
        # self.replaced = False
        if not self.replaced:
            for i, color_data in enumerate(self.colors):
                if abs(color_data['position'] - position) < 0.001:  # Use small tolerance for float comparison
                    # Replace the existing color at this position
                    self.colors[i]['color'] = rgb_normalized
                    self.replaced = True
                    break
        
        # If we didn't replace, add the new color normally
        # if not self.replaced:
        else:
            self.colors.append({'position': position, 'color': rgb_normalized})
            self.colors.sort(key=lambda x: x['position'])
        
        self.update_color_list()
        self.update_colormap_preview()

    def remove_color(self):
        """Remove selected color"""
        selection = self.color_listbox.curselection()
        if selection:
            idx = selection[0]
            self.colors.pop(idx)
            self.update_color_list()
            self.update_colormap_preview()
        else:
            messagebox.showinfo("No Selection", "Please select a color to remove.")
    
    def clear_all(self):
        """Clear all colors"""
        if messagebox.askyesno("Clear All", "Remove all colors from the colormap?"):
            self.colors = []
            self.update_color_list()
            self.update_colormap_preview()
    
    def update_color_list(self):
        """Update the listbox with colors"""
        self.color_listbox.delete(0, tk.END)
        for i, color_data in enumerate(self.colors):
            color_255 = tuple(int(c*255) for c in color_data['color'])
            hex_color = '#{:02x}{:02x}{:02x}'.format(*color_255)
            
            self.color_listbox.insert(tk.END, 
                f"Pos: {color_data['position']:.2f} - RGB: {color_255}")
            
            # Color the listbox item
            idx = self.color_listbox.size() - 1
            # Determine if we need dark or light text based on brightness
            rgb = color_data['color']
            brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000
            fg_color = 'black' if brightness > 0.5 else 'white'
            self.color_listbox.itemconfig(idx, {'bg': hex_color, 'fg': fg_color})
    
    def edit_color_position(self):
        """Edit the position of selected color"""
        selection = self.color_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a color to edit")
            return
        
        idx = selection[0]
        current_pos = self.colors[idx]['position']
        
        new_position = simpledialog.askfloat("Edit Position", 
                                            f"Current position: {current_pos:.2f}\nEnter new position (0-1):",
                                            minvalue=0.0, maxvalue=1.0,
                                            initialvalue=current_pos)
        
        if new_position is not None:
            self.colors[idx]['position'] = new_position
            self.colors.sort(key=lambda x: x['position'])
            self.update_color_list()
            self.update_colormap_preview()

    # def edit_color_rgb(self):
    #     """Edit the color of selected item using color wheel"""
    #     selection = self.color_listbox.curselection()
    #     if not selection:
    #         messagebox.showwarning("No Selection", "Please select a color to edit")
    #         return
        
    #     idx = selection[0]
        
    #     # Ask for confirmation
    #     result = messagebox.askokcancel("Edit Color", 
    #                                     "Use the color wheel to select a new color, then click OK to apply.")
        
    #     if result:
    #         # Use the current color from the color wheel
    #         rgb_normalized = self.current_rgb
            
    #         self.colors[idx]['color'] = rgb_normalized
    #         self.update_color_list()
    #         self.update_colormap_preview()

    def edit_color_rgb(self):
        """Edit the color of selected item using color wheel"""
        selection = self.color_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a color to edit")
            return
        
        idx = selection[0]
        
        # Store the original color in case of cancel
        original_color = self.colors[idx]['color']
        
        # Load the selected color into the color wheel first
        selected_color = self.colors[idx]['color']
        
        # Convert RGB to HSV
        h, s, v = colorsys.rgb_to_hsv(*selected_color)
        self.current_hue = h
        self.current_saturation = s
        self.current_value = v
        self.current_rgb = selected_color
        self.current_color = '#{:02x}{:02x}{:02x}'.format(
            int(selected_color[0]*255), 
            int(selected_color[1]*255), 
            int(selected_color[2]*255)
        )
        
        # Update displays
        self.update_current_color_display()
        self.value_var.set(self.current_value)
        self.draw_color_wheel()
        self.draw_value_bar()
        
        # Create a dialog window for color editing
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Color")
        edit_window.geometry("400x350")
        edit_window.transient(self.root)
        # Remove grab_set() to allow interaction with main window
        
        # Center the window
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (edit_window.winfo_width() // 2)
        y = (edit_window.winfo_screenheight() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f'+{x}+{y}')
        
        # Keep window on top
        edit_window.attributes('-topmost', True)
        
        frame = ttk.Frame(edit_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(frame, text="Editing Color", 
                font=('TkDefaultFont', 12, 'bold')).pack(pady=(0, 10))
        
        instruction_text = """Use the color wheel and brightness slider
    on the main window to select a new color.

    The preview below updates in real-time."""
        
        ttk.Label(frame, text=instruction_text, 
                justify=tk.CENTER).pack(pady=10)
        
        # Current color preview
        preview_frame = ttk.Frame(frame)
        preview_frame.pack(pady=10)
        
        ttk.Label(preview_frame, text="Current selection:").pack(side=tk.LEFT, padx=5)
        
        color_preview = tk.Canvas(preview_frame, width=80, height=80, 
                                bg=self.current_color, highlightthickness=2,
                                highlightbackground='black')
        color_preview.pack(side=tk.LEFT, padx=5)
        
        # Color info label
        color_info = ttk.Label(preview_frame, text="", justify=tk.LEFT)
        color_info.pack(side=tk.LEFT, padx=10)
        
        # Update preview as user changes color
        def update_preview():
            if edit_window.winfo_exists():
                color_preview.config(bg=self.current_color)
                rgb_255 = tuple(int(c*255) for c in self.current_rgb)
                info_text = f"RGB: {rgb_255}\nHEX: {self.current_color}"
                color_info.config(text=info_text)
                edit_window.after(100, update_preview)
        
        update_preview()
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)
        
        def apply_color():
            # Apply the current color from the wheel
            self.colors[idx]['color'] = self.current_rgb
            self.update_color_list()
            self.update_colormap_preview()
            edit_window.destroy()
        
        def cancel_edit():
            # Restore original color
            self.current_rgb = original_color
            h, s, v = colorsys.rgb_to_hsv(*original_color)
            self.current_hue = h
            self.current_saturation = s
            self.current_value = v
            self.current_color = '#{:02x}{:02x}{:02x}'.format(
                int(original_color[0]*255), 
                int(original_color[1]*255), 
                int(original_color[2]*255)
            )
            self.update_current_color_display()
            self.value_var.set(self.current_value)
            self.draw_color_wheel()
            self.draw_value_bar()
            edit_window.destroy()
        
        ttk.Button(button_frame, text="✓ Apply", 
                command=apply_color, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✗ Cancel", 
                command=cancel_edit, width=15).pack(side=tk.LEFT, padx=5)
        
        # Handle window close button (X)
        edit_window.protocol("WM_DELETE_WINDOW", cancel_edit)


    def update_colormap_preview(self):
        """Update colormap preview"""
        self.ax_preview.clear()
        
        if len(self.colors) >= 2:
            # Create colormap from colors list
            positions = [c['position'] for c in self.colors]
            colors = [c['color'] for c in self.colors]
            
            cmap = LinearSegmentedColormap.from_list(
                'custom_cmap',
                list(zip(positions, colors))
            )
            self.custom_cmap = cmap
            
            # Create gradient
            gradient = np.linspace(0, 1, 256).reshape(1, -1)
            self.ax_preview.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
            self.ax_preview.set_xlim(0, 1)
            self.ax_preview.set_ylim(0, 1)
            self.ax_preview.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
            self.ax_preview.set_xticklabels(['0.0', '0.25', '0.5', '0.75', '1.0'])
            self.ax_preview.set_yticks([])
            self.ax_preview.set_xlabel('Position', fontsize=9)
            
        else:
            self.custom_cmap = None
            self.ax_preview.text(0.5, 0.5, 'Add at least 2 colors to preview', 
                               ha='center', va='center', transform=self.ax_preview.transAxes,
                               fontsize=10)
            self.ax_preview.set_xticks([])
            self.ax_preview.set_yticks([])
        
        self.fig_preview.tight_layout()
        self.canvas_preview.draw()
    
    def save_colormap_npy(self):
        """Save colormap as numpy array"""
        if self.custom_cmap is None:
            messagebox.showwarning("No Colormap", 
                                  "Please add at least 2 colors to create a colormap.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".npy",
            filetypes=[("NumPy files", "*.npy"), ("All files", "*.*")],
            title="Save Colormap"
        )
        
        if filename:
            # Save color data as dictionary
            colormap_data = {
                'colors': self.colors,
                'name': 'custom_cmap'
            }
            np.save(filename, colormap_data, allow_pickle=True)
            messagebox.showinfo("Saved", f"Colormap saved to:\n{filename}\n\nLoad with:\ndata = np.load('{filename}', allow_pickle=True).item()")
    
    def save_colormap_image(self):
        """Save colormap preview as image"""
        if self.custom_cmap is None:
            messagebox.showwarning("No Colormap", 
                                  "Please add at least 2 colors to create a colormap.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), 
                      ("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save Colormap Image"
        )
        
        if filename:
            # Create a high-quality figure
            fig, ax = plt.subplots(figsize=(10, 2))
            gradient = np.linspace(0, 1, 1000).reshape(1, -1)
            ax.imshow(gradient, aspect='auto', cmap=self.custom_cmap)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_position([0, 0, 1, 1])  # Make axis fill the entire figure
            ax.axis('off')  # Turn off the axis frame

            plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            messagebox.showinfo("Saved", f"Colormap image saved to:\n{filename}")
    
    def export_python_code(self):
        """Export colormap as Python code"""
        if len(self.colors) < 2:
            messagebox.showwarning("Not Enough Colors", 
                                  "Please add at least 2 colors to create a colormap.")
            return
        
        # Extract positions and colors
        positions = [c['position'] for c in self.colors]
        colors = [c['color'] for c in self.colors]
        
        code = f"""# Custom Colormap
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import numpy as np

# Define colors and positions
colors = {colors}
positions = {positions}

# Create colormap
custom_cmap = LinearSegmentedColormap.from_list(
    'custom_cmap', 
    list(zip(positions, colors))
)

# Example usage:
# Create sample data
data = np.random.rand(10, 10)

# Plot with custom colormap
plt.figure(figsize=(8, 6))
plt.imshow(data, cmap=custom_cmap)
plt.colorbar(label='Value')
plt.title('Data with Custom Colormap')
plt.show()

# You can also use it with other plot types:
# plt.contourf(X, Y, Z, cmap=custom_cmap)
# plt.pcolormesh(X, Y, Z, cmap=custom_cmap)
# plt.scatter(x, y, c=values, cmap=custom_cmap)
"""
        
        # Ask where to save
        filename = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Python Code"
        )
        
        if filename:
            with open(filename, 'w') as f:
                f.write(code)
            messagebox.showinfo("Saved", f"Python code saved to:\n{filename}")
        else:
            # Show in window if user cancels save
            self.show_code_window(code)
    
    def show_code_window(self, code):
        """Show code in a popup window"""
        code_window = tk.Toplevel(self.root)
        code_window.title("Python Code")
        code_window.geometry("700x500")
        
        # Add frame with padding
        frame = ttk.Frame(code_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(frame, text="Copy this code to use your custom colormap:", 
                 font=('TkDefaultFont', 11, 'bold')).pack(pady=(0, 10))
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 10),
                             yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        text_widget.insert('1.0', code)
        text_widget.config(state=tk.NORMAL)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        def copy_to_clipboard():
            code_window.clipboard_clear()
            code_window.clipboard_append(code)
            messagebox.showinfo("Copied", "Code copied to clipboard!")
        
        ttk.Button(button_frame, text="📋 Copy to Clipboard", 
                  command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✖ Close", 
                  command=code_window.destroy).pack(side=tk.LEFT, padx=5)

def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = ColorMapCreator(root)
    root.mainloop()

if __name__ == "__main__":
    main()