/* oxlint-disable next/no-html-link-for-pages -- Static GitHub Pages navigation must avoid root-relative links. */
import { ArrowLeft, ExternalLink, Plus } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { buttonVariants } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import sourcesData from '@/data/sources.json';
import type { LectureSource } from '@/lib/lectures';

const sources = (sourcesData as LectureSource[]).filter((source) => source.enabled);

export const dynamic = 'force-static';

const kindLabels: Record<LectureSource['kind'], string> = {
  'event-list': '讲座预告',
  mixed: '预告与回顾',
  'review-archive': '回顾反查',
  wechat: '微信公众号',
};

export default function SourcesPage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="border-b bg-card/90">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <a className="flex items-center gap-2 font-serif text-lg font-semibold" href="./">
            <ArrowLeft className="size-4" />
            未名讲座
          </a>
          <a
            className={buttonVariants({ size: 'sm' })}
            href="https://github.com/wangzi2006/pku-lectures/issues/new?template=source.yml"
          >
            <Plus className="size-4" />
            推荐来源
          </a>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-5 py-10 sm:px-8">
        <div className="mb-7">
          <p className="text-xs font-semibold tracking-[0.14em] text-primary uppercase">
            Sources
          </p>
          <h1 className="mt-2 font-serif text-3xl font-semibold sm:text-4xl">来源目录</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            当前启用 {sources.length} 个来源。新来源由公开推荐、Owner 审批后加入。
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sources.map((source) => (
            <Card className="border-0 shadow-sm ring-border" key={source.id}>
              <CardHeader className="gap-3">
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="secondary">{kindLabels[source.kind]}</Badge>
                  <Badge variant="outline">第 {source.tier} 级</Badge>
                  {source.crawlPriority === 'high' ? <Badge variant="outline">重点监控</Badge> : null}
                  {source.reviewMining ? <Badge variant="outline">回顾反查</Badge> : null}
                </div>
                <CardTitle className="font-serif text-lg leading-snug">
                  <a
                    className="inline-flex items-start gap-1.5 hover:text-primary hover:underline"
                    href={source.url}
                    rel="noreferrer"
                    target="_blank"
                  >
                    {source.name}
                    <ExternalLink className="mt-1 size-3.5 shrink-0" />
                  </a>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm leading-6 text-muted-foreground">
                <div className="flex flex-wrap gap-1.5">
                  {source.topics.map((topic) => (
                    <Badge key={topic} variant="outline">
                      {topic}
                    </Badge>
                  ))}
                </div>
                <p>{source.notes}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </main>
  );
}
