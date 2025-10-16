'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownMessageProps {
  content: string;
  isUser?: boolean;
}

export default function MarkdownMessage({ content, isUser = false }: MarkdownMessageProps) {
  if (isUser) {
    // User messages don't need markdown rendering
    return <p className="text-sm whitespace-pre-wrap">{content}</p>;
  }

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Customize heading styles
          h1: ({ node, ...props }) => <h1 className="text-xl font-bold mt-4 mb-2" {...props} />,
          h2: ({ node, ...props }) => <h2 className="text-lg font-bold mt-3 mb-2" {...props} />,
          h3: ({ node, ...props }) => <h3 className="text-base font-bold mt-2 mb-1" {...props} />,
          
          // Customize paragraph
          p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
          
          // Customize lists
          ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-2 space-y-1" {...props} />,
          ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />,
          li: ({ node, ...props }) => <li className="ml-2" {...props} />,
          
          // Customize code blocks
          code: ({ node, inline, className, children, ...props }: any) => {
            if (inline) {
              return (
                <code
                  className="bg-base-300 text-accent px-1.5 py-0.5 rounded text-xs font-mono"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code
                className="block bg-base-300 text-sm p-3 rounded-lg overflow-x-auto font-mono my-2"
                {...props}
              >
                {children}
              </code>
            );
          },
          
          // Customize blockquotes
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-l-4 border-primary pl-4 italic my-2 text-base-content/80"
              {...props}
            />
          ),
          
          // Customize links
          a: ({ node, ...props }) => (
            <a
              className="text-primary hover:text-primary-focus underline"
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            />
          ),
          
          // Customize tables
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-2">
              <table className="table table-sm table-zebra" {...props} />
            </div>
          ),
          
          // Customize horizontal rules
          hr: ({ node, ...props }) => <hr className="my-4 border-base-300" {...props} />,
          
          // Customize strong/bold
          strong: ({ node, ...props }) => <strong className="font-bold text-base-content" {...props} />,
          
          // Customize emphasis/italic
          em: ({ node, ...props }) => <em className="italic" {...props} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
