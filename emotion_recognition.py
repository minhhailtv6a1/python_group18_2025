import tkinter as tk # Thư viện để tạo giao diện 
from tkinter.filedialog import askopenfilename, asksaveasfilename # Thư viện để chọn file input
import ctypes
import sys 
import os
import cv2 # Thư viện để nhận diện
from fer import FER # Thư viện để nhận diện
import time
from PIL import Image, ImageTk, ImageFilter, ImageDraw # Thư viện để định dạng image


image_reference = []  # Danh sách lưu trữ hình ảnh

# Hàm kiểm tra đường dưỡng icon
def check_icon(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image file '{file_path}' not found.")

    img = tk.PhotoImage(file=file_path)
    image_reference.append(img)  # Lưu trữ hình ảnh để không bị xóa
    return img

# Hàm thêm hiệu ứng chuyển màu khi hover
def fade_color(start_color, end_color, steps, widget):
    """Hàm tạo hiệu ứng chuyển màu mượt"""
    # Chuyển từ mã màu hex thành RGB
    start_rgb = widget.winfo_rgb(start_color)
    end_rgb = widget.winfo_rgb(end_color)

    # Tính khoảng cách màu giữa các bước
    delta_r = (end_rgb[0] - start_rgb[0]) // steps
    delta_g = (end_rgb[1] - start_rgb[1]) // steps
    delta_b = (end_rgb[2] - start_rgb[2]) // steps

    colors = [
        f"#{(start_rgb[0] + i * delta_r) // 256:02x}"
        f"{(start_rgb[1] + i * delta_g) // 256:02x}"
        f"{(start_rgb[2] + i * delta_b) // 256:02x}"
        for i in range(steps + 1)
    ]

    def update_color(index=0):
        if index < len(colors):
            widget.config(bg=colors[index])
            widget.after(30, update_color, index + 1)  # 30ms giữa mỗi bước

    update_color()

# Hàm xuất ra thông báo lỗi khi chọn file input
def printErrorInput(frm_mid, announce):
    frm_mid.update_idletasks()  # Đảm bảo frm_mid có kích thước trước khi gọi printErrorInput
    # Xóa nội dung cũ trong `frm_mid`  
    for widget in frm_mid.winfo_children():  
        widget.destroy() 

    frm_mid.update_idletasks()  # Đảm bảo frm_mid có kích thước trước khi gọi printErrorInput
    # Thông báo không thể truy cập video
    label = tk.Label(
        master=frm_mid,
        text=announce,
        font=("Helvetica", 18),
        fg="red",
        wraplength=frm_mid.winfo_width() - 20,  # Độ dài tối đa trước khi xuống dòng (trừ một chút padding)
        justify='center'  # Căn chỉnh văn bản (tùy chọn)
    )
    label.pack(fill="both", expand=True)
     # Update wraplength on resize  
    frm_mid.bind("<Configure>", lambda  event: updateErrorWrapLength(frm_mid, label))  

# Hàm cập nhật wraplength
def updateErrorWrapLength(frm_mid, error_label):  
    error_label.config(wraplength=frm_mid.winfo_width() - 20)  


# /////////////////////////////////////////////////////----CAMERA WINDOW----////////////////////////////////////////////////////////////

# Các biến toàn cục để nhận diện qua cam
cap = None  
update_task = None  
camera_label = None  
detect_closed = False

# Hàm nhận diên qua camera
def detect_camera(frm_mid):  
    global camera_label, cap, update_task, detect_closed  # Thêm biến toàn cục  

    # Nếu camera đang mở, dừng lại trước khi mở lại  
    if cap is not None:  
        cap.release()  
    if update_task is not None:  
        frm_mid.after_cancel(update_task)  

    detector = FER()  # Khởi tạo bộ phát hiện cảm xúc  

    # Mở camera  
    cap = cv2.VideoCapture(0)  
    if not cap.isOpened():  
        print("Không thể mở camera!")  
        # Thông báo lỗi trên GUI
        printErrorInput(frm_mid, f"Can't open camera. Please check your camera system!")
        # Thêm sự kiện nếu thu phóng frame thì sẽ gọi lại hàm printErrorInput để cập nhật lại wraplength
        frm_mid.bind("<Configure>", lambda  event:printErrorInput(frm_mid, f"Can't open camera. Please check your camera system!"))
        return  

    def update_frame():  
        global update_task, detect_closed  # Biến lưu task after()  

        # Kiểm tra nếu tắt camera thì ko detect nữa
        if detect_closed:
            detect_closed = False
            return

        start_time = time.time()  
        ret, frame = cap.read()  
        if not ret:  
            cap.release()  
            print("Không thể đọc dữ liệu từ camera!")  
            # Thông báo lỗi trên GUI
            printErrorInput(frm_mid, f"Can't read the data from camera!")
            # Thêm sự kiện nếu thu phóng frame thì sẽ gọi lại hàm printErrorInput để cập nhật lại wraplength
            frm_mid.bind("<Configure>", lambda  event:printErrorInput(frm_mid, f"Can't read the data from camera!"))
            return   

        # Kiểm tra kích thước khung hình  
        if frame is None:  
            print("Dữ liệu khung hình không hợp lệ!")  
            # Thông báo lỗi trên GUI
            printErrorInput(frm_mid, f"Frame data is not invalid!")
            # Thêm sự kiện nếu thu phóng frame thì sẽ gọi lại hàm printErrorInput để cập nhật lại wraplength
            frm_mid.bind("<Configure>", lambda  event:printErrorInput(frm_mid, f"Frame data is not invalid!"))
            return  
        
        frame_height, frame_width, _ = frame.shape  
        
        # Tính tỷ lệ scale  
        scale = frm_mid.winfo_height() / frame_height  
        
        # Resize về kích thước mới (phải chuyển thành số nguyên)  
        new_width = int(scale * frame_width)  
        new_height = int(frm_mid.winfo_height())  
        
        frame = cv2.resize(frame, (new_width, new_height))  
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  

        # Nhận diện khuôn mặt & cảm xúc  
        result = detector.detect_emotions(frame)  
        if result:  
            for face in result:  
                x, y, w, h = face['box']  
                top_emotion = max(face["emotions"], key=face["emotions"].get)  
                percent = max(face["emotions"].values())  

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  
                cv2.putText(frame, f"{top_emotion} {percent*100:.0f}%",   
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)  
        else:  
            cv2.putText(frame, "No face detected", (50, 50),   
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)  

        # Tính FPS  
        # fps = 1.0 / (time.time() - start_time)  
        # cv2.putText(frame, f"FPS: {fps:.2f}", (50, 100),   
        #             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)  

        # Hiển thị trên Tkinter  
        img = Image.fromarray(frame)  
        img_tk = ImageTk.PhotoImage(image=img)  

        camera_label.config(image=img_tk)  
        camera_label.image = img_tk  

        # Lặp lại sau 20ms  
        update_task = frm_mid.after(20, update_frame)  

    # Xóa nội dung cũ trong `frm_mid`  
    for widget in frm_mid.winfo_children():  
        widget.destroy()  

    camera_label = tk.Label(frm_mid)  
    camera_label.pack(fill="both", expand=True)  

    update_frame()  # Gọi lần đầu để bắt đầu hiển thị video  

# Hàm reset frm_mid để hình default
def close_camera_video_img(frm_mid, imgPath):
    global detect_closed
    # global processed_results, tk_img, tk_original_img, video_label, detect_closed
    # processed_results, tk_img, tk_original_img, video_label = None, None, None, None
    
    # Xóa nội dung cũ trong `frm_mid`  
    for widget in frm_mid.winfo_children():  
        widget.destroy()  
    # del processed_results, tk_img, tk_original_img, video_label

    # Tắt cam
    if cap is not None:
        cap.release()
        cv2.destroyAllWindows()
    # Cập nhật biến để xác nhận đã tắt cam
    detect_closed = True
    
    # Hiển thị camera
    global camera_img
    camera_img = tk.PhotoImage(file=imgPath)

    frm_mid.rowconfigure(0, weight=1)
    frm_mid.rowconfigure(1, weight=0)
    frm_mid.columnconfigure(0, weight=1)
    frm_mid.columnconfigure(1, weight=0)

    camera_lbl = tk.Label(master=frm_mid, image=camera_img)
    camera_lbl.grid(row=0, column=0, sticky="nsew")

def close_img(frm_mid, imgPath):
    global processed_results, tk_img, tk_original_img, detect_closed
    processed_results, tk_img, tk_original_img = None, None, None
    
    # Xóa nội dung cũ trong `frm_mid`  
    for widget in frm_mid.winfo_children():  
        widget.destroy()  
    del processed_results, tk_img, tk_original_img
    
    # Hiển thị camera
    global camera_img
    camera_img = tk.PhotoImage(file=imgPath)

    frm_mid.rowconfigure(0, weight=1)
    frm_mid.rowconfigure(1, weight=0)
    frm_mid.columnconfigure(0, weight=1)
    frm_mid.columnconfigure(1, weight=0)

    camera_lbl = tk.Label(master=frm_mid, image=camera_img)
    camera_lbl.grid(row=0, column=0, sticky="nsew")

# Tạo GUI cho camera window
def camera_window(title, window):
    window.update_idletasks()  # Đảm bảo lấy kích thước chính xác
    
    # Lưu kích thước và vị trí hiện tại
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    window_x = window.winfo_x()
    window_y = window.winfo_y()

    is_maximized = window.state() == "zoomed"

    # Tạo cửa sổ mới và giữ vị trí cũ
    create_camera_window(window, title, window_width, window_height, window_x, window_y,is_maximized)

# Hàm tạo cửa sổ con
def create_camera_window(window, title, width, height, original_x, original_y,is_maximized):
    # Ẩn cửa sổ chính
    window.withdraw()
    
    new_window = tk.Toplevel(bg="white")
    if is_maximized:
        new_window.state("zoomed")
    else:
        new_window.title(title)
        new_window.geometry(f"{width}x{height}+{original_x}+{original_y}")  # Giữ kích thước và vị trí cũ

    # center_window(new_window)
    # Cấu trúc lưới của cửa sổ mới
    new_window.rowconfigure(1, weight=9)  
    new_window.rowconfigure(2, weight=1)  
    new_window.columnconfigure(0, weight=1)  

    # Xử lý khi quay về cửa sổ chính
    def back_to_main_window():
        global detect_closed
    # Lấy thông tin cửa sổ con
        new_window.update_idletasks()
        if new_window.state() == "zoomed":
            window.state("zoomed")
        else:
            new_window_width = new_window.winfo_width()
            new_window_height = new_window.winfo_height()
            new_window_x = new_window.winfo_x()
            new_window_y = new_window.winfo_y()
            # Thêm thời gian chờ trước khi hiển thị lại cửa sổ chính
            window.after(0, lambda: window.geometry(f"{new_window_width}x{new_window_height}+{new_window_x}+{new_window_y}"))

        close_camera_video_img(frm_mid, "img/frm_camera.png")
        detect_closed = False
        new_window.destroy()

        window.deiconify()

    # Xử lý khi đóng cửa sổ con
    def close_new_window():
        sys.exit()

    new_window.protocol("WM_DELETE_WINDOW", close_new_window)  # Xử lý sự kiện đóng cửa sổ

    # Tạo các khung và nút trong cửa sổ mới
    frm_top = tk.Frame(master=new_window, bg="white")
    frm_top.grid(row=0, column=0, sticky="nsew")

    # Load icon với biến toàn cục để không bị xóa
    global back_img
    back_img = tk.PhotoImage(file="img/back-button.png")  

    btn_back = tk.Button(
        master=frm_top,
        image=back_img,
        command=back_to_main_window, # Thêm xử kiện để trở về trang chi
        borderwidth=0,
        highlightthickness=0,
        cursor="hand2"
    )
    btn_back.grid(row=0, column=0, padx=15, pady=15)

    # Set sự kiện khi hover
    btn_back.bind("<Enter>", lambda e: on_enter(btn_back, "SystemButtonFace", "#F4A460"))
    btn_back.bind("<Leave>", lambda e: on_leave(btn_back, "SystemButtonFace", "#F4A460"))

    # Hiển thị camera
    global camera_img
    camera_img = tk.PhotoImage(file="img/frm_camera.png")

    frm_mid = tk.Frame(master=new_window)
    frm_mid.rowconfigure(0, weight=1)
    frm_mid.columnconfigure(0, weight=1)

    camera_lbl = tk.Label(master=frm_mid, image=camera_img)
    camera_lbl.grid(row=0, column=0, sticky="nsew")
    frm_mid.grid(row=1, column=0, sticky="nsew", pady=(0, 20), padx=20)

    # frm chứa 2 nút nằm dưới cùng
    frm_bottom = tk.Frame(master=new_window, bg="white")
    frm_bottom.columnconfigure(0, weight=1)
    frm_bottom.columnconfigure(1, weight=8)
    frm_bottom.columnconfigure(2, weight=8)
    frm_bottom.columnconfigure(3, weight=8)
    frm_bottom.columnconfigure(4, weight=1)

    # Nút mở camera
    btn_open_cam = tk.Button(
        master=frm_bottom,
        text="Open camera",
        font=("Helvetica", 15),
        cursor="hand2",
        command= lambda: detect_camera(frm_mid),
    )

    # Nút đóng camera
    btn_close_cam = tk.Button(
        master=frm_bottom,
        text="Close camera",
        font=("Helvetica", 15),
        cursor= "hand2",
        command= lambda: close_camera_video_img(frm_mid, "img/frm_camera.png"),
    )
    btn_open_cam.grid(row=0, column=0, sticky="nsew")
    btn_close_cam.grid(row=0, column=4, sticky="nsew")
    frm_bottom.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

    # Set sự kiện khi hover
    btn_open_cam.bind("<Enter>", lambda e: on_enter(btn_open_cam, "SystemButtonFace", "#F4A460"))
    btn_open_cam.bind("<Leave>", lambda e: on_leave(btn_open_cam, "SystemButtonFace", "#F4A460"))
    btn_close_cam.bind("<Enter>", lambda e: on_enter(btn_close_cam, "SystemButtonFace", "#F4A460"))
    btn_close_cam.bind("<Leave>", lambda e: on_leave(btn_close_cam, "SystemButtonFace", "#F4A460"))


#/////////////////////////////////////////////////////----VIDEO WINDOW----////////////////////////////////////////////////////////////

# Chọn file video
def openVideoFile(frm_mid):
    # Xoá video cũ nếu có để ko bị đụng độ
    close_camera_video_img(frm_mid, "img/film.png")
    filepath = askopenfilename(
        filetypes=[("Video files", "*.mp4;*.avi;*.mov;*.mkv;*.flv;*.wmv"), ("All files", "*.*")]
    )
    return filepath if filepath else None

# Hàm nhận diện qua video
def detect_video(frm_mid):
    global video_label, detect_closed  # Label để hiển thị video
    detector = FER()

    filePath = openVideoFile(frm_mid)
    if not filePath:
        return  # Không chọn file thì thoát luôn

    cap = cv2.VideoCapture(filePath)

    # Nếu ko mở video được thì thông báo lỗi
    if not cap.isOpened():  
        print(f"Không thể mở file video!")  
        # Thông báo lỗi trên GUI
        printErrorInput(frm_mid, f"Can't read video data for the file '{filePath}'. The file may be corrupted or does not contain valid video data.")
        return  

    # Lấy thông tin xoay của frame
    rotation = cap.get(cv2.CAP_PROP_ORIENTATION_META) # Hoặc các thuộc tính tương tự

    def update_frame():
        global video_label, detect_closed

    # # Kiểm tra nếu bấm xóa video thì dừng lại
    # if detect_closed:
    #     detect_closed = False
    #     return

        start_time = time.time()
        ret, frame = cap.read()
        if not ret:
            cap.release()
            return  # Khi hết video thì thoát
        
        if rotation == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE) # Xoay 90' theo chiều kim đồng hồ
        elif rotation == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180) # Xoay 180'
        elif rotation == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE) # Xoay 90' theo ngược chiều kim đồng hồ

        frame_height, frame_width, _ = frame.shape
        # print(frame_height)
        # print(frame_width)
        
        # Tính tỷ lệ scale
        scale = frm_mid.winfo_height() / frame_height
        
        # Resize về kích thước mới (phải chuyển thành số nguyên)
        new_width = int(scale * frame_width)
        new_height = int(frm_mid.winfo_height())
        
        frame = cv2.resize(frame, (new_width, new_height))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


        result = detector.detect_emotions(frame)
        if result:
            for face in result:
                x, y, w, h = face['box']
                top_emotion = max(face["emotions"], key=face["emotions"].get)
                percent = max(face["emotions"].values())

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{top_emotion} {percent*100:.0f}%", 
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "No face detected", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Tính FPS
        # fps = 1.0 / (time.time() - start_time)
        # cv2.putText(frame, f"FPS: {fps:.2f}", (50, 100), 
        #             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Hiển thị trên Tkinter
        img = Image.fromarray(frame)
        img_tk = ImageTk.PhotoImage(image=img)

        # video_label = None
        video_label.config(image=img_tk)
        video_label.image = img_tk

        # Cập nhật frm_mid sau 15ms
        frm_mid.after(15, update_frame)  # Lặp lại sau 15ms

    # Xóa nội dung cũ trong `frm_mid`
    for widget in frm_mid.winfo_children():
        widget.destroy()

    video_label = tk.Label(frm_mid)
    video_label.pack(fill="both", expand=True)

    update_frame()  # Gọi lần đầu để bắt đầu hiển thị video

