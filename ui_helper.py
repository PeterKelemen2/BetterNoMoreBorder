import customtkinter as ctk

def add_entry_with_label(object, text_label, text_entry, row, col, padx=5, pady=5, width=50):
    ctk.CTkLabel(object, text=text_label, anchor="w").grid(row=row, column=col, padx=padx, pady=pady)
    ctk.CTkEntry(object, textvariable=text_entry, width=width).grid(row=row, column=col+1, padx=padx, pady=pady)