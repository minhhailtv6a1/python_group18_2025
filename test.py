# $env:TF_ENABLE_ONEDNN_OPTS="0"
import cv2
from fer import FER

# Khởi tạo FER
detector = FER()

# Đọc ảnh
path = r'C:\Users\Admin\Downloads\test_project_python\sample.png'
img = cv2.imread(path)

# Kiểm tra ảnh có tồn tại không
if img is None:
    print("❌ Lỗi: Không thể đọc ảnh! Kiểm tra đường dẫn.")
    exit()

# Lấy kích thước ảnh
height, width, channels = img.shape
print(f"Height: {height}, Width: {width}, Channels: {channels}") 

# Resize ảnh theo tỉ lệ gốc
frame = cv2.resize(img, None, fx=1, fy=1)

# Nhận diện cảm xúc
result = detector.detect_emotions(frame)

if result:
    for face in result:
        x, y, w, h = face['box']  # Đúng thứ tự
        top_emotion = max(face["emotions"], key=face["emotions"].get)
        percent = max(face["emotions"].values())  # Đúng key
        
        # Vẽ hình chữ nhật quanh mặt
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Hiển thị cảm xúc lên ảnh
        cv2.putText(frame, f"{top_emotion} - {percent*100:.2f}%", 
                    (x, y - 10), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 0), 2)   
    
    cv2.imshow('Emotion Detection', frame)
    cv2.waitKey(0)  # Đợi nhấn phím bất kỳ để đóng cửa sổ
    cv2.destroyAllWindows()
else:
    print("⚠ Không tìm thấy khuôn mặt nào trong ảnh!")