# Tạo GUI cho video window
def video_window(title, window):
    window.update_idletasks()  # Đảm bảo lấy kích thước chính xác
    
    # Lưu kích thước và vị trí hiện tại
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    window_x = window.winfo_x()
    window_y = window.winfo_y()
        # Kiểm tra trạng thái của cửa sổ chính
    is_maximized = window.state() == "zoomed"
    # Tạo cửa sổ mới và giữ vị trí cũ
    create_video_window(window, title, window_width, window_height, window_x, window_y, is_maximized)

# Hàm tạo video_window
def create_video_window(window, title, width, height, original_x, original_y, is_maximized):
    window.withdraw()  # Hide the main window instead of destroying it
    new_window = tk.Toplevel(
        bg="white"
    )  # Create a new Toplevel window
    new_window.title(title)
    if is_maximized:
        new_window.state("zoomed")
    else:
        new_window.geometry(f"{width}x{height}+{original_x}+{original_y}")  # Giữ kích thước và vị trí cũ

    new_window.rowconfigure(0)  # frm_top chiếm ít không gian hơn
    new_window.rowconfigure(1, weight=9)  # frm_mid chiếm nhiều không gian hơn
    new_window.rowconfigure(2, weight=1)  # frm_mid chiếm nhiều không gian hơn
    new_window.columnconfigure(0, weight=1)

    # Hàm trở về cửa số chính
    def back_to_main_window():
        global detect_closed
    # Lấy thông tin cửa sổ con
        new_window.update_idletasks()
        if new_window.state() == "zoomed":
            window.state("zoomed")
        else:
            new_window_width = new_window.winfo_width()
            new_window_height = new_window.winfo_height()
            new_window_x = new_window.winfo_x()
            new_window_y = new_window.winfo_y()
            # Thêm thời gian chờ trước khi hiển thị lại cửa sổ chính
            window.after(0, lambda: window.geometry(f"{new_window_width}x{new_window_height}+{new_window_x}+{new_window_y}"))

        close_camera_video_img(frm_mid, "img/film.png")
        detect_closed = False
        new_window.destroy()

        window.deiconify()

    # Hàm đóng cửa sổ con
    def close_new_window():
        sys.exit()

    # Gắn sự kiện vào nút X (đóng cửa sổ con)
    new_window.protocol("WM_DELETE_WINDOW", close_new_window)

    frm_top = tk.Frame(
        master=new_window,
        bg="white"
        # bg="red",
        # height=30,
        # width=100,
    )


    back_img = check_icon("img/back-button.png")
    btn_back = tk.Button(
        master=frm_top,
        image=back_img,
        command=back_to_main_window, # Thêm xử kiện để trở về trang chi
        borderwidth=0,  # Xóa viền
        highlightthickness=0,  # Xóa viền sáng khi được chọn
        cursor="hand2"
    )
    btn_back.bind("<Enter>", lambda e: on_enter(btn_back, "SystemButtonFace", "#F4A460"))
    btn_back.bind("<Leave>", lambda e: on_leave(btn_back, "SystemButtonFace", "#F4A460"))

    btn_back.grid(row=0, column=0, padx=15,pady=15)
    frm_top.grid(row=0, column=0, sticky="nsew")

    video_img = check_icon("img/film.png")
    
    frm_mid = tk.Frame(
        master=new_window,
        # bg="yellow",
    )
    frm_mid.rowconfigure(0, weight=1)
    frm_mid.columnconfigure(0, weight=1)

    video_lbl = tk.Label(
        master = frm_mid,
        image=video_img,
    )
    video_lbl.grid(row=0, column=0, sticky="nsew")

    frm_mid.grid(row=1,column=0, stick="nsew", pady=(0,20), padx=20)

    frm_bottom = tk.Frame(
        master=new_window,
        bg="white",
    )
    frm_bottom.columnconfigure(0, weight=1)
    frm_bottom.columnconfigure(1, weight=8)
    frm_bottom.columnconfigure(2, weight=8)
    frm_bottom.columnconfigure(3, weight=8)
    frm_bottom.columnconfigure(4, weight=1)

    # Nút thêm video
    btn_add_video = tk.Button(
        master=frm_bottom,
        command= lambda: detect_video(frm_mid),
        text="Add video",
        font=("Helvetica", 15),
        cursor="hand2"
    )

    # Nút xoá video
    btn_delete_video = tk.Button(
        master=frm_bottom,
        text="Delete video",
        font=("Helvetica", 15),
        cursor= "hand2",
        command= lambda: close_camera_video_img(frm_mid, "img/film.png"),
    )

    btn_add_video.bind("<Enter>", lambda e: on_enter(btn_add_video, "SystemButtonFace", "#F4A460"))
    btn_add_video.bind("<Leave>", lambda e: on_leave(btn_add_video, "SystemButtonFace", "#F4A460"))
    btn_delete_video.bind("<Enter>", lambda e: on_enter(btn_delete_video, "SystemButtonFace", "#F4A460"))
    btn_delete_video.bind("<Leave>", lambda e: on_leave(btn_delete_video, "SystemButtonFace", "#F4A460"))
    btn_add_video.grid(row=0,column=0, sticky="nsew")
    btn_delete_video.grid(row=0,column=4, sticky="nsew")
    frm_bottom.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0,20))


