"""
Base UI components and utilities for the DMX Light Show GUI
"""

import tkinter as tk
from tkinter import ttk
import time
from abc import ABC, abstractmethod


class BaseUIComponent(ABC):
    """Base class for all UI components"""
    
    def __init__(self, parent, controllers=None):
        self.parent = parent
        self.controllers = controllers or {}
        self.frame = None
        self.widgets = {}
        self.setup_ui()
    
    @abstractmethod
    def setup_ui(self):
        """Setup the UI components - must be implemented by subclasses"""
        pass
    
    def get_controller(self, name):
        """Get a controller by name"""
        return self.controllers.get(name)
    
    def get_widget(self, name):
        """Get a widget by name"""
        return self.widgets.get(name)
    
    def set_widget(self, name, widget):
        """Store a widget reference"""
        self.widgets[name] = widget
    
    def get_frame(self):
        """Get the main frame for this component"""
        return self.frame


class LoggingMixin:
    """Mixin class for components that need logging functionality"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.info_display = None
        self.status_display = None
    
    def set_info_display(self, info_display):
        """Set the info display widget"""
        self.info_display = info_display
    
    def set_status_display(self, status_display):
        """Set the status display widget"""
        self.status_display = status_display
    
    def log_info(self, message):
        """Log message to info display"""
        if self.info_display:
            self.info_display.config(state=tk.NORMAL)
            self.info_display.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
            self.info_display.see(tk.END)
            self.info_display.config(state=tk.DISABLED)
    
    def log_status(self, message):
        """Log message to status display"""
        if self.status_display:
            self.status_display.config(state=tk.NORMAL)
            self.status_display.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
            self.status_display.see(tk.END)
            self.status_display.config(state=tk.DISABLED)
    
    def log_error(self, message):
        """Log error message to both displays"""
        self.log_info(f"ERROR: {message}")
        self.log_status(f"ERROR: {message}")


class StyleMixin:
    """Mixin class for consistent styling"""
    
    @staticmethod
    def setup_styles():
        """Configure ttk styles for macOS-like appearance"""
        style = ttk.Style()
        
        # Use native macOS theme if available
        try:
            style.theme_use('aqua')  # macOS native theme
        except:
            style.theme_use('clam')  # Fallback
            
        # Custom styles
        style.configure('Title.TLabel', font=('SF Pro Display', 16, 'bold'))
        style.configure('Heading.TLabel', font=('SF Pro Display', 12, 'bold'))
        style.configure('Status.TLabel', font=('SF Mono', 10))
        
        return style


class FormHelper:
    """Helper class for creating forms with consistent layout"""
    
    @staticmethod
    def create_labeled_entry(parent, row, label_text, textvariable, column_span=1, width=30):
        """Create a labeled entry widget"""
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=2)
        entry = ttk.Entry(parent, textvariable=textvariable, width=width)
        entry.grid(row=row, column=1, columnspan=column_span, padx=(10, 0), sticky=(tk.W, tk.E), pady=2)
        return entry
    
    @staticmethod
    def create_labeled_combobox(parent, row, label_text, textvariable, values, column_span=1, width=30):
        """Create a labeled combobox widget"""
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=2)
        combo = ttk.Combobox(parent, textvariable=textvariable, values=values, 
                           state="readonly", width=width)
        combo.grid(row=row, column=1, columnspan=column_span, padx=(10, 0), sticky=(tk.W, tk.E), pady=2)
        return combo
    
    @staticmethod
    def create_labeled_scale(parent, row, label_text, variable, from_=0, to=255, column_span=1):
        """Create a labeled scale widget with value display"""
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=2)
        
        scale_frame = ttk.Frame(parent)
        scale_frame.grid(row=row, column=1, columnspan=column_span, padx=(10, 0), sticky=(tk.W, tk.E), pady=2)
        
        scale = ttk.Scale(scale_frame, from_=from_, to=to, variable=variable, orient=tk.HORIZONTAL)
        scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        label = ttk.Label(scale_frame, textvariable=variable)
        label.grid(row=0, column=1, padx=(10, 0))
        
        scale_frame.columnconfigure(0, weight=1)
        return scale, label
    
    @staticmethod
    def create_button_frame(parent, row, buttons_config, column_span=2):
        """Create a frame with multiple buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=column_span, pady=(10, 0))
        
        buttons = []
        for i, (text, command) in enumerate(buttons_config):
            btn = ttk.Button(button_frame, text=text, command=command)
            btn.grid(row=0, column=i, padx=(0, 5) if i < len(buttons_config) - 1 else 0)
            buttons.append(btn)
        
        return button_frame, buttons


class TreeViewHelper:
    """Helper class for creating and managing treeviews"""
    
    @staticmethod
    def create_treeview_with_scrollbar(parent, columns, height=8):
        """Create a treeview with scrollbar"""
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=height)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.config(yscrollcommand=scrollbar.set)
        
        return tree, scrollbar
    
    @staticmethod
    def populate_tree(tree, data, clear_first=True):
        """Populate treeview with data"""
        if clear_first:
            for item in tree.get_children():
                tree.delete(item)
        
        for row_data in data:
            tree.insert('', 'end', values=row_data)


class VariableManager:
    """Helper class for managing tkinter variables"""
    
    def __init__(self):
        self.variables = {}
    
    def add_string_var(self, name, default=""):
        """Add a StringVar"""
        self.variables[name] = tk.StringVar(value=default)
        return self.variables[name]
    
    def add_int_var(self, name, default=0):
        """Add an IntVar"""
        self.variables[name] = tk.IntVar(value=default)
        return self.variables[name]
    
    def add_double_var(self, name, default=0.0):
        """Add a DoubleVar"""
        self.variables[name] = tk.DoubleVar(value=default)
        return self.variables[name]
    
    def add_bool_var(self, name, default=False):
        """Add a BooleanVar"""
        self.variables[name] = tk.BooleanVar(value=default)
        return self.variables[name]
    
    def get_var(self, name):
        """Get a variable by name"""
        return self.variables.get(name)
    
    def get_value(self, name):
        """Get the value of a variable by name"""
        var = self.variables.get(name)
        return var.get() if var else None
    
    def set_value(self, name, value):
        """Set the value of a variable by name"""
        var = self.variables.get(name)
        if var:
            var.set(value)
    
    def clear_all(self):
        """Clear all variables"""
        for name, var in self.variables.items():
            if isinstance(var, (tk.StringVar, tk.IntVar, tk.DoubleVar)):
                var.set("")
            elif isinstance(var, tk.BooleanVar):
                var.set(False)