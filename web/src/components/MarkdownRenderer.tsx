import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import type { Components } from "react-markdown";

interface MarkdownRendererProps {
  content: string;
  /** 紧凑模式：字号更小，间距更紧 */
  compact?: boolean;
}

export default function MarkdownRenderer({ content, compact = false }: MarkdownRendererProps) {
  const components = useMemo((): Components => ({
    // 代码块
    pre({ children }) {
      return (
        <pre className="markdown-pre bg-[#0d0d0d] border border-surface-border rounded-lg p-4 overflow-x-auto text-[13px] leading-relaxed my-3 scrollbar-thin">
          {children}
        </pre>
      );
    },
    code({ className, children, ...props }) {
      const isInline = !className;
      if (isInline) {
        return (
          <code
            className="bg-surface-overlay text-accent-hover px-1.5 py-0.5 rounded text-[0.88em] font-mono"
            {...props}
          >
            {children}
          </code>
        );
      }
      return (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
    // 标题
    h1({ children }) {
      return <h1 className={`text-[1.35em] font-bold mt-6 mb-3 text-white/95 ${compact ? "mt-4 mb-2" : ""}`}>{children}</h1>;
    },
    h2({ children }) {
      return <h2 className={`text-[1.18em] font-semibold mt-5 mb-2.5 text-white/90 ${compact ? "mt-3 mb-1.5" : ""}`}>{children}</h2>;
    },
    h3({ children }) {
      return <h3 className={`text-[1.05em] font-semibold mt-4 mb-2 text-white/85 ${compact ? "mt-2.5 mb-1" : ""}`}>{children}</h3>;
    },
    h4({ children }) {
      return <h4 className={`text-[0.95em] font-medium mt-3 mb-1.5 text-white/80 ${compact ? "mt-2 mb-1" : ""}`}>{children}</h4>;
    },
    // 段落
    p({ children }) {
      return <p className="text-sm leading-[1.72] text-muted-foreground/90 my-2 first:mt-0 last:mb-0">{children}</p>;
    },
    // 粗体 / 斜体
    strong({ children }) {
      return <strong className="font-semibold text-white/90">{children}</strong>;
    },
    em({ children }) {
      return <em className="italic text-white/80">{children}</em>;
    },
    // 删除线
    del({ children }) {
      return <del className="line-through text-muted/60">{children}</del>;
    },
    // 链接
    a({ href, children }) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent hover:text-accent-hover underline underline-offset-2 decoration-accent/30 hover:decoration-accent/60 transition-colors"
        >
          {children}
        </a>
      );
    },
    // 列表
    ul({ children }) {
      return <ul className="list-disc pl-5 my-2 space-y-1 text-sm text-muted-foreground/90">{children}</ul>;
    },
    ol({ children }) {
      return <ol className="list-decimal pl-5 my-2 space-y-1 text-sm text-muted-foreground/90">{children}</ol>;
    },
    li({ children }) {
      return <li className="leading-relaxed pl-1">{children}</li>;
    },
    // 引用块
    blockquote({ children }) {
      return (
        <blockquote className="border-l-[3px] border-accent/30 pl-4 my-3 py-1 bg-accent/5 rounded-r-lg italic text-white/70 text-sm">
          {children}
        </blockquote>
      );
    },
    // 水平线
    hr() {
      return <hr className="my-4 border-surface-border" />;
    },
    // 表格
    table({ children }) {
      return (
        <div className="overflow-x-auto my-3 rounded-lg border border-surface-border">
          <table className="min-w-full text-sm border-collapse">{children}</table>
        </div>
      );
    },
    thead({ children }) {
      return <thead className="bg-surface-overlay">{children}</thead>;
    },
    th({ children }) {
      return (
        <th className="px-3 py-2 text-left font-medium text-white/70 text-xs border-b border-surface-border whitespace-nowrap">
          {children}
        </th>
      );
    },
    td({ children }) {
      return (
        <td className="px-3 py-2 text-muted-foreground/90 border-b border-surface-border/50">
          {children}
        </td>
      );
    },
    // 图片
    img({ src, alt }) {
      return (
        <img
          src={src}
          alt={alt}
          className="max-w-full h-auto rounded-lg my-3 border border-surface-border"
          loading="lazy"
        />
      );
    },
    // 任务列表 (GFM)
    input({ type, checked, disabled }) {
      if (type === "checkbox") {
        return (
          <input
            type="checkbox"
            checked={checked}
            readOnly
            disabled={disabled}
            className="mr-2 accent-accent"
          />
        );
      }
      return <input type={type} checked={checked} disabled={disabled} />;
    },
  }), [compact]);

  return (
    <div className={compact ? "markdown-body markdown-compact" : "markdown-body"}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