# /////////////////////////////////////////////////////----IMAGE WINDOW----////////////////////////////////////////////////////////////

# Global biến chứa ảnh để tránh bị xóa bởi garbage collector
global tk_img
global tk_original_img
global processed_results  # Biến lưu kết quả nhận diện cảm xúc
global original_frame    # Biến lưu ảnh gốc

# Chọn file ảnh
def openImageFile():
    filepath = askopenfilename(
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All files", "*.*")]
    )
    return filepath if filepath else None

# Hàm nhận diện ảnh
def detect_by_image():
    global processed_results, original_frame  # Biến toàn cục

    # Khởi tạo FER
    detector = FER()

    # Chọn file
    file_path = openImageFile()

    # Đọc ảnh gốc
    img = cv2.imread(file_path)
    if img is None:
        print("Lỗi: Không thể đọc ảnh!")
        return (None, file_path)

    # Nhận diện cảm xúc một lần
    result = detector.detect_emotions(img)
    processed_results = result
    original_frame = img  # Lưu ảnh gốc
    return (img, file_path)

# 
def redraw_image(frm_mid, img, filePath):
    global processed_results, original_frame, tk_img, tk_original_img

    # Nếu ảnh None thì hiển thị file ảnh bị lỗi
    if img is None:
        # Thông báo lỗi không đọc được ảnh trên GUI
        printErrorInput(frm_mid, f"Can't read image data from the file '{filePath}'. The file may be corrupted or does not contain valid image data.")
        # Thêm sự kiện nếu thu phóng frame thì sẽ gọi lại hàm printErrorInput để cập nhật lại wraplength
        frm_mid.bind("<Configure>", lambda  event: printErrorInput(frm_mid, f"Can't read image data from the file '{filePath}'. The file may be corrupted or does not contain valid image data.")) # Bind lại printErrorInput
        return

    # Resize ảnh dựa trên kích thước frame
    orig_height, orig_width, _ = original_frame.shape
    frame_height = frm_mid.winfo_height() / 1.2
    scale = (frame_height - 30) / orig_height
    new_width = int(orig_width * scale)
    new_height = int(orig_height * scale)

    frame_width = frm_mid.winfo_width()  # Lấy chiều rộng của frame

    # Nếu frame_width chưa có giá trị hợp lệ, cập nhật giao diện để lấy kích thước thật
    if frame_width == 0:
        frm_mid.update_idletasks()
        frame_width = frm_mid.winfo_width()

    if new_width > frame_width / 2:
        max_width = frame_width / 2
        new_width = int(frame_width / 2 - 30)  # Giới hạn new_width tối đa bằng 1/2 frame
        scale = min((frame_height) / orig_height, (max_width - 30) / orig_width)
        new_height = int(new_width * (orig_height / orig_width))  # Giữ tỷ lệ khung hình

    # Đảm bảo giá trị là số nguyên trước khi resize
    new_width = max(1, int(new_width))
    new_height = max(1, int(new_height))

    resized_frame = cv2.resize(original_frame, (new_width, new_height))
    resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

    # Lấy ra ảnh gốc
    original_img_pil = Image.fromarray(resized_frame)
    if original_img_pil.mode != "RGBA":
        original_img_pil = original_img_pil.convert("RGBA")
    # Thêm box-shadow cho ảnh gốc
    original_img_with_shadow = add_box_shadow(original_img_pil, offset=(2, 2), blur_radius=4, shadow_color=(0, 0, 0, 77))


    # Vẽ kết quả nhận diện dựa trên kết quả đã lưu
    if processed_results:
        for face in processed_results:
            x, y, w, h = face['box']
            x, y, w, h = int(x * scale), int(y * scale), int(w * scale), int(h * scale)
            top_emotion = max(face["emotions"], key=face["emotions"].get)
            percent = max(face["emotions"].values())
            cv2.rectangle(resized_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Set font_scale và thickness cho text
            font_scale = 0.65
            thickness = 2
            cv2.putText(
                resized_frame,
                f"{top_emotion} - {percent*100:.2f}%",
                (x, y - 10),
                cv2.FONT_HERSHEY_COMPLEX,
                font_scale,
                (0, 255, 0),
                thickness,
            )
    else:
        # Nếu không có khuôn mặt nào thì hiển thị thông báo trên ảnh 
        print("No faces found in the photo!") 
        text = "No faces found in the photo!" 
        font = cv2.FONT_HERSHEY_COMPLEX 
        font_scale = 2 * scale
        thickness = 2 
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0] # Lấy kích thước text 
        text_x = (new_width - text_size[0]) // 2 # Căn giữa theo chiều ngang 
        text_y = (new_height + text_size[1]) // 2 # Căn giữa theo chiều dọc 
        cv2.putText(resized_frame, text, (text_x, text_y), font, font_scale, (255, 0, 0), thickness)


    # Hiển thị kết quả sau khi nhận diện
    # Lấy ra ảnh sau khi nhận diện
    img_pil = Image.fromarray(resized_frame)
    # Thêm box-shadow cho ảnh
    img_with_shadow = add_box_shadow(img_pil, offset=(2, 2), blur_radius=4, shadow_color=(0, 0, 0, 77))
    # Chuyển đổi ảnh PIL sang Tkinter PhotoImage cho cả ảnh gốc và ảnh sau khi nhận diện
    tk_img = ImageTk.PhotoImage(img_with_shadow)
    tk_original_img = ImageTk.PhotoImage(original_img_with_shadow)

    # Xóa ảnh cũ và hiển thị ảnh mới
    for widget in frm_mid.winfo_children():
        widget.destroy()

    frm_mid.columnconfigure(1, weight=1)  # Cột 2 cho ảnh gốc
    frm_mid.rowconfigure(1, weight=1)  # Cột 2 cho ảnh gốc

    # Label cho ảnh gốc
    lbl_original_img = tk.Label(
        master=frm_mid,
        text="Original Image",
        font=("Helvetica", 30),
        bg="white",
    )

    # Label cho ảnh sau khi nhận diện
    lbl_recognized_img = tk.Label(
        master=frm_mid,
        text="Recognized Image",
        font=("Helvetica", 30),
        bg="white",
    )

    lbl_original_img.grid(row=0, column=0, sticky="nsew")
    lbl_recognized_img.grid(row=0, column=1, sticky="nsew")

    # Hiển thị ảnh gốc (có box-shadow)
    original_img_lbl = tk.Label(master=frm_mid, image=tk_original_img, bg="white")
    original_img_lbl.grid(row=1, column=0, sticky="nsew")  # Cột 0

    # Hiển thị ảnh xử lý (có box-shadow)
    img_lbl = tk.Label(master=frm_mid, image=tk_img, bg="white")
    img_lbl.grid(row=1, column=1, sticky="nsew")  # Cột 1

    # Khi resize màn hình thì sẽ gọi lại hàm redraw_image để chỉnh lại bố cục của frm_mid
    frm_mid.bind("<Configure>", lambda event: redraw_image(frm_mid, img, filePath))

