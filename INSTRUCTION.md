# 闹钟会话执行说明

本文件存放在公开仓库，读取不需要任何凭证。

## 你的任务（按顺序执行）

### 第1步（验证读取链路）
读取本文件本身，确认你能访问 raw.githubusercontent.com。
如果能读到这段文字，说明「闹钟唤醒 → 新会话 → 访问 GitHub」这一段是通的。

### 第2步（读取现有内容）
读取 https://raw.githubusercontent.com/c6r99A/desc-inbox/main/desc.txt
这是当前已推送的全部 desc 条目。

### 第3步（汇报）
把第1步、第2步的结果如实汇报给用户，包括：
- 是否读取成功
- desc.txt 的条目数
- 如果失败，贴出完整报错

## 关于写入（重要）
向本仓库写入需要 GitHub token。token 保存在沙盒本地文件
/data/workspace/.gh_token ，该文件**不会**在新会话中继承。

因此第3步只做读取与汇报，不执行写入。
