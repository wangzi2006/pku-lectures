# 未名讲座

展示北京大学校内及东门骑行约 30 分钟范围内、未来 14 天的公开讲座。官网每日抓取，经过规则预筛、GLM 结构化抽取、去重和 GitHub Issue 人工审核后发布。

网站：<https://wangzi2006.github.io/pku-lectures/>

> 本项目是独立、非官方的信息索引，与北京大学及各主办单位无隶属关系。时间、地点和报名要求以主办方最新通知为准。

## 收录重点

- 概率方向尽量完整收录；统计、纯数学、数学物理、应用数学次之。
- 其他专业报告要求本科生可听，或讲者/来访足够重要。
- 校外活动约以北大东门 6 km / 30 分钟骑行为范围，并提高质量门槛。
- 排除课程、招生、招聘、社团招新、竞赛、付费和仅限内部人员的活动。
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
收录来源：SABCD1234
拒绝来源：SEFGH5678
```

首期所有条目均需人工审核。GLM 只抽取事实和给出独立维度分数，是否进入审核及最终发布由固定规则和人工决定。

## 配置 GLM

1. 在 Z.AI 开放平台创建 API Key。
2. 打开仓库 **Settings → Secrets and variables → Actions**。
3. 新建 Repository secret，名称为 `ZAI_API_KEY`，值为 API Key。

预算默认按公开标价保守估算：月度软提醒 35 元，达到 45 元停止非必要 AI 调用，低于用户设定的 50 元上限。真实 Key 只能放在 GitHub Secret，不要写进 Issue、代码或聊天。

## 自动化

- `每日抓取与审核`：北京时间每天 07:00；手动首次运行默认展示 30 条，日常为 10 条。
- `应用讲座审核`：仅接受仓库所有者的审核评论。
- `部署 GitHub Pages`：`main` 分支变化后自动构建部署。

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
- `data/feedback.json`：由“我听了这场讲座” Issue Form 自动保存五维反馈；首期仅用于内部校准，不在网站公开展示个人评价。

代码采用 MIT License。讲座文字、商标和链接内容的权利归各原始发布方所有。
