# Runbook Demo Day - Nhóm A1 IoT Ingestion

File này là checklist thao tác trên máy demo. Không ghi mật khẩu HiveMQ thật
vào tài liệu hoặc ảnh chụp.

## 1. Chuẩn bị trước khi đến lớp

- Cài và mở Docker Desktop.
- Đảm bảo repo mới nhất nằm trên máy demo.
- Mang sạc laptop và điện thoại/router phát hotspot.
- Nhận credential HiveMQ qua kênh riêng.
- Điền credential thật vào file `.env`, không sửa `.env.example`.
- Chạy thử toàn bộ quy trình ít nhất một lần.

Kiểm tra `.env` có các biến:

```env
APP_HOST=0.0.0.0
APP_PORT=8000
SERVICE_NAME=iot-ingestion
SERVICE_VERSION=1.0.0

MQTT_HOST=<host-do-giang-vien-cung-cap>
MQTT_PORT=8883
MQTT_USERNAME=<username-thuc>
MQTT_PASSWORD=<password-thuc>
MQTT_INPUT_TOPIC=smart-campus/raw/iot/environment
MQTT_OUTPUT_TOPIC=smart-campus/events/sensor
```

## 2. Khởi động tại Demo Day

Mở terminal tại thư mục dự án:

```bash
cd /mnt/e/baitap1/demo-day-team-iot
docker compose up -d --build
docker compose ps
```

Kết quả mong đợi:

```text
fit4110-api-demo-day ... Up ... (healthy) ... 0.0.0.0:8000->8000/tcp
```

Nếu trạng thái còn `health: starting`, chờ khoảng 10-30 giây rồi chạy lại:

```bash
docker compose ps
```

## 3. Kiểm tra Health

```bash
curl -i http://127.0.0.1:8000/health
```

Kết quả thành công:

```text
HTTP/1.1 200 OK
```

```json
{
  "status": "ok",
  "service": "iot-ingestion",
  "version": "1.0.0",
  "mqtt": "connected"
}
```

Chụp màn hình và lưu thành:

```text
reports/health-local.png
```

## 4. Kiểm tra Luồng MQTT

Theo dõi log:

```bash
docker compose logs -f api
```

Phải thấy các dòng tương tự:

```text
Connected to HiveMQ successfully.
Subscribed to topic: smart-campus/raw/iot/environment
Received raw data for device: ...
Processed status: normal, published to smart-campus/events/sensor
```

Nhấn `Ctrl+C` chỉ để thoát màn hình log. Container vẫn tiếp tục chạy.

Lưu log làm minh chứng:

```bash
docker compose logs --no-color api > reports/logs-compose.txt
```

## 5. Chụp Minh chứng

Danh sách file cần có:

```text
reports/
├── docker-compose-ps.png
├── health-local.png
├── mqtt-subscribe-evidence.png
├── integration-evidence.png
├── logs-compose.txt
└── readiness-checklist.md
```

Nội dung từng ảnh:

- `docker-compose-ps.png`: Docker Desktop hoặc terminal hiển thị container healthy.
- `health-local.png`: lệnh `curl` trả HTTP 200 và `mqtt=connected`.
- `mqtt-subscribe-evidence.png`: MQTTX/MQTT Explorer nhận payload trên
  `smart-campus/events/sensor`.
- `integration-evidence.png`: màn hình nhóm Analytics/Core nhận đúng event của
  nhóm A1.

Không để mật khẩu MQTT xuất hiện trong ảnh.

## 6. Phối hợp với Analytics/Core

Gửi cho nhóm nhận dữ liệu:

```text
Broker: HiveMQ được giảng viên cung cấp
Port: 8883
Protocol: MQTTS
Topic: smart-campus/events/sensor
QoS: 1
Contract: contracts/mqtt-contract.md
```

Yêu cầu nhóm đối tác:

1. Subscribe topic output.
2. Xác nhận nhận được event có `source_service=team-iot`.
3. Kiểm tra đủ các field theo contract.
4. Chụp màn hình có topic và payload để làm minh chứng tích hợp chéo.

## 7. Kịch bản trình bày ngắn

1. Giới thiệu luồng: Simulator -> HiveMQ raw topic -> A1 -> processed topic.
2. Cho xem `docker compose ps`: container healthy.
3. Gọi `/health`: HTTP 200, MQTT connected.
4. Cho xem log nhận raw event.
5. Cho xem processed payload không có `scenario_hint_for_teacher`.
6. Giải thích các trạng thái `normal`, `warning`, `danger`, `sensor_error`,
   `invalid_device`.
7. Cho xem Analytics/Core nhận event thật.
8. Giải thích khi MQTT mất kết nối, `/health` trả HTTP 503 và worker tự reconnect.

## 8. Demo Health 503 an toàn

Không sửa hoặc làm hỏng file `.env` chính ngay trước phần demo quan trọng.
Chỉ trình diễn lỗi sau khi đã có đầy đủ ảnh và minh chứng luồng thành công.

Cách đơn giản:

1. Sao lưu `.env`.
2. Tạm đổi `MQTT_PORT` sang một port không hợp lệ.
3. Chạy lại stack.
4. Gọi `/health` và chụp HTTP 503.
5. Khôi phục `.env` ngay và chạy lại stack.
6. Xác nhận `/health` trở về HTTP 200.

## 9. Xử lý sự cố nhanh

### `/health` trả 503

```bash
docker compose logs --no-color --tail=100 api
```

Kiểm tra:

- Máy có Internet không.
- `MQTT_HOST`, port, username và password có đúng không.
- Topic có viết đúng tuyệt đối không.
- Đồng hồ hệ thống có đúng ngày giờ không.

### Container không xuất hiện

```bash
docker compose up -d --build
docker compose ps -a
docker compose logs --no-color api
```

### Port 8000 bị chiếm

Tìm và dừng ứng dụng đang dùng port 8000, sau đó:

```bash
docker compose down
docker compose up -d
```

### Không nhận được raw event

- Xác nhận log đã có `Subscribed to topic`.
- Chờ ít nhất 1-2 phút.
- Kiểm tra đúng input topic.
- Nhờ giảng viên kiểm tra simulator.

### Nhóm Analytics/Core không nhận được output

- Hai nhóm đối chiếu cùng broker, credential, topic và QoS.
- Dùng MQTTX/MQTT Explorer subscribe trực tiếp để xác định phía nào lỗi.
- Cho đối tác xem `contracts/mqtt-contract.md`.

## 10. Kết thúc

Sau khi demo xong và đã lưu đủ minh chứng:

```bash
docker compose logs --no-color api > reports/logs-compose.txt
docker compose down
```

Kiểm tra lại checklist:

```text
checklists/readiness-checklist.md
```

Chỉ đánh dấu hoàn thành khi đã có ảnh nhóm Analytics/Core nhận event thật.
