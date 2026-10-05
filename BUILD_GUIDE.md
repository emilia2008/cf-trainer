# Hướng dẫn build CF Trainer cùng Claude

File này đi kèm với `LEARNING.md`. `LEARNING.md` cho biết **cần học gì**, còn file này cho biết **làm theo thứ tự nào** và **nhắn gì cho Claude** ở mỗi bước.

**Mục tiêu sản phẩm:** nhập một Codeforces handle, nhận báo cáo phân tích chuyên sâu: rating và rank hiện tại, cần cải thiện gì, cần học gì, và nên luyện bài nào để tăng rating.

Tổng thời gian dự kiến: khoảng 7–8 ngày.

---

## Phần 0: Chuẩn bị (khoảng 1 giờ)

### Phần mềm cần tải

| Phần mềm | Dùng để | Tải ở đâu | Kiểm tra sau khi cài |
|---|---|---|---|
| **Git** | Quản lý code, push lên GitHub | git-scm.com | `git --version` |
| **Python 3.12+** | Chạy backend | python.org (Windows: tick "Add Python to PATH" khi cài) | `python --version` |
| **Node.js 22 LTS** | Chạy frontend (có sẵn `npm`) | nodejs.org | `node --version` và `npm --version` |
| **VS Code** | Viết code | code.visualstudio.com | — |
| **Docker Desktop** | Chạy PostgreSQL (từ Bước 9, cài sau cũng được) | docker.com | `docker --version` |

Trên Windows, nên dùng **Git Bash** (cài cùng Git) hoặc terminal trong VS Code để chạy các lệnh trong file này.

### Extension VS Code

Mở VS Code, bấm biểu tượng Extensions (Ctrl+Shift+X) rồi tìm theo tên:

**Bắt buộc**
- **Python** (Microsoft): chạy và debug Python, tự kèm **Pylance** để gợi ý code và báo lỗi kiểu dữ liệu.
- **ES7+ React/Redux/React-Native snippets**: gõ tắt khi viết React.
- **ESLint**: báo lỗi JavaScript/React.

**Rất nên có**
- **SQLite Viewer**: mở file `dev.db` để xem dữ liệu trong bảng (dùng ở Bước 1, 5).
- **Ruff**: tự format code Python và bắt lỗi phổ biến. Bật "Format on Save" trong Settings.
- **Prettier**: tự format code JavaScript.
- **Docker** (Microsoft): xem container đang chạy (từ Bước 9).
- **GitLens**: xem lịch sử từng dòng code, ai sửa lúc nào.

**Tùy chọn**
- **Thunder Client**: gửi request thử API ngay trong VS Code (thay cho trang `/docs`).
- **Error Lens**: hiện lỗi ngay trên dòng code.

Sau khi mở thư mục `backend`, bấm Ctrl+Shift+P → **Python: Select Interpreter** → chọn bản trong `.venv`. Nếu không chọn, VS Code sẽ báo lỗi import dù code đúng.

### Tài khoản cần có

- **GitHub**: đã có (`emilia2008`).
- Tài khoản hosting để deploy: chưa cần, tạo ở Bước 10.

### Đưa code lên GitHub

```bash
cd cf-trainer
git remote add origin https://github.com/emilia2008/cf-trainer.git
git push -u origin main
```

