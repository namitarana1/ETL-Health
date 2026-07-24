import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HealthLake | Healthcare Pipeline Demo",
  description: "Interactive multi-cloud healthcare data pipeline demonstration using synthetic payer data.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
