# Ghi chú phỏng vấn CF Trainer

Tài liệu này dành cho bạn khi ôn phỏng vấn: mọi quyết định thiết kế và lý do, độ phức tạp từng hàm
phân tích, luồng dữ liệu, điểm yếu và cách cải thiện, cùng 20 câu hỏi hay gặp kèm gợi ý trả lời.

**Mục lục**

1. Tóm tắt dự án và số liệu
2. Luồng dữ liệu từ Codeforces đến màn hình
3. Nhật ký quyết định (theo từng bước build)
4. Độ phức tạp các hàm trong `analysis.py`
5. Điểm yếu và cách cải thiện
6. Về `test_analysis.py`
7. 20 câu hỏi phỏng vấn kèm gợi ý trả lời

---

## 1. Tóm tắt dự án và số liệu

CF Trainer là web app phân tích sâu **một** tài khoản Codeforces: rank và số điểm còn thiếu, xu hướng
rating, độ khó thoải mái và khoảng nên luyện, thống kê từng tag, 5 tag yếu kèm tài liệu học, thói quen
nộp bài, danh sách upsolve, và 10 bài gợi ý cụ thể.

- **Backend:** FastAPI + SQLAlchemy 2 + Pydantic + httpx; SQLite khi dev, PostgreSQL khi chạy Docker/production.
- **Frontend:** React 19 + Vite + Recharts, CSS thuần, có dark mode và responsive.
- **Hạ tầng:** Docker Compose (PostgreSQL + API + nginx), GitHub Actions với 4 job.
- **Test:** 114 test backend (24 đặc tả trong `test_analysis.py` + 16 edge case, 17 client, 7 cache,
  3 model, 20 API, 22 resources, 5 app/config). Không test nào gọi Codeforces thật.
- **CI:** pytest trên SQLite, pytest trên PostgreSQL (service container), `npm ci && npm run build`,
  và smoke test toàn bộ stack Docker Compose. Cả 4 job đều xanh.
- **Số đo thật:** sync tourist (5.491 submission, 308 contest) khoảng 8 giây (bị chặn bởi rate limit
  2 giây/lần gọi); report đầu tiên 2,5 giây (gồm tải danh sách bài), các lần sau dùng cache;
  snapshot của tourist chiếm 1,9 MB.

Câu giới thiệu mẫu (phỏng vấn bằng tiếng Anh thì bạn nên tự nói lại bằng lời của mình):

> "I built CF Trainer, a web app that analyses one Codeforces account and tells the user which
> topics hold their rating back and exactly which problems to practise next. The core is a set of
> pure, unit-tested analysis functions; around it there's a FastAPI backend that syncs data under
> Codeforces' rate limit, stores a JSON snapshot per user in PostgreSQL, and caches the
> 10,000-problem list for a day; and a React front end with charts. It's tested in CI against both
> SQLite and PostgreSQL, and the whole stack runs with Docker Compose."

## 2. Luồng dữ liệu từ Codeforces đến màn hình

```
Trình duyệt (React)
  │ 1. người dùng nhập handle, bấm Analyse  (App.jsx: status = loading)
  │ 2. POST /api/users/{handle}/sync        (api.js; dev: Vite proxy, Docker: nginx, prod: VITE_API_BASE)
  ▼
FastAPI route sync_user  ── kiểm tra handle bằng regex (422 nếu sai)
  ▼
services/sync.sync_user
  │ 3. CodeforcesClient: user.info → user.rating → user.status  (lang=en)
  │    mỗi lời gọi đi qua RateLimiter dùng chung (≥ 2 giây giữa hai lần gọi)
  │    FAILED "not found" → HandleNotFound → 404;  lỗi khác → CodeforcesError → 502
  │ 4. slim_submission: chỉ giữ các trường cần dùng
  │ 5. ghi users + user_snapshots (một snapshot mỗi user, cập nhật tại chỗ), commit
  ▼
Trình duyệt nhận SyncResult → 6. GET /api/users/{handle}/report
  ▼
FastAPI route get_report
  │ 7. find_user (không phân biệt hoa thường); chưa sync → 404
  │ 8. ProblemCache.get(client.problemset): bộ nhớ, TTL 24 giờ; hết hạn → problemset.problems
  │    (gộp solvedCount từ problemStatistics)
  │ 9. build_report: gọi các hàm thuần trong analysis.py
  │    rank_info, rating_trend, difficulty_profile → comfort_rating → target_range,
  │    tag_stats, weak_topics (dùng tag_importance), verdict_breakdown, contest_level,
  │    upsolve_list, recommend; ghép resources.py (link học, lời khuyên verdict)
  │ 10. Pydantic Report → JSON
  ▼
Trình duyệt: setReport(data) → mỗi phần là một component
  OverviewCard · RatingChart (LineChart) · DifficultyChart (BarChart + vùng target) · WeakTopics
  Recommendations · Habits · UpsolveList · TopicTable  → Recharts vẽ SVG
```

