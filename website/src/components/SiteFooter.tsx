import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <Link className="brand footer-brand" href="/">
        <span className="brand-mark" aria-hidden="true">D</span>
        <span>DukaanDesk</span>
      </Link>
      <p>Simple shop operations, with your business data kept on your device.</p>
      <div className="footer-links">
        <Link href="/product/">Product</Link>
        <Link href="/features/">Features</Link>
        <Link href="/how-to-use/">How to use</Link>
        <Link href="/about/">About</Link>
        <Link href="/download/">Download</Link>
      </div>
      <small>© {new Date().getFullYear()} DukaanDesk</small>
    </footer>
  );
}
