# Ghi chú phỏng vấn CF Trainer

File này ghi lại mọi quyết định thiết kế và lý do. Bản đầy đủ (độ phức tạp, luồng dữ liệu,
câu hỏi phỏng vấn) được hoàn thiện ở bước tài liệu cuối cùng.

## Nhật ký quyết định

### 0. Thiết lập Git

- **Tình huống:** thư mục `Desktop/cf-trainer` là một repo Git chỉ chứa một *gitlink* (submodule
  không có `.gitmodules`) trỏ tới repo bên trong `Desktop/cf-trainer/cf-trainer`. Commit gitlink đó
  (`bd74ec4`) đã được push lên `origin/main`, nên trên GitHub chỉ thấy một submodule hỏng.
  Code thật và lịch sử (3 commit) nằm ở repo bên trong, chưa có remote.
- **Quyết định:** dùng repo bên trong làm repo chính, thêm `origin`, rồi
  `git merge -s ours --allow-unrelated-histories origin/main`.
- **Lý do:** giữ nguyên lịch sử trên remote nên push là fast-forward, không cần `--force`
  (không phá dữ liệu trên GitHub). Strategy `ours` giữ nguyên cây thư mục của repo bên trong,
  nên gitlink bị loại bỏ.
- **Phương án khác:** `git push --force` cho lịch sử gọn hơn nhưng ghi đè remote; chép file ra
  repo ngoài thì mất 3 commit lịch sử. Cả hai đều kém hơn.
- **Việc còn lại:** repo ngoài (`Desktop/cf-trainer/.git`) giờ không còn cần thiết; nên xóa
  thư mục `.git` đó để VS Code không hiển thị hai repo lồng nhau.

### 1. Môi trường

- Dùng `py -3.12` để tạo `backend/.venv` (máy có cả 3.11 và 3.12; dự án yêu cầu 3.12).
- `sqlalchemy>=2.0,<3`: pip cài 2.1.x, tương thích API 2.0; chặn trên để tránh thay đổi phá vỡ ở bản 3.
- Starlette 1.7 cảnh báo `Using httpx with starlette.testclient is deprecated; install httpx2`.
  Việc cài gói `httpx2` bị chặn bởi chính sách quyền của phiên làm việc, nên mình **không** thêm nó;
  cảnh báo vô hại và test vẫn chạy đúng. Nếu muốn hết cảnh báo: thêm `httpx2` vào requirements
  (gói chính thức của tác giả httpx, repo `pydantic/httpx2`). Client Codeforces vẫn dùng `httpx`.
- `.gitattributes` với `eol=lf`: máy Windows đang bật `core.autocrlf=true`; ép LF trong repo để
  Docker image và CI (Linux) nhận cùng một nội dung file.

### 2. Database: snapshot JSON (thiết kế B)

- **Bảng:** `users` (một dòng mỗi handle) và `user_snapshots` (một dòng mỗi user: `submissions`,
  `rating_history` dạng JSON, `fetched_at`). `user_snapshots.user_id` là khóa ngoại **unique**.
- **Vì sao snapshot:** các hàm trong `analysis.py` nhận đúng dữ liệu thô của API; báo cáo luôn đọc
  toàn bộ lịch sử của một user một lần, không cần truy vấn SQL vào bên trong submissions.
  Snapshot cho code ít nhất và dữ liệu trung thực nhất.
- **Không trùng khi sync lại:** ràng buộc unique trên `user_id` đảm bảo ở tầng database chỉ có một
  snapshot mỗi user; service cập nhật dòng cũ thay vì thêm dòng mới.
- **Chạy trên cả SQLite và PostgreSQL:** `JSON().with_variant(JSONB(), "postgresql")`; JSONB nhỏ hơn
  và đọc nhanh hơn trên PostgreSQL.
- **Phương án khác (bảng chuẩn hóa `submissions`, `rating_changes`):** truy vấn SQL được (ví dụ
  "số bài giải mỗi tháng"), nhưng phải viết nhiều code ánh xạ hơn và sync lại phải xóa/chèn hàng
  nghìn dòng. Với nhu cầu hiện tại (đọc nguyên khối để phân tích) thì không đáng.
- **Nhược điểm:** không truy vấn chéo nhiều user được (ví dụ "tag nào khó nhất với mọi user").
  Khi cần, có thể thêm bảng chuẩn hóa song song mà không bỏ snapshot.
- `normalize_database_url`: Render/Neon trả URL dạng `postgres://`, SQLAlchemy sẽ hiểu là
  psycopg2 (không cài); hàm này đổi sang `postgresql+psycopg://` (psycopg 3).
- Test luôn ép `DATABASE_URL=sqlite://` trong `conftest.py` để không bao giờ đụng vào `dev.db`.
  Đặt `TEST_DATABASE_URL` thì chính các test đó chạy trên PostgreSQL (CI làm việc này).

### 3. Codeforces client

- **Rate limiter dùng chung cả process** (`_shared_limiter`): mọi `CodeforcesClient` dùng chung một
  `RateLimiter`. Nếu mỗi client có lock riêng thì hai request đến cùng lúc (FastAPI chạy route `def`
  trong threadpool) vẫn có thể gọi Codeforces sát nhau và vi phạm giới hạn.
- **Giữ lock trong lúc `sleep`:** các luồng xếp hàng và đi lần lượt, mỗi lượt cách nhau ít nhất 2 giây.
  Không giữ lock khi gửi HTTP, vì chỉ cần giãn thời điểm *bắt đầu* các request.
- **Lịch được tính chính xác:** `_next_allowed = start + interval`, nên dù `sleep` ngủ quá một chút,
  lịch vẫn không trôi.
