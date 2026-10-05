# Hướng dẫn build CF Trainer cùng Claude

File này đi kèm với `LEARNING.md`. `LEARNING.md` cho biết **cần học gì**, còn file này cho biết **làm theo thứ tự nào** và **nhắn gì cho Claude** ở mỗi bước.

Tổng thời gian dự kiến: khoảng 7 ngày (ngày 6 đến 12 trong kế hoạch 14 ngày).

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
- **SQLite Viewer**: mở file `dev.db` để xem dữ liệu trong bảng (dùng ở Bước 1, 4).
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

## Cách làm việc với Claude

**Mỗi bước làm theo đúng vòng lặp này:**

1. Đọc phần tương ứng trong `LEARNING.md` (15–30 phút).
2. Gửi prompt của bước đó cho Claude.
3. Đọc code Claude viết, **chạy test**, chạy thử trên `/docs`.
4. Gửi **prompt kiểm tra hiểu bài** (cuối mỗi bước). Không trả lời được thì hỏi lại cho đến khi hiểu.
5. Commit: `git add -A && git commit -m "<mô tả ngắn>"` rồi `git push`.

**Nếu dùng Claude trong chat (không phải trong terminal):** Claude không tự đọc được repo của bạn. Mỗi prompt hãy dán kèm nội dung các file được nhắc tới. Nếu repo đã kết nối với Claude qua GitHub thì chỉ cần nói tên file.

**Hai chế độ:** mỗi bước có prompt **Tự làm** (Claude chỉ gợi ý, bạn viết code) và **Làm nhanh** (Claude viết, bạn đọc hiểu). Phần lõi (Bước 3) nên dùng chế độ Tự làm vì phỏng vấn sẽ hỏi sâu nhất ở đây.

### Prompt mở đầu (gửi ở đầu mỗi phiên làm việc mới)

```
Mình đang build project CF Trainer: web app phân tích dữ liệu Codeforces,
FastAPI + SQLAlchemy + PostgreSQL ở backend, React + Vite ở frontend.
Mục tiêu: đưa vào CV để nộp intern SWE (Citadel, TikTok) trong 2 tuần.

Quy tắc khi làm việc với mình:
- Giải thích ngắn gọn bằng tiếng Việt, code và comment bằng tiếng Anh.
- Mỗi lần chỉ làm một bước nhỏ, không sửa file ngoài phạm vi được yêu cầu.
- Không đổi tên hàm hay chữ ký hàm đã có, vì test phụ thuộc vào chúng.
- Sau khi viết code, nói rõ mình cần chạy lệnh gì để kiểm tra.
- Với mỗi quyết định thiết kế, nêu 1 lựa chọn khác và vì sao không chọn.

Cấu trúc repo: xem README.md. Hôm nay mình làm Bước <số> trong BUILD_GUIDE.md.
```

---

## Bước 1: Thiết kế database (`app/models.py`)

**Mục tiêu:** thêm bảng bài tập (problem) và bảng bài đã giải (solve).

**Prompt (Tự làm):**
```
Mở app/models.py. Mình cần thiết kế 2 bảng còn thiếu: problems và solves.
Đừng viết code. Hãy hỏi mình 3–4 câu để mình tự nghĩ ra schema
(khóa chính là gì, lưu tags thế nào, làm sao chặn trùng lặp, cần index cột nào).
Sau khi mình trả lời, nhận xét và chỉ ra chỗ sai.
```

**Prompt (Làm nhanh):**
```
Mở app/models.py. Hãy thêm 2 model SQLAlchemy 2.0: Problem và Solve.
- Problem: định danh bằng (contest_id, index), có name, rating (có thể null), tags.
- Solve: user nào giải bài nào, lúc nào; một user không được có 2 dòng cho cùng một bài.
Giải thích: khóa chính, khóa ngoại, unique constraint, index bạn chọn, và cách bạn lưu tags.
Vẽ sơ đồ quan hệ bằng text.
```

