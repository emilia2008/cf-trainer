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

### 6. Sync (`POST /api/users/{handle}/sync`)

- **Service tách khỏi route:** `services/sync.py` không biết gì về HTTP (nhận `Session` và client,
  trả `User`); route chỉ đổi exception thành mã lỗi: `HandleNotFound` → 404,
  `CodeforcesError` → **502 Bad Gateway** (lỗi nằm ở dịch vụ phía sau, không phải ở client).
- **Gọi hết API rồi mới ghi DB:** nếu Codeforces lỗi giữa chừng, dữ liệu cũ còn nguyên (có test).
- **Handle không phân biệt hoa thường:** tra cứu bằng `lower(handle)`, lưu cách viết chuẩn của
  Codeforces (`info["handle"]`). Gọi `user.rating`/`user.status` bằng handle chuẩn, nên handle cũ đã
  đổi tên vẫn hoạt động (`user.info` tự tra handle lịch sử).
- **Race khi hai request cùng tạo một user mới:** request thứ hai vi phạm unique → bắt
  `IntegrityError`, rollback, thử lại một lần (lúc này tìm thấy dòng và cập nhật). Có test mô phỏng.
- **Lưu submission "gọn"** (`slim_submission`): chỉ giữ các trường phân tích dùng, cộng
  `relativeTimeSeconds` và `programmingLanguage` cho tính năng sau này. Bỏ thống kê chấm, danh sách
  thành viên... nên JSON nhỏ còn khoảng 1/3. Đánh đổi: muốn dùng trường đã bỏ thì phải sync lại.
- **Kiểm tra handle ở route** bằng regex `^[A-Za-z0-9_.\-]{1,64}$` → 422 khi sai định dạng. Việc này
  còn chặn `a;b`, vì `user.info` coi dấu `;` là phân cách nhiều handle.
- Thời gian lưu là UTC; SQLite làm mất múi giờ, nên schema Pydantic gắn lại UTC khi trả JSON
  (`UTCDateTime`), để frontend không hiểu nhầm thành giờ địa phương.

### 7. Report (`GET /api/users/{handle}/report`) và ProblemCache

- **`build_report` chỉ ghép các hàm trong `analysis.py`,** không viết lại logic phân tích. Phần
  thêm vào chỉ là trình bày: lý do của tag yếu, nhãn verdict, URL bài, `usually_solves_up_to`.
- **ProblemCache:** danh sách bài (~10.000 bài, vài MB JSON) giữ trong bộ nhớ, TTL 24 giờ, `clock`
  truyền qua constructor để test "24 giờ sau" mà không phải chờ.
  - **Giữ lock trong lúc tải:** khi cache rỗng, 5 request đồng thời chỉ tải một lần (tránh
    *cache stampede*); có test bằng thread thật.
  - **Dùng bản cũ khi làm mới thất bại** (stale-on-error): nếu Codeforces sập lúc hết hạn, vẫn
    phục vụ bản cũ và hẹn thử lại sau 5 phút (không gọi lại Codeforces ở *mọi* request).
  - **Giới hạn:** cache nằm trong từng process; chạy 3 server thì có 3 bản và mỗi bản tự tải lại.
    Muốn dùng chung thì đưa vào Redis hoặc một bảng `problems` trong PostgreSQL và làm mới bằng job định kỳ.
- **`get_problem_cache()` là dependency** nên mỗi test dùng một cache mới, không rò trạng thái.
- **Lời khuyên verdict** chỉ hiện khi verdict chiếm *hơn* 15% số lần nộp sai (`share > 0.15`).
- **`usually_solves_up_to`** = chữ cái xa nhất được giải trong ít nhất 50% số contest live.
  Không đòi các chữ liên tiếp từ A, vì có người bỏ B để làm C.
- **URL bài:** `https://codeforces.com/problemset/problem/{contestId}/{index}` như yêu cầu. Riêng
  contest gym (id ≥ 100000) không có trong problemset nên link đó sẽ 404; với gym mình dùng
  `https://codeforces.com/gym/{id}/problem/{index}`. Đây là sai khác có chủ ý để link luôn mở được.
- **Upsolve** trả `total` cùng tối đa 10 bài, để giao diện hiện được "10 of 37".
- **404 trước khi sync** kèm hướng dẫn gọi sync; **502** khi không tải được danh sách bài.

### 8. Test API