Chi tiết đáng nhớ: dữ liệu Codeforces được **lưu lại**, nên report không phải gọi lại API của user
(chỉ cần danh sách bài, vốn đã được cache). Mọi lời gọi API trong sync diễn ra **trước** khi ghi DB,
nên sync lỗi giữa chừng không làm hỏng dữ liệu cũ.

---

## 3. Nhật ký quyết định

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
- `test_analysis_edge_cases.py` bổ sung 15 test cho biên rank, thứ tự đầu vào, submission đang chấm,
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
- Đã chụp màn hình bằng Edge headless (profile tạm): chế độ sáng và tối ở 1280px, toàn bộ báo cáo ở
  500px (Edge headless không cho cửa sổ hẹp hơn), và khung 375px qua iframe (thanh trên cùng và trang
  chào mừng vừa khít; trong iframe headless, báo cáo không kịp tải xong trước lúc chụp).
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
  - DmitriyH: rating 1709 nhưng đã giải ≥ 3 bài 2500 (luyện tập/upsolve), nên với định nghĩa ban đầu
    comfort = 2500 và target = 2600–2800, quá cao so với rating thi đấu. Sau đó bạn yêu cầu đổi ngưỡng
    (xem mục 14).
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

### 12. CI (GitHub Actions)

- **4 job:** `backend` (pytest trên SQLite), `backend-postgres` (cùng bộ test, chạy trên service container
  `postgres:16` qua `TEST_DATABASE_URL`), `frontend` (`npm ci && npm run build`), và `docker` (chạy sau hai
  job đầu): `docker compose up --build --wait`, rồi gọi `/api/health` trực tiếp và qua nginx, kiểm tra
  fallback SPA, và gọi report của một user không tồn tại để chắc API truy vấn được PostgreSQL (phải trả 404).
  Job docker **không** gọi Codeforces.
- **Vì sao chạy test trên cả PostgreSQL:** SQLite và PostgreSQL khác nhau ở JSON/JSONB, múi giờ, cách báo
  lỗi unique. Bug kiểu "chạy được trên máy, hỏng trên production" thường nằm ở đây.
- **Kiểm tra CI không cần `gh`:** repo public nên đọc trạng thái qua GitHub REST API
  (`/commits/{sha}/check-runs`) bằng `curl`.
- **Nâng phiên bản action:** CI cảnh báo `checkout@v4`, `setup-python@v5`, `setup-node@v4` chạy trên Node 20
  (đã deprecated). Mình đọc `action.yml` của các tag mới để xác nhận chúng chạy Node 24, rồi chuyển sang
  `checkout@v6`, `setup-python@v6`, `setup-node@v6`. Sau đó CI không còn cảnh báo.
- `concurrency` hủy lần chạy cũ khi có push mới trên cùng nhánh; `permissions: contents: read` (quyền tối thiểu).
- CI ở các commit `0ec5ad2`, `1b65262` (trước khi implement `analysis.py`) bị đỏ là **đúng dự kiến**:
  khi đó test đặc tả chưa có code để chạy. Từ commit `4cb66e1` trở đi, CI luôn xanh.

### 13. Tài liệu

- `README.md` (tiếng Anh): các phần của báo cáo, quy tắc phân tích, tech stack, cấu trúc, cách chạy,
  biến môi trường, API, Design notes (lưu trữ, rate limit, cache, giới hạn của weak score).
- `DEPLOY.md` (tiếng Anh): Neon (PostgreSQL) + Render (backend Docker, static site). Thông tin gói miễn
  phí được tra lại vào ngày 05/10/2026: Render free web service ngủ sau 15 phút, có 750 giờ/tháng; từ
  01/08/2026 workspace Hobby chỉ còn 5 GB bandwidth/tháng; PostgreSQL free của Render hết hạn sau 30 ngày,
  nên chọn Neon (0,5 GB, không hết hạn). Mình không tạo tài khoản dịch vụ nào.