### Chạy thử lần đầu

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q                # sẽ có test đỏ, đó là bình thường
uvicorn app.main:app --reload      # mở http://localhost:8000/docs
```

Nếu mở được trang `/docs` và thấy `GET /api/health` trả về `{"status": "ok"}` khi bấm "Try it out" là đã sẵn sàng.


---

## Sản phẩm cuối cùng trông như thế nào

Người dùng nhập handle, bấm **Analyse**, và nhận một trang báo cáo gồm:

| Phần | Trả lời câu hỏi | Hàm trong `analysis.py` |
|---|---|---|
| Tổng quan | Mình đang ở rank nào, còn bao nhiêu điểm nữa lên rank tiếp? | `rank_info`, `solved_problems` |
| Xu hướng rating | Mình đang lên hay xuống? | `rating_trend` |
| Độ khó | Mình thoải mái ở mức nào, nên luyện mức nào? | `difficulty_profile`, `comfort_rating`, `target_range` |
| Chủ đề | Mình mạnh/yếu chủ đề nào? | `tag_stats` |
| Chủ đề yếu + cần học gì | Chủ đề nào kéo rating xuống, học ở đâu? | `weak_topics` + `resources.py` |
| Thói quen | Hay sai kiểu gì (WA/TLE)? Contest thường giải tới bài nào? | `verdict_breakdown`, `contest_level` |
| Upsolve | Bài nào trong contest mình bỏ dở? | `upsolve_list` |
| Gợi ý luyện | Nên làm bài nào tiếp theo? | `recommend` |

---

## Cách làm việc với Claude

**Mỗi bước làm theo đúng vòng lặp này:**

1. Đọc phần tương ứng trong `LEARNING.md` (15–30 phút).
2. Gửi prompt của bước đó cho Claude.
3. Đọc code, **chạy test**, chạy thử trên `/docs`.
4. Gửi **prompt kiểm tra hiểu bài** (cuối mỗi bước). Không trả lời được thì hỏi lại cho đến khi hiểu.
5. Commit: `git add -A && git commit -m "<mô tả ngắn>"` rồi `git push`.

**Nếu dùng Claude trong chat:** Claude không tự đọc được máy của bạn. Mỗi prompt hãy dán kèm nội dung các file được nhắc tới (hoặc chỉ cần nói tên file nếu repo đã kết nối qua GitHub).

**Hai chế độ:** mỗi bước có prompt **Tự làm** (Claude chỉ gợi ý, bạn viết code) và **Làm nhanh** (Claude viết, bạn đọc hiểu). **Bước 3 và 4 (phân tích) nên tự làm**, vì đây là phần phỏng vấn hỏi sâu nhất và cũng gần với CP nhất.

### Prompt mở đầu (gửi ở đầu mỗi phiên làm việc mới)

```
Mình đang build CF Trainer: web app phân tích chuyên sâu một tài khoản Codeforces
(rank hiện tại, chủ đề yếu, cần học gì, nên luyện bài nào để tăng rating).
Backend FastAPI + SQLAlchemy + PostgreSQL, frontend React + Vite.
Mục tiêu: đưa vào CV để nộp intern SWE (Citadel, TikTok) trong 2 tuần.

Quy tắc khi làm việc với mình:
- Giải thích ngắn gọn bằng tiếng Việt, code và comment bằng tiếng Anh.
- Mỗi lần chỉ làm một bước nhỏ, không sửa file ngoài phạm vi được yêu cầu.
- Không đổi tên hay chữ ký các hàm đã có trong app/analysis.py, vì test phụ thuộc vào chúng.
- Sau khi viết code, nói rõ mình cần chạy lệnh gì để kiểm tra.
- Với mỗi quyết định thiết kế, nêu 1 lựa chọn khác và vì sao không chọn.

