import type { Metadata } from "next";
import { Fraunces, Nunito, Space_Mono } from "next/font/google";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  axes: ["SOFT", "WONK", "opsz"],
});
const nunito = Nunito({ subsets: ["latin"], variable: "--font-nunito" });
const spaceMono = Space_Mono({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-space-mono",
});

export const metadata: Metadata = {
  title: "Noor · Ask your textbook",
  description:
    "Noor is your friendly study buddy — ask anything from your own school textbooks and get answers with the exact page they came from.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${fraunces.variable} ${nunito.variable} ${spaceMono.variable}`}>
        {children}
      </body>
    </html>
  );
}