### 14. Đổi ngưỡng comfort rating: hơn 20 bài (theo yêu cầu của bạn)

- **Yêu cầu:** phải giải *hơn 20 bài* ở một mức rating thì mức đó mới được tính là "thoải mái" và
  mới đẩy target lên cao hơn. Trước đây chỉ cần 3 bài.
- **Cách làm:** thêm hằng số `COMFORT_MIN_SOLVED = 21` trong `analysis.py` và dùng làm giá trị mặc
  định của `comfort_rating(profile, min_solved=...)`. Tên hàm và tham số giữ nguyên; `test_analysis.py`
  vẫn truyền `min_solved=3`/`6` tường minh nên không phải sửa và vẫn xanh.
- **"Hơn 20" hiểu theo nghĩa đen là ≥ 21.** Muốn "từ 20 bài trở lên" thì chỉ cần đổi hằng số thành 20.
- API trả thêm `difficulty.comfort_min_solved`, để giao diện ghi "highest rating with 21+ solves" theo
  đúng con số trong backend (không ghi cứng ở frontend).
- **Ảnh hưởng trên dữ liệu thật:** DmitriyH (rating 1709) từ target 2600–2800 xuống 2300–2500 (giải 25 bài
  ở mức 2200); tourist không đổi (61 bài ở mức 3500); MikeMirzayanov không đổi (target theo mức sàn 800).
- Test mới: biên 20 so với 21 bài ở cấp hàm, và test API cho thấy target chỉ tăng lên 1600–1800 khi có
  21 bài ở mức 1500 (20 bài thì vẫn theo rating 1350, tức 1400–1600).

### 15. Deploy và kiểm tra bản live (06/10/2026)

- **Bạn đã deploy:** frontend `https://cf-trainer-1.onrender.com` (Render static site), backend
  `https://cf-trainer-1rga.onrender.com` (Render web service; địa chỉ này mình đọc ra từ bundle JavaScript,
  nơi `VITE_API_BASE` được nhúng lúc build), database Neon.
- **Kết quả kiểm tra (gọi thật từ máy ở Việt Nam):**
  - `/api/health` 200 (~0,8 giây, chủ yếu là độ trễ mạng sang server Render); `/docs` 200.
  - CORS đúng: preflight và GET đều trả `access-control-allow-origin: https://cf-trainer-1.onrender.com`.
  - Sync DmitriyH: 200 trong 7,5 giây (3 lời gọi Codeforces cách nhau 2 giây). Report: 200 trong 2,2 giây;
    gọi lại 1,8 giây. Instance free chỉ có 0,1 CPU và phải đọc snapshot ~0,9 MB từ Neon mỗi lần, nên nếu
    cần nhanh hơn thì cache report theo `last_synced_at` (xem phần 5).
  - Handle không tồn tại → 404; handle sai định dạng → 422; link lạ (`/some/spa/route`) vẫn mở app (rewrite đúng).
  - Báo cáo live dùng ngưỡng comfort mới (DmitriyH: comfort 2200, target 2300–2500), tức backend đang
    chạy đúng code mới nhất. Ảnh chụp trang live đã đưa vào README (`docs/screenshot.png`).
- **Lỗi tìm thêm và đã sửa:**
  1. **Image backend crash nếu thiếu `DATABASE_URL`:** container chạy bằng `appuser` nhưng `/app` thuộc root,
     nên SQLite không tạo được `dev.db` và `create_all` lỗi ngay lúc khởi động. Bản của bạn không bị vì đã
     đặt Neon. Sửa: `chown appuser:appuser /app`; CI thêm bước chạy image *không có* `DATABASE_URL` và chờ
     `/api/health`.
  2. **Thông báo trống ở "Practise next"** sai lý do với user rating rất cao (tourist): giờ ghi rõ là target
     range không có bài nào, thay vì "không có tag yếu".
- **Dữ liệu trong ảnh README:** DmitriyH là tài khoản Codeforces công khai (dữ liệu từ API public). Khi bạn có
  handle của mình, nên thay ảnh bằng báo cáo của chính bạn.

---

## 4. Độ phức tạp các hàm trong `analysis.py`

