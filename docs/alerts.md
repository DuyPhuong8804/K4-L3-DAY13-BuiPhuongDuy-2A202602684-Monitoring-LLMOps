# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `fast_successful_requests` (latency <= 3000 ms, target 99.5%/28 ngày)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` liên tục 5 phút
- Ảnh hưởng tới người dùng: người dùng chờ lâu hơn 3 giây mới nhận câu trả lời; error budget bị tiêu nhanh
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Latency trên dashboard, xác nhận P95/P99 và TTFT P95 tăng từ lúc nào.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse; so sánh span `retrieval` và `generation` để xem bước nào chậm.
- Mitigation tạm thời: nếu span `retrieval` chậm thì tắt scenario/khôi phục vector store; nếu `generation` chậm sau khi đổi prompt thì rollback label `production` về version cũ.
- Owner: `student-2A202602684`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: guardrail `error_rate_pct_max: 2` và `retrieval_success_rate_pct_min: 90`
- Điều kiện và thời gian duy trì: `request_failed / request_received * 100 > 2` liên tục 5 phút
- Ảnh hưởng tới người dùng: người dùng nhận HTTP 500 và không có câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors, xem breakdown theo `error_type` và retrieval success.
  2. Lọc log `event == "request_failed"`, đọc `error_type`, `tool_name`, `tool_success` và lấy `correlation_id`.
  3. Mở trace cùng `correlation_id`, xem span `retrieval` có level ERROR và status message.
- Mitigation tạm thời: khôi phục dependency lỗi (vector store), tắt scenario `tool_fail` nếu đang bật, giảm tải trong lúc khắc phục.
- Owner: `student-2A202602684`

## Alert 3

- Tên: `CostBudgetBurn`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: guardrail `daily_cost_usd_max: 2.5`
- Điều kiện và thời gian duy trì: tổng `cost_usd` trong 1 giờ vượt 2.5 USD, hoặc `tokens_out` trung bình gấp hơn 2 lần baseline, liên tục 10 phút
- Ảnh hưởng tới người dùng: chưa lỗi ngay, nhưng vượt ngân sách vận hành và có thể dẫn tới giới hạn dịch vụ
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Cost và Tokens, xác nhận `tokens_out` tăng đột biến từ lúc nào.
  2. Lọc log `response_sent` có `tokens_out`/`cost_usd` cao và lấy `correlation_id`.
  3. Mở trace, xem `generation` (usage, cost, prompt version) để biết do prompt mới hay do đầu ra dài bất thường.
- Mitigation tạm thời: rollback prompt `production`, giới hạn `max_tokens`, hoặc tắt scenario `cost_spike` khi đang thử.
- Owner: `student-2A202602684`
