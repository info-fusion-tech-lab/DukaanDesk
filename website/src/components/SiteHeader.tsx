import Link from "next/link";

const links = [
  { href: "/product/", label: "Product" },
  { href: "/features/", label: "Features" },
  { href: "/how-to-use/", label: "How to use" },
  { href: "/about/", label: "About" },
];

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link className="brand" href="/" aria-label="DukaanDesk home">
        <span className="brand-mark" aria-hidden="true">D</span>
        <span>DukaanDesk</span>
      </Link>
      <nav className="site-nav" aria-label="Main navigation">
        {links.map((link) => (
          <Link href={link.href} key={link.href}>{link.label}</Link>
        ))}
        <Link className="nav-download" href="/download/">Download</Link>
      </nav>
    </header>
  );
}
