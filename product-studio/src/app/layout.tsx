import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "产品图工作台",
  description: "AI 产品图分析与精修工具",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  )
}
