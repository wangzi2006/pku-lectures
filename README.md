# 未名讲座

展示北京大学校内及周边区域、未来 14 天的公开讲座。官网每日抓取，经过规则预筛、DeepSeek 结构化抽取、去重和 GitHub Issue 人工审核后发布。

网站：<https://wangzi2006.github.io/pku-lectures/>

> 本项目是独立、非官方的信息索引，与北京大学及各主办单位无隶属关系。时间、地点和报名要求以主办方最新通知为准。

## 收录重点

- 概率方向尽量完整收录；统计、纯数学、数学物理、应用数学次之。
- 其他专业报告要求本科生可听，或讲者/来访足够重要。
- 校外活动按清华校内、中关村—海淀黄庄、五道口—知春路、圆明园—颐和园等粗粒度区域判断，并提高质量门槛。
- 排除招生、招聘、社团招新、付费、课程通知、培训班和仅限内部人员的活动。宣讲会、竞赛不再硬排除，由正常评分与人工审核决定。
- 官网的讲座回顾只用于反向发现稳定的预告/报名来源，不会被当作未来活动发布。

## 审核方法

每日抓取会创建一个 Issue，仓库所有者评论即可：

```text
收录：L001 L002
拒绝：L003
待定：L004
```

来源发现 Issue 使用：

```text
收录来源：S001
拒绝来源：S002
```

首期所有条目均需人工审核。模型只抽取事实和给出独立维度分数，是否进入审核及最终发布由固定规则和人工决定。

任何人都可以通过 Issue Form 推荐官网或公众号。Bot 会为来源生成简短连续的 `S001、S002…` 编号并更新统一来源审核 Issue；只有仓库 Owner 的 `收录来源：S...` 评论可以把它加入正式目录。批准后的新来源从下一次抓取开始工作，每场讲座仍需人工审核。

Owner 还可以新建“Owner 系统设置”Issue，通过评论调整硬排除词、标签、来源开关与来源等级：

```text
新增硬排除：培训营
移除硬排除：宣讲会 竞赛
启用来源：pku-history
停用来源：pku-bio
设置来源等级：pku-aais 3
新增标签：数字人文
删除标签：旧标签
```

## 配置模型

1. 在 DeepSeek 开放平台充值并创建 API Key。
2. 打开仓库 **Settings → Secrets and variables → Actions**。
3. 新建 Repository secret，名称为 `DEEPSEEK_API_KEY`，值为 API Key。

默认使用 `deepseek-v4-flash` 非思考模式。工作流每天 07:13 运行，08:13 备用；费用按工作流配置的单价估算。原有 `ZAI_API_KEY` 可保留，以后用于智谱视觉模型或备用抽取。

预算根据工作流内配置的每百万 Token 单价估算：月度软提醒 35 元，达到 45 元停止非必要 AI 调用，低于用户设定的 50 元上限。真实 Key 只能放在 GitHub Secret，不要写进 Issue、代码或聊天。

## 自动化

- `每日抓取与审核`：北京时间每天 07:13，08:13 备用；各来源轮流取样，日常最多提供 10 条新候选。
- 同一页面只分析一次；同日重复运行会刷新已有审核 Issue，不会重复创建。
- `应用讲座审核`：仅接受仓库所有者的审核评论。
- `部署 GitHub Pages`：`main` 分支变化后自动构建部署。

## 公众号文章

已登记的公众号会显示在公开来源目录中。公众号的持续监控由私有本地采集器完成，微信扫码凭据和原始图片不得进入公开仓库。发现文章后，可由 Owner 使用“提交公众号文章”Issue；Bot 会尝试读取正文，对文章截图执行中文 OCR，再把未来活动送入每日讲座审核。

手动提交图片型文章时，如果 Bot 无法读取正文，应附截图作为兜底。网站只保存结构化讲座信息、短摘要和微信原文链接，不公开转载公众号全文或海报。`PKU学生创新学社`及其 2024-11-08 示例文章已登记为首个图片型回归来源。

本地采集器使用 Docker Desktop 与私有 WeRSS。电脑无需全天在线：启动后补抓离线期间文章，白天每 2 小时检查一次；授权失效时需重新扫码。

本机桥接位于 `local_bridge/`：读取 `data/sources.json` 中已启用且配置了 `feedId` 的公众号，只把公众号名、标题、发布日期和微信原文链接提交到 GitHub；跨次去重，每天最多 10 条。`crawlPriority` 只控制读取次序，不绕过内容筛选；当前优先处理 `PKU学生创新学社` 和 `P-Lib official`。Token 由 `install.ps1` 交互式读取，经 Windows 当前用户加密后保存在本机，不进入仓库或日志。桥接任务在登录时及每天 08:27–20:27 每两小时运行一次。

批准新的公众号来源后，还需在本机 WeRSS 中订阅，并把其 WeRSS ID 写入该来源的 `feedId`；完成前它会显示在公开目录中，但不会被本机监控。桥接输出“没有需要新提交的公众号文章”只表示桥接正常，不代表 WeRSS 已成功抓到文章。

首次安装时，以管理员身份打开 Windows PowerShell，进入仓库后运行：

```powershell
.\local_bridge\install.ps1
```

之后可在 GitHub 的 Issues 和 Actions 页面观察处理结果。本机日志位于 `%LOCALAPPDATA%\pku-lectures\bridge.log`。

公众号单篇导入依赖：

```bash
pip install -r pipeline/requirements-wechat.txt
```

## Owner 可编辑配置

- `data/sources.json`：正式来源、启用状态、等级、主题、来源类型与公众号读取优先级。
- `config/policy.json`：硬排除词、评分权重、加减分和门槛。
- `config/topics.json`：规范标签、显示顺序和旧标签别名。
- `config/regions.json`：粗粒度区域、来源默认校区和地点匹配规则。

Owner 可以直接在 GitHub 网页编辑这些文件并提交，也可以使用“Owner 系统设置”Issue。配置提交后，网站会重新部署，下一次抓取使用新规则。

本地运行：

```bash
npm ci
npm run dev
```

本地验证抓取（无 Key 时只生成已有候选的审核稿）：

```bash
pip install -r pipeline/requirements.txt
python pipeline/crawl.py --days 14 --max-review 30
```

## 数据与反馈

- `data/sources.json`：已批准来源。
- `data/source-suggestions.json`：待审核的新来源。
- `data/candidates.json`：待审核讲座。
- `data/lectures.json`：网站公开讲座。
- `data/decisions.json`：保留收录/拒绝快照，供阈值回测。
- `data/seen-pages.json`：已分析页面记录，用于避免跨日重复抓取。
- `data/feedback.json`：由“我听了这场讲座” Issue Form 自动保存五维反馈；首期仅用于内部校准，不在网站公开展示个人评价。

当前听后反馈只保存，不会自动改变权重、来源等级或发布结果。

代码采用 MIT License。讲座文字、商标和链接内容的权利归各原始发布方所有。