**Kiểm tra:** chạy `uvicorn` lại, không lỗi. Mở file `dev.db` bằng extension SQLite của VS Code và thấy các bảng mới.

**Prompt kiểm tra hiểu bài:**
```
Đóng vai người phỏng vấn. Hỏi mình 3 câu về schema vừa làm, từng câu một,
chờ mình trả lời rồi mới hỏi câu tiếp. Cuối cùng chấm điểm và chỉ chỗ cần học thêm.
```

**Commit:** `Add Problem and Solve models`

---

## Bước 2: Client gọi Codeforces (`app/cf_client.py`)

**Mục tiêu:** gọi được API Codeforces, tự giới hạn 1 request mỗi 2 giây, báo lỗi rõ ràng.

**Prompt (Tự làm):**
```
Mở app/cf_client.py. Mình sẽ tự viết hàm _get. Cho mình gợi ý từng bước:
1) cách nhớ thời điểm gọi lần cuối và chờ cho đủ khoảng cách,
2) cách xử lý lỗi HTTP và lỗi status FAILED.
Chỉ đưa gợi ý, không đưa code hoàn chỉnh. Sau khi mình viết xong sẽ dán lại để bạn review.
```

**Prompt (Làm nhanh):**
```
Hoàn thiện app/cf_client.py: _get (có rate limit theo settings.codeforces_min_interval_seconds,
dùng time.monotonic), user_info, user_submissions. Thêm hàm problemset() trả về
danh sách problems từ /problemset.problems.
Sau đó viết tests/test_cf_client.py dùng httpx.MockTransport để test mà không gọi mạng thật:
- trả về result khi status OK,
- ném CodeforcesError khi status FAILED,
- ném CodeforcesError khi HTTP 500.
Giải thích MockTransport hoạt động thế nào.
```

**Kiểm tra:** `python -m pytest -q tests/test_cf_client.py` xanh. Thử nhanh trong terminal:
```bash
python -c "from app.cf_client import CodeforcesClient; print(CodeforcesClient().user_info('tourist')['rating'])"
```

**Prompt kiểm tra hiểu bài:**
```
Hỏi mình: nếu 20 người bấm đăng ký cùng lúc thì rate limit của mình còn đúng không?
Chờ mình trả lời, rồi giải thích vấn đề và cách sửa (lock, hàng đợi).
```

**Commit:** `Implement rate-limited Codeforces client`

---

## Bước 3: Logic lõi (`app/stats.py`): NÊN TỰ LÀM

**Mục tiêu:** cả 6 test trong `tests/test_stats.py` đều xanh. Đây là phần thuật toán, gần với CP nhất, và là phần phỏng vấn hỏi nhiều nhất.

**Cách làm:** viết từng hàm theo thứ tự `solved_problems` → `tag_stats` → `weakest_tags` → `recommend`. Sau mỗi hàm chạy:
```bash
python -m pytest -q tests/test_stats.py
```

**Prompt khi bí:**
```
Mình đang viết hàm <tên hàm> trong app/stats.py. Đây là code hiện tại của mình:
<dán code>
Test đang báo lỗi:
<dán lỗi>
Chỉ cho mình gợi ý về chỗ sai, đừng sửa hộ.
```

**Prompt review sau khi xanh hết:**
```
Đây là app/stats.py mình vừa viết, test đã xanh hết:
<dán code>
Review như một senior engineer: độ phức tạp, tên biến, trường hợp biên
(problem không có rating, không có tags, danh sách rỗng), và code đã đủ sạch cho phỏng vấn chưa.
```

**Prompt kiểm tra hiểu bài:**
```
Hỏi mình: độ phức tạp của tag_stats là bao nhiêu? Định nghĩa "tag yếu" của mình
có điểm yếu gì? Đề xuất một định nghĩa tốt hơn và để mình phản biện.
```

**Commit:** `Implement tag statistics and recommendations`

---