Ký hiệu: `S` = số submission của user, `U` = số bài khác nhau user đã nộp (`U ≤ S`), `P` = số bài trên
Codeforces (~10.000), `T` = số tag mỗi bài (thường ≤ 5, coi là hằng số nhỏ), `K` = số tag khác nhau (~37),
`H` = số contest có rating, `B` = số mức rating (≤ 28), `C` = số contest live, `L` = số chữ cái bài (≤ 26),
`R` = số rank (10), `X` = số bài cần upsolve, `k`/`limit` = số kết quả trả về.

| Hàm | Thời gian | Bộ nhớ thêm | Ghi chú |
|---|---|---|---|
| `problem_key`, `real_tags` | O(1), O(T) | O(T) | |
| `_problem_histories` (helper) | O(S) | O(U) | một lượt duyệt; lần nộp sớm nhất so theo `(time, id)` |
| `rank_info` | O(log R) | O(1) | `bisect_right` trên danh sách ngưỡng |
| `solved_problems` | O(S) | O(U) | `setdefault`: mỗi bài được giữ một lần |
| `rating_trend` | O(H) | O(H) | danh sách delta |
| `difficulty_profile` | O(S + B log B) | O(B) | thực tế là O(S) |
| `comfort_rating` | O(B) | O(1) | |
| `target_range` | O(1) | O(1) | |
| `tag_stats` | O(S + U·T + K log K) | O(U + K) | |
| `tag_importance` | O(P·T) | O(K) | quét toàn bộ danh sách bài |
| `weak_topics` | O(P·T + S + U·T + K log K) | O(U + K) | gọi `tag_importance` và `solved_problems` |
| `verdict_breakdown` | O(S) | O(U) | |
| `contest_level` | O(S + L log L) | O(C·L) | tập contest theo từng chữ cái |
| `upsolve_list` | O(S + X log X) | O(U) | |
| `recommend` | O(P·T + P log limit) | O(P) | `heapq.nsmallest`, không sắp xếp cả danh sách |

**Cả một report:** O(S + P·T). Với S = 5.000 và P = 10.000 chỉ khoảng 10^5 phép tính, mất vài mili giây.
Thời gian thật nằm ở mạng (rate limit của Codeforces), không nằm ở thuật toán.

**Nếu phải nhanh hơn** (ví dụ phục vụ rất nhiều người):

- Đánh chỉ mục danh sách bài theo mức rating ngay khi làm mới cache. Khi đó `tag_importance` và
  `recommend` chỉ quét các bài trong target range (khoảng 300 trong 10.000), tức O(P_range·T).
- Tính sẵn `tag_importance` cho từng target range (chỉ có khoảng 30 range khả dĩ) mỗi lần làm mới cache: O(1) khi tra.
- Cache cả report theo `(user, last_synced_at, phiên bản cache)`, vì report không đổi nếu không sync lại.

---

## 5. Điểm yếu và cách cải thiện

**Về phân tích (định nghĩa bắt buộc nên mình giữ nguyên, nhưng phải biết nói về chúng):**

1. **`comfort_rating` nhạy với ngoại lệ.** Với ngưỡng ban đầu (3 bài), DmitriyH (rating 1709) có comfort
   2500 và target 2600–2800. Đã giảm bớt bằng cách nâng ngưỡng lên hơn 20 bài (mục 14), nhưng target vẫn có
   thể cao hơn rating thi đấu (DmitriyH: 2300–2500), và ngưỡng cố định không phân biệt người mới với người
   đã giải hàng nghìn bài. *Cải thiện tiếp:* yêu cầu thêm tỉ lệ AC ở mức đó ≥ 50%, chỉ xét 6–12 tháng gần
   đây, hoặc chặn `base ≤ rating + 300`.
2. **Target vượt thang rating của bài.** Từ khoảng 3300 trở lên, range (ví dụ 3600–3800 của tourist)
   không có bài nào, nên không có tag yếu hay gợi ý. *Cải thiện:* kẹp range vào [800, rating cao nhất của bài].
3. **Weak score bỏ qua lần thử thất bại và thời gian.** Một tag thử 10 lần không giải được có điểm bằng tag
   chưa bao giờ đụng tới. *Cải thiện:* đưa tỉ lệ thất bại vào công thức, giảm trọng số bài giải đã lâu,
   hoặc so tỉ lệ giải từng tag của user với trung bình những người cùng rating (cần dữ liệu nhiều user).
