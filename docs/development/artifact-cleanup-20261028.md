# .codex-artifacts 清理（2026-10-28）

用户要求清理 D:/GitHub/CyIME/.codex-artifacts。目录现已清空，最终根目录条目数为 0；未执行 gradlew clean、构建或设备操作。

主要占用来自历史九键回放重复资源：按目录逻辑长度统计，.gram 约 37.37 GiB、ZIP 约 29.05 GiB。删除 61 个资源归档容器前，逐项保存并校验全部唯一条目；118 份唯一资源约 0.474 GiB。另删除 999 份 SHA-256 相同的展开资源副本。

其余 25,459 个文件（报告、截图、日志、源码快照、词库、历史 APK 等）保持相对路径压缩保存，每个归档条目均重新读取并校验 SHA-256、长度后才删除原文件。226 个旧回放运行库／日志文件链接单独记录后删除链接本身，不访问链接目标。首次预检因发现文件链接停止，尚未删除数据；修正同一入口后继续。

保留档案：D:/CyIME-Data/eval/artifact-cleanup-20261028/，合计 4.486 GiB。README.md 说明资源映射及恢复方式；original-files.json、resource-map.jsonl、duplicate-map.jsonl、removed-runtime-links.json 与 final-verification.json 保存清理证据。原资源 ZIP 的条目内容保留，容器字节及元数据不保证重建；复用旧回放前需解压证据并依映射恢复资源。

首次盘符检查：C 60.61 GiB、D 119.43 GiB；最终：C 60.261 GiB、D 137.138 GiB。主清理进程自身窗口观测 D 可用增加 18.969 GiB；机器同时有其他实验运行，因此以最终盘符可用量为准，不将目录逻辑长度当作实际释放量。归档新增量低于本轮 5 GiB 预算。应用源码、用户未提交改动、活动实验和 app/build 中的交付回执均未改动。

## tmp 追加清理

同日按用户要求清理 D:/CyIME-Data/tmp 中六个旧实验，本体由 17.738 GiB 降至 1.209 GiB；唯一资源和 4,564 个报告/脚本等文件校验归档到 D:/CyIME-Data/eval/tmp-cleanup-20261028（2.273 GiB）。移除两个指向 Windows work 的链接本身，目标未操作。录音、源码和词库备份保留。具体资源映射、验证和空间记录见该归档 README.md 与 final-verification.json。
