# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Bùi Phương Duy
- **MSSV:** 2A202602684
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/DuyPhuong8804/K4-L3-DAY13-BuiPhuongDuy-2A202602684-Monitoring-LLMOps
- **Commit SHA cuối:** _(điền sau khi commit và push; SHA hiển thị trong ảnh 01)_
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-02684`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08a-trace-metadata.png`, `evidence/08b-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10a-prompt-rollback.png`, `evidence/10b-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 (21 records; 20 thiếu required fields, 20 thiếu enrichment, 0 correlation ID; PII scrub PASSED) | 100/100 sau CP1 (10 correlation ID, 0 PII leak) | Baseline trước khi sửa code CP1 |
| `validate_dashboard.py` | HỢP LỆ 6/6 panel | HỢP LỆ 6/6 panel | Dashboard `scripts/dashboard.py` khớp `config/dashboard.yaml` |
| `pytest` | 22 passed | 26 passed (CP1, thêm test CCCD/thẻ/passport) | |
| Số traces hợp lệ | | ≥ 12 trace `lab-agent-run`, mỗi trace có child `retrieval` và `generation` | Xem ảnh 06 |
| Số PII leak | 0 | 0 | `validate_logs.py`: Potential PII leaks detected: 0 |
| Latency P95 / TTFT P95 | ~152 ms / 50 ms (9 request baseline, đã loại request warm-up đầu tiên ~1.300 ms) | 2,654 ms / 50 ms (gồm request bị `rag_slow`) | Chỉ latency tăng, TTFT không đổi |
| Retrieval success rate | 100% | 100% (`tool_success=true` mọi request) | Sự cố làm chậm chứ không làm lỗi retrieval |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** middleware `app/middleware.py` xoá context cũ, lấy header `x-request-id` hoặc tự sinh `req-<8 hex>`, gắn vào `structlog.contextvars` và `request.state`, rồi trả lại trong response header `x-request-id`. Mọi log trong request tự mang ID; `app/agent.py` ghi thêm vào metadata trace Langfuse.
- **Các metadata được ghi vào structured log:** `ts`, `level`, `service`, `env`, `event`, `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `tool_name`, `tool_success`, `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `payload`.
- **Cách bảo đảm PII được scrub trước khi ghi:** `app/pii.py` có regex cho email, SĐT VN, CCCD 12 số, thẻ tín dụng, hộ chiếu VN; `scrub_text`/`summarize_text` được áp dụng trước khi ghi nên log chỉ chứa `[REDACTED_*]`. `user_id` được băm SHA-256 (12 ký tự đầu) thành `user_id_hash`, không log thô.
- **Cách kiểm chứng kết quả:** `python scripts/validate_logs.py` đạt 100/100 (0 thiếu field, 0 PII leak, correlation ID đầy đủ); `pytest` 26 passed gồm test PII cho CCCD/thẻ/passport; ảnh 05 cho thấy input chứa PII bị thay bằng `[REDACTED_*]`.
- **Correlation ID của ảnh 04 (`evidence/04-structured-log.png`):** `req-04c0ffee` (chụp lại sau CP2; trace `438fca2fb9263db6f9fcac85b51c2a23` dùng cho ảnh 07 và 08a)
- **Correlation ID của ảnh 05 (`evidence/05-pii-redaction.png`):** `req-0e5f6a7b`

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** `.env` dùng cặp key của project Langfuse cá nhân của tôi; trace trong ảnh 06/07 có `correlation_id` khớp log tôi vừa chạy và chỉ xuất hiện trong project này.
- **Cấu trúc root/retrieval/generation observations:** root `lab-agent-run` (agent) là cha của `retrieval` (retriever, metadata `doc_count`) và `generation` (generation, có model, usage, cost và link prompt `day13-chat`). `capture_input/output=False` nên Input/Output trống.
- **Cách nối trace với log:** `correlation_id` của log được ghi vào metadata trace (`lab-agent-run`), nên lọc log theo ID rồi tìm trace có cùng `correlation_id`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** v1 (`baseline`, `production`)
- **Version/label candidate:** v2 (`candidate`), thêm ràng buộc trả lời tối đa 3 câu
- **Trace ID của mỗi version:** baseline v1 `9c8a709902d34b14d22d69f48de67196` (`req-ba5e0003`); candidate v2 `a16542b5cd7e4df1be22177398d1e8e7` (`req-ca9d0004`); cùng input `What is the refund policy?`
- **Trace sau khi promote `production` sang v2:** `a74e3814eb377a9a204a05941de12d1c` (`req-10a00001`, `prompt_label=production`, `prompt_version=2`, generation gắn `day13-chat` v2)
- **Cách promote và rollback `production`:** trên Langfuse UI chuyển nhãn `production` từ v1 sang v2 (ảnh 10a), chờ hết cache prompt 60 giây, gửi request và thấy trace dùng v2; sau đó chuyển nhãn `production` về v1 (ảnh 10b). Không sửa code hay `.env`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Streamlit `scripts/dashboard.py` đọc `data/logs.jsonl` theo `config/dashboard.yaml`: Latency (P50/P95/P99 + TTFT P95), Traffic, Errors (error rate + retrieval success), Cost, Tokens, Quality; time range 60 phút, refresh 30 giây, có đường threshold.
- **SLO và lý do chọn:** 99.5% request `response_sent` có `latency_ms <= 3000` trong 28 ngày. Baseline P95 chỉ khoảng 0.4 s nên ngưỡng 3 s là an toàn, đủ phát hiện sự cố chậm.
- **Cách tính error budget:** 100% - 99.5% = 0.5%. Với 10,000 request trong 28 ngày, tối đa 50 request được phép chậm hơn 3 s hoặc lỗi.
- **Ba alert và runbook tương ứng:** `HighLatencyP95` (warning, 5m), `HighErrorRate` (critical, 5m), `CostBudgetBurn` (warning, 10m); kênh Slack `#k4-l3b-alerts`; runbook ở `docs/alerts.md`.

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1` (cohort K4)
- **Khoảng thời gian điều tra:** 05:59:01–05:59:15 UTC ngày 2026-09-30 (12:59–12:59 giờ VN); baseline 05:58:34–05:58:35 UTC
- **Triệu chứng từ metrics:** ảnh 12 chụp với time range 1440 phút (không phải 60 phút mặc định) vì sự cố xảy ra lúc 12:59 giờ VN, đã ngoài cửa sổ 60 phút; điểm nhô ~1.300 ms ở đầu biểu đồ là request warm-up đầu tiên, không thuộc sự cố. Panel Latency: `latency_ms` của `response_sent` tăng từ khoảng 150–160 ms (baseline, 10 request) lên 2,653 ms (5 request đầu challenge, xếp hàng thêm khiến một số request lâu hơn ở phía client). TTFT giữ 50 ms, tokens_in/out, cost, quality và error rate không đổi (0 lỗi, `tool_success=true`). Chỉ latency đổi nên nguyên nhân nằm ở bước trước generation.
- **Log line và correlation ID liên quan:** `correlation_id=req-6b5eb8c7`, `event=response_sent`, `ts=2026-09-30T05:59:04.902Z`, `feature=monitoring`, `latency_ms=2654`, `ttft_ms=50`, `tokens_out=93`
- **Trace ID và span gây ảnh hưởng:** trace `a64eb300e4733eeec02c38877e4fc734` (cùng `correlation_id`): `lab-agent-run` 2.655 s, trong đó `retrieval` 2.5 s và `generation` 0.153 s. Trace baseline `b9f60553bc6edf5fe18c9414380c3ab0` (`req-9602031c`): `retrieval` ~0 s, `generation` 0.151 s, tổng 0.152 s.
- **Root cause:** bước retrieval (vector store/tìm tài liệu) bị chậm khoảng 2.5 s cho mỗi request; generation không đổi. Đây là incident `rag_slow` do challenge bật.
- **Fix action:** tắt incident (`python scripts/inject_incident.py --disable`), `/health` xác nhận cả ba incident là `false`. Trong sự cố thật: khôi phục hoặc scale vector store, thêm timeout và cache cho retrieval.
- **Preventive measure:** alert `HighLatencyP95` (p95 > 3000 ms trong 5 phút) có runbook kiểm tra span `retrieval`; thêm alert/metric riêng cho thời gian retrieval và timeout cho bước retrieval.

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** dùng `correlation_id` làm khoá chung: sinh ở middleware, đưa vào log và metadata trace, để đi từ metric sang log rồi sang trace mà không phải đoán. Prompt đi qua Langfuse prompt management (v1/v2, nhãn) có fallback cục bộ, nên rollback không cần sửa code.
- **Một lỗi/blocker đã gặp:** (1) test mock thiếu `start_as_current_observation` nên test prompt v4 fail; (2) lỗi bind port 8000 trên Windows khi khởi động uvicorn; (3) file challenge suýt bị commit nên phải dọn lịch sử git và ignore.
- **Cách tìm nguyên nhân và xử lý:** đọc traceback rồi bổ sung method vào mock (26 test pass); kiểm tra tiến trình đang giữ port rồi khởi động lại API; sao lưu công việc, gỡ file khỏi git, khôi phục `.gitignore`, chạy lại test.
- **Cách hiểu luồng Metrics → Logs → Traces:** metric cho biết *có* vấn đề và khi nào (latency tăng); log cho request cụ thể qua `correlation_id`; trace cho biết *ở bước nào* (retrieval 2.5 s, generation 0.15 s). Mỗi lớp thu hẹp phạm vi cho lớp sau.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** prompt version cho phép so sánh v1/v2 trên cùng input và quy lỗi đúng phiên bản; token/cost cho thấy chi phí thay đổi theo prompt; SLO và error budget biến "chậm" thành ngưỡng đo được để alert; rollback nhãn `production` khôi phục ngay mà không cần deploy lại.
- **Điều quan trọng nhất đã học:** nối được metric, log, trace bằng một ID thì điều tra sự cố nhanh và có bằng chứng; alert nên dựa trên triệu chứng người dùng thấy (latency, lỗi, chi phí) chứ không dựa trên nguyên nhân đoán trước.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** dashboard đọc từ `data/logs.jsonl` thay vì hệ thống metrics thật; số liệu lấy từ lần chạy lab ngắn (vài chục request) nên P95 chưa có ý nghĩa thống kê mạnh; chỉ điều tra một incident (`rag_slow`).

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
