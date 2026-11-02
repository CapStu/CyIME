# 智能联想只用 n-gram 联想表（2026-11-02）

## 决定

用户问「智能联想我还有必要依赖这个模型吗? 我自己都有ngram模型」，看过对比后交给 Agent 决定：去掉神经联想模型，
智能联想只用 APK 内置的 n-gram 联想表（`association/lccc-base-v1.bin`，和九键词组模型同一份分词语料统计）加个人学习。

## 依据（离线对比，电脑 CPU，复刻 App 代码，未上真机）

位置：jieba 切词，在每个词边界整段上屏，看前 K 个联想是否接上后文；个人学习不计。

| 语料 | 只用表 前3 | 表+完整模型 前3 | 表+轻量模型 前3 | 只用完整模型 前3 |
|---|---|---|---|---|
| NUS 短信 1500 条（8805 处） | 22.2% | 23.1% | 23.5% | 14.8% |
| 日常短句 120 句（397 处） | 33.2% | 31.7% | 31.0% | 21.9% |
| 日常聊天 1100 字（257 处） | 16.7% | 19.1% | 17.5% | 14.4% |

模型权重调到 0.5 或以模型为主，三套全部变差。模型代价：每次上屏推理 3 次（电脑完整版中位 11 ms），
常驻内存约 +90 MB（完整）/ +60 MB（轻量），下载 19.7–36 MB，完整版 APK 内置两份约 56 MB，键盘收起 3 分钟卸载后重载会让第一次联想变慢。
复现脚本与逐处结果：项目文件 `predict-model-eval-1102/`。

## 改了什么

- 联想：`NgramFusionEngine` 只混联想表（0.7）和个人学习（0.15）；`AssociationManager` 不再加载、预热、闲置卸载、后台重载模型；
  删 `OnnxAssociationEngine`、`FragmentCompletion`、`ModelCandidateScores` 及测试；`InferenceService` 不再加载联想模型（`predict` 返回空，AIDL 不变）。
  `NativeOnnxEngine` 和 `onnx_jni.cc` 保留：手写也靠它加载 ONNX Runtime 共享库和共享环境。
- 设置：智能联想页去掉「选择模型」和「下载模型可增强预测」提示，说明改成一句；设置搜索去掉「选择模型」；相关 9 条多语言字符串删除，界面语言说明改为只翻译了设置首页。
- 模型：目录、首次自动下载、完整版内置、设置向导（推荐、删除、名字、类别）、模型市场「联想」分类都去掉联想模型；旧索引里 `category: prediction` 的条目不再列出。
  `DeviceModelProfile` 不再带联想档位，`prediction_selected_model`、`device_default_prediction_model` 不再读写。
- 旧文件：启动清理（`StorageHousekeeping`）把 `models/predictive-text-base`、`models/predictive-text-small` 一并删掉。
- 打包：`cyime_packager.py` 老人包固定集合、`config.json` 完整发布包、`prepare-bundled-models.py` 都不再带联想模型。
- 鸣谢：去掉 predictive-text。

## 未做 / 待办

- 未编译、未跑单元测试、未打包、未真机验收（云端没有 Android SDK）。
- 「性能与省电」里智能联想的实测代价（`assets/perf_costs.json`）含模型内存，需要在真机重测。
- README 里提到 predictive-text 的段落由改写介绍的那一轮处理。
- GitHub Release `models` 里的联想模型文件和魔搭镜像没删（旧版本还在用）。
