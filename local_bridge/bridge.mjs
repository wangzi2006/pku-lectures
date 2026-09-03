import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const SHANGHAI_OFFSET_MS = 8 * 60 * 60 * 1000;
const USER_AGENT = "pku-lectures-werss-bridge/1.0";
const MARKER = "<!-- pku-lectures-werss-bridge -->";
const ARTICLE_WORDS = /讲座|演讲|报告|报名|活动|大会|峰会|论坛|沙龙|分享|对话|研讨|工作坊|会议|学术|嘉宾|公开课|圆桌|讲堂|讲坛|交流会/i;
const WECHAT_URLS = /https:\/\/mp\.weixin\.qq\.com\/[^\s<>)]+/gi;

function decodeXml(value = "") {
  return value
    .replace(/^<!\[CDATA\[|\]\]>$/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, number) => String.fromCodePoint(Number(number)))
    .replace(/&#x([0-9a-f]+);/gi, (_, number) => String.fromCodePoint(parseInt(number, 16)));
}

function cleanText(value = "") {
  return decodeXml(value).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

function tagValue(xml, name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = xml.match(new RegExp(`<${escaped}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${escaped}>`, "i"));
  return match ? decodeXml(match[1].trim()) : "";
}

export function canonicalUrl(value) {
  try {
    const url = new URL(decodeXml(String(value)).replace(/[.,，。]+$/, ""));
    url.hash = "";
    for (const key of [...url.searchParams.keys()]) {
      if (!["__biz", "mid", "idx", "sn"].includes(key)) url.searchParams.delete(key);
    }
    return url.toString();
  } catch {
    return String(value).trim();
  }
}

export function parseFeed(xml, feedId, source) {
  const items = [...xml.matchAll(/<item(?:\s[^>]*)?>([\s\S]*?)<\/item>/gi)];
  return items.flatMap((match) => {
    const body = match[1];
    const title = cleanText(tagValue(body, "title"));
    const url = canonicalUrl(cleanText(tagValue(body, "link")));
    const published = tagValue(body, "pubDate");
    const summary = cleanText(tagValue(body, "description"));
    const publishedAt = new Date(published);
    if (!title || !url || Number.isNaN(publishedAt.getTime())) return [];
    return [{ feedId, source, title, url, publishedAt, summary }];
  });
}

export function articleIsRelevant(article) {
  return ARTICLE_WORDS.test(`${article.title} ${article.summary}`);
}

export function catalogFeeds(sources) {
  const ranks = { high: 0, normal: 1, low: 2 };
  return sources
    .filter((source) => source.enabled !== false && source.kind === "wechat" && source.feedId)
    .sort((left, right) =>
      (ranks[left.crawlPriority] ?? ranks.normal) -
      (ranks[right.crawlPriority] ?? ranks.normal)
    );
}

function shanghaiDay(date = new Date()) {
  return new Date(date.getTime() + SHANGHAI_OFFSET_MS).toISOString().slice(0, 10);
}

function readJson(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") return fallback;
    throw error;
  }
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temporary = `${file}.tmp`;
  fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  fs.renameSync(temporary, file);
}

async function request(url, { token, method = "GET", payload } = {}) {
  const headers = { Accept: "application/vnd.github+json", "User-Agent": USER_AGENT };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
    headers["X-GitHub-Api-Version"] = "2022-11-28";
  }
  if (payload) headers["Content-Type"] = "application/json";
  let response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: payload ? JSON.stringify(payload) : undefined,
      signal: AbortSignal.timeout(30_000),
    });
  } catch (error) {
    throw new Error(`无法连接 ${new URL(url).host}：${error.message}`);
  }
  const text = await response.text();
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${text.slice(0, 500)}`);
  return response.headers.get("content-type")?.includes("json") ? JSON.parse(text) : text;
}

async function githubIssues(repository, token) {
  const result = await request(`https://api.github.com/repos/${repository}/issues?state=all&per_page=100`, { token });
  if (!Array.isArray(result)) throw new Error("GitHub 返回了无法识别的 Issue 列表");
  return result;
}

function knownIssueUrls(issues) {
  const urls = new Set();
  for (const issue of issues) {
    for (const raw of String(issue.body || "").match(WECHAT_URLS) || []) {
      urls.add(canonicalUrl(raw));
    }
  }
  return urls;
}

function issuesCreatedToday(issues, today) {
  return issues.filter((issue) =>
    String(issue.body || "").includes(MARKER) && shanghaiDay(new Date(issue.created_at)) === today
  ).length;
}