## Bước 4: Đồng bộ dữ liệu user (`POST /users/{handle}`)

**Mục tiêu:** nhập handle, server kéo dữ liệu từ Codeforces và lưu vào database.

**Prompt:**
```
Implement route register_user trong app/routes/users.py.
Tách phần đồng bộ ra file mới app/services/sync.py với hàm sync_user(session, client, handle),
để route chỉ gọi hàm đó.
Yêu cầu:
- 404 nếu Codeforces không biết handle.
- Tạo hoặc cập nhật User (rating, max_rating, last_synced_at).
- Lưu các bài đã giải vào bảng solves, không tạo bản ghi trùng khi đồng bộ lại.
- Tạo CodeforcesClient qua một dependency get_cf_client() để sau này test có thể thay bằng bản giả.
Giải thích vì sao tách service khỏi route, và "upsert" là gì.
```

**Kiểm tra:** trên `/docs`, gọi `POST /api/users/<handle của bạn>` hai lần liên tiếp. Lần hai không lỗi, không tạo dữ liệu trùng.

**Commit:** `Sync user submissions from Codeforces`

---

## Bước 5: Thống kê, gợi ý bài và cache

**Prompt:**
```
Implement 2 route get_stats và get_recommendations trong app/routes/users.py,
dùng các hàm trong app/stats.py.
- Trả JSON gọn bằng Pydantic response model (tạo app/schemas.py).
- Danh sách toàn bộ problem của Codeforces rất lớn: cache trong bộ nhớ,
  tải lại tối đa mỗi 24 giờ. Viết cache thành một class nhỏ có thể test được
  (truyền hàm lấy thời gian vào để test không phải chờ thật).
- 404 nếu user chưa đăng ký.
Viết test cho class cache.
```

**Prompt kiểm tra hiểu bài:**
```
Hỏi mình: cache này có vấn đề gì nếu chạy 3 server cùng lúc? Khi nào nên dùng Redis?
```

**Commit:** `Add stats and recommendation endpoints with problem cache`

---

## Bước 6: Bảng xếp hạng

**Prompt:**
```
Implement get_leaderboard: tất cả user, sắp xếp theo số bài giải trong 7 ngày gần nhất,
hòa thì theo rating. Viết bằng một câu query SQLAlchemy (GROUP BY + COUNT + LEFT JOIN),
không lặp trong Python. Giải thích câu SQL tương đương được sinh ra,
và vì sao phải LEFT JOIN thay vì JOIN.
```

**Commit:** `Add weekly leaderboard`

---

## Bước 7: Test API

**Prompt:**
```
Viết tests/test_users_api.py dùng TestClient:
- Dùng app.dependency_overrides để thay get_cf_client bằng client giả trả dữ liệu cố định,
  và thay database bằng SQLite trong bộ nhớ (sqlite:// với StaticPool).
- Test: đăng ký user thành công, handle không tồn tại trả 404,
  đồng bộ 2 lần không trùng dữ liệu, stats đúng, leaderboard đúng thứ tự.
Giải thích dependency_overrides và vì sao test không được gọi mạng thật.
```

**Kiểm tra:** `python -m pytest -q` xanh toàn bộ. Push lên GitHub và xem tab **Actions**: CI phải xanh.

**Commit:** `Add API tests`

---

