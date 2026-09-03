import assert from "node:assert/strict";
import test from "node:test";

import { articleIsRelevant, catalogFeeds, issueBody, parseFeed } from "./bridge.mjs";

const rss = `<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>测试</title><item>
<title>活动报名｜AI 时代青年创业对话峰会</title>
<link>https://mp.weixin.qq.com/s/example_123</link>
<description><![CDATA[<p>9月6日下午举行</p>]]></description>
<pubDate>Wed, 02 Sep 2026 17:04:00 +0800</pubDate>
</item></channel></rss>`;

test("parses and filters a WeRSS item", () => {
  const article = parseFeed(rss, "feed-1", "测试公众号")[0];
  assert.equal(article.source, "测试公众号");
  assert.equal(article.publishedAt.toISOString(), "2026-09-02T09:04:00.000Z");
  assert.equal(articleIsRelevant(article), true);
});

test("creates a body compatible with the Issue form", () => {
  const body = issueBody(parseFeed(rss, "feed-1", "测试公众号")[0]);
  assert.match(body, /### 公众号名称\n测试公众号/);
  assert.match(body, /### 公众号文章链接\nhttps:\/\/mp\.weixin\.qq\.com\/s\/example_123/);
  assert.match(body, /pku-lectures-werss-bridge/);
});

test("ignores a plain newsletter", () => {
  assert.equal(articleIsRelevant({ title: "九月月报", summary: "校园新闻汇总" }), false);
});

test("uses only enabled WeChat sources with a WeRSS feed ID", () => {
  const sources = [
    { name: "A", kind: "wechat", enabled: true, feedId: "MP_A" },
    { name: "B", kind: "wechat", enabled: true },
    { name: "C", kind: "event-list", enabled: true, feedId: "MP_C" },
    { name: "D", kind: "wechat", enabled: false, feedId: "MP_D" },
  ];
  assert.deepEqual(catalogFeeds(sources).map((source) => source.feedId), ["MP_A"]);
});
