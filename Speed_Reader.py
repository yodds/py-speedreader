import tkinter as tk
from tkinter import messagebox
import time
import threading

class ProSpeedReader:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Python Speed Reader")
        self.root.geometry("850x700")  # Slightly wider to comfortably house the new +/- buttons
        
        # --- State Variables ---
        self.is_reading = False
        self.words = []
        self.current_word_index = 0
        self.wpm = 300
        self.context_width = 4  # How many words to show on left/right
        
        self.start_time = 0
        self.elapsed_time = 0 
        self.session_start = 0
        
        # --- UI Layout ---
        
        # 1. Main Display Area (The Big Word)
        self.display_frame = tk.Frame(root, pady=20)
        self.display_frame.pack(expand=True, fill='both')
        
        self.word_display = tk.Text(self.display_frame, height=1, width=20, 
                                    font=("Courier New", 50, "bold"), 
                                    bg="#f0f0f0", bd=0, highlightthickness=0)
        self.word_display.tag_configure("center", justify='center')
        self.word_display.tag_configure("red_highlight", foreground="red")
        self.word_display.pack(pady=(20, 0))
        self.word_display.bind("<Key>", lambda e: "break")

        # 2. Context Line (The "Ticker Tape")
        self.context_frame = tk.Frame(root, bg="#e0e0e0", pady=10)
        self.context_frame.pack(fill='x', padx=20, pady=20)
        
        self.context_frame.columnconfigure(0, weight=1)  # Left side expands
        self.context_frame.columnconfigure(1, weight=0)  # Center stays fixed
        self.context_frame.columnconfigure(2, weight=1)  # Right side expands

        self.lbl_left = tk.Label(self.context_frame, text="", 
                                 font=("Arial", 14), fg="#666666", bg="#e0e0e0", anchor="e")
        self.lbl_left.grid(row=0, column=0, sticky="ew")

        self.lbl_center = tk.Label(self.context_frame, text="Ready", 
                                   font=("Arial", 16, "bold"), fg="red", bg="#e0e0e0", anchor="center")
        self.lbl_center.grid(row=0, column=1, padx=5)

        self.lbl_right = tk.Label(self.context_frame, text="", 
                                  font=("Arial", 14), fg="#666666", bg="#e0e0e0", anchor="w")
        self.lbl_right.grid(row=0, column=2, sticky="ew")

        # 3. Context Control (Expand/Contract Slider)
        self.ctx_slider = tk.Scale(root, from_=0, to=10, 
                                   orient=tk.HORIZONTAL, label="Context Width (+/- Words)",
                                   command=self.update_context_width, length=200)
        self.ctx_slider.set(self.context_width)
        self.ctx_slider.pack(pady=5)

        # 4. Input Controls
        text_btn_frame = tk.Frame(root)
        text_btn_frame.pack(pady=(0, 5))

        tk.Button(text_btn_frame, text="Paste from Clipboard", 
                  command=self.paste_text, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(text_btn_frame, text="Clear Text", 
                  command=self.clear_text, bg="#9E9E9E", fg="white").pack(side=tk.LEFT, padx=5)

        self.text_input = tk.Text(root, height=5, width=60)
        self.text_input.pack(pady=5)
        self.text_input.insert("1.0", "Paste your text here. Use the slider to expand the context line below the main word.")

        # 5. Playback Controls
        controls_frame = tk.Frame(root)
        controls_frame.pack(pady=20)

        # Back Button
        tk.Button(controls_frame, text="<< Back", command=self.step_back, 
                  bg="#FF9800", fg="white", font=("Arial", 10, "bold"), width=8).pack(side=tk.LEFT, padx=5)

        # Start / Pause / Resume
        self.toggle_button = tk.Button(controls_frame, text="Start Reading", 
                                       command=self.toggle_reading, 
                                       bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                                       width=14)
        self.toggle_button.pack(side=tk.LEFT, padx=10)

        # Forward Button
        tk.Button(controls_frame, text="Fwd >>", command=self.step_forward, 
                  bg="#FF9800", fg="white", font=("Arial", 10, "bold"), width=8).pack(side=tk.LEFT, padx=5)

        # Restart Button
        tk.Button(controls_frame, text="Restart", command=self.restart_reading, 
                  bg="#607D8B", fg="white", font=("Arial", 10, "bold"), width=8).pack(side=tk.LEFT, padx=15)

        # WPM Adjuster Container with - / + Buttons (Feature 1)
        wpm_box = tk.Frame(controls_frame)
        wpm_box.pack(side=tk.LEFT, padx=5)

        tk.Button(wpm_box, text="−", command=lambda: self.adjust_wpm(-1),
                  font=("Arial", 10, "bold"), width=2).pack(side=tk.LEFT, padx=2)

        self.wpm_scale = tk.Scale(wpm_box, from_=60, to=800, 
                                  orient=tk.HORIZONTAL, label="Target WPM",
                                  command=self.update_wpm, length=140)
        self.wpm_scale.set(self.wpm)
        self.wpm_scale.pack(side=tk.LEFT, padx=2)

        tk.Button(wpm_box, text="+", command=lambda: self.adjust_wpm(1),
                  font=("Arial", 10, "bold"), width=2).pack(side=tk.LEFT, padx=2)

    # --- Helpers ---

    def adjust_wpm(self, delta):
        """Feature 1: Increment or decrement WPM by 1."""
        new_val = max(60, min(800, self.wpm + delta))
        self.wpm_scale.set(new_val)
        self.wpm = new_val

    def paste_text(self):
        try:
            content = self.root.clipboard_get()
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert("1.0", content)
        except:
            pass

    def clear_text(self):
        """Feature 3: Clears the entire buffer, tokens, and active displays."""
        self.is_reading = False
        self.words = []
        self.current_word_index = 0
        self.elapsed_time = 0
        self.session_start = 0
        self.toggle_button.config(text="Start Reading", bg="#4CAF50", fg="white")
        
        self.text_input.delete("1.0", tk.END)
        self.update_display("Ready")

    def update_wpm(self, val):
        self.wpm = int(val)

    def update_context_width(self, val):
        self.context_width = int(val)
        # Update display immediately if we have words
        if self.words and self.current_word_index < len(self.words):
            word = self.words[self.current_word_index]
            self.update_display(word)

    def update_display(self, main_word, color_center=False):
        """Updates both the Big Word and the Context Line"""
        
        # A. Update Big Word
        self.word_display.delete("1.0", tk.END)
        self.word_display.insert("1.0", main_word)
        self.word_display.tag_add("center", "1.0", "end")
        
        if color_center and len(main_word) > 1:
            mid_index = len(main_word) // 2
            if len(main_word) % 2 == 0: 
                mid_index -= 1 
            start_idx = f"1.{mid_index}"
            end_idx = f"1.{mid_index + 1}"
            self.word_display.tag_add("red_highlight", start_idx, end_idx)

        # B. Update Context Line (The Ticker Tape)
        if not self.words:
            self.lbl_center.config(text=main_word)
            self.lbl_left.config(text="")
            self.lbl_right.config(text="")
            return

        # 1. Center Word
        self.lbl_center.config(text=main_word)

        # 2. Left Context
        start_idx = max(0, self.current_word_index - self.context_width)
        left_words = self.words[start_idx : self.current_word_index]
        self.lbl_left.config(text=" ".join(left_words))

        # 3. Right Context
        end_idx = min(len(self.words), self.current_word_index + 1 + self.context_width)
        right_words = self.words[self.current_word_index + 1 : end_idx]
        self.lbl_right.config(text=" ".join(right_words))

    # --- Control Logic ---

    def step_back(self):
        """Go back one word. Auto-pauses."""
        if self.is_reading:
            self.pause_reading()
        
        if self.words and self.current_word_index > 0:
            self.current_word_index -= 1
            self.update_display(self.words[self.current_word_index], color_center=True)

    def step_forward(self):
        """Go forward one word. Auto-pauses."""
        if self.is_reading:
            self.pause_reading()
        
        if self.words and self.current_word_index < len(self.words) - 1:
            self.current_word_index += 1
            self.update_display(self.words[self.current_word_index], color_center=True)

    def toggle_reading(self):
        if self.is_reading:
            self.pause_reading()
        else:
            self.resume_or_start_reading()

    def resume_or_start_reading(self):
        if self.current_word_index == 0 or not self.words:
            raw_text = self.text_input.get("1.0", tk.END).replace('\n', ' ')
            self.words = raw_text.split()
            if not self.words: 
                return
            self.elapsed_time = 0
            self.session_start = 0

        self.is_reading = True
        self.toggle_button.config(text="Pause", bg="#FFC107", fg="black")
        self.session_start = time.time()
        
        self.thread = threading.Thread(target=self.reading_loop)
        self.thread.daemon = True
        self.thread.start()

    def pause_reading(self):
        self.is_reading = False
        if self.session_start > 0:
            self.elapsed_time += (time.time() - self.session_start)
            self.session_start = 0
        self.toggle_button.config(text="Resume", bg="#4CAF50", fg="white")

    def restart_reading(self):
        self.is_reading = False
        self.current_word_index = 0
        self.elapsed_time = 0
        self.session_start = 0
        self.toggle_button.config(text="Start Reading", bg="#4CAF50", fg="white")
        self.update_display("Ready")

    def finish_reading(self):
        self.is_reading = False
        if self.session_start > 0:
            self.elapsed_time += (time.time() - self.session_start)
            
        self.restart_reading() 
        self.update_display("Done!")
        
        duration_min = self.elapsed_time / 60
        count = len(self.words)
        
        if duration_min > 0:
            actual_wpm = int(count / duration_min)
            summary = (f"Reading Complete!\n\n"
                       f"Total Words: {count}\n"
                       f"Words Per Minute: {actual_wpm}")
            messagebox.showinfo("Summary", summary)

    def reading_loop(self):
        while self.is_reading and self.current_word_index < len(self.words):
            word = self.words[self.current_word_index]
            
            self.update_display(word, color_center=True)
            
            # --- Feature 2: Smart Adaptive Timing ---
            base_delay = 60 / self.wpm
            multiplier = 1.0

            clean_word = word.strip(".,!?;:\"'()[]{}")
            if '-' in clean_word:
                # Add delay proportional to the number of hyphenated parts
                parts = len(clean_word.split('-'))
                multiplier += max(0.6, (parts - 1) * 0.5)
            elif len(clean_word) > 12:
                # Scale up delay for long compound or multi-syllabic words
                multiplier += 0.5 + ((len(clean_word) - 12) * 0.08)

            # Punctuation multiplier
            if word.endswith('.'):
                multiplier *= 3.0 
            elif word.endswith('!') or word.endswith('?'):
                multiplier *= 3.0 
            elif word.endswith(',') or word.endswith(';') or word.endswith(':'):
                multiplier *= 2.0 
            
            time.sleep(base_delay * multiplier)
            
            if self.is_reading:
                self.current_word_index += 1
        
        if self.current_word_index >= len(self.words) and self.is_reading:
            self.root.after(0, self.finish_reading)

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="#f0f0f0") 
    app = ProSpeedReader(root)
    root.mainloop()