# Dùng hàm này để chạy chức năng nhận diện qua video
def process_detected_image(frm_mid):
    img, filePath = detect_by_image() 
    redraw_image(frm_mid, img, filePath)

# Hàm dùng để thêm box-shadow
def add_box_shadow(image, offset=(2, 2), blur_radius=4, shadow_color=(0, 0, 0, 77)):
    # Chuyển đổi ảnh sang RGBA nếu chưa đúng định dạng
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    
    # Kích thước ảnh gốc
    width, height = image.size

    # Tạo ảnh nền với bóng đổ
    shadow = Image.new(
        "RGBA",
        (width + abs(offset[0]) + blur_radius * 2, height + abs(offset[1]) + blur_radius * 2),
        (0, 0, 0, 0)  # Trong suốt
    )

    shadow_draw = ImageDraw.Draw(shadow)

    # Tạo hình chữ nhật tương ứng với ảnh, thêm shadow
    shadow_draw.rectangle(
        [blur_radius, blur_radius, width + blur_radius, height + blur_radius],
        fill=shadow_color
    )

    # Làm mờ bóng đổ
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))

    # Chèn ảnh gốc lên trên bóng
    shadow.paste(image, (blur_radius + offset[0], blur_radius + offset[1]), mask=image)
    
    return shadow