- **Đồng hồ thô trên Windows:** Python 3.12 trên Windows dùng `GetTickCount64` cho `time.monotonic`
  (độ phân giải 15,6 ms), nên limiter có thể bắt đầu sớm tối đa 1 tick (không cộng dồn). Với khoảng
  2 giây, sai số dưới 1%. Trên Linux (production) độ phân giải tính bằng nano giây.
- **`clock` và `sleep` truyền qua constructor:** test kiểm tra lịch chờ bằng đồng hồ giả, không phải chờ thật.
- **Đọc body JSON trước status code:** Codeforces trả lỗi `FAILED` với HTTP 400 *kèm JSON*. Nếu gọi
  `raise_for_status()` trước thì sẽ mất comment "handle not found". Chỉ khi không có body hợp lệ
  (ví dụ trang HTML lỗi 502) mới báo lỗi theo status code.
- **Nhận diện handle không tồn tại:** comment bắt đầu bằng `handle:`/`handles:` (lỗi tham số handle,
  kể cả sai định dạng) hoặc chứa "handle ... not found" → `HandleNotFound`; còn lại là `CodeforcesError`.
- **Tự thử lại khi "Call limit exceeded"** (tối đa 2 lần, mỗi lần đi qua limiter). Lỗi này chỉ xảy ra
  khi có process khác dùng chung IP (ví dụ nhiều server), vì limiter đã giới hạn trong process.
- **`get_cf_client()` với `lru_cache`:** một client mỗi process (dùng chung connection pool và
  limiter); test thay nó bằng client giả qua `app.dependency_overrides`.
- `problemset()` chỉ gán `solvedCount` khi có thống kê; nếu thiếu thì để trống, và `recommend` coi là 0.

### 4. analysis.py

- Giữ nguyên tên, chữ ký và docstring của mọi hàm; `test_analysis.py` không bị sửa và xanh toàn bộ
  (24/24). Mình không thấy test nào sai đặc tả.
- **Helper `_problem_histories`:** gom submissions theo bài (một lượt duyệt), lưu lần nộp sớm nhất
  và cờ đã giải. `difficulty_profile`, `tag_stats`, `verdict_breakdown` dùng chung, nên định nghĩa
  "first try" nhất quán ở mọi nơi.
- **Lần nộp sớm nhất** so theo `(creationTimeSeconds, id)`: không phụ thuộc thứ tự đầu vào (API trả
  mới nhất trước), và hai lần nộp trong cùng một giây được phân xử bằng id (id tăng dần theo thời gian).
- **Bỏ qua submission đang chấm** (`verdict` thiếu hoặc `TESTING`) ở mọi phân tích theo bài, không
  chỉ ở `verdict_breakdown`. Một lần nộp chưa có kết quả không được coi là "lần thử đầu bị sai".
- **`rank_info` dùng `bisect_right`** trên danh sách ngưỡng: O(log R), và đúng tại biên (1200 → Pupil).
- **`weak_topics` làm tròn điểm tới 12 chữ số khi sắp xếp:** 0.6/3 = 0.19999999999999998 < 0.2 trên
  float, nên hai điểm bằng nhau trên giấy sẽ không hòa và luật "hòa thì theo tên tag" bị phá.
  Có test riêng chứng minh (test fail nếu bỏ làm tròn).
- **`recommend` dùng `heapq.nsmallest(limit, ...)`:** O(P log limit) thay vì sắp xếp toàn bộ O(P log P);
  kết quả giống hệt `sorted(...)[:limit]` (Python đảm bảo điều này trong tài liệu).
- **`worst_drop` = delta nhỏ nhất**, đúng theo docstring (chỉ lịch sử rỗng mới trả `None`). Nếu user
  chưa bao giờ tụt rating thì giá trị này dương; giao diện hiển thị "No drops yet" trong trường hợp đó.
- `test_analysis_edge_cases.py` bổ sung 17 test cho biên rank, thứ tự đầu vào, submission đang chấm,
  hòa điểm float, giới hạn bao gồm hai đầu của target range, tag `*special` trong gợi ý.

### 5. Tài liệu học (resources.py)

- **Mọi đường dẫn sâu đều được kiểm tra bằng HTTP** (mã 200 *và* `<title>` khớp chủ đề). Trước đó đã
  thử một đường dẫn bịa trên từng site để chắc chúng trả 404 thật (không phải trang 200 giả kiểu SPA).
- 5 đường dẫn mình đoán đã trả 404 và bị loại: `usaco.guide/gold/combinatorics`,
  `/gold/string-hashing`, `/gold/topo-sort`, `/bronze/complete-search`, `/bronze/intro-math`.
  Đây là bằng chứng rằng việc "đoán URL" rất dễ sai.
- Với CSES chỉ dùng trang chủ `cses.fi/problemset/`, tiêu đề ghi rõ section cần làm
  (ví dụ "Dynamic Programming section").
- Đủ 19 tag yêu cầu, thêm `hashing`; tag khác dùng `GENERAL_RESOURCES` (3 trang chủ).
- Có test không cần mạng: đủ tag bắt buộc, mọi URL là https và thuộc 3 domain được phép.
- `VERDICT_ADVICE` thêm lời khuyên cho CE, bị hack (`CHALLENGED`) và ILE (bài interactive);
  `VERDICT_LABELS` đổi mã verdict thành chữ dễ đọc cho giao diện.
- **Giới hạn:** link có thể chết theo thời gian; nên có một job định kỳ (không chạy trong test)
  kiểm tra lại link.
