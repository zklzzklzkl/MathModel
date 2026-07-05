import type { Metadata } from "next";
import type { ReactNode } from "react";
import { ShellLayout } from "@/components/layout/ShellLayout";
import "./globals.css";

export const metadata: Metadata = {
  title: "MathModel Studio V3",
  description: "Local AI modeling and research studio",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>
        <ShellLayout>{children}</ShellLayout>
      </body>
    </html>
  );
}
