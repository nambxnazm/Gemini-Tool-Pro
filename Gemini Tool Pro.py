import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import google.generativeai as genai
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json

class GeminiToolPro:
    def __init__(self, master):
        self.master = master
        master.title("Gemini Polish & Translater Tool")

        # --- Style TTK ---
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Hoặc thử 'alt', 'default'
        self.style.configure('TButton', padding=10, relief="raised", font=('Arial', 10)) # Font chữ Arial, padding lớn hơn
        self.style.configure('TRadiobutton', padding=8, font=('Arial', 10))
        self.style.configure('TCombobox', padding=8, font=('Arial', 10))
        self.style.configure('TLabel', padding=8, font=('Arial', 10))
        self.style.configure('TLabelframe.Label', font=('Arial', 12, 'bold')) # Font chữ Arial, lớn hơn và đậm cho LabelFrame

        self.model_list = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
        self.model_var = tk.StringVar(value="gemini-2.5-flash")
        self.current_model_index = self.model_list.index(self.model_var.get())

        # --- PanedWindow chính để chia bố cục ---
        main_paned = ttk.PanedWindow(master, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Khu vực Cấu hình chung ---
        config_frame = ttk.LabelFrame(main_paned, text="Cấu hình", padding=15) # Padding lớn hơn
        main_paned.add(config_frame, weight=1)

        # API Key chính
        api_key_frame = ttk.Frame(config_frame)
        api_key_frame.pack(fill=tk.X, pady=5) # pack thay vì grid để bố cục đơn giản
        ttk.Label(api_key_frame, text="API Key chính:", width=15, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        self.api_key_entry = tk.Entry(api_key_frame, width=45, show="*")
        self.api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.show_api_key_var = tk.BooleanVar()
        ttk.Checkbutton(api_key_frame, text="Hiện", variable=self.show_api_key_var, command=self.toggle_api_key_visibility).pack(side=tk.LEFT, padx=5)
        
        # API Key phụ
        api_key_backup_frame = ttk.Frame(config_frame)
        api_key_backup_frame.pack(fill=tk.X, pady=5)
        ttk.Label(api_key_backup_frame, text="API Key phụ:", width=15, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        self.api_key_backup_entry = tk.Entry(api_key_backup_frame, width=45, show="*")
        self.api_key_backup_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.show_backup_api_key_var = tk.BooleanVar()
        ttk.Checkbutton(api_key_backup_frame, text="Hiện", variable=self.show_backup_api_key_var, command=self.toggle_backup_api_key_visibility).pack(side=tk.LEFT, padx=5)
        
        # Nút lưu/tải API Keys
        api_save_frame = ttk.Frame(config_frame)
        api_save_frame.pack(fill=tk.X, pady=5)
        ttk.Label(api_save_frame, text="", width=15).pack(side=tk.LEFT)  # Spacer
        ttk.Button(api_save_frame, text="Lưu API Keys", command=self.save_api_keys, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(api_save_frame, text="Tải API Keys", command=self.load_api_keys, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(api_save_frame, text="Xóa lưu trữ", command=self.clear_saved_keys, width=12).pack(side=tk.LEFT)

        # Model
        model_frame = ttk.Frame(config_frame)
        model_frame.pack(fill=tk.X, pady=5)
        ttk.Label(model_frame, text="Chọn Model:", width=15, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, values=self.model_list, width=47)
        self.model_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Hành động
        action_frame = ttk.Frame(config_frame)
        action_frame.pack(fill=tk.X, pady=5)
        ttk.Label(action_frame, text="Hành động:", width=15, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        self.action_var = tk.StringVar(value="polish")
        polish_radio = ttk.Radiobutton(action_frame, text="Đánh bóng", variable=self.action_var, value="polish")
        polish_radio.pack(side=tk.LEFT, padx=(0,10))
        translate_radio = ttk.Radiobutton(action_frame, text="Dịch thuật", variable=self.action_var, value="translate")
        translate_radio.pack(side=tk.LEFT)

        # Thêm tùy chọn xử lý song song
        parallel_frame = ttk.Frame(config_frame)
        parallel_frame.pack(fill=tk.X, pady=5)
        ttk.Label(parallel_frame, text="Xử lý song song:", width=15, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        self.enable_parallel_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parallel_frame, text="Bật xử lý song song", variable=self.enable_parallel_var).pack(side=tk.LEFT, padx=(0,10))
        ttk.Label(parallel_frame, text="Số luồng:").pack(side=tk.LEFT, padx=(0, 5))
        self.thread_count_var = tk.StringVar(value="3")
        thread_spinbox = tk.Spinbox(parallel_frame, from_=1, to=10, width=5, textvariable=self.thread_count_var)
        thread_spinbox.pack(side=tk.LEFT)

        # Model Ưu Tiên
        priority_model_frame = ttk.LabelFrame(config_frame, text="Model Ưu Tiên (khi lỗi API)", padding=10)
        priority_model_frame.pack(fill=tk.X, pady=5)
        self.prioritized_models_vars = {}
        for i, model in enumerate(self.model_list):
            var = tk.BooleanVar()
            self.prioritized_models_vars[model] = var
            cb = ttk.Checkbutton(priority_model_frame, text=model, variable=var)
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=5, pady=2) # Vẫn dùng grid cho checkbox

        # Prompt
        prompt_frame = ttk.Frame(config_frame)
        prompt_frame.pack(fill=tk.X, pady=5)
        ttk.Label(prompt_frame, text="Prompt (tùy chọn):", width=15, anchor="ne").pack(side=tk.LEFT, padx=(0, 5), pady=(5,0), anchor="n") # anchor="n"
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, height=3, width=50, font=('Arial', 10)) # height=3, font Arial
        self.prompt_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Khu vực Đầu vào/Đầu ra ---
        io_frame = ttk.LabelFrame(main_paned, text="Đầu vào/Đầu ra", padding=15) # Padding lớn hơn
        main_paned.add(io_frame, weight=1)

        # Chọn File/Thư mục đầu vào
        input_frame = ttk.Frame(io_frame)
        input_frame.pack(fill=tk.X, pady=5)
        ttk.Label(input_frame, text="Đầu vào:", width=15, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        self.input_file_button = ttk.Button(input_frame, text="Chọn File(s)", command=self.choose_files)
        self.input_file_button.pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(input_frame, text="hoặc").pack(side=tk.LEFT, padx=5)
        self.input_dir_entry = tk.Entry(input_frame, width=40)
        self.input_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_dir_button = ttk.Button(input_frame, text="Chọn Thư mục", command=self.choose_input_dir)
        self.input_dir_button.pack(side=tk.LEFT, padx=5)

        # File đã chọn hiển thị
        selected_files_frame = ttk.Frame(io_frame)
        selected_files_frame.pack(fill=tk.X, pady=5)
        ttk.Label(selected_files_frame, text="File đã chọn:", width=15, anchor="ne").pack(side=tk.LEFT, padx=(0, 5), pady=(2,2), anchor="n")
        self.selected_files_text = scrolledtext.ScrolledText(selected_files_frame, height=3, width=50, state=tk.DISABLED, wrap=tk.WORD, font=('Arial', 10)) # height=3, font Arial
        self.selected_files_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Thư mục đầu ra
        output_frame = ttk.Frame(io_frame)
        output_frame.pack(fill=tk.X, pady=5)
        ttk.Label(output_frame, text="Đầu ra:", width=15, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        self.output_dir_entry = tk.Entry(output_frame, width=50)
        self.output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.output_dir_button = ttk.Button(output_frame, text="Chọn Thư mục", command=self.choose_output_dir)
        self.output_dir_button.pack(side=tk.LEFT, padx=5)

        # Tùy chọn tên file đầu ra
        filename_output_frame = ttk.Frame(io_frame)
        filename_output_frame.pack(fill=tk.X, pady=5)
        ttk.Label(filename_output_frame, text="Tên file đầu ra:", width=15, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        self.filename_option_var = tk.StringVar(value="suffix")
        self.original_name_radio = ttk.Radiobutton(filename_output_frame, text="Giữ nguyên tên", variable=self.filename_option_var, value="original")
        self.original_name_radio.pack(side=tk.LEFT)
        self.custom_name_radio = ttk.Radiobutton(filename_output_frame, text="Tên tùy chỉnh:", variable=self.filename_option_var, value="custom")
        self.custom_name_radio.pack(side=tk.LEFT, padx=10)
        self.custom_filename_entry = tk.Entry(filename_output_frame, width=25, state=tk.DISABLED)
        self.custom_filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.suffix_radio = ttk.Radiobutton(filename_output_frame, text="Thêm hậu tố", variable=self.filename_option_var, value="suffix")
        self.suffix_radio.pack(side=tk.LEFT, padx=10)

        # --- Khu vực Trạng thái ---
        action_status_frame = ttk.LabelFrame(main_paned, text="Trạng thái & Thực hiện", padding=15) # Padding lớn hơn, tiêu đề rõ ràng hơn
        main_paned.add(action_status_frame, weight=1)

        self.process_button = ttk.Button(action_status_frame, text="Thực hiện", command=self.process_files_threaded, width=15, style='TButton') # Style đã được cấu hình
        self.process_button.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 10)) # Đặt bên trái
        
        # Nút tạm dừng/tiếp tục
        self.pause_button = ttk.Button(action_status_frame, text="Tạm dừng", command=self.toggle_pause, width=15, style='TButton', state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 10))
        
        # Nút dừng hoàn toàn
        self.stop_button = ttk.Button(action_status_frame, text="Dừng", command=self.stop_processing, width=15, style='TButton', state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, pady=(0, 10))

        ttk.Label(action_status_frame, text="Tiến trình:", anchor="nw").pack(fill=tk.X, padx=5, anchor="nw") # anchor="nw"
        self.status_text = scrolledtext.ScrolledText(action_status_frame, height=6, wrap=tk.WORD, state=tk.DISABLED, font=('Arial', 10)) # height=6, font Arial
        self.status_text.pack(fill=tk.BOTH, expand=True)

        self.selected_files = []
        self.filename_option_var.trace_add('write', self.update_custom_filename_entry_state)
        
        # Cache API client để tránh configure lại nhiều lần
        self.api_clients = {}
        self.lock = threading.Lock()
        
        # Biến điều khiển tạm dừng/tiếp tục
        self.is_paused = False
        self.is_processing = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Ban đầu không bị pause
        
        # File log tổng hợp cho các lỗi
        self.error_log_file = None
        
        # Tải API keys đã lưu khi khởi động
        self.load_api_keys()

    # ... (các hàm còn lại không thay đổi) ...

    def toggle_api_key_visibility(self):
        if self.show_api_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")

    def toggle_backup_api_key_visibility(self):
        if self.show_backup_api_key_var.get():
            self.api_key_backup_entry.config(show="")
        else:
            self.api_key_backup_entry.config(show="*")

    def save_api_keys(self):
        """Lưu API keys vào file để sử dụng lại"""
        api_data = {
            "primary_api": self.api_key_entry.get(),
            "backup_api": self.api_key_backup_entry.get()
        }
        
        try:
            with open("api_keys.json", "w", encoding="utf-8") as f:
                json.dump(api_data, f)
            messagebox.showinfo("Thành công", "Đã lưu API Keys thành công!")
            self.update_status("✓ Đã lưu API Keys vào file api_keys.json")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu API Keys: {e}")

    def load_api_keys(self):
        """Tải API keys từ file đã lưu"""
        try:
            if os.path.exists("api_keys.json"):
                with open("api_keys.json", "r", encoding="utf-8") as f:
                    api_data = json.load(f)
                
                self.api_key_entry.delete(0, tk.END)
                self.api_key_entry.insert(0, api_data.get("primary_api", ""))
                
                self.api_key_backup_entry.delete(0, tk.END)
                self.api_key_backup_entry.insert(0, api_data.get("backup_api", ""))
                
                if hasattr(self, 'status_text'):  # Chỉ update status nếu UI đã khởi tạo
                    self.update_status("✓ Đã tải API Keys từ file đã lưu")
        except Exception as e:
            if hasattr(self, 'status_text'):
                self.update_status(f"⚠️ Không thể tải API Keys: {e}")

    def clear_saved_keys(self):
        """Xóa file lưu trữ API keys"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa API Keys đã lưu?"):
            try:
                if os.path.exists("api_keys.json"):
                    os.remove("api_keys.json")
                self.api_key_entry.delete(0, tk.END)
                self.api_key_backup_entry.delete(0, tk.END)
                messagebox.showinfo("Thành công", "Đã xóa API Keys đã lưu!")
                self.update_status("✓ Đã xóa file lưu trữ API Keys")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa file: {e}")

    def choose_input_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.input_dir_entry.delete(0, tk.END)
            self.input_dir_entry.insert(0, dir_path)
            self.selected_files = []
            self.update_selected_files_display()

    def choose_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("DOCX files", "*.docx"), ("HTML files", "*.html"), ("RTF files", "*.rtf"), ("All files", "*.*")])
        if file_paths:
            self.selected_files = list(file_paths)
            self.input_dir_entry.delete(0, tk.END)
            self.update_selected_files_display()
        else:
            self.selected_files = []
            self.update_selected_files_display()

    def update_selected_files_display(self):
        self.selected_files_text.config(state=tk.NORMAL)
        self.selected_files_text.delete("1.0", tk.END)
        if self.selected_files:
            filenames = [os.path.basename(f) for f in self.selected_files]
            files_string = "\n".join(filenames)
            self.selected_files_text.insert(tk.END, files_string)
        else:
            self.selected_files_text.insert(tk.END, "Không có file nào được chọn.")
        self.selected_files_text.config(state=tk.DISABLED)

    def choose_output_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, dir_path)

    def update_status(self, message):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.master.update()

    def get_api_client(self, api_key, model_name):
        """Lấy hoặc tạo API client với cache để tránh configure lại"""
        client_key = f"{api_key}_{model_name}"
        
        if client_key not in self.api_clients:
            with self.lock:
                if client_key not in self.api_clients:
                    genai.configure(api_key=api_key)
                    self.api_clients[client_key] = genai.GenerativeModel(model_name)
        
        return self.api_clients[client_key]

    def process_text_with_gemini(self, model_name, text, api_key, action, prompt=None, backup_api_key=None):
        """Xử lý text với Gemini, tự động chuyển sang API phụ nếu API chính bị limit"""
        apis_to_try = [api_key]
        if backup_api_key and backup_api_key.strip():
            apis_to_try.append(backup_api_key)
        
        for current_api in apis_to_try:
            if not current_api.strip():
                continue
                
            try:
                model = self.get_api_client(current_api, model_name)

                if action == "polish":
                    default_prompt = """Chỉnh sửa và nâng cao văn bản sau theo phong cách chuyên nghiệp, thanh lịch và mạch lạc, tập trung vào các yếu tố:

1. Tính trôi chảy & cấu trúc:

Tối ưu trật tự từ, điều chỉnh độ dài câu, tách/nhóm câu để tạo nhịp điệu tự nhiên

Loại bỏ từ thừa, lặp lại; đảm bảo kết nối mượt mà giữa các ý

Sắp xếp logic thông tin, duy trì mạch văn thống nhất

2. Chất lượng ngôn ngữ:

Thay thế từ ngữ sơ sài/đơn giản bằng từ vựng chính xác, trang trọng và phù hợp ngữ cảnh

Sử dụng cấu trúc đa dạng, diễn đạt tinh tế thay cho cách viết thông thường

Đảm bảo tính nhất quán về giọng điệu và văn phong

3. Độ chính xác kỹ thuật:

Kiểm tra tuyệt đối ngữ pháp, chính tả, dấu câu và chia thì động từ

Xóa bỏ mọi sự mơ hồ, đảm bảo mỗi câu chỉ truyền tải một thông điệp rõ ràng

Duy trì tính chính thức trong cách diễn đạt

4. Tính rõ ràng & mạch lạc:

Sắp xếp ý tưởng theo thứ tự logic, loại bỏ sự mơ hồ
Điều chỉnh độ dài câu để văn bản trôi chảy và dễ đọc

Yêu cầu nghiêm ngặt:

Giữ nguyên nội dung gốc, ý nghĩa, tone và định dạng (heading, bullet, số thứ tự...)

Không thêm/bớt thông tin, ví dụ hoặc phân tích ngoài phạm vi văn bản

Chỉ trả về bản đã chỉnh sửa, không giải thích hay bình luận."""
                    final_prompt = prompt if prompt else default_prompt
                    prompt_parts = [final_prompt + "\n\n" + text]
                elif action == "translate":
                    default_prompt = "Hãy dịch đoạn văn sau sang tiếng Việt một cách tự nhiên và chính xác."
                    final_prompt = prompt if prompt else default_prompt
                    prompt_parts = [final_prompt + "\n\n" + text]
                else:
                    return "Hành động không hợp lệ."

                response = model.generate_content(prompt_parts)
                
                # Thành công, trả về kết quả với thông tin API đã sử dụng
                api_type = "chính" if current_api == api_key else "phụ"
                return f"[API {api_type}] {response.text}"
                
            except Exception as e:
                error_msg = str(e)
                api_type = "chính" if current_api == api_key else "phụ"
                
                if "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
                    # Rate limit - thử API tiếp theo
                    if current_api != apis_to_try[-1]:  # Không phải API cuối cùng
                        continue
                    else:
                        return f"Lỗi API Gemini: Cả 2 API đều bị giới hạn - {error_msg}"
                else:
                    # Lỗi khác - trả về ngay
                    return f"Lỗi API Gemini ({api_type}): {error_msg}"
        
        return "Lỗi API Gemini: Không có API nào khả dụng"

    def update_custom_filename_entry_state(self, *args):
        if self.filename_option_var.get() == "custom":
            self.custom_filename_entry.config(state=tk.NORMAL)
        else:
            self.custom_filename_entry.config(state=tk.DISABLED)
            self.custom_filename_entry.delete(0, tk.END)

    def process_files_threaded(self):
        api_key = self.api_key_entry.get()
        backup_api_key = self.api_key_backup_entry.get()
        
        if not api_key:
            messagebox.showerror("Lỗi", "Vui lòng nhập API Key chính.")
            return
        
        if not backup_api_key.strip():
            if not messagebox.askyesno("Cảnh báo", "Bạn chưa nhập API Key phụ. Tiếp tục với chỉ 1 API Key?"):
                return

        output_dir = self.output_dir_entry.get()
        if not output_dir:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục đầu ra.")
            return

        self.process_button.config(state=tk.DISABLED)
        self.update_status("Bắt đầu xử lý, vui lòng chờ...")

        # Cập nhật trạng thái nút
        self.is_processing = True
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)

        thread = threading.Thread(target=self.process_files_background, args=(
            api_key,
            backup_api_key,
            self.input_dir_entry.get(),
            output_dir,
            self.action_var.get(),
            self.prompt_text.get("1.0", tk.END).strip(),
            self.model_var.get(),
            self.filename_option_var.get(),
            self.custom_filename_entry.get().strip(),
            list(self.selected_files),
            self.enable_parallel_var.get(),
            int(self.thread_count_var.get())
        ))
        thread.start()

    def toggle_pause(self):
        """Chuyển đổi giữa tạm dừng và tiếp tục"""
        if self.is_paused:
            # Tiếp tục
            self.is_paused = False
            self.pause_event.set()
            self.pause_button.config(text="Tạm dừng")
            self.update_status("⏵️ Tiếp tục xử lý...")
        else:
            # Tạm dừng
            self.is_paused = True
            self.pause_event.clear()
            self.pause_button.config(text="Tiếp tục")
            self.update_status("⏸️ Đã tạm dừng. Nhấn 'Tiếp tục' để tiếp tục xử lý.")

    def stop_processing(self):
        """Dừng hoàn toàn quá trình xử lý"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn dừng hoàn toàn quá trình xử lý?"):
            self.is_processing = False
            self.is_paused = False
            self.pause_event.set()  # Đảm bảo không bị block
            self.update_status("🛑 Đã dừng xử lý theo yêu cầu của người dùng.")
            
            # Reset trạng thái nút
            self.process_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED, text="Tạm dừng")
            self.stop_button.config(state=tk.DISABLED)

    def reset_button_states(self):
        """Reset trạng thái các nút về ban đầu"""
        self.is_processing = False
        self.is_paused = False
        self.pause_event.set()
        self.process_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Tạm dừng")
        self.stop_button.config(state=tk.DISABLED)

    def save_error_file(self, input_file_path, output_dir, error_message):
        """Lưu file gốc vào folder 'error file' khi xử lý bị lỗi"""
        try:
            # Tạo folder 'error file' nếu chưa tồn tại
            error_folder = os.path.join(output_dir, "error file")
            os.makedirs(error_folder, exist_ok=True)
            
            # Sao chép file gốc vào folder error
            file_name = os.path.basename(input_file_path)
            error_file_path = os.path.join(error_folder, file_name)
            
            # Đọc nội dung file gốc và sao chép
            with open(input_file_path, 'r', encoding='utf-8') as infile:
                content = infile.read()
            
            with open(error_file_path, 'w', encoding='utf-8') as outfile:
                outfile.write(content)
            
            # Ghi vào file log tổng hợp
            self.write_to_error_log(input_file_path, error_message)
                
        except Exception as e:
            # Nếu không thể lưu vào folder error, chỉ ghi log
            print(f"Không thể lưu file lỗi: {e}")

    def init_error_log(self, output_dir):
        """Khởi tạo file log tổng hợp cho session xử lý"""
        try:
            error_folder = os.path.join(output_dir, "error file")
            os.makedirs(error_folder, exist_ok=True)
            
            # Tạo tên file log với timestamp
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            log_filename = f"error_summary_{timestamp}.log"
            self.error_log_file = os.path.join(error_folder, log_filename)
            
            # Ghi header cho file log
            with open(self.error_log_file, 'w', encoding='utf-8') as log_file:
                log_file.write("="*80 + "\n")
                log_file.write(f"GEMINI TOOL - BÁO CÁO LỖI TỔNG HỢP\n")
                log_file.write(f"Thời gian bắt đầu: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write("="*80 + "\n\n")
                
        except Exception as e:
            print(f"Không thể khởi tạo file log: {e}")
            self.error_log_file = None

    def write_to_error_log(self, input_file_path, error_message):
        """Ghi thông tin lỗi vào file log tổng hợp"""
        if not self.error_log_file:
            return
            
        try:
            with open(self.error_log_file, 'a', encoding='utf-8') as log_file:
                log_file.write(f"[{time.strftime('%H:%M:%S')}] ФАЙЛ ЛỖI\n")
                log_file.write(f"File gốc: {input_file_path}\n")
                log_file.write(f"Tên file: {os.path.basename(input_file_path)}\n")
                log_file.write(f"Chi tiết lỗi: {error_message}\n")
                log_file.write("-" * 60 + "\n\n")
                
        except Exception as e:
            print(f"Không thể ghi vào log file: {e}")

    def finalize_error_log(self, total_files, success_count, error_count):
        """Hoàn thiện file log với thống kê tổng kết"""
        if not self.error_log_file:
            return
            
        try:
            with open(self.error_log_file, 'a', encoding='utf-8') as log_file:
                log_file.write("="*80 + "\n")
                log_file.write("THỐNG KÊ TỔNG KẾT\n")
                log_file.write("="*80 + "\n")
                log_file.write(f"Tổng số file xử lý: {total_files}\n")
                log_file.write(f"Số file thành công: {success_count}\n")
                log_file.write(f"Số file lỗi: {error_count}\n")
                log_file.write(f"Tỷ lệ thành công: {(success_count/total_files*100):.1f}%\n")
                log_file.write(f"Thời gian kết thúc: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write("="*80 + "\n")
                
        except Exception as e:
            print(f"Không thể hoàn thiện log file: {e}")

    def remove_from_error_folder(self, input_file_path, output_dir):
        """Xóa file khỏi folder 'error file' khi xử lý thành công"""
        try:
            error_folder = os.path.join(output_dir, "error file")
            if not os.path.exists(error_folder):
                return
            
            file_name = os.path.basename(input_file_path)
            error_file_path = os.path.join(error_folder, file_name)
            
            # Xóa file gốc nếu tồn tại trong folder error
            if os.path.exists(error_file_path):
                os.remove(error_file_path)
                print(f"✓ Đã xóa file khỏi folder 'error file': {file_name}")
                
        except Exception as e:
            print(f"Không thể xóa file khỏi folder 'error file': {e}")

    def process_single_file(self, file_info):
        """Xử lý một file đơn lẻ - dùng cho xử lý song song"""
        # Kiểm tra xem có bị dừng không
        if not self.is_processing:
            return {"success": False, "error": "Đã bị dừng", "file": "Unknown"}
            
        # Chờ nếu bị pause
        self.pause_event.wait()
        
        if not self.is_processing:  # Kiểm tra lại sau khi wait
            return {"success": False, "error": "Đã bị dừng", "file": "Unknown"}
            
        (input_file_path, api_key, backup_api_key, action, prompt, initial_model_name, 
         filename_option, custom_filename, output_dir) = file_info
        
        file_name = os.path.basename(input_file_path)
        file_extension = os.path.splitext(file_name)[1]
        base_filename_without_ext = os.path.splitext(file_name)[0]

        if filename_option == "original":
            output_filename = file_name
        elif filename_option == "custom":
            if not custom_filename:
                return {"success": False, "error": "Tên file tùy chỉnh không được để trống", "file": file_name}
            output_filename = custom_filename + file_extension
        elif filename_option == "suffix":
            output_filename = f"{base_filename_without_ext}_{action}_{initial_model_name.replace('-','_')}{file_extension}"
        else:
            output_filename = f"{base_filename_without_ext}_{action}_{initial_model_name.replace('-','_')}{file_extension}"
        
        output_file_path = os.path.join(output_dir, output_filename)

        # Chuẩn bị danh sách model để thử
        models_to_try = [initial_model_name]
        prioritized_models = [model for model, var in self.prioritized_models_vars.items() 
                            if var.get() and model != initial_model_name]
        if prioritized_models:
            models_to_try.extend(prioritized_models)
        for model in self.model_list:
            if model != initial_model_name and model not in prioritized_models:
                models_to_try.append(model)

        tried_models = set()
        for model_name in models_to_try:
            if model_name in tried_models:
                continue
            tried_models.add(model_name)

            # Kiểm tra pause/stop trước mỗi lần thử model
            if not self.is_processing:
                return {"success": False, "error": "Đã bị dừng", "file": file_name}
            self.pause_event.wait()
            if not self.is_processing:
                return {"success": False, "error": "Đã bị dừng", "file": file_name}

            try:
                with open(input_file_path, 'r', encoding='utf-8') as infile:
                    text = infile.read()

                processed_text = self.process_text_with_gemini(model_name, text, api_key, action, prompt, backup_api_key)

                if processed_text.startswith("Lỗi API Gemini:"):
                    if "429 Resource has been exhausted" in processed_text:
                        continue  # Thử model tiếp theo
                    else:
                        # Lưu file gốc vào folder error
                        self.save_error_file(input_file_path, output_dir, processed_text)
                        return {"success": False, "error": processed_text, "file": file_name, "model": model_name}
                else:
                    # Xử lý thành công, loại bỏ prefix [API chính/phụ] khỏi nội dung
                    if processed_text.startswith("[API"):
                        # Tìm vị trí kết thúc của prefix
                        end_prefix = processed_text.find("] ") + 2
                        clean_text = processed_text[end_prefix:]
                        api_info = processed_text[:end_prefix-1]  # Lấy thông tin API
                    else:
                        clean_text = processed_text
                        api_info = "[API chính]"
                    
                    with open(output_file_path, 'w', encoding='utf-8') as outfile:
                        outfile.write(clean_text)
                    
                    # Xóa file khỏi folder "error file" nếu tồn tại (đã xử lý thành công)
                    self.remove_from_error_folder(input_file_path, output_dir)
                    
                    return {"success": True, "file": file_name, "output": os.path.basename(output_file_path), "model": model_name, "api_info": api_info}
                    
            except Exception as e:
                # Lưu file gốc vào folder error khi có exception
                self.save_error_file(input_file_path, output_dir, str(e))
                return {"success": False, "error": str(e), "file": file_name, "model": model_name}
        
        # Lưu file gốc vào folder error khi không thể xử lý với bất kỳ model nào
        self.save_error_file(input_file_path, output_dir, "Không thể xử lý sau khi thử tất cả model")
        return {"success": False, "error": "Không thể xử lý sau khi thử tất cả model", "file": file_name}

    def process_files_background(self, api_key, backup_api_key, input_dir, output_dir, action, prompt, initial_model_name, 
                               filename_option, custom_filename, selected_files, enable_parallel=True, thread_count=3):
        # Khởi tạo file log tổng hợp
        if output_dir and os.path.exists(output_dir):
            self.init_error_log(output_dir)
        
        files_to_process = []

        if selected_files:
            files_to_process = selected_files
        elif input_dir and os.path.isdir(input_dir):
            files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)) and f.endswith(('.txt', '.md', '.docx', '.html', '.rtf'))]
            files_to_process = [os.path.join(input_dir, f) for f in files]
        else:
            self.master.after(0, messagebox.showerror, "Lỗi", "Vui lòng chọn file hoặc thư mục đầu vào hợp lệ.")
            self.master.after(0, self.process_button.config, {"state": tk.NORMAL})
            return

        if not files_to_process:
            self.master.after(0, messagebox.showinfo, "Thông báo", "Không tìm thấy file văn bản nào để xử lý.")
            self.master.after(0, self.process_button.config, {"state": tk.NORMAL})
            return

        total_files = len(files_to_process)
        processed_count = 0
        error_count = 0
        self.master.after(0, self.update_status, f"Bắt đầu xử lý {total_files} file...")
        
        try:
            if enable_parallel and total_files > 1:
                # Xử lý song song
                self.master.after(0, self.update_status, f"Sử dụng xử lý song song với {thread_count} luồng")
                
                # Chuẩn bị thông tin cho từng file
                file_infos = [(file_path, api_key, backup_api_key, action, prompt, initial_model_name, 
                              filename_option, custom_filename, output_dir) for file_path in files_to_process]
                
                with ThreadPoolExecutor(max_workers=thread_count) as executor:
                    # Submit tất cả các task
                    future_to_file = {executor.submit(self.process_single_file, file_info): file_info[0] 
                                    for file_info in file_infos}
                    
                    # Xử lý kết quả khi hoàn thành
                    for future in as_completed(future_to_file):
                        if not self.is_processing:  # Kiểm tra stop
                            break
                                
                        result = future.result()
                        if result["success"]:
                            processed_count += 1
                            self.master.after(0, self.update_status, 
                                            f"✓ Hoàn thành: {result['output']} ({result.get('api_info', '[API chính]')} - model: {result['model']}) - {processed_count}/{total_files}")
                        else:
                            if "Đã bị dừng" not in result["error"]:
                                error_count += 1
                                self.master.after(0, self.update_status, 
                                                f"✗ Lỗi {result['file']}: {result['error']} → Đã lưu vào folder 'error file'")
                            
            else:
                # Xử lý tuần tự (như cũ nhưng tối ưu hơn)
                for input_file_path in files_to_process:
                    if not self.is_processing:  # Kiểm tra stop
                        break
                        
                    file_info = (input_file_path, api_key, backup_api_key, action, prompt, initial_model_name, 
                               filename_option, custom_filename, output_dir)
                    result = self.process_single_file(file_info)
                    
                    if result["success"]:
                        processed_count += 1
                        self.master.after(0, self.update_status, 
                                        f"✓ Hoàn thành: {result['output']} ({result.get('api_info', '[API chính]')} - model: {result['model']}) - {processed_count}/{total_files}")
                    else:
                        if "Đã bị dừng" not in result["error"]:
                            error_count += 1
                            self.master.after(0, self.update_status, 
                                            f"✗ Lỗi {result['file']}: {result['error']} → Đã lưu vào folder 'error file'")

            # Hoàn thiện file log tổng hợp
            if self.error_log_file:
                self.finalize_error_log(total_files, processed_count, error_count)

            if self.is_processing:
                if error_count > 0:
                    self.master.after(0, self.update_status, f"Hoàn thành! Thành công: {processed_count}/{total_files} file. Lỗi: {error_count} file → Xem trong folder 'error file'")
                    self.master.after(0, messagebox.showinfo, "Thông báo", f"Đã hoàn thành xử lý!\nThành công: {processed_count}/{total_files} file\nLỗi: {error_count} file (đã lưu vào folder 'error file')")
                else:
                    self.master.after(0, self.update_status, f"Hoàn thành! Đã xử lý thành công {processed_count}/{total_files} file.")
                    self.master.after(0, messagebox.showinfo, "Thông báo", f"Đã hoàn thành xử lý! Thành công: {processed_count}/{total_files} file")
            else:
                self.master.after(0, self.update_status, f"Đã dừng! Đã xử lý được {processed_count}/{total_files} file. Lỗi: {error_count} file.")
                
        finally:
            # Reset trạng thái nút khi hoàn thành hoặc bị dừng
            self.master.after(0, self.reset_button_states)

if __name__ == '__main__':
    root = tk.Tk()
    tool = GeminiToolPro(root) 

    root.mainloop()
