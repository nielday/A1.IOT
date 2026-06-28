# Dự án Demo Day: Dịch vụ Ingestion IoT (Nhóm A1)

Đây là mã nguồn chính thức cho buổi **Demo Day** của hệ thống Smart Campus. Dự án này được thiết kế theo đúng kiến trúc tích hợp mới nhất, rút gọn tối đa so với Lab 05 để tập trung vào luồng giao tiếp thực tế qua **HiveMQ Cloud (MQTT)**.

## Điểm Khác Biệt So Với Lab 05

1. **Không còn PostgreSQL và AI-Service:** 
   Để tối ưu hóa tài nguyên chạy trên cùng một máy (hotspot), dự án đã gỡ bỏ hoàn toàn sự phụ thuộc vào Database (PostgreSQL) và AI-Service cục bộ. Tất cả logic nghiệp vụ đều nằm gọn trong FastAPI worker.
2. **Rule Engine MQTT Thời gian thực:**
   Hệ thống sử dụng thư viện `paho-mqtt` (v2.1) chạy ngầm (background thread) bên trong FastAPI để giao tiếp hai chiều với Cloud MQTT.
3. **Phân Loại Thiết Bị & Cảnh Báo:**
   Hệ thống đọc danh sách thiết bị hợp lệ từ file `data/IoT_device_registry.csv`. Mỗi event được chuẩn hoá, gán `status` (`normal`, `warning`, `danger`, `sensor_error`, `invalid_device`) và `alert_level` (`none`, `medium`, `high`).

## Kiến Trúc (Architecture)

- **API Framework:** `FastAPI`
- **MQTT Client:** `paho-mqtt` (TLS encryption)
- **Containerization:** `Docker` & `Docker Compose` (chỉ gồm 1 service duy nhất là `api`)
- **Port:** `8000` (đã expose ra ngoài)

## Hướng Dẫn Chạy Bằng Docker Compose (Demo Day)

Vào đầu buổi học, khi nhận được IP từ hệ thống mạng chung, bạn chỉ cần sửa file `.env` và chạy đúng 1 lệnh sau:

```bash
# 1. Điền IP hoặc config mới vào biến môi trường (nếu có)
# Lưu ý KHÔNG được dùng localhost cho giao tiếp giữa các nhóm

# 2. Khởi động hệ thống
docker compose up -d --build

# 3. Theo dõi Log thời gian thực
docker compose logs -f
```

## Kiểm Tra Sức Khỏe (Health Check)

Hệ thống bắt buộc lộ ra endpoint `/health`. Các nhóm đối tác sẽ "ping" vào endpoint này trước khi trao đổi dữ liệu:

```bash
curl http://127.0.0.1:8000/health
```

**Kỳ vọng trả về 200 OK:**
```json
{
  "status": "ok",
  "service": "iot-ingestion",
  "version": "1.0.0",
  "mqtt": "connected"
}
```

Khi MQTT chưa kết nối, endpoint trả `503 Service Unavailable` với
`"status": "error"` và `"mqtt": "disconnected"`.

## Chạy Unit Test

```bash
pip install -r requirements.txt
pytest -q
```

Bộ test kiểm tra schema đầu vào, các ngưỡng cảnh báo, ép kiểu an toàn,
thiết bị không hợp lệ, malformed JSON, lọc field debug và trạng thái health.

## Luồng Hoạt Động (Workflow)

1. Service lắng nghe tại Topic: `smart-campus/raw/iot/environment`
2. Nhận gói tin JSON -> Check Registry -> Kiểm lỗi Payload -> Đánh giá mức độ cảnh báo (Danger, Warning, Normal).
3. Đóng gói Payload theo Schema chuẩn -> Bắn lên Topic: `smart-campus/events/sensor` để kích hoạt báo cháy, hệ thống quạt, ...

---
**Nhóm A1 — Smart Campus Operations Platform (FIT4110).** 