# Tạo GUI cho image window
def img_window(title, window):
    window.update_idletasks()  # Đảm bảo lấy kích thước chính xác
    
    # Lưu kích thước và vị trí hiện tại
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    window_x = window.winfo_x()
    window_y = window.winfo_y()

    is_maximized = window.state() == "zoomed"

    # Tạo cửa sổ mới và giữ vị trí cũ
    create_img_window(window, title, window_width, window_height, window_x, window_y,is_maximized)

# Hàm để tạo image window
def create_img_window(window, title, width, height, original_x, original_y,is_maximized):
    # Ẩn cửa sổ cha window
    window.withdraw()  
    # Tạo window con mới
    new_window = tk.Toplevel(
        bg="white"
    )

    # Nếu cửa sổ window phóng to màn hình thì cửa sổ con cũng phóng to ra
    if is_maximized:
        new_window.state("zoomed")
    # Nếu không thì giữa kích thướt và vị trí cũ
    else:
        new_window.geometry(f"{width}x{height}+{original_x}+{original_y}")  # Giữ kích thước và vị trí cũ

    new_window.rowconfigure(0)  # frm_top chiếm ít không gian hơn
    new_window.rowconfigure(1, weight=9)  # frm_mid chiếm nhiều không gian hơn
    new_window.rowconfigure(2, weight=1)  # frm_mid chiếm nhiều không gian hơn
    new_window.columnconfigure(0, weight=1)

    # Quay về cửa sổ cha
    def back_to_main_window():
    # Lấy thông tin cửa sổ con
        new_window.update_idletasks()
        if new_window.state() == "zoomed":
            window.state("zoomed")
        else:
            new_window_width = new_window.winfo_width()
            new_window_height = new_window.winfo_height()
            new_window_x = new_window.winfo_x()
            new_window_y = new_window.winfo_y()
            # Thêm thời gian chờ trước khi hiển thị lại cửa sổ chính
            window.after(0, lambda: window.geometry(f"{new_window_width}x{new_window_height}+{new_window_x}+{new_window_y}"))

        new_window.destroy()
        # close_camera_video_img(frm_mid, "img/film.png")

        window.deiconify()

    # Đóng cửa sổ con
    def close_new_window():
        sys.exit()

    # Gắn sự kiện vào nút X (đóng cửa sổ con)
    new_window.protocol("WM_DELETE_WINDOW", close_new_window)

    frm_top = tk.Frame(
        master=new_window,
        bg="white"
    )
    
    # Thêm btn_back trong frm_top
    back_img = check_icon("img/back-button.png")
    btn_back = tk.Button(
        master=frm_top,
        image=back_img,
        command=back_to_main_window, # Thêm xử kiện để trở về trang chi
        borderwidth=0,  # Xóa viền
        highlightthickness=0,  # Xóa viền sáng khi được chọn
        cursor="hand2"
    )

    # Thêm sự kiện khi hover
    btn_back.bind("<Enter>", lambda e: on_enter(btn_back, "SystemButtonFace", "#F4A460"))
    btn_back.bind("<Leave>", lambda e: on_leave(btn_back, "SystemButtonFace", "#F4A460"))

    btn_back.grid(row=0, column=0, padx=15,pady=15)
    frm_top.grid(row=0, column=0, sticky="nsew")

    img_img = check_icon("img/frm_img.png")
  
    frm_mid = tk.Frame(
        master=new_window,
    )

    frm_mid.rowconfigure(0, weight=1)
    frm_mid.columnconfigure(0, weight=1)

    img_lbl = tk.Label(
        master = frm_mid,
        image=img_img,
    )
    img_lbl.grid(row=0, column=0, sticky="nsew")

    frm_mid.grid(row=1,column=0, stick="nsew", pady=(0,20), padx=20)

    frm_bottom = tk.Frame(
        master=new_window,
        bg="white",
    )

    frm_bottom.columnconfigure(0, weight=1)
    frm_bottom.columnconfigure(1, weight=8)
    frm_bottom.columnconfigure(2, weight=8)
    frm_bottom.columnconfigure(3, weight=8)
    frm_bottom.columnconfigure(4, weight=1)

    # Nút thêm ảnh
    btn_add_img = tk.Button(
        master=frm_bottom,
        command= lambda: process_detected_image(frm_mid),
        text="Add image",
        font=("Helvetica", 15),
        cursor="hand2"
    )

    # Nút xoá ảnh
    btn_delete_img = tk.Button(
        master=frm_bottom,
        text="Delete image",
        font=("Helvetica", 15),
        cursor= "hand2",
        command= lambda: close_img(frm_mid, "img/frm_img.png"),
    )

    btn_add_img.bind("<Enter>", lambda e: on_enter(btn_add_img, "SystemButtonFace", "#F4A460"))
    btn_add_img.bind("<Leave>", lambda e: on_leave(btn_add_img, "SystemButtonFace", "#F4A460"))
    btn_delete_img.bind("<Enter>", lambda e: on_enter(btn_delete_img, "SystemButtonFace", "#F4A460"))
    btn_delete_img.bind("<Leave>", lambda e: on_leave(btn_delete_img, "SystemButtonFace", "#F4A460"))
    btn_add_img.grid(row=0,column=0, sticky="nsew")
    btn_delete_img.grid(row=0,column=4, sticky="nsew")
    frm_bottom.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0,20))