4. **Các tag không độc lập** (`dp` và `math` hay đi cùng nhau), nên top 5 có thể trùng ý. *Cải thiện:*
   đa dạng hóa kết quả (kiểu MMR) hoặc gom tag hay đi cùng nhau thành cụm.
5. **Tag và rating của Codeforces không hoàn hảo:** tag thiếu, bài mới chưa có rating (bị loại khỏi phân tích).
6. **Bài trùng giữa Div. 1 và Div. 2** có id khác nhau, nên có thể gợi ý một bài mà user đã giải ở bản kia.
   *Cải thiện:* gộp theo `(name, rating)`.
7. **Mẫu số của `contest_level`** chỉ đếm những contest có submission. Contest đăng ký mà không nộp bài nào
   thì không được đếm, nên tỉ lệ bị thổi phồng một chút. *Cải thiện:* lấy thêm contest từ `user.rating`.
8. **`solvedCount` làm tiêu chí phụ** ưu tiên bài cũ, nhiều người giải (dễ tìm editorial). Đó là ưu
   điểm, nhưng cũng nghiêng về bài cũ.

**Về hệ thống:**

9. **Rate limiter và cache nằm trong từng process.** Chạy nhiều instance thì mỗi instance có giới hạn và
   cache riêng. *Cải thiện:* Redis (token bucket dùng chung, cache dùng chung) hoặc một worker duy nhất
   giữ toàn bộ lưu lượng tới Codeforces.
10. **Sync chạy đồng bộ** (5–10 giây) và chiếm một thread của threadpool (mặc định 40 thread), nên nhiều
    người sync cùng lúc phải xếp hàng sau rate limit. *Cải thiện:* hàng đợi job (RQ/Arq/Celery) với
    `POST /sync` trả 202 cùng job id, frontend hỏi trạng thái định kỳ hoặc dùng SSE.
11. **Sync luôn tải lại toàn bộ `user.status`.** *Cải thiện:* sync tăng dần (`user.status` có tham số
    `from`/`count`), chỉ lấy submission mới hơn id lớn nhất đã lưu.
12. **Không có chống lạm dụng:** ai cũng có thể bấm sync liên tục. *Cải thiện:* cooldown theo handle (ví
    dụ không sync lại trong 5 phút mà trả bản đã lưu), rate limit theo IP.
13. **`create_all` thay vì migration.** *Cải thiện:* Alembic khi schema bắt đầu thay đổi.
14. **Frontend chưa có test.** *Cải thiện:* Vitest + Testing Library cho component, Playwright cho E2E
    (luồng nhập handle → báo cáo, với API giả).
15. **Link tài liệu có thể chết theo thời gian.** *Cải thiện:* job định kỳ kiểm tra link (không chạy trong unit test).
16. **Cảnh báo của Starlette** về `httpx2` trong TestClient (xem bước 1): vô hại; thêm `httpx2` vào
    requirements nếu muốn hết cảnh báo.

---

## 6. Về `test_analysis.py`

- **Không sửa file này.** Cả 24 test đều xanh với code hiện tại, và mình không thấy test nào sai đặc tả.
- Nhận xét nhỏ, không phải lỗi: test của `rating_trend` chỉ có trường hợp có tụt rating. Theo docstring,
  `worst_drop` là delta nhỏ nhất, nên với lịch sử toàn tăng nó là số **dương**. Đúng đặc tả, nhưng tên
  dễ gây hiểu nhầm, nên giao diện hiện "No drops yet" khi `worst_drop ≥ 0`.
- `test_analysis_edge_cases.py` (16 test) phủ những chỗ đặc tả chưa nói (kể cả ngưỡng hơn 20 bài mới): biên rank, thứ tự đầu vào,
  hòa trong cùng một giây, submission đang chấm, hòa điểm float, hai đầu của range, `*special` trong gợi ý.

---

## 7. 20 câu hỏi phỏng vấn kèm gợi ý trả lời

**1. "Tell me about a project you're proud of."**
Dùng câu mẫu ở phần 1, rồi chọn *một* điểm kỹ thuật để đào sâu (rate limit dùng chung, cache có
stale-on-error, hoặc bug float khi xếp hạng). Kết bằng một điểm yếu bạn biết và cách sửa: người phỏng vấn
thích người tự thấy giới hạn của mình.

