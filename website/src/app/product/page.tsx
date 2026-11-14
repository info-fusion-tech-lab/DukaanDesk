import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Offline Shop Management App",
  description:
    "Explore DukaanDesk, a free offline shop management app for inventory, customer balances, sales and reports.",
};

export default function ProductPage() {
  return (
    <>
      <section className="page-hero">
        <div className="page-hero-inner">
          <p className="eyebrow">The product</p>
          <h1>Everyday shop management, in one desktop app.</h1>
          <p className="lead">
            A practical workspace for keeping track of stock, customer balances,
            sales and business reports from a single computer.
          </p>
          <div className="actions"><Link className="button" href="/download/">Download options</Link></div>
        </div>
      </section>
      <section className="section content-section">
        <div className="split">
          <div>
            <p className="eyebrow">How it fits your day</p>
            <h2>Keep routine tasks connected.</h2>
          </div>
          <div className="split-copy">
            <p>
              Add products and track quantities, look up a customer&apos;s ledger,
              create a sale and review recent activity without switching between
              separate tools.
            </p>
            <p>
              The application runs on your desktop and stores its operational
              records locally. You can continue using it without a hosted database
              or an online account.
            </p>
            <Link className="button secondary" href="/features/">Browse all features</Link>
          </div>
        </div>
      </section>
      <section className="section">
        <div className="section-heading">
          <p className="eyebrow">Built for a focused workflow</p>
          <h2>Simple tools, clear records.</h2>
        </div>
        <div className="card-grid">
          <article className="card"><div className="card-icon" aria-hidden="true">▦</div><h3>Products and stock</h3><p>Maintain a product list, update quantities and use low-stock indicators.</p></article>
          <article className="card"><div className="card-icon" aria-hidden="true">₹</div><h3>Sales and payments</h3><p>Record sales with cash, online, credit or split payment methods.</p></article>
          <article className="card"><div className="card-icon" aria-hidden="true">▤</div><h3>Customer ledger</h3><p>Keep customer balances and transaction history available in the app.</p></article>
        </div>
      </section>
    </>
  );
}