Cấu trúc repo: xem README.md. Hôm nay mình làm Bước <số> trong BUILD_GUIDE.md.
```

---

## Bước 1: Thiết kế database (`app/models.py`)

**Mục tiêu:** lưu submissions và lịch sử rating của mỗi user. Đọc comment trong file: có 2 thiết kế A (bảng chuẩn hóa) và B (snapshot JSON).

**Prompt (Tự làm):**
```
Mở app/models.py. Mình cần chọn giữa thiết kế A (bảng submissions + rating_changes)
và B (một bảng snapshot với cột JSON). Đừng viết code.
Hỏi mình 3 câu để mình tự quyết định (dữ liệu dùng thế nào, có cần query SQL bên trong không,
đồng bộ lại thì xử lý ra sao). Sau đó nhận xét lựa chọn của mình.
```

**Prompt (Làm nhanh):**
```
Mở app/models.py. Hãy implement thiết kế <A hoặc B> bằng SQLAlchemy 2.0.
Yêu cầu: đồng bộ lại một user phải thay dữ liệu cũ, không tạo bản trùng.
Giải thích khóa chính, khóa ngoại, unique constraint, index, và vẽ sơ đồ quan hệ bằng text.
```

**Kiểm tra:** chạy lại `uvicorn`, không lỗi; mở `dev.db` bằng SQLite Viewer thấy bảng mới.

**Prompt kiểm tra hiểu bài:**
```
Đóng vai người phỏng vấn. Hỏi mình 3 câu về thiết kế database vừa làm, từng câu một,
chờ mình trả lời rồi mới hỏi câu tiếp. Cuối cùng chấm điểm và chỉ chỗ cần học thêm.
```

**Commit:** `Add storage for submissions and rating history`

---

## Bước 2: Client gọi Codeforces (`app/cf_client.py`)

**Mục tiêu:** gọi 4 endpoint, tự giới hạn 1 request mỗi 2 giây, báo lỗi rõ ràng.

Trước khi code, mở thử trên trình duyệt để xem dữ liệu thật:
`https://codeforces.com/api/user.rating?handle=<handle của bạn>`

**Prompt (Tự làm):**
```
Mở app/cf_client.py. Mình sẽ tự viết hàm _get. Cho mình gợi ý từng bước:
1) cách nhớ thời điểm gọi lần cuối và chờ cho đủ khoảng cách,
2) cách xử lý lỗi HTTP, status FAILED, và nhận ra lỗi "handle not found".
Chỉ đưa gợi ý, không đưa code. Mình viết xong sẽ dán lại để bạn review.
```

**Prompt (Làm nhanh):**
```
Hoàn thiện app/cf_client.py: _get (rate limit theo settings.codeforces_min_interval_seconds,
dùng time.monotonic), user_info, user_rating, user_submissions, problemset
(gộp solvedCount từ problemStatistics vào từng problem).
Viết tests/test_cf_client.py dùng httpx.MockTransport, không gọi mạng thật:
status OK trả về result; status FAILED ném CodeforcesError; handle không tồn tại ném HandleNotFound;
HTTP 500 ném CodeforcesError; problemset gộp đúng solvedCount.
Giải thích MockTransport hoạt động thế nào.
```

**Kiểm tra:** `python -m pytest -q tests/test_cf_client.py` xanh, rồi thử thật:
```bash
python -c "from app.cf_client import CodeforcesClient as C; c=C(); print(c.user_info('tourist')['rating'], len(c.user_rating('tourist')))"
```

**Prompt kiểm tra hiểu bài:**
```
Hỏi mình: nếu 20 người bấm Analyse cùng lúc thì rate limit của mình còn đúng không?
Chờ mình trả lời, rồi giải thích vấn đề và cách sửa (lock, hàng đợi).
```

**Commit:** `Implement rate-limited Codeforces client`

---

## Bước 3: Phân tích phần A: tổng quan, độ khó, chủ đề (TỰ LÀM)

**Mục tiêu:** viết trong `app/analysis.py`, theo thứ tự:
`rank_info` → `solved_problems` → `rating_trend` → `difficulty_profile` → `comfort_rating` → `target_range` → `tag_stats`.

Đọc kỹ docstring của từng hàm: nó là đề bài. Sau mỗi hàm, chạy đúng test của hàm đó:
```bash
python -m pytest -q tests/test_analysis.py -k rank_info
python -m pytest -q tests/test_analysis.py -k difficulty
```

Coi mỗi hàm như một bài CP: đọc đề, nghĩ, code, chạy test. Bài khó nhất là `tag_stats` (phải tìm lần nộp **sớm nhất** của mỗi bài để tính `first_try_rate`; API trả submissions mới nhất trước).

**Prompt khi bí:**
```
Mình đang viết hàm <tên hàm> trong app/analysis.py. Code hiện tại:
<dán code>
Test báo lỗi:
<dán lỗi>
Chỉ cho mình gợi ý về chỗ sai, đừng sửa hộ.
```

