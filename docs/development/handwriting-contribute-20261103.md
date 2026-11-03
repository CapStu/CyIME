# 贡献手写样本（2026-11-03）

用户反馈有人想把自己写的字交给作者改进手写。训练模式（能导出、分享样本）只在自用包里，公开版没有入口。
公开的中文联机手写数据（CASIA、SCUT-COUCH、HIT-OR3C、DCOH-120K）都限研究用；用户明确同意用途后贡献的样本没有这个限制。

## 做法

- 入口：设置 › 手写 › 改进手写 › 贡献手写样本，各个包都有。复用训练模式的画板（`HandwritingTrainingScreen(contribute = true)`）。
- 题目固定 150 道（`assets/handwriting/contribute_prompts.tsv`，`tools/handwriting_training/build_contribute_prompts.py` 生成）：
  常用字 100（提示「按平时的速度写」，收连笔）、生僻字 20（提示读音，测生僻字模板）、两字词 30（测一次写几个字）。
- 只收这一页写的字。样本存 `files/handwriting_contribute/`，和训练模式分开；不做「认错重写」，不改本机手写模板。
- 每条样本多一个 `writer`：本机随机生成的 16 位编号，只用来把同一个人的字归在一起（按人划分训练/测试）。
- 第一次分享或上传前弹「样本用途」，同意后才继续；隐私策略「数据收集」一段同步写明。
- 分享：系统分享面板发 .jsonl 文件，不需要服务器。
- 上传：`HandwritingContribution.UPLOAD_URL` 为空时菜单里没有「上传」。接收端建好后填地址；只传上次之后新写的行，gzip，≤ 8 MB。
- 接收端（魔搭创空间，代码在项目文件 `handwriting-contribute-1103/receiver/`）：只收 `source=contribute` 的本格式行，限大小、条数、每 IP 每小时 20 次，
  用作者令牌写入私有数据集 `<writer>/<时间>.jsonl.gz`。App 里不放任何密钥。

## 检查

- `HandwritingContributionTest` 4 条（题目 150 道且 id 不重复、生僻字有读音、writer 只出现在贡献样本里、没有地址时不显示上传）：
  云端单独编译 TrainingPrompt/TrainingSampleStore/HandwritingContribution 后通过。Compose 页面和整套 `./gradlew test` 未在云端编译，需 PC 跑。
- 接收端：格式校验、压缩炸弹、限流 4 条单元测试 + 本机 HTTP 往返通过；没有部署，没有连魔搭。
- 真机：未验收（页面渲染、分享面板、同意弹窗都没看过）。