# Hàm tạo hiệu ứng khi hover
def on_enter(e, inColor, outColor):
    fade_color(inColor, outColor, 10, e)  # Thay đổi màu nền và chữ khi hover

def on_leave(e, inColor, outColor):
    fade_color(outColor, inColor, 10, e)  # Trở về màu gốc khi rời chuột


# /////////////////////////////////////////////////////----LEFT MENU----////////////////////////////////////////////////////////////
def create_left_menu(window):
    left_frm = tk.Frame(master=window, relief=tk.RAISED, bd=2, bg="lightgrey")
    left_frm.rowconfigure(1, minsize=50)
    left_frm.columnconfigure(0, minsize=50)
    menu_icon = check_icon("img/menu.png")
    img_icon = check_icon("img/btn_img.png")
    video_icon = check_icon("img/btn_video.png")
    cam_icon = check_icon("img/btn_camera.png")

    # Label menu
    lbl_menu = tk.Label(
        master=left_frm,
        text="Menu",
        image=menu_icon,
        compound=tk.LEFT,
        padx=10,
        pady=10,
        font=("Helvetica", 18)
    )

    # Frame chứa button
    btn_frm = tk.Frame(master=left_frm)

    # Button Image
    btn_Img = tk.Button(
        master=btn_frm,
        image=img_icon,
        compound=tk.LEFT,
        text="Image",
        padx=10,
        bg="lightpink",
        fg="black",
        font=("Helvetica", 14),
        command=lambda: img_window("Image", window),
        cursor="hand2",
    )

    btn_Img.bind("<Enter>", lambda e: on_enter(btn_Img, "lightpink", "#ee687f"))
    btn_Img.bind("<Leave>", lambda e: on_leave(btn_Img, "lightpink", "#ee687f"))

    # Button Video
    btn_Vid = tk.Button(
        master=btn_frm,
        image=video_icon,
        compound=tk.LEFT,
        text="Video",
        padx=10,
        bg="#ebe5c1",
        fg="black",
        font=("Helvetica", 14),
        command=lambda: video_window("Video", window),
        cursor="hand2",
    )
    btn_Vid.bind("<Enter>", lambda e: on_enter(btn_Vid, "#ebe5c1", "#cec489"))
    btn_Vid.bind("<Leave>", lambda e: on_leave(btn_Vid, "#ebe5c1", "#cec489"))

    # Button Camera
    btn_Cam = tk.Button(
        master=btn_frm,
        image=cam_icon,
        text="Camera",
        compound=tk.LEFT,
        padx=10,
        bg="lightblue",
        fg="black",
        font=("Helvetica", 14),
        command=lambda: camera_window("Camera", window),
        cursor="hand2",
    )
    btn_Cam.bind("<Enter>", lambda e: on_enter(btn_Cam, "lightblue", "#7eb6ff"))
    btn_Cam.bind("<Leave>", lambda e: on_leave(btn_Cam, "lightblue", "#7eb6ff"))

    # Thêm button vào frame
    btn_Img.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
    btn_Vid.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
    btn_Cam.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

    # Thêm vào giao diện
    lbl_menu.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    btn_frm.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

    return left_frm