**Commit:** `Implement overview, difficulty and topic analysis`

---

## Bước 4: Phân tích phần B: chủ đề yếu, thói quen, gợi ý bài (TỰ LÀM)

**Mục tiêu:** `tag_importance` → `weak_topics` → `verdict_breakdown` → `contest_level` → `upsolve_list` → `recommend`. Xong bước này, `python -m pytest -q tests/test_analysis.py` phải xanh toàn bộ.

**Gợi ý tư duy:**
- `weak_topics` dùng lại `tag_importance` và `solved_problems`, đừng viết lại.
- `contest_level` chỉ xét submission có `participantType == "CONTESTANT"`; mẫu số là số contest đã tham gia, không phải số bài.
- `recommend` sắp xếp theo 4 tiêu chí: dùng một tuple làm key.

**Prompt review sau khi xanh hết:**
```
Đây là app/analysis.py mình vừa viết, test đã xanh hết:
<dán code>
Review như một senior engineer: độ phức tạp từng hàm, tên biến, code lặp lại,
trường hợp biên chưa được test. Code đã đủ sạch cho phỏng vấn chưa?
Đừng viết lại hộ, chỉ liệt kê vấn đề theo mức độ quan trọng.
```

**Prompt kiểm tra hiểu bài:**
```
Đóng vai interviewer. Hỏi mình về công thức weak topic score = importance / (1 + solved_in_range):
vì sao hợp lý, điểm yếu là gì, và đề xuất cách tốt hơn. Sau đó hỏi độ phức tạp của weak_topics
và recommend khi có 10.000 bài và 5.000 submissions. Từng câu một.
```

**Commit:** `Implement weak topics, habits and recommendations`

---

## Bước 5: Đồng bộ dữ liệu (`POST /api/users/{handle}/sync`)

**Prompt:**
```
Implement route sync_user trong app/routes/report.py.
Tạo app/services/sync.py với hàm sync_user(session, client, handle):
- gọi user_info, user_rating, user_submissions;
- tạo hoặc cập nhật User (rating, max_rating, rank, last_synced_at);
- lưu submissions và rating history theo thiết kế ở Bước 1, thay dữ liệu cũ;
- HandleNotFound → 404.
Tạo dependency get_cf_client() để sau này test có thể thay bằng client giả.
Giải thích vì sao tách service khỏi route, và cách đảm bảo không lưu trùng dữ liệu.
```

**Kiểm tra:** trên `/docs`, gọi `POST /api/users/<handle của bạn>/sync` hai lần. Lần hai không lỗi, dữ liệu không bị nhân đôi (xem bằng SQLite Viewer). Thử handle không tồn tại: phải ra 404.

**Commit:** `Sync user data from Codeforces`

---

## Bước 6: Báo cáo (`GET /api/users/{handle}/report`)

**6a. Điền tài liệu học:** mở `app/resources.py`, thêm link học cho khoảng 10 tag hay gặp ở mức rating của bạn (dp, graphs, greedy, math, number theory, strings, trees, sortings, constructive algorithms, two pointers). Tự mở từng link để chắc nó tồn tại. Viết lại `VERDICT_ADVICE` bằng lời của bạn.

**6b. Prompt:**
```
Implement get_report trong app/routes/report.py, logic đặt trong app/services/report.py.
- Đọc dữ liệu đã lưu của user (404 nếu chưa sync).
- Lấy danh sách problem qua một class ProblemCache: cache trong bộ nhớ, hết hạn sau 24 giờ,
  nhận hàm lấy thời gian qua constructor để test được. Viết test cho ProblemCache.
- Gọi các hàm trong app/analysis.py và trả JSON gồm các phần: overview, rating_trend
  (kèm lịch sử để vẽ biểu đồ), difficulty, topics, weak_topics (kèm RESOURCES),
  habits (verdict kèm VERDICT_ADVICE cho verdict chiếm trên 15% số lần nộp sai), upsolve (10 bài),
  recommendations (10 bài, kèm link codeforces.com/problemset/problem/<contestId>/<index>).
- Định nghĩa JSON bằng Pydantic model trong app/schemas.py.
Không viết lại logic đã có trong analysis.py.
```

