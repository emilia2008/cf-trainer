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
