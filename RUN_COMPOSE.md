# Hướng dẫn Chạy Docker Compose cho Demo Day (Nhóm A1)

## 1. Chuẩn bị Mạng (Theo chuẩn Radmin VPN)
Theo yêu cầu mới của môn học, chúng ta sẽ sử dụng **Radmin VPN** thay vì bắt buộc dùng chung một Wifi Hotspot.

1. Đảm bảo máy tính Windows (máy demo chính) đã cài đặt Radmin VPN và join vào Network chung của lớp (ví dụ: `FIT4110-DEMO-A`).
2. Ghi nhận IP Radmin của máy bạn (ví dụ `26.x.x.x`) để gửi cho các nhóm khác ping `/health`.
3. Mở quyền tường lửa cho port 8000 bằng cách chạy PowerShell (Quyền Admin):
   `netsh advfirewall firewall add rule name="FIT4110 Demo API 8000" dir=in action=allow protocol=TCP localport=8000`
4. Copy file mẫu thành `.env` rồi điền cấu hình HiveMQ thật (file `.env` không có sẵn trong repo vì đã được `.gitignore`):
   ```bash
   cp .env.example .env
   ```
   Sau đó mở `.env` điền `MQTT_USERNAME`, `MQTT_PASSWORD`... Hệ thống sẽ tự dùng Internet của bạn bắn thẳng lên Cloud.

## 2. Khởi động hệ thống
Mở terminal tại thư mục gốc của dự án (`demo-day-team-iot`) và gõ:

```bash
docker compose up -d --build
```

Hệ thống sẽ tải image và build code Python. Quá trình này sẽ mất khoảng vài phút cho lần chạy đầu tiên.

## 3. Kiểm tra trạng thái
```bash
docker compose logs -f
```
Bạn phải nhìn thấy dòng:
```text
INFO - Connected to HiveMQ successfully.
INFO - Subscribed to topic: smart-campus/raw/iot/environment
```

## 4. Test Healthcheck
```bash
curl -s http://127.0.0.1:8000/health
```
Kết quả phải là HTTP 200 OK và:
```json
{"status": "ok", "service": "iot-ingestion", "version": "1.0.0", "mqtt": "connected"}
```
*(Nếu trả về HTTP 503, hãy kiểm tra lại file `.env` hoặc xem máy tính có kết nối được ra Internet không).*

## 5. Minh chứng Tích hợp (Tự Chụp)
- Dùng MQTTX, subscribe vào topic output `smart-campus/events/sensor` để chụp hình bắt được dữ liệu chuẩn hóa từ hệ thống.
- Yêu cầu nhóm Analytics (A5) cho xem màn hình họ bắt được dữ liệu của nhóm mình. Chụp lại màn hình đó đưa vào báo cáo!