**Kiểm tra:** gọi report cho handle của bạn trên `/docs`. **Đọc kỹ báo cáo:** nó có đúng với cảm nhận của bạn về điểm mạnh/yếu của chính mình không? Nếu không, ghi lại lý do; đó là chất liệu tốt cho phần "Design notes" và phỏng vấn.

**Prompt kiểm tra hiểu bài:**
```
Hỏi mình: cache của mình có vấn đề gì nếu chạy 3 server cùng lúc? Khi nào nên dùng Redis?
Lần đầu gọi report sau khi server khởi động thì mất bao lâu, vì sao, và có cách nào cải thiện?
```

**Commit:** `Add analysis report endpoint with problem cache`

---

## Bước 7: Test API

**Prompt:**
```
Viết tests/test_report_api.py dùng TestClient:
- Dùng app.dependency_overrides để thay get_cf_client bằng client giả trả dữ liệu cố định
  (vài submissions, rating history, problemset nhỏ), và thay database bằng SQLite
  trong bộ nhớ (sqlite:// với StaticPool).
- Test: sync thành công; handle không tồn tại trả 404; sync 2 lần không trùng dữ liệu;
  report trước khi sync trả 404; report sau khi sync có đủ các phần và số liệu đúng.
Giải thích dependency_overrides và vì sao test không được gọi mạng thật.
```

**Kiểm tra:** `python -m pytest -q` xanh toàn bộ. Push lên GitHub, xem tab **Actions**: CI phải xanh.

**Commit:** `Add API tests`

---

## Bước 8: Frontend trang báo cáo

```bash
cd frontend
npm install
npm install recharts
npm run dev          # http://localhost:5173 (backend phải đang chạy)
```

**Prompt:**
```
Mở frontend/src/App.jsx. Thay phần in JSON bằng trang báo cáo, mỗi phần một component
trong src/components/:
1) OverviewCard: rank (tô màu theo rank của Codeforces), rating, "còn X điểm lên <rank tiếp>".
2) RatingChart: biểu đồ đường lịch sử rating (Recharts LineChart).
3) DifficultyChart: biểu đồ cột số bài giải theo rating, tô nổi vùng target range.
4) TopicTable: bảng chủ đề (solved, attempted, first-try %, bài khó nhất), sắp xếp được.
5) WeakTopics: mỗi chủ đề yếu kèm lý do ("xuất hiện 35% ở mức 1400–1600, bạn mới giải 1 bài") và link học.
6) Habits: tỉ lệ các loại lỗi kèm lời khuyên; "trong contest bạn thường giải tới bài C".
7) UpsolveList và Recommendations: danh sách bài, mỗi bài là link mở Codeforces.
Có trạng thái loading và lỗi. CSS gọn, đọc tốt trên điện thoại, không thêm thư viện UI.
Giải thích luồng dữ liệu: state → fetch → render.
```

**Prompt kiểm tra hiểu bài:**
```
Hỏi mình: useState là gì, vì sao chia nhiều component nhỏ, và Vite proxy giải quyết vấn đề gì.
```

**Commit:** `Build analysis report UI`

---

## Bước 9: Chạy với PostgreSQL bằng Docker

```bash
docker compose up --build
```

Nếu dùng cột JSON ở Bước 1, kiểm tra nó chạy được trên cả SQLite và PostgreSQL.

**Prompt khi gặp lỗi:**
```
Mình chạy docker compose up --build và gặp lỗi:
<dán lỗi>
Giải thích nguyên nhân và cách sửa. Đây là docker-compose.yml và backend/Dockerfile: <dán>
```

**Prompt kiểm tra hiểu bài:**
```
Hỏi mình: image khác container thế nào? Vì sao backend gọi database bằng host "db"
chứ không phải "localhost"? Dữ liệu PostgreSQL được giữ ở đâu khi tắt container?
```

