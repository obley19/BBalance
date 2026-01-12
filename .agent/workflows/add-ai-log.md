---
description: Thêm log chat AI vào file ai_log.md
---

# Thêm AI Log

Khi người dùng yêu cầu thêm log, thực hiện các bước sau:

1. Mở file `ai_log.md` tại thư mục gốc dự án
2. Thêm nội dung chat vào **đầu file** theo format:

```markdown
---
## [Ngày giờ] | [Tên AI: Claude/Gemini/etc]

[Nội dung chat copy-paste vào đây]

---
```

3. Lưu file và commit nếu cần:
```bash
git add ai_log.md
git commit -m "AI Log: [Mô tả ngắn nội dung chat]"
```
