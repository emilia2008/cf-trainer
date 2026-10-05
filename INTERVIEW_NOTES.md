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
