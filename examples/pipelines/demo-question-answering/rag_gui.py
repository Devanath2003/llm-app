import tkinter as tk
import customtkinter as ctk
import subprocess
import threading
import requests
import json
import time
import atexit
import signal
import os

class RAGApplication(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("RAG Application")
        self.geometry("600x400")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        self.run_button = ctk.CTkButton(self.main_frame, text="Run Engine", command=self.start_engine)
        self.run_button.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.prompt_frame = ctk.CTkFrame(self.main_frame)
        self.prompt_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.prompt_frame.grid_columnconfigure(0, weight=1)

        self.prompt_entry = ctk.CTkEntry(self.prompt_frame, placeholder_text="Enter your prompt here")
        self.prompt_entry.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")

        self.execute_button = ctk.CTkButton(self.prompt_frame, text="Execute", command=self.execute_prompt)
        self.execute_button.grid(row=0, column=1, pady=5)

        self.output_text = ctk.CTkTextbox(self.main_frame, wrap="word")
        self.output_text.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        self.engine_process = None

        # Register the shutdown function to be called on exit
        atexit.register(self.shutdown_engine)

        # Bind the close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_engine(self):
        if self.engine_process is None or self.engine_process.poll() is not None:
            command = 'docker run -v "C:\\Users\\devan\\Desktop\\pathway\\llm-app\\examples\\pipelines\\demo-question-answering:/app" -p 8080:8000 raggem'
            self.engine_process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            threading.Thread(target=self.update_output, args=(self.engine_process.stdout,), daemon=True).start()
            threading.Thread(target=self.update_output, args=(self.engine_process.stderr,), daemon=True).start()
            self.output_text.insert("end", "Engine started. Please wait...\n\n")
            self.animate_loading(10)  # 10 seconds animation
        else:
            self.output_text.insert("end", "Engine is already running.\n\n")

    def animate_loading(self, seconds):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        for i in range(seconds * 2):  # 2 frames per second
            self.output_text.delete("end-2l", "end")
            self.output_text.insert("end", f"Loading {frames[i % len(frames)]}\n")
            self.output_text.see("end")
            self.update()
            time.sleep(0.5)
        self.output_text.delete("end-2l", "end")  # Remove the last loading frame
        self.output_text.insert("end", "You can now enter your prompt and click Execute.\n\n")

    def execute_prompt(self):
        prompt = self.prompt_entry.get()
        if not prompt:
            self.output_text.insert("end", "Please enter a prompt.\n\n")
            return

        try:
            url = "http://localhost:8080/v1/pw_ai_answer"
            headers = {
                "accept": "*/*",
                "Content-Type": "application/json"
            }
            data = {
                "prompt": prompt
            }
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.output_text.insert("end", "Here is the answer for what you asked:\n\n")
                self.output_text.insert("end", f"{result}\n\n")
            else:
                self.output_text.insert("end", f"Error: Received status code {response.status_code}\n")
                self.output_text.insert("end", "You may need to wait a little more for the engine to set up.\n\n")
        except requests.RequestException as e:
            self.output_text.insert("end", f"Error: {str(e)}\n")
            self.output_text.insert("end", "You may need to wait a little more for the engine to set up.\n\n")
        
        self.output_text.see("end")

    def update_output(self, pipe):
        for line in iter(pipe.readline, b''):
            print(line.decode().strip())  # Print to console/VS Code terminal

    def shutdown_engine(self):
        if self.engine_process:
            print("Shutting down the engine...")
            if os.name == 'nt':  # Windows
                self.engine_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:  # Unix/Linux
                self.engine_process.send_signal(signal.SIGINT)
            try:
                self.engine_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.engine_process.kill()
            print("Engine shut down.")

    def on_closing(self):
        self.shutdown_engine()
        self.quit()

if __name__ == "__main__":
    app = RAGApplication()
    app.mainloop()