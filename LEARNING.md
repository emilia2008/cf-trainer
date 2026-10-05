# Tài liệu học cho CF Trainer

Học theo đúng thứ tự. Mỗi phần có: cần hiểu gì, học ở đâu, và câu hỏi phỏng vấn bạn phải tự trả lời được.

---

## 0. Nền tảng web (khoảng 2 giờ)

**Cần hiểu:**
- HTTP: request/response, các method GET/POST, status code (200, 404, 429, 500, 501).
- REST API là gì, JSON là gì.
- Môi trường ảo Python (`venv`) và `requirements.txt`.

**Học ở đâu:** MDN Web Docs: "An overview of HTTP" và "HTTP response status codes".

**Câu hỏi tự kiểm tra:** Khi trình duyệt gọi `GET /api/users/tourist/report`, chuyện gì xảy ra từ đầu đến cuối?

---

## 1. FastAPI

**Cần hiểu:**
- Định nghĩa route, tham số đường dẫn và query.
- Dependency injection: `Depends(get_session)` cho mỗi request một phiên database riêng.
- `HTTPException` để trả lỗi đúng chuẩn; Pydantic model để định nghĩa JSON trả về.
- Trang `/docs` tự sinh, dùng để thử API.

**Học ở đâu:** FastAPI Tutorial (fastapi.tiangolo.com/tutorial), từ "First Steps" đến "Dependencies" và "SQL (Relational) Databases".

**Câu hỏi phỏng vấn:**
- Vì sao mỗi request cần một database session riêng?
- Vì sao tách logic ra `services/` thay vì viết hết trong route?

---

## 2. Cơ sở dữ liệu và SQLAlchemy

**Cần hiểu:**
- Bảng, khóa chính, khóa ngoại, ràng buộc unique, index.
- Chuẩn hóa dữ liệu (normalisation) và khi nào lưu JSON nguyên khối thì hợp lý hơn.
- SQLAlchemy ORM: model, `session.add`, `session.commit`, `select(...)`.
- Kiểu cột JSON (PostgreSQL có `JSONB`).

**Việc cần làm:** chọn thiết kế A hoặc B trong `app/models.py`. Vẽ sơ đồ ra giấy trước khi code.

**Học ở đâu:** SQLBolt (sqlbolt.com, làm hết bài tập); SQLAlchemy 2.0 "ORM Quick Start".

**Câu hỏi phỏng vấn:**
- Vì sao bạn chọn bảng chuẩn hóa (hoặc snapshot JSON)? Nhược điểm của lựa chọn đó là gì?
- Đồng bộ lại một user thì làm sao không bị dữ liệu trùng?

---

## 3. Codeforces API và rate limit

**Cần hiểu:**
- 4 endpoint dùng trong project: `user.info`, `user.rating`, `user.status`, `problemset.problems`. Mở thử trên trình duyệt để xem dữ liệu thật, ví dụ `https://codeforces.com/api/user.rating?handle=tourist`.
- Rate limit: Codeforces chỉ cho khoảng 1 request mỗi 2 giây.
- Gọi HTTP bằng `httpx`, xử lý timeout và lỗi; test bằng `httpx.MockTransport` để không gọi mạng thật.

**Học ở đâu:** codeforces.com/apiHelp; httpx Quickstart (python-httpx.org/quickstart).

**Câu hỏi phỏng vấn:**
- Nếu 20 người bấm Analyse cùng lúc, rate limit của bạn còn đúng không?
- Khi Codeforces sập thì app phản ứng thế nào?

---

## 4. Phân tích dữ liệu: phần lõi của project

Đây là phần **quan trọng nhất**, phỏng vấn sẽ hỏi sâu nhất. Bạn tự viết các hàm trong `app/analysis.py` cho đến khi `tests/test_analysis.py` xanh hết.

