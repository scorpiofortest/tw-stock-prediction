import StockPageClient from './StockPageClient'

// Pre-generate pages for common stocks at build time.
// Other stock codes work via client-side navigation from the app.
export function generateStaticParams() {
  return [
    { code: '2330' },
    { code: '2317' },
    { code: '2454' },
    { code: '0050' },
    { code: '2603' },
    { code: '2881' },
    { code: '2882' },
    { code: '2412' },
    { code: '3008' },
    { code: '2308' },
  ]
}

export default function StockPage() {
  return <StockPageClient />
}