**2. Vì sao lưu snapshot JSON thay vì bảng chuẩn hóa? Nhược điểm?**
Report luôn đọc toàn bộ lịch sử của một user, và các hàm phân tích nhận đúng dữ liệu thô của API, nên
snapshot ít code nhất và không phải ánh xạ. Nhược điểm: không truy vấn SQL được bên trong (ví dụ "số bài
giải theo tháng" hay thống kê nhiều user). Khi cần thì thêm bảng chuẩn hóa song song.

**3. Sync lại làm sao không trùng? Hai request sync cùng lúc thì sao?**
`user_snapshots.user_id` unique, nên service cập nhật dòng cũ. Nếu hai request cùng tạo một user mới,
request thứ hai dính `IntegrityError`; mình rollback, tra lại rồi cập nhật dòng vừa được tạo (có test mô
phỏng). Ràng buộc đặt ở tầng DB, nên đúng kể cả khi code có bug.

**4. 20 người bấm Analyse cùng lúc, rate limit còn đúng không?**
Trong một process thì đúng: một `RateLimiter` dùng chung, lock được giữ trong lúc chờ, nên các request
xếp hàng cách nhau 2 giây (có test bằng thread thật). Người thứ 20 phải chờ khoảng 20 × 3 × 2 = 120 giây,
nên trải nghiệm kém. Chạy nhiều process thì sai, vì mỗi process có limiter riêng. Cách sửa: limiter dùng
chung qua Redis, hoặc hàng đợi job với một worker gọi Codeforces.

**5. Codeforces sập thì app phản ứng thế nào?**
Client đổi lỗi mạng/HTTP thành `CodeforcesError` → API trả 502 kèm thông báo rõ. Cache danh sách bài vẫn
phục vụ bản cũ nếu làm mới thất bại, và hẹn thử lại sau 5 phút. Frontend: nếu sync trả 502 mà đã có bản
lưu thì vẫn hiện báo cáo cũ kèm cảnh báo. Sync không ghi gì khi lỗi, nên dữ liệu cũ còn nguyên.

**6. Giải thích công thức weak score. Một tag chỉ xuất hiện 2% thì có nên luyện không?**
`importance` = mức độ phổ biến ở mức bạn sắp lên; chia cho `1 + solved_in_range` để tag bạn đã giải nhiều
thì giảm ưu tiên; `+1` tránh chia cho 0 và làm điểm giảm dần. Tag 2% bị loại bởi `min_importance = 0.05`:
luyện nó ít có lợi cho rating. Điểm yếu: xem phần 5, mục 3–4.

**7. Độ phức tạp của `weak_topics` và `recommend` với 10.000 bài và 5.000 submission? Nhanh hơn được không?**
`weak_topics`: O(P·T + S); `recommend`: O(P·T + P log 10) nhờ `heapq.nsmallest`. Khoảng 10^5 phép tính,
vài ms. Muốn nhanh hơn: chỉ mục bài theo rating, tính sẵn importance cho từng range khi làm mới cache,
cache report (phần 4).

**8. `first_try_rate` tính thế nào? Có bẫy gì?**
API trả mới nhất trước, nên không được lấy phần tử đầu. Phải lấy lần nộp có `creationTimeSeconds` nhỏ
nhất; hai lần nộp cùng giây thì so theo `id`. Submission đang chấm (`TESTING`) bị bỏ qua, không bị coi là
lần thử đầu bị sai.

**9. Gợi ý bài có thể sai ở đâu?**
Rating bài là ước lượng; tag thiếu hoặc sai; bài trùng Div. 1/Div. 2; target có thể cao hơn rating thi đấu
(ngưỡng hơn 20 bài đã giảm bớt việc vài bài khó giải lúc luyện tập đẩy target lên); user có thể đã giải bài đó ở tài khoản khác. Cách kiểm chứng: hỏi người dùng thật
xem gợi ý có hữu ích không, rồi đo tỉ lệ họ giải các bài được gợi ý.

**10. Vì sao dùng `solvedCount` làm tiêu chí phụ?**
Nhiều người giải thường nghĩa là đề rõ ràng, có editorial và lời giải tham khảo, nên là thước đo chất
lượng rẻ. Nhược điểm: nghiêng về bài cũ. Nó chỉ là tiêu chí phụ, sau số tag yếu khớp và độ khó.

**11. Cache danh sách bài: chạy 3 server thì sao? Khi nào cần Redis? Lần đầu gọi report mất bao lâu?**
Mỗi server một bản và tự tải lại (3 lần gọi Codeforces mỗi ngày, chấp nhận được). Cần Redis khi muốn
dùng chung giữa các instance, khi restart thường xuyên (ví dụ Render free ngủ sau 15 phút), hoặc khi
rate limit dùng chung. Lần đầu khoảng 2,5 giây vì tải vài MB JSON; có thể làm ấm cache bằng job nền lúc khởi động.

**12. Vì sao truyền hàm lấy thời gian vào `ProblemCache` và `RateLimiter`?**
Để test xác định được và chạy tức thì: test "24 giờ sau hết hạn" chỉ cần cộng số vào đồng hồ giả,
không phải `sleep`. Đây là dependency injection ở mức hàm.

**13. Làm sao test API mà không gọi mạng? Vì sao cần `StaticPool`?**
`app.dependency_overrides` thay `get_cf_client` bằng client giả, `get_session` bằng SQLite in-memory,
`get_problem_cache` bằng cache mới. Client thật thì test bằng `httpx.MockTransport`. `StaticPool`: mỗi
connection tới `sqlite://` là một database rỗng riêng, nên cần dùng chung một connection để dữ liệu ghi
trong request còn thấy được trong test.

**14. Vì sao mỗi request cần một database session riêng?**
Session giữ transaction và identity map, và không an toàn khi dùng chung giữa các thread. Mỗi request
một session thì lỗi của request này không làm hỏng request khác, và session luôn được đóng (dependency
dùng `yield` + `finally`).

**15. Vì sao tách logic ra `services/` thay vì viết hết trong route?**
Route chỉ lo HTTP (tham số, mã lỗi); service lo nghiệp vụ và test được mà không cần HTTP. Phân tích còn
tách xa hơn nữa: hàm thuần, không DB, không mạng. Nhờ đó 39 test phân tích chạy trong 0,06 giây.

**16. Số người dùng tăng 100 lần, phần nào gặp vấn đề trước?**
Rate limit của Codeforces (một lời gọi mỗi 2 giây, mỗi sync tốn 3 lời gọi), nên tối đa khoảng 10 sync
mỗi phút cho mỗi IP. Sau đó là threadpool bị chiếm bởi các sync đang chờ. Cách sửa: hàng đợi job, sync
tăng dần, cooldown theo handle, cache report. Database và CPU phân tích còn rất xa giới hạn.

**17. Dữ liệu đi từ Codeforces đến biểu đồ qua những bước nào?**
Xem sơ đồ ở phần 2: sync (3 lời gọi API, rate limit, lưu snapshot) → report (đọc snapshot, danh sách bài
từ cache, các hàm phân tích, Pydantic) → React state → component → Recharts SVG.

**18. Vite proxy giải quyết vấn đề gì? CORS là gì? Production xử lý thế nào?**
Khi dev, frontend ở `:5173` và backend ở `:8000` là hai origin khác nhau. Proxy giúp trình duyệt chỉ thấy
một origin, nên không cần CORS. Ở Docker, nginx làm việc tương tự (`/api` → backend). Khi deploy tách
domain: `VITE_API_BASE` trỏ tới backend lúc build, và backend đặt `CORS_ORIGINS` đúng domain frontend.

**19. Image khác container thế nào? Vì sao backend gọi DB bằng host `db`? Dữ liệu PostgreSQL ở đâu khi tắt container?**
Image là bản đóng gói chỉ đọc; container là một lần chạy của image. Trong Compose, mỗi service là một host
trong mạng nội bộ có DNS theo tên service; `localhost` trong container backend là chính nó. Dữ liệu nằm
trong named volume `pgdata`, nên còn nguyên khi container bị xóa (trừ khi `down --volumes`).

**20. Kể một bug bạn đã tìm ra và sửa.**
Chọn một trong ba: (a) chạy với API thật thì thấy rank trả về bằng tiếng Nga, vì Codeforces mặc định tiếng
Nga khi thiếu `lang=en`. Đây là bug mà mock không bao giờ lộ ra, và bài học là luôn chạy thử với dữ liệu
thật. (b) Lỗi float: 0.6/3 < 0.2 làm luật hòa theo tên tag sai; sửa bằng làm tròn khi so sánh, và viết test
chứng minh. (c) Codeforces trả HTTP 400 *kèm JSON* khi handle không tồn tại; gọi `raise_for_status()`
trước thì mất thông tin, nên phải đọc body trước.