export function issueBody(article) {
  return [
    "### 公众号名称",
    article.source,
    "",
    "### 公众号文章链接",
    article.url,
    "",
    "### 文章标题和发布日期",
    `${article.title}；${shanghaiDay(article.publishedAt)}`,
    "",
    "### 文章截图",
    "",
    "_No response_",
    "",
    "### 补充文字或说明",
    "由本机 WeRSS 自动发现。GitHub Bot 将读取正文和图片，并判断是否含未来活动。",
    "",
    MARKER,
  ].join("\n");
}

async function createIssue(repository, token, article) {
  const result = await request(`https://api.github.com/repos/${repository}/issues`, {
    token,
    method: "POST",
    payload: {
      title: `[公众号文章] ${article.title.slice(0, 180)}`,
      body: issueBody(article),
    },
  });
  if (!result?.html_url) throw new Error("GitHub 未返回新 Issue 地址");
  return result;
}

export async function run({ configPath, statePath, dryRun = false }) {
  const config = readJson(configPath, null);
  if (!config) throw new Error(`无法读取配置：${configPath}`);
  const token = String(process.env.PKU_LECTURES_GITHUB_TOKEN || "").trim();
  if (!dryRun && !token) throw new Error("尚未配置本机 GitHub Token");

  const baseUrl = String(config.werssBaseUrl || "http://127.0.0.1:8001").replace(/\/$/, "");
  const repository = String(config.repository || "wangzi2006/pku-lectures");
  const cap = Math.max(1, Number(config.dailyIssueCap || 10));
  const cutoff = Date.now() - Number(config.lookbackDays || 21) * 86_400_000;
  const sourcesPath = path.resolve(
    path.dirname(configPath),
    String(config.sourcesPath || "../data/sources.json"),
  );
  const feeds = catalogFeeds(readJson(sourcesPath, []));
  const articles = [];
  for (const feed of feeds) {
    const xml = await request(`${baseUrl}/rss/${encodeURIComponent(feed.feedId)}?limit=100`);
    articles.push(...parseFeed(xml, feed.feedId, feed.name).filter(
      (article) => article.publishedAt.getTime() >= cutoff && articleIsRelevant(article)
    ));
  }

  const unique = new Map();
  for (const article of articles) unique.set(article.url, article);
  const candidates = [...unique.values()].sort((a, b) => b.publishedAt - a.publishedAt);
  if (dryRun) {
    console.log(`检查完成：发现 ${candidates.length} 篇近期疑似活动文章；未创建 Issue。`);
    return 0;
  }

  const state = readJson(statePath, { submitted: {} });
  state.submitted ||= {};
  const issues = await githubIssues(repository, token);
  const knownUrls = new Set([...knownIssueUrls(issues), ...Object.keys(state.submitted)]);
  const today = shanghaiDay();
  let remaining = Math.max(0, cap - issuesCreatedToday(issues, today));
  let created = 0;

  for (const article of candidates) {
    if (remaining <= 0) break;
    if (knownUrls.has(article.url)) continue;
    const issue = await createIssue(repository, token, article);
    state.submitted[article.url] = {
      issue: issue.number,
      issueUrl: issue.html_url,
      submittedAt: new Date().toISOString(),
      title: article.title,
    };
    writeJson(statePath, state);
    knownUrls.add(article.url);
    remaining -= 1;
    created += 1;
    console.log(`已提交：${article.title} -> ${issue.html_url}`);
  }

  if (created) console.log(`本次创建 ${created} 个 Issue；GitHub Bot 将继续识别与筛选。`);
  else if (remaining === 0) console.log(`今天已经达到 ${cap} 条上限，剩余文章将在以后补交。`);
  else console.log("没有需要新提交的公众号文章。");
  return created;
}

function parseArgs(argv) {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const result = {
    configPath: path.join(here, "config.json"),
    statePath: path.join(process.env.LOCALAPPDATA || os.homedir(), "pku-lectures", "werss-bridge-state.json"),
    dryRun: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--dry-run") result.dryRun = true;
    else if (argv[i] === "--config") result.configPath = argv[++i];
    else if (argv[i] === "--state") result.statePath = argv[++i];
  }
  return result;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  run(parseArgs(process.argv.slice(2))).catch((error) => {
    console.error(`桥接失败：${error.message}`);
    process.exitCode = 1;
  });
}
