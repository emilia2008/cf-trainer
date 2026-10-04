# Tài liệu học cho CF Trainer

Học theo đúng thứ tự. Mỗi phần có: cần hiểu gì, học ở đâu, và câu hỏi phỏng vấn bạn phải tự trả lời được.

---

## 0. Nền tảng web (Ngày 6, khoảng 2 giờ)

**Cần hiểu:**
- HTTP: request/response, các method GET/POST, status code (200, 201, 404, 429, 500, 501).
- REST API là gì, JSON là gì.
- Môi trường ảo Python (`venv`) và `requirements.txt`.

**Học ở đâu:**
- MDN Web Docs: "An overview of HTTP" và "HTTP response status codes".

**Câu hỏi tự kiểm tra:** Khi trình duyệt gọi `GET /api/users/tourist/stats`, chuyện gì xảy ra từ đầu đến cuối?

---

## 1. FastAPI (Ngày 6)

**Cần hiểu:**
- Định nghĩa route với `@router.get`, tham số đường dẫn và query.
- Dependency injection: `Depends(get_session)` cho mỗi request một phiên database riêng.
- `HTTPException` để trả lỗi đúng chuẩn.
- Trang `/docs` tự sinh (OpenAPI), dùng để thử API.

**Học ở đâu:**
- FastAPI Tutorial (fastapi.tiangolo.com/tutorial): đọc từ "First Steps" đến "Dependencies" và "SQL (Relational) Databases".

**Câu hỏi phỏng vấn:**
- Vì sao mỗi request cần một database session riêng?
- Vì sao chọn FastAPI thay vì Flask hay Django?

---

## 2. Cơ sở dữ liệu và SQLAlchemy (Ngày 6–7)

**Cần hiểu:**
- Bảng, khóa chính (primary key), khóa ngoại (foreign key), ràng buộc unique.
- Index: vì sao cột `handle` cần index (tìm kiếm O(log n) thay vì quét cả bảng).
- Quan hệ một-nhiều (một user giải nhiều bài) và nhiều-nhiều (một bài có nhiều tag, một tag thuộc nhiều bài).
- SQLAlchemy ORM: định nghĩa model, `session.add`, `session.commit`, `select(...)`.
- SQLite cho phát triển, PostgreSQL khi chạy thật.

**Việc cần làm:** thiết kế 2 bảng còn thiếu trong `app/models.py`. Vẽ sơ đồ ra giấy trước khi code.

**Học ở đâu:**
- SQLBolt (sqlbolt.com): làm hết các bài tập, khoảng 1–2 giờ.
- SQLAlchemy 2.0 "ORM Quick Start" (docs.sqlalchemy.org).

**Câu hỏi phỏng vấn:**
- Vẽ schema của bạn và giải thích từng bảng.
- Lưu tag thành bảng riêng hay chuỗi phân cách bằng dấu phẩy? Ưu nhược điểm?
- Làm sao đảm bảo một bài không bị lưu hai lần cho cùng một user?

---

## 3. Gọi API bên ngoài và rate limit (Ngày 7)

**Cần hiểu:**
- Gọi HTTP bằng `httpx`, xử lý timeout và lỗi.
- Rate limit: Codeforces chỉ cho khoảng 1 request mỗi 2 giây. Vượt quá sẽ bị chặn.
- Cách tự giới hạn: nhớ thời điểm gọi lần cuối, chờ nếu chưa đủ 2 giây.

**Học ở đâu:**
- Codeforces API docs (codeforces.com/apiHelp).
- httpx Quickstart (python-httpx.org/quickstart).

**Câu hỏi phỏng vấn:**
- Nếu 50 người đăng ký cùng lúc thì rate limit của bạn còn đúng không? (Gợi ý: nhiều request song song, cần lock hoặc hàng đợi.)
- Khi Codeforces sập thì app của bạn phản ứng thế nào?

---

## 4. Logic lõi, cache và test (Ngày 8)

**Cần hiểu:**
- Vì sao tách logic thuần (`stats.py`) khỏi database và mạng: dễ test, dễ thay đổi.
- Unit test với pytest. Test trong `tests/test_stats.py` đã viết sẵn, bạn viết code cho đến khi tất cả đều xanh.
- Cache: danh sách toàn bộ bài Codeforces rất lớn và ít thay đổi, nên chỉ tải lại tối đa mỗi ngày một lần. Cache trong bộ nhớ (biến + thời điểm hết hạn) là đủ cho MVP.

**Học ở đâu:**
- pytest "Get Started" (docs.pytest.org).
- Đọc về "cache invalidation" và "TTL cache".

**Câu hỏi phỏng vấn:**
- Bạn định nghĩa "tag yếu" thế nào? Có cách nào tốt hơn không?
- Cache của bạn hết hạn khi nào? Có vấn đề gì nếu chạy nhiều server cùng lúc?

---

## 5. React frontend (Ngày 9–10)

**Cần hiểu:**
- Component, props, state (`useState`), gọi API bằng `fetch`.
- Hiển thị danh sách bằng `.map()`, điều kiện loading và lỗi.
- Vite proxy: trong lúc phát triển, `/api` được chuyển sang backend ở cổng 8000.

**Học ở đâu:**
- react.dev/learn: đọc "Quick Start", "Describing the UI", "Adding Interactivity".

**Câu hỏi phỏng vấn:** Dữ liệu đi từ Codeforces đến màn hình của người dùng qua những bước nào?

---

## 6. Docker, CI và deploy (Ngày 10–12)

**Cần hiểu:**
- Docker image và container, `Dockerfile`, `docker compose` chạy nhiều service cùng lúc.
- Biến môi trường để cấu hình (không ghi mật khẩu vào code).
- GitHub Actions: mỗi lần push, CI tự chạy test.
- Deploy: đưa backend + PostgreSQL và frontend lên một dịch vụ hosting có gói miễn phí. So sánh vài dịch vụ trước khi chọn vì điều khoản gói miễn phí hay thay đổi.

**Học ở đâu:**
- Docker "Get Started" (docs.docker.com/get-started).
- GitHub Actions "Quickstart" (docs.github.com/actions).

**Câu hỏi phỏng vấn:**
- Vì sao dùng Docker?
- Nếu số người dùng tăng 100 lần, phần nào của hệ thống gặp vấn đề trước?

---

## 7. Người dùng thật (Ngày 11–12)

- Đăng link lên nhóm UTS ProgSoc và đội ICPC, nhờ mọi người dùng thử.
- Ghi lại số người dùng và phản hồi, sửa những lỗi họ gặp.
- Cập nhật README với link và số người dùng. Đây là dòng có giá trị nhất trên CV.

## Mở rộng (sau khi đã nộp đơn)

- Đồng bộ tự động định kỳ (background job).
- Migration bằng Alembic thay cho `create_all`.
- Biểu đồ rating theo thời gian.
- Đăng nhập bằng Codeforces handle + xác minh.