## Bước 8: Frontend (`frontend/`)

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (backend phải đang chạy)
```

**Prompt:**
```
Mở frontend/src/App.jsx. Mình muốn giao diện gồm:
1) Ô nhập handle + nút Analyse (đã có).
2) Bảng thống kê theo tag, có thanh ngang thể hiện tỉ lệ solved/attempted.
3) Danh sách bài gợi ý, mỗi bài là link tới codeforces.com/problemset/problem/<contestId>/<index>.
4) Trang Leaderboard (chuyển trang bằng state đơn giản, chưa cần thư viện router).
5) Trạng thái loading và lỗi rõ ràng.
Tách thành component nhỏ trong src/components/. CSS đơn giản, gọn, không thêm thư viện UI.
Giải thích luồng dữ liệu: state → fetch → render.
```

**Prompt kiểm tra hiểu bài:**
```
Hỏi mình: useState là gì, vì sao gọi fetch trong hàm xử lý sự kiện thay vì trực tiếp trong
thân component, và Vite proxy giải quyết vấn đề gì khi phát triển.
```

**Commit:** `Build dashboard UI`

---

## Bước 9: Chạy với PostgreSQL bằng Docker

```bash
docker compose up --build
```

**Prompt khi gặp lỗi:**
```
Mình chạy docker compose up --build và gặp lỗi sau:
<dán lỗi>
Giải thích nguyên nhân và cách sửa. Đây là docker-compose.yml và backend/Dockerfile: <dán>
```

**Prompt kiểm tra hiểu bài:**
```
Hỏi mình: image khác container thế nào? Vì sao backend gọi database bằng host "db"
chứ không phải "localhost"? Dữ liệu PostgreSQL được giữ lại ở đâu khi tắt container?
```

**Commit:** `Run with PostgreSQL via Docker Compose`

---

## Bước 10: Deploy

**Prompt:**
```
Mình muốn deploy CF Trainer miễn phí hoặc gần như miễn phí:
backend FastAPI + PostgreSQL, frontend React tĩnh.
Hãy tìm và so sánh 3 lựa chọn hiện tại (gói miễn phí, giới hạn, có ngủ khi không dùng không),
khuyên một lựa chọn, rồi hướng dẫn từng bước. Nhắc mình những biến môi trường cần đặt
(DATABASE_URL, CORS_ORIGINS) và cách để frontend gọi đúng địa chỉ backend khi đã deploy.
```

**Kiểm tra:** mở link từ điện thoại, nhập handle của bạn, mọi thứ chạy đúng.

**Commit:** `Configure production deployment`

---

## Bước 11: Người dùng thật

- Đăng link lên Discord/nhóm UTS ProgSoc và đội ICPC. Gợi ý tin nhắn:

```
Prompt: Viết giúp mình một tin nhắn ngắn, thân thiện bằng tiếng Anh để đăng lên Discord
của hội lập trình trường, giới thiệu CF Trainer: nhập Codeforces handle để xem tag yếu
và nhận gợi ý bài. Nhờ mọi người dùng thử và góp ý. Link: <link>
```

- Ghi lại số người dùng (đếm số dòng trong bảng `users`) và các lỗi họ báo. Sửa lỗi nghiêm trọng nhất.

---

## Bước 12: README, CV và tập kể về project

**Prompt README:**
```
Đây là README.md hiện tại và mô tả những gì mình đã làm:
<dán>
Giúp mình viết phần "Design notes" (schema, rate limit, cache, định nghĩa tag yếu).
Viết theo ý của mình, ngắn gọn; chỗ nào bạn không chắc thì hỏi mình chứ đừng tự bịa.
Thêm link deploy và số người dùng thật: <số>.
```

**Prompt dòng CV:**
```
Viết 2 gạch đầu dòng CV (tiếng Anh, bắt đầu bằng động từ mạnh, có số liệu) cho CF Trainer.
Số liệu thật: <số người dùng>, <số bài trong cache>, <thời gian phản hồi nếu đo được>.
Không được phóng đại.
```

**Prompt luyện phỏng vấn (làm ít nhất 2 lần):**
```
Đóng vai interviewer của TikTok. Bắt đầu bằng "Tell me about a project you're proud of".
Mình trả lời bằng tiếng Anh. Sau đó hỏi follow-up sâu về thiết kế, scale, lỗi và trade-off,
mỗi lần một câu. Cuối buổi nhận xét cả nội dung lẫn cách diễn đạt tiếng Anh.
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

**Quy tắc vàng:** dòng nào Claude viết, bạn phải đọc và tự giải thích lại được trước khi commit.
