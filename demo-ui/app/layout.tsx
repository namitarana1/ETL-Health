import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HealthLake Execution Lab",
  description: "Run an interactive multi-cloud healthcare data pipeline and watch records move from ingestion through trusted gold analytics.",
  openGraph: {
    title: "HealthLake Execution Lab",
    description: "Press run. Watch data become trusted.",
    images: [{ url: "/og.png", width: 1733, height: 909, alt: "HealthLake Execution Lab pipeline preview" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "HealthLake Execution Lab",
    description: "Press run. Watch data become trusted.",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