# Set kích thướt và vị trí nằm giữa màn hình của frame
def center_window(window, width=800, height=600):
    # Lấy kích thước màn hình
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Tính toán tọa độ để đặt cửa sổ ở giữa màn hình
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))

    # Đặt kích thước và vị trí cửa sổ
    window.geometry(f"{width}x{height}+{x}+{y}")

# Set Icon cho window
def setIconWindow(window):
    iconWindow = check_icon("img/emotion.png")
    iconWindow = check_icon("img/emotion.png")  # Lưu icon vào biến toàn cục
    window.iconphoto(False, iconWindow)  # Sử dụng iconWindow thay vì "icon"

    if os.name == 'nt':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('mycompany.myproduct.subproduct.version')
        window.iconbitmap(default='img/emotion.ico')


# /////////////////////////////////////////////////////----CONTENT FRAME----////////////////////////////////////////////////////////////
def createContentFrame(window):
    # from PIL import Image, ImageTk  # Import Pillow
    background_img_path = "img/bg3.png"
    content_frm = tk.Frame(master=window)
    canvas = tk.Canvas(master=content_frm)
    canvas.grid(row=0, column=0, sticky="nsew")

    content_frm.rowconfigure(0, weight=1)
    content_frm.columnconfigure(0, weight=1)

    # Tải và Resize lại image 
    img = Image.open(background_img_path)
    img = img.resize((800, 600), Image.Resampling.LANCZOS)  # Correct resizing method
    img = ImageTk.PhotoImage(img)

    # Persistently store the image reference
    canvas.bg_image = img
    image_id = canvas.create_image(0, 0, image=img, anchor="center")  # Canh giữa image

    # Thêm text
    canvas.create_text(
        170, 70, text="Emotion", font=("Helvetica", 50, "bold"), fill="white"
    )

    canvas.create_text(
        250, 150, text="Recognition", font=("Helvetica", 50, "bold"), fill="white"
    )

    # Hàm xử lý resize
    def resize_image(event):
        new_width = event.width
        new_height = event.height
        resized = Image.open(background_img_path).resize((new_width, new_height), Image.Resampling.LANCZOS)
        resized_img = ImageTk.PhotoImage(resized)

        # Persistently store the resized image
        canvas.bg_image = resized_img
        canvas.itemconfig(image_id, image=resized_img)  # Cập nhật ảnh
        canvas.coords(image_id, new_width // 2, new_height // 2)  # Canh giữa ảnh

    # Thêm sự kiến khi resize màn hình sẽ resize lại image
    canvas.bind("<Configure>", resize_image)

    return content_frm

# /////////////////////////////////////////////////////----HÀM MAIN----////////////////////////////////////////////////////////////

if __name__ == "__main__":
    window = tk.Tk()
    window.title("Emotion Recognition")
    window.rowconfigure(0, minsize=800, weight=1)
    window.columnconfigure(1, minsize=800, weight=1)

    # Khởi tạo frame giao diện
    content_frm = createContentFrame(window)
    left_frm = create_left_menu(window)  # GỌI HÀM SAU KHI CÓ ICON

    # Thêm vào layout
    left_frm.grid(row=0, column=0, sticky="ns")
    content_frm.grid(row=0, column=1, sticky="nsew")

    # Đặt icon cửa sổ
    setIconWindow(window)
    # Đặt cửa sổ giữa màn hình
    center_window(window, 800, 600)

    # Chạy ứng dụng
    window.mainloop()