- **`TestClient` + `app.dependency_overrides`:** thay `get_session` (SQLite in-memory với
  `StaticPool`), `get_cf_client` (`FakeCodeforces` trả dữ liệu cố định) và `get_problem_cache`
  (cache mới cho mỗi test). Không test nào gọi Codeforces thật.
- **Vì sao `StaticPool`:** với `sqlite://`, mỗi connection mới là một database rỗng riêng.
  `StaticPool` dùng chung một connection, nên dữ liệu ghi trong request còn thấy được trong test.
- **Dữ liệu giả = kịch bản của `test_analysis.py`** nhưng đủ trường như API thật, nên mọi con số
  của báo cáo tính tay được và test so sánh chính xác (target 1400–1600, tag yếu dp/graphs/math,
  gợi ý 10A, 10C, 10F, 10B, upsolve 6B, 4D, 3C...).
- Các test chính: sync thành công; handle không tồn tại → 404; sync hai lần không trùng (đếm dòng);
  report trước sync → 404; report sau sync đủ các phần và đúng số liệu. Thêm: không phân biệt hoa
  thường, handle sai định dạng → 422, Codeforces lỗi → 502 và giữ dữ liệu cũ, race khi insert,
  ngưỡng 15% của lời khuyên verdict, danh sách bài chỉ tải 1 lần qua nhiều report, user chưa có
  hoạt động, link gym.
- Một lỗi gặp khi viết test (lỗi của test, không phải của code): chèn vào đầu list trong vòng lặp
  làm `subs[2]` trỏ sang phần tử khác. Đã sửa bằng cách lấy phần tử cần sao chép ra trước vòng lặp.

### 9. Frontend

- **Cấu trúc:** `App.jsx` giữ trạng thái (`idle | loading | ready | error`), `api.js` gói `fetch`
  (đọc `detail` của FastAPI làm thông báo lỗi), mỗi phần báo cáo là một component trong
  `src/components/`, helper định dạng và màu rank trong `src/format.js`.
- **Chống race ở client:** mỗi lần bấm Analyse tăng một bộ đếm (`useRef`); kết quả của request
  cũ bị bỏ qua, nên gõ nhanh hai handle không bao giờ hiện nhầm báo cáo.
- **Khi Codeforces sập:** nếu sync trả 502 mà server đã có bản lưu, vẫn hiện báo cáo kèm cảnh báo
  "đang dùng dữ liệu lần sync trước".
- **Link chia sẻ được:** handle nằm trên URL (`?handle=tourist`), mở link là tự phân tích.
- **Giữ khung khi tải lại:** báo cáo cũ mờ đi trong lúc tải, không nhấp nháy hay nhảy bố cục.
- **Biểu đồ (theo skill dataviz):** cặp màu xanh dương/cam lấy từ bảng màu đã kiểm định; đã chạy
  validator cho cả chế độ sáng và tối (CVD ΔE ≈ 25, đều đạt). Đường 2px, cột tối đa 24px với khe
  2px, lưới mảnh, tooltip ở mọi biểu đồ, và một bảng dữ liệu tương đương dưới mỗi biểu đồ
  (tooltip không phải cách duy nhất để đọc số). Biểu đồ một series không cần chú giải; biểu đồ hai
  series có chú giải.
- **Màu rank Codeforces** được chỉnh tối hơn ở chế độ sáng (Specialist, Master) và sáng hơn ở chế
  độ tối (Expert), để chữ đạt độ tương phản ≥ 3:1 mà vẫn nhận ra màu quen thuộc.
- **Dark mode:** mặc định theo hệ điều hành; nút chuyển lưu lựa chọn vào `localStorage` (bọc
  try/catch); script nhỏ trong `index.html` áp theme trước lần vẽ đầu tiên để không chớp trắng.
- **Responsive:** lưới 12 cột, dưới 900px còn một cột; bảng cuộn ngang trong khung riêng, nên
  trang không bao giờ cuộn ngang; thanh điều hướng các phần dính trên cùng khi cuộn.
- **Tách chunk:** react và vendor (recharts, d3) riêng khỏi code app (27 kB), nên khi deploy bản mới
  trình duyệt chỉ tải lại phần app.
- `VITE_API_BASE` rỗng khi dev (đi qua Vite proxy `/api` → `:8000`), và đặt URL backend khi deploy riêng.

### 10. Chạy thật với dữ liệu Codeforces