**Commit:** `Run with PostgreSQL via Docker Compose`

---

## Bước 10: Deploy

**Prompt:**
```
Mình muốn deploy CF Trainer miễn phí hoặc gần như miễn phí:
backend FastAPI + PostgreSQL, frontend React tĩnh.
Hãy tìm và so sánh 3 lựa chọn hiện tại (gói miễn phí, giới hạn, có ngủ khi không dùng không),
khuyên một lựa chọn, rồi hướng dẫn từng bước. Nhắc mình các biến môi trường cần đặt
(DATABASE_URL, CORS_ORIGINS) và cách để frontend gọi đúng địa chỉ backend khi đã deploy.
```

**Kiểm tra:** mở link trên điện thoại, nhập handle của bạn, báo cáo hiện đầy đủ.

**Commit:** `Configure production deployment`

---

## Bước 11: Người dùng thật

Với hướng phân tích cá nhân, cách thu hút người dùng tốt nhất là **cho mỗi người xem báo cáo của chính họ**.

- Đăng lên Discord/nhóm UTS ProgSoc và đội ICPC:

```
Prompt: Viết giúp mình một tin nhắn ngắn, thân thiện bằng tiếng Anh để đăng lên Discord
của hội lập trình trường: giới thiệu CF Trainer, nhập Codeforces handle để xem mình yếu chủ đề nào
và nên luyện bài nào để lên rank tiếp theo. Nhờ mọi người dùng thử và góp ý xem báo cáo
có đúng với họ không. Link: <link>
```

- Hỏi trực tiếp vài người: "Báo cáo có đúng với cảm nhận của bạn không? Gợi ý bài có hữu ích không?"
- Đếm số handle trong bảng `users`, ghi lại góp ý, sửa vấn đề lớn nhất.

---

## Bước 12: README, CV và tập kể về project

**Prompt README:**
```
Đây là README.md hiện tại và những gì mình đã làm:
<dán>
Giúp mình viết phần "Design notes": cách lưu dữ liệu và lý do, cách xử lý rate limit,
cache danh sách bài, và giới hạn của công thức weak topic. Viết theo ý của mình, ngắn gọn;
chỗ nào bạn không chắc thì hỏi mình chứ đừng tự bịa. Thêm link deploy, ảnh chụp màn hình
và số người dùng thật: <số>.
```

**Prompt dòng CV:**
```
Viết 2 gạch đầu dòng CV (tiếng Anh, bắt đầu bằng động từ mạnh, có số liệu thật) cho CF Trainer:
một dòng về sản phẩm và tác động (số người dùng: <số>), một dòng về kỹ thuật
(FastAPI, PostgreSQL, caching, rate limiting, test). Không được phóng đại.
```

**Prompt luyện phỏng vấn (làm ít nhất 2 lần):**
```
Đóng vai interviewer của TikTok. Bắt đầu bằng "Tell me about a project you're proud of".
Mình trả lời bằng tiếng Anh. Sau đó hỏi follow-up sâu về thiết kế phân tích, độ chính xác
của gợi ý, scale, lỗi và trade-off, mỗi lần một câu. Cuối buổi nhận xét cả nội dung lẫn
cách diễn đạt tiếng Anh.
```

---

## Khi gặp lỗi bất kỳ

```
Mình đang ở Bước <số>. Mình chạy lệnh:
<lệnh>
và gặp lỗi:
<dán toàn bộ lỗi>
File liên quan:
<dán code>
Giải thích nguyên nhân trước, rồi mới đưa cách sửa.
```

## Sau khi nộp đơn: mở rộng

Xem cuối `LEARNING.md`: AI coach viết nhận xét và kế hoạch tuần, theo dõi tiến bộ theo tuần, đo tốc độ giải trong contest.

**Quy tắc vàng:** dòng nào Claude viết, bạn phải đọc và tự giải thích lại được trước khi commit.
