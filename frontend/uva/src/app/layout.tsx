import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Vector AI Vision",
    description: "Advanced Computer Vision & OCR Platform",
};

export default function RootLayout({
                                       children,
                                   }: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
        <body className={inter.className} style={{ margin: 0, padding: 0 }}>
        {/*
           This renders your new page.tsx.
           We removed all hardcoded headers/footers from here.
        */}
        {children}
        </body>
        </html>
    );
}