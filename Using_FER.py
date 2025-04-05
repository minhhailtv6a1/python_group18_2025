from tkinter.filedialog import askopenfilename
import cv2
from fer import FER
import time

def openVideoFile():
    filepath = askopenfilename(
        filetypes=[("Video files", "*.mp4;*.avi;*.mov;*.mkv;*.flv;*.wmv"), ("All files", "*.*")]
    )
    return filepath if filepath else None

# Khởi tạo mô hình FER
detector = FER()

filePath = openVideoFile()
# Mở camera
cap = cv2.VideoCapture(filePath)
# Thử lấy thông tin xoay (mã có thể khác nhau tùy thuộc vào codec và container)
rotation = cap.get(cv2.CAP_PROP_ORIENTATION_META) # Hoặc các thuộc tính tương tự
while True:
    start_time = time.time()
    ret, frame = cap.read()
    if not ret:
        break

    if rotation == 90:
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        frame = cv2.rotate(frame, cv2.ROTATE_180)
    elif rotation == 270:
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    
    # Phát hiện cảm xúc
    result = detector.detect_emotions(frame)
    # print(result)
    print(frame.shape)

    if result:  # Nếu có ít nhất một khuôn mặt
        for face in result:
            x, y, w, h = face['box']  # Lấy tọa độ khuôn mặt
            top_emotion = max(face["emotions"], key=face["emotions"].get)  # Chọn cảm xúc có giá trị cao nhất
            percent = max(face["emotions"].values())  # Phần trăm cảm xúc cao nhất
            # Vẽ hình chữ nhật quanh khuôn mặt
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"Emotion: {top_emotion } {percent} ", (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "No face detected", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    fps = 1.0 / (time.time() - start_time)
    cv2.putText(frame, f"FPS: {fps:.2f}", (50, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    cv2.imshow("Emotion Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
