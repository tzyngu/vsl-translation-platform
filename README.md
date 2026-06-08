# VSL Studio - Vietnamese Sign Language Recognition Platform

## Tiếng Việt

### Giới thiệu

VSL Studio là hệ thống nhận diện Ngôn ngữ Ký hiệu Việt Nam theo thời gian thực bằng webcam. Dự án sử dụng MediaPipe Hands để trích xuất keypoints bàn tay, TensorFlow/Keras để phân loại ký hiệu, FastAPI WebSocket để inference realtime và Django để xây dựng giao diện người dùng.

Hệ thống hỗ trợ đăng ký/đăng nhập, chọn avatar, nhận diện ký hiệu realtime, hiển thị nhãn tiếng Việt có dấu, thư viện ký hiệu cộng đồng, upload video mẫu để tạo dữ liệu keypoint cá nhân và tích hợp OpenAI API để hỗ trợ dịch chuỗi ký hiệu thành câu tiếng Việt tự nhiên.

### Điểm nổi bật

- Xử lý 1,199 video gốc, tạo 5,939 keypoint samples thuộc 36 lớp ký hiệu.
- Chuẩn hóa mỗi sample thành tensor shape `(30, 126)`.
- Huấn luyện và so sánh 4 kiến trúc: LSTM, LSTM + Attention, LSTM + Transformer, Transformer.
- Transformer đạt khoảng 93.39% mean cross-validation accuracy và 93.22% mean macro-F1.
- Graph inference latency khoảng 1.71 ms/sample, throughput khoảng 583 samples/second.
- Web app realtime với Django, FastAPI, PostgreSQL, WebSocket và OpenAI API.

### Công nghệ sử dụng

- Python, TensorFlow/Keras, MediaPipe, OpenCV, NumPy
- Django, Django Auth/Admin, FastAPI, WebSocket
- PostgreSQL, Docker Compose
- HTML, CSS, JavaScript
- OpenAI API

### Cấu trúc dự án

```text
VSL/
├── deploy/
│   ├── backend/              # FastAPI backend, inference, API routers
│   └── frontend/             # Django frontend, templates, static files
├── models/                   # MediaPipe hand landmarker model
├── scripts/                  # Scripts chạy frontend/backend và xử lý dữ liệu
├── src/                      # Preprocessing, augmentation, sampling utilities
├── tests/                    # Unit tests
├── training_outputs/         # Model .keras, metrics, label classes
├── docker-compose.yml        # PostgreSQL service
├── requirements.txt          # Core preprocessing dependencies
├── requirements-deploy.txt   # Web deployment dependencies
└── .env.example              # Mẫu cấu hình môi trường
```

Các thư mục `dataset/`, `media/`, `note/` và file `.env` được ignore để tránh push dữ liệu lớn hoặc secrets lên GitHub.

### Cách chạy local

1. Tạo và kích hoạt môi trường ảo:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Cài dependencies:

```powershell
pip install -r requirements-deploy.txt
```

3. Tạo file cấu hình:

```powershell
Copy-Item .env.example .env
```

4. Mở Docker Desktop và chạy PostgreSQL:

```powershell
docker compose up -d postgres
```

5. Chạy migration:

```powershell
.\.venv\Scripts\python.exe deploy\frontend\manage.py migrate
```

6. Chạy frontend:

```powershell
.\scripts\start_frontend.ps1
```

7. Chạy backend trong terminal khác:

```powershell
.\scripts\start_backend.ps1
```

8. Mở ứng dụng:

```text
Frontend: http://127.0.0.1:8000/
Backend health: http://127.0.0.1:8001/api/health
Django Admin: http://127.0.0.1:8000/admin/
```

### Tạo admin

```powershell
.\.venv\Scripts\python.exe deploy\frontend\manage.py createsuperuser
```

### Cấu hình OpenAI API

Trong `.env`:

```env
OPENAI_ENABLED=true
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-5
```

Không commit `.env` lên GitHub.

### Kế hoạch push lên GitHub

```powershell
git init
git add .
git status
git commit -m "Initial commit: VSL Studio"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

Trước khi commit, kiểm tra chắc chắn `.env`, `dataset/`, `media/` và `note/` không xuất hiện trong `git status`.

---

## English

### Overview

VSL Studio is a real-time Vietnamese Sign Language recognition system using a laptop webcam. The project uses MediaPipe Hands for hand keypoint extraction, TensorFlow/Keras for gesture classification, FastAPI WebSocket for realtime inference, and Django for the user interface.

The system supports authentication, user avatars, realtime gesture recognition, Vietnamese label display, a community gesture library, user video uploads for keypoint generation, and OpenAI API integration for translating recognized sign labels into natural Vietnamese sentences.

### Highlights

- Processed 1,199 source videos into 5,939 keypoint samples across 36 gesture classes.
- Standardized each sample into a `(30, 126)` keypoint sequence.
- Trained and compared 4 sequence models: LSTM, LSTM + Attention, LSTM + Transformer, and Transformer.
- Transformer achieved around 93.39% mean cross-validation accuracy and 93.22% mean macro-F1.
- Graph inference latency is around 1.71 ms/sample, with approximately 583 samples/second throughput.
- Full-stack realtime web app using Django, FastAPI, PostgreSQL, WebSocket, and OpenAI API.

### Tech Stack

- Python, TensorFlow/Keras, MediaPipe, OpenCV, NumPy
- Django, Django Auth/Admin, FastAPI, WebSocket
- PostgreSQL, Docker Compose
- HTML, CSS, JavaScript
- OpenAI API

### Project Structure

```text
VSL/
├── deploy/
│   ├── backend/              # FastAPI backend, inference, API routers
│   └── frontend/             # Django frontend, templates, static files
├── models/                   # MediaPipe hand landmarker model
├── scripts/                  # Frontend/backend and preprocessing scripts
├── src/                      # Preprocessing, augmentation, sampling utilities
├── tests/                    # Unit tests
├── training_outputs/         # .keras models, metrics, label classes
├── docker-compose.yml        # PostgreSQL service
├── requirements.txt          # Core preprocessing dependencies
├── requirements-deploy.txt   # Web deployment dependencies
└── .env.example              # Example environment config
```

The `dataset/`, `media/`, `note/`, and `.env` paths are ignored to avoid pushing large data or secrets to GitHub.

### Local Setup

1. Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements-deploy.txt
```

3. Create local environment config:

```powershell
Copy-Item .env.example .env
```

4. Open Docker Desktop and start PostgreSQL:

```powershell
docker compose up -d postgres
```

5. Run database migrations:

```powershell
.\.venv\Scripts\python.exe deploy\frontend\manage.py migrate
```

6. Start the frontend:

```powershell
.\scripts\start_frontend.ps1
```

7. Start the backend in another terminal:

```powershell
.\scripts\start_backend.ps1
```

8. Open the app:

```text
Frontend: http://127.0.0.1:8000/
Backend health: http://127.0.0.1:8001/api/health
Django Admin: http://127.0.0.1:8000/admin/
```

### Create Admin User

```powershell
.\.venv\Scripts\python.exe deploy\frontend\manage.py createsuperuser
```

### OpenAI API Configuration

In `.env`:

```env
OPENAI_ENABLED=true
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-5
```

Never commit `.env` to GitHub.

### GitHub Push Plan

```powershell
git init
git add .
git status
git commit -m "Initial commit: VSL Studio"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

Before committing, confirm that `.env`, `dataset/`, `media/`, and `note/` are not listed in `git status`.
