import type { Metadata } from "next";
import Script from "next/script";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/nav";
import { Footer } from "@/components/footer";
import { seoConfig } from "@/lib/seo.config";
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { DataSourceProvider } from "@/lib/data-source-context";
import { ThemeProvider } from "@/components/theme-provider";

const geistSans = Geist({ subsets: ["latin"], variable: "--font-sans" });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: {
    default: seoConfig.title,
    template: `%s | ${seoConfig.title}`,
  },
  description: seoConfig.description,
  metadataBase: new URL(seoConfig.canonical),
  alternates: {
    canonical: seoConfig.canonical,
  },
  openGraph: {
    ...seoConfig.openGraph,
    images: [
      {
        url: "/images/og-image.png",
        width: 1200,
        height: 630,
        alt: "C-SWON — Zapier for Subnets",
      },
    ],
  },
  twitter: seoConfig.twitter,
  icons: {
    icon: [
      { url: "/images/favicon.ico" },
      { url: "/images/favicon-96x96.png", sizes: "96x96", type: "image/png" },
      { url: "/images/favicon.svg", type: "image/svg+xml" },
    ],
    apple: [
      { url: "/images/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
  manifest: "/images/site.webmanifest",
  verification: {
    google: "WnaeKbRB9LIW77kvZTKfbOwFX24eDJApdNn78nZvksc",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "C-SWON",
  "description": "Cross-Subnet Workflow Orchestration Network for Bittensor.",
  "applicationCategory": "BlockchainApplication",
  "operatingSystem": "Web",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "publisher": {
    "@type": "Organization",
    "name": "C-SWON Network",
    "logo": {
      "@type": "ImageObject",
      "url": "https://c-swon.vercel.app/images/web-app-manifest-512x512.png"
    }
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-SCB526X0ZV"
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());

            gtag('config', 'G-SCB526X0ZV');
          `}
        </Script>
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased selection:bg-[var(--color-teal)]/30`}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
          <DataSourceProvider>
            <Nav />
            <main className="mx-auto max-w-7xl px-6 py-8 min-h-[calc(100vh-13rem)]">{children}</main>
            <Footer />
          </DataSourceProvider>
        </ThemeProvider>
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