**Cần hiểu:**
- **Hệ thống rating của Codeforces:** rating của bạn và rating của bài toán, các mốc rank (1200 Pupil, 1400 Specialist, 1600 Expert, 1900 Candidate Master, 2100 Master...).
- **Gom nhóm và đếm:** dict, set, `defaultdict`, `Counter`. Đếm bài **khác nhau** (dùng set theo `problem_key`), không đếm số lần nộp.
- **Sắp xếp nhiều tiêu chí:** `sorted(..., key=lambda x: (-a, b, c))`.
- **Tỉ lệ và trọng số:** `tag_importance` là tỉ lệ, `weak_topics` là điểm có trọng số. Hiểu vì sao công thức `importance / (1 + solved)` hợp lý và điểm yếu của nó.
- **Trường hợp biên:** bài không có rating, user chưa có rating, danh sách rỗng, chia cho 0.

**Học ở đâu:**
- Tài liệu Python: `collections` (Counter, defaultdict), `dataclasses`, "Sorting HOW TO".
- Blog "How to practice on Codeforces" trên codeforces.com (đọc để hiểu lời khuyên luyện bài theo rating +100 đến +300).

**Câu hỏi phỏng vấn:**
- Giải thích công thức tag yếu. Một tag xuất hiện 2% ở mức mục tiêu thì có nên luyện không? Bạn xử lý thế nào?
- Độ phức tạp của `weak_topics` là bao nhiêu? Có thể làm nhanh hơn không?
- Gợi ý bài của bạn có thể sai ở đâu? (Gợi ý: rating bài không chính xác tuyệt đối; tag không đầy đủ.)
- Vì sao dùng `solvedCount` làm tiêu chí phụ khi xếp hạng gợi ý?

---

## 5. Cache và test

**Cần hiểu:**
- Danh sách toàn bộ bài Codeforces rất lớn (vài nghìn bài) và ít thay đổi: cache trong bộ nhớ, hết hạn sau 24 giờ.
- Truyền hàm lấy thời gian vào class cache để test không phải chờ thật.
- pytest: test hàm thuần, test API bằng `TestClient` + `app.dependency_overrides`.

**Học ở đâu:** pytest "Get Started"; FastAPI docs "Testing" và "Testing Dependencies with Overrides".

**Câu hỏi phỏng vấn:**
- Cache của bạn có vấn đề gì nếu chạy 3 server cùng lúc? Khi nào cần Redis?

---

## 6. React frontend và biểu đồ

**Cần hiểu:**
- Component, props, state (`useState`), gọi API bằng `fetch`, trạng thái loading/lỗi.
- Vẽ biểu đồ bằng thư viện Recharts: `LineChart` cho lịch sử rating, `BarChart` cho số bài theo độ khó.
- Vite proxy: trong lúc phát triển, `/api` được chuyển sang backend ở cổng 8000.

**Học ở đâu:** react.dev/learn ("Quick Start", "Describing the UI", "Adding Interactivity"); recharts.org (Examples).

**Câu hỏi phỏng vấn:** Dữ liệu đi từ Codeforces đến biểu đồ trên màn hình qua những bước nào?

---

## 7. Docker, CI và deploy

**Cần hiểu:**
- Docker image và container, `Dockerfile`, `docker compose`.
- Biến môi trường để cấu hình (không ghi mật khẩu vào code).
- GitHub Actions: mỗi lần push, CI tự chạy test.

**Học ở đâu:** Docker "Get Started"; GitHub Actions "Quickstart".

**Câu hỏi phỏng vấn:** Nếu số người dùng tăng 100 lần, phần nào của hệ thống gặp vấn đề trước?

---

## Mở rộng (sau khi đã nộp đơn)

- **AI coach:** gửi số liệu phân tích cho một LLM qua API để viết đoạn nhận xét và kế hoạch luyện tập theo tuần. Chú ý chi phí và giữ API key ở biến môi trường.
- **Theo dõi tiến bộ:** lưu báo cáo theo tuần, so sánh tag yếu tuần này với tuần trước.
- **So sánh với người khác:** đối chiếu hồ sơ của bạn với trung bình những người vừa lên rank tiếp theo.
- **Tốc độ trong contest:** dùng `relativeTimeSeconds` để đo thời gian giải từng bài trong contest.
