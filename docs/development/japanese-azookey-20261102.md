# 日语转换换成 azooKey（2026-11-02）

用户 11-02 看到对比结果后确认「可以换」。26 键和九宫格日语的假名汉字转换从 Rime + jaroomaji 词库换成 azooKey；
Rime 仍管输入串、分段、候选栏、部分选词、回车上屏和无痕。构建与来源见 `tools/azookey/README.md`。

## 对比（同一套输入，学习关闭）

测试集：97 句日常句（自编）+ AJIMEE-Bench 200 句（azooKey 团队，维基百科错字语料）。按标点切块，训令式罗马字（ん 用 nn，促音双写辅音），
逐键输入后取首选；整句与答案在 NFKC 归一后完全一致算对，另计字错率。时间是电脑上同一台机器的逐键耗时。

| 引擎 | 日常 整句全对 | 日常 字错率 | 日常 每键 | AJIMEE 整句全对 | AJIMEE 字错率 | AJIMEE 每键 |
|---|---|---|---|---|---|---|
| 旧：Rime + jaroomaji | 28.9% | 28.9% | 13.33 ms | 18.5% | 23.3% | 11.49 ms |
| azooKey 直接调用 | 85.6% | 2.1% | 3.53 ms | 42.0% | 8.3% | 3.71 ms |
| azooKey 经 Rime 翻译器（本次接入） | 85.6% | 2.1% | 6.78 ms | 41.5% | 8.4% | 6.59 ms |

接入版另加了助词按读音（wa/e/o → は/へ/を）；加之前 AJIMEE 为 42.5%，差 1 句（選手権→選手県）。
最慢一键 P95：旧 60.9 / 59.9 ms，新 61.2 / 82.7 ms（AJIMEE 长句）。Zenzai 神经模型未测（模型只在 Hugging Face，环境访问不到）。

## 体积

- arm64 库 17,989,344 字节（压缩约 6.3 MB）；armv7 17.8 MB；x86_64 19.1 MB。32 位 x86 无 Swift 目标，不带库，日语不转换。
- 词典 3382 个文件 25.3 MB，压缩后约 10.5 MB。
- 旧 jaroomaji 词库：APK 内约 21 MB（压缩），手机上 89 MB 源文件 + 70 MB 编译表。升级时未改过的旧词库文件会被删掉。

## 电脑端检查（Linux，宿主库 + 系统 librime）

部分选词（記者の 后继续转换）、回车上屏假名（とうきょう）、学习（攻勢 提到首位）、无痕不学习、大写 TESUTO 首选テスト、
假名键盘编码 xka/xke/vu/xwa/wo/di/du、预编辑 kyouk→きょうk、私は学生です / それは / ではない / 今日はいい天気ですね。

单元测试：JapaneseRomajiPreeditTest、JapaneseKanaInputTest、BundledRimeSyncTest、JapaneseSchemasTest 在单独的 JVM 工程里跑（云端没有安卓 SDK），35 项通过；
`./gradlew test` 全量和安卓构建未在云端运行。翻译器源码对 CyIME 自带 librime 头文件做了语法检查。

## 未验收

未编译 APK、未真机验证：安卓 CMake 插件接入、库加载、手机上词典解压、升级清理旧词库都要等打包后在手机上看。