- Đã chạy backend + frontend (Vite proxy), sync và report cho `tourist`, `DmitriyH` (Expert, 1709),
  `MikeMirzayanov` (chưa có rating). `emilia2008` **không tồn tại** trên Codeforces → 404 đúng như
  thiết kế (đã kiểm tra cả trên giao diện); vì vậy dùng các handle trên thay thế.
- Đã chụp màn hình bằng Edge headless (profile tạm) ở chế độ sáng, tối, desktop và màn hình hẹp
  (500px, và khung 375px qua iframe) để soát bố cục.
- **Lỗi thật tìm được và đã sửa:**
  1. **Codeforces trả tiếng Nga** (rank "легендарный гроссмейстер", tên contest/bài tiếng Nga) khi
     không có tham số `lang`. Sửa: client luôn gửi `lang=en`; thêm test.
  2. **Verdict `PARTIAL`** (contest có subtask) chiếm 39% số lần nộp sai của tourist nhưng chưa có
     lời khuyên → thêm `VERDICT_ADVICE["PARTIAL"]`.
  3. **Danh sách chữ cái quá dài** (A–U từ contest kiểu ICPC) và nhiều verdict 0% → giao diện chỉ hiện
     8 chữ cái / 5 verdict đầu, có nút "Show all".
  4. Mốc trục Y lẻ (1550, 55, 165) → tự tính mốc tròn; ô "Target range" bị ngắt dòng trên điện thoại → sửa CSS.
- **Số đo:** sync tourist (5.491 submission, 308 contest) mất khoảng 8 giây (3 lời gọi cách nhau 2 giây,
  cộng thời gian tải); report đầu tiên mất 2,5 giây (tải danh sách bài); các lần sau dùng cache.
- **Quan sát về định nghĩa (không sửa vì đề bài bắt buộc):**
  - tourist: comfort 3500 → target 3600–3800, nhưng bài khó nhất trên Codeforces là 3500, nên không có
    tag yếu và gợi ý; giao diện giải thích lý do.
  - DmitriyH: rating 1709 nhưng đã giải ≥ 3 bài 2500 (luyện tập/upsolve), nên comfort = 2500 và
    target = 2600–2800, quá cao so với rating thi đấu. Đây là điểm yếu của định nghĩa `comfort_rating`
    (xem phần "Điểm yếu và cách cải thiện").
  - `live_contests` (405) của tourist lớn hơn số contest có rating (308), vì có cả contest không tính
    rating mà vẫn thi trực tiếp.

### 11. Docker

- **Máy không cài Docker** (`docker: command not found`), nên không chạy được `docker compose up`
  ở local. Thay vào đó, CI chạy job `docker` trên GitHub: build cả hai image, `docker compose up`,
  rồi gọi `/api/health` trực tiếp và qua nginx (xem bước 12).
- **Backend image:** `python:3.12-slim`, chạy bằng user không phải root, `CMD` đọc `$PORT` (Render,
  Railway, Koyeb truyền cổng qua biến này), `--proxy-headers` vì chạy sau reverse proxy.
  `.dockerignore` loại `.venv`, test, file `.db`, `.env`.
- **Frontend image (multi-stage):** stage `node:22-alpine` chạy `npm ci && npm run build`; stage
  `nginx:alpine` chỉ chứa thư mục `dist` (image nhỏ, không có Node). `nginx.conf`:
  - `/api/` → `proxy_pass ${BACKEND_URL}`: trình duyệt gọi cùng origin nên **không cần CORS**.
    `BACKEND_URL` được điền lúc container khởi động (cơ chế `templates/` + `envsubst` của image
    nginx), nên cùng một image dùng được ở nơi khác.
  - `/assets/` cache 1 năm (`immutable`, vì tên file có hash); `index.html` thì `no-cache`;
    fallback SPA bằng `try_files $uri /index.html`.
- **Compose:** `db` (postgres:16) có healthcheck `pg_isready`; `backend` chờ `db` *healthy*, có
  healthcheck gọi `/api/health` bằng Python (image slim không có curl); `frontend` chờ backend *healthy*.
  Dữ liệu PostgreSQL nằm trong volume `pgdata`, nên tắt container không mất dữ liệu.
- **Vì sao backend gọi DB bằng host `db` chứ không phải `localhost`:** mỗi container có network
  namespace riêng; `localhost` trong container backend là chính nó. Compose tạo DNS nội bộ theo tên service.
- Đã kiểm tra `package-lock.json` (tạo trên Windows) có đủ binary rollup/esbuild cho Linux (gnu và
  musl), nên `npm ci` chạy được trong Alpine và trên Ubuntu của CI.
