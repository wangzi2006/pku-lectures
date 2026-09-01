'use client';

import {
  ArrowUpRight,
  CalendarDays,
  Clock3,
  MapPin,
  Search,
  Sparkles,
} from 'lucide-react';
import { useMemo, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import candidatesData from '@/data/candidates.json';
import lecturesData from '@/data/lectures.json';
import {
  distanceLabel,
  formatLectureDate,
  type Lecture,
  topicOrder,
} from '@/lib/lectures';

const lecturesSource = lecturesData as Lecture[];
const buildTimestamp = new Date().getTime();
const windowEndTimestamp = buildTimestamp + 14 * 24 * 60 * 60 * 1000;
const pendingCount = candidatesData.filter((item) => item.status === 'pending').length;
const visibleTopics = topicOrder.filter(
  (topic) =>
    topic === '全部' || lecturesSource.some((lecture) => lecture.topic === topic),
);

export default function Home() {
  const [activeTopic, setActiveTopic] = useState('全部');
  const [query, setQuery] = useState('');

  const lectures = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return lecturesSource
      .filter((lecture) => new Date(lecture.startAt).getTime() >= buildTimestamp)
      .filter(
        (lecture) => new Date(lecture.startAt).getTime() <= windowEndTimestamp,
      )
      .sort(
        (left, right) =>
          new Date(left.startAt).getTime() - new Date(right.startAt).getTime(),
      )
      .filter((lecture) => {
      const matchesTopic =
        activeTopic === '全部' || lecture.topic === activeTopic;
      const matchesQuery =
        !normalized ||
        [lecture.title, lecture.speaker, lecture.location, lecture.summary]
          .join(' ')
          .toLowerCase()
          .includes(normalized);
      return matchesTopic && matchesQuery;
      });
  }, [activeTopic, query]);

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-30 border-b border-border/70 bg-background/92 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3 sm:px-6">
          <a className="flex min-w-fit items-center gap-3" href="#top">
            <span className="grid size-10 place-items-center rounded-xl bg-primary font-serif text-xl font-semibold text-primary-foreground shadow-sm">
              未
            </span>
            <span>
              <strong className="block font-serif text-[17px] leading-tight tracking-wide">
                未名讲座
              </strong>
              <span className="hidden text-[11px] tracking-[0.12em] text-muted-foreground sm:block">
                未来十四天 · 值得去现场
              </span>
            </span>
          </a>

          <label className="relative ml-auto hidden w-full max-w-sm sm:block">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <span className="sr-only">搜索讲座</span>
            <input
              className="h-10 w-full rounded-xl border border-input bg-card pl-9 pr-3 text-sm shadow-xs outline-none transition focus:border-primary/40 focus:ring-3 focus:ring-primary/10"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索主题、讲者或地点"
              value={query}
            />
          </label>

          <a
            className="hidden rounded-lg px-2 py-1.5 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground md:block"
            href="https://github.com/wangzi2006/pku-lectures/issues/new/choose"
          >
            提交讲座
          </a>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-4 pb-16 pt-8 sm:px-6" id="top">
        <section className="mb-7 grid gap-5 border-b border-border/80 pb-7 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <p className="mb-2 flex items-center gap-2 text-xs font-semibold tracking-[0.14em] text-primary uppercase">
              <Sparkles className="size-3.5" />
              今日讲座雷达
            </p>
            <h1 className="max-w-3xl font-serif text-3xl font-semibold leading-tight tracking-tight sm:text-5xl">
              别让值得听的讲座，
              <span className="text-primary">消失在信息流里。</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
              聚合北京大学及骑行可达范围内的公开讲座，经来源核验、去重与人工审核后呈现。
            </p>
          </div>
          <div className="grid grid-cols-3 gap-px overflow-hidden rounded-xl border bg-border text-center shadow-xs">
            {[
              ['14', '未来天数'],
              ['07:00', '每日更新'],
              ['≈ 6 km', '校外范围'],
            ].map(([value, label]) => (
              <div className="min-w-24 bg-card px-4 py-3" key={label}>
                <strong className="block font-serif text-lg">{value}</strong>
                <span className="text-[11px] text-muted-foreground">{label}</span>
              </div>
            ))}
          </div>
        </section>

        <section aria-label="讲座筛选" className="mb-6 space-y-3">
          <label className="relative block sm:hidden">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <span className="sr-only">搜索讲座</span>
            <input
              className="h-11 w-full rounded-xl border border-input bg-card pl-9 pr-3 text-sm outline-none focus:ring-3 focus:ring-primary/10"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索主题、讲者或地点"
              value={query}
            />
          </label>
          <div className="flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none]">
            {visibleTopics.map((topic) => (
              <Button
                aria-pressed={activeTopic === topic}
                className="min-w-fit rounded-full"
                key={topic}
                onClick={() => setActiveTopic(topic)}
                size="sm"
                variant={activeTopic === topic ? 'default' : 'outline'}
              >
                {topic}
              </Button>
            ))}
          </div>
        </section>

        <div className="grid gap-7 lg:grid-cols-[minmax(0,1fr)_280px]">
          <section aria-labelledby="lecture-list-title">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="font-serif text-xl font-semibold" id="lecture-list-title">
                  接下来值得听
                </h2>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  已发布条目 · 未来 14 天
                </p>
              </div>
              <span className="text-sm text-muted-foreground">
                {lectures.length} 场
              </span>
            </div>

            <div className="space-y-4">
              {lectures.map((lecture) => (
                <article className="grid gap-3 sm:grid-cols-[72px_1fr]" key={lecture.id}>
                  {(() => {
                    const date = formatLectureDate(lecture.startAt);
                    return (
                      <>
                  <div className="hidden pt-4 text-center sm:block">
                    <span className="block text-[11px] font-medium tracking-widest text-muted-foreground uppercase">
                      {date.month}
                    </span>
                    <strong className="block font-serif text-3xl leading-none text-primary">
                      {date.day}
                    </strong>
                    <span className="mt-1 block text-xs text-muted-foreground">
                      {date.weekday}
                    </span>
                  </div>

                  <Card className="border-0 shadow-[0_7px_28px_rgb(46_32_24/7%)] ring-border transition hover:-translate-y-0.5 hover:shadow-[0_12px_34px_rgb(46_32_24/10%)]">
                    <CardHeader>
                      <div className="mb-2 flex flex-wrap items-center gap-1.5">
                        <Badge className="bg-accent text-accent-foreground" variant="secondary">
                          {lecture.topic}
                        </Badge>
                        {lecture.flags.map((flag) => (
                          <Badge key={flag} variant="outline">
                            {flag}
                          </Badge>
                        ))}
                        <span className="ml-auto text-xs text-muted-foreground sm:hidden">
                          {date.month}{date.day}日 · {date.weekday}
                        </span>
                      </div>
                      <CardTitle className="font-serif text-xl font-semibold leading-snug sm:text-2xl">
                        {lecture.titleZh || lecture.title}
                      </CardTitle>
                      {lecture.titleZh ? (
                        <p className="text-xs leading-5 text-muted-foreground">
                          {lecture.title}
                        </p>
                      ) : null}
                      <p className="text-sm text-muted-foreground">{lecture.speaker}</p>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1.5">
                          <Clock3 className="size-3.5 text-primary" />
                          {date.time}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <MapPin className="size-3.5 text-primary" />
                          {lecture.location} · {distanceLabel(lecture)}
                        </span>
                      </div>
                      <p className="text-sm leading-6 text-foreground/84">
                        {lecture.summary}
                      </p>
                      <div className="rounded-lg border-l-2 border-accent bg-accent/45 px-3 py-2.5 text-sm leading-5">
                        <span className="font-semibold text-accent-foreground">为什么值得听：</span>
                        {lecture.reason}
                      </div>
                    </CardContent>
                    <CardFooter className="justify-between border-border/70 bg-muted/35">
                      <span className="text-[11px] text-muted-foreground">
                        {lecture.sourceName} · 核验于{' '}
                        {new Date(lecture.verifiedAt).toLocaleDateString('zh-CN', {
                          timeZone: 'Asia/Shanghai',
                        })}
                      </span>
                      <a
                        className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline"
                        href={lecture.registrationUrl || lecture.sourceUrl}
                        rel="noreferrer"
                        target="_blank"
                      >
                        查看原文 <ArrowUpRight className="size-3.5" />
                      </a>
                    </CardFooter>
                  </Card>
                      </>
                    );
                  })()}
                </article>
              ))}

              {lectures.length === 0 ? (
                <div className="rounded-2xl border border-dashed bg-card px-6 py-14 text-center">
                  <Search className="mx-auto mb-3 size-6 text-muted-foreground" />
                  <p className="font-medium">
                    {lecturesSource.length === 0
                      ? '首轮候选正在人工审核'
                      : '没有符合当前条件的讲座'}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {lecturesSource.length === 0
                      ? `已有 ${pendingCount} 条候选等待确认；只有审核通过后才会出现在这里。`
                      : '可以清除筛选查看全部已发布讲座。'}
                  </p>
                  {lecturesSource.length > 0 ? (
                    <button
                      className="mt-2 text-sm text-primary hover:underline"
                      onClick={() => {
                        setActiveTopic('全部');
                        setQuery('');
                      }}
                      type="button"
                    >
                      清除筛选
                    </button>
                  ) : null}
                </div>
              ) : null}
            </div>
          </section>

          <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
            <Card className="border-0 bg-primary text-primary-foreground ring-0">
              <CardHeader>
                <CalendarDays className="mb-3 size-6 opacity-80" />
                <CardTitle className="font-serif text-xl font-semibold">
                  每天一次，替你找讲座
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-6 text-primary-foreground/78">
                  官网信息每天早晨更新；来源不确定或质量难判断的活动，会进入人工审核。
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 bg-card shadow-sm ring-border">
              <CardHeader>
                <CardTitle className="font-serif text-lg font-semibold">收录原则</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li className="flex gap-2">
                    <span className="mt-1 size-1.5 shrink-0 rounded-full bg-primary" />
                    概率方向尽量完整收录
                  </li>
                  <li className="flex gap-2">
                    <span className="mt-1 size-1.5 shrink-0 rounded-full bg-accent-foreground" />
                    其他专业报告重视本科生可听性
                  </li>
                  <li className="flex gap-2">
                    <span className="mt-1 size-1.5 shrink-0 rounded-full bg-primary" />
                    重要来访与稀缺演讲单独标记
                  </li>
                  <li className="flex gap-2">
                    <span className="mt-1 size-1.5 shrink-0 rounded-full bg-accent-foreground" />
                    校外活动执行更严格的质量门槛
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card className="border-0 bg-card shadow-sm ring-border">
              <CardHeader>
                <CardTitle className="font-serif text-lg font-semibold">一起校准</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm leading-6 text-muted-foreground">
                <p>听过一场后，用五个 1–5 分告诉系统实际质量；反馈首期只用于筛选校准。</p>
                <a
                  className="inline-flex items-center gap-1 font-semibold text-primary hover:underline"
                  href="https://github.com/wangzi2006/pku-lectures/issues/new?template=feedback.yml"
                >
                  提交听后反馈 <ArrowUpRight className="size-3.5" />
                </a>
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>

      <footer className="border-t bg-card">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-xs leading-5 text-muted-foreground sm:px-6">
          <p>未名讲座是独立、非官方的信息索引，与北京大学及各主办单位无隶属关系。</p>
          <p>页面仅提供活动摘要与原文索引；时间、地点及报名要求请以主办方最新通知为准。</p>
          <p className="flex flex-wrap gap-x-4 gap-y-1">
            <a className="hover:text-foreground hover:underline" href="https://github.com/wangzi2006/pku-lectures/issues/new?template=lecture.yml">提交讲座</a>
            <a className="hover:text-foreground hover:underline" href="https://github.com/wangzi2006/pku-lectures/issues/new?template=source.yml">推荐来源</a>
            <a className="hover:text-foreground hover:underline" href="https://github.com/wangzi2006/pku-lectures/issues/new?template=correction.yml">更正或移除</a>
            <a className="hover:text-foreground hover:underline" href="https://github.com/wangzi2006/pku-lectures">开放源码</a>
          </p>
        </div>
      </footer>
    </main>
  );
}
