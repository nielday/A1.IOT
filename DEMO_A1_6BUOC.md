# DEMO A1 — IoT Ingestion · 6 BƯỚC (theo mẫu báo cáo của thầy)

> A1 nhận dữ liệu cảm biến qua **MQTT** (không phải REST). Vì vậy bước 1–5 chạy
> như mọi nhóm, **riêng bước 6** chứng minh nghiệp vụ bằng MQTT (log / dashboard),
> KHÔNG dùng `curl POST` (A1 không có REST input → sẽ 404).

Thông tin nhanh:
```
Service : iot-ingestion (FastAPI)   Port: 8000
Radmin IP A1 : 26.58.120.30
Input  (MQTT) : smart-campus/raw/iot/environment   (simulator thầy bắn)
Output (MQTT) : smart-campus/events/sensor          (A1 publish cho A5, A6)
```

---

## 1. Kiểm tra container đang chạy
```powershell
docker compose ps
```
→ `fit4110-api-demo-day` ở trạng thái **Up (healthy)**.

## 2. Kiểm tra health local
```powershell
curl http://localhost:8000/health
```
→ `{"status":"ok","service":"iot-ingestion","version":"1.0.0","mqtt":"connected"}`

## 3. Kiểm tra IP máy demo
```powershell
ipconfig
```
→ Lấy IPv4 / hoặc IP Radmin **26.58.120.30** (để nhóm khác & giảng viên gọi sang).

## 4. Kiểm tra gọi chéo qua mạng
Từ máy khác (hoặc nhờ giảng viên) gọi:
```powershell
curl http://26.58.120.30:8000/health
```
→ Trả 200 = máy khác chạm tới A1 được.

## 5. Xem log xử lý
```powershell
docker compose logs --tail=100
```
→ Thấy luồng: `Received raw data for device: ...` rồi
`Processed status: warning, published to smart-campus/events/sensor`.

## 6. Test nghiệp vụ / chứng minh input → output  (A1 dùng MQTT)
A1 KHÔNG nhận input qua REST nên không dùng `curl POST`. Chứng minh input→output
bằng 1 trong các cách sau (chọn cách C cho thầy xem là trực quan nhất):

**Cách A — Log: raw VÀO → processed RA**
```powershell
docker compose logs --tail=20
```
Giải thích: `raw-iot-xxxx` (input từ simulator) → A1 gắn `status/alert_level/reason`
→ publish `events/sensor` (output cho A5, A6).

**Cách B — Xem chi tiết payload A1 publish lên topic**
```powershell
pip install paho-mqtt   # nếu chưa có
python tools/watch_sensor.py
```
→ In full JSON mỗi event A1 đẩy lên `events/sensor`.

**Cách C — Dashboard trực quan (khuyên dùng khi demo)**
```
Mở trình duyệt: http://localhost:8000/dashboard
```
→ Hiển thị realtime: thiết bị, các chỉ số, và kết luận `status/alert_level/reason`,
màu theo mức độ (xanh normal / vàng warning / đỏ danger).

---

## Câu chốt nghiệp vụ
> "A1 nhận dữ liệu cảm biến thô từ simulator qua **MQTT**, thực hiện
> **validate → chuẩn hóa → đối chiếu thiết bị → phân loại theo ngưỡng**, rồi gắn
> 3 field kết luận **`status` / `alert_level` / `reason`** và publish lên
> `smart-campus/events/sensor`. **A5 và A6 nhận cùng dữ liệu này**: A6 đọc `status`,
> nếu `danger/warning/invalid_device` thì gọi A7 gửi cảnh báo; A5 lưu DB và thống kê.
> Nhờ 3 field kết luận đó, các nhóm khác **không cần tự hiểu các con số** — đọc
> `status` là xử lý được. Vì A1 dùng MQTT (pub/sub) nên bước 6 em chứng minh
> input→output bằng log và dashboard, thay cho lệnh `curl POST`."

---

## Bảng ngưỡng phân loại của A1 (để giải thích status)
| status | alert_level | điều kiện |
|---|---|---|
| danger | high | temp ≥ 40 \| co2 ≥ 1800 \| smoke ≥ 1.0 |
| warning | medium | temp ≥ 35 \| hum ≥ 85 \| co2 ≥ 1200 \| smoke ≥ 0.5 \| battery < 20 |
| invalid_device | high | thiết bị không có trong registry |
| sensor_error | medium | cảm biến lỗi / giá trị null |
| normal | none | không rơi vào các trường hợp trên |
