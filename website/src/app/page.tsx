import Link from "next/link";

const modules = [
  {
    icon: "▦",
    title: "Inventory",
    copy: "Keep product details, prices and stock counts together. Find items quickly and see when stock is running low.",
  },
  {
    icon: "◎",
    title: "Customer ledger",
    copy: "Keep customer contact details and a clear record of balances and transactions.",
  },
  {
    icon: "↗",
    title: "Sales and reports",
    copy: "Record multi-item sales with cash, online, credit or split payments, then review sales history.",
  },
];

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <p className="eyebrow">Free offline shop management for independent shops</p>
          <h1>Manage your shop. Keep your records on your computer.</h1>
          <p className="lead">
            DukaanDesk is free shop management software for inventory, customer
            ledgers, sales and reports. The desktop app works offline and stores
            business records locally on your computer.
          </p>
          <div className="actions">
            <Link className="button" href="/download/">Explore downloads <span aria-hidden="true">→</span></Link>
            <Link className="button secondary" href="/product/">See how it works</Link>
          </div>
          <p className="hero-note">Designed for single-computer shop operations. No cloud account is required.</p>
          <div className="preview-wrap" aria-label="Illustration of the shop dashboard">
            <div className="preview">
              <div className="preview-side">
                <div className="preview-logo">DukaanDesk</div>
                <div className="preview-nav">
                  <span>Dashboard</span><span>Inventory</span><span>Customers</span><span>Sales</span><span>Reports</span>
                </div>
              </div>
              <div className="preview-main">
                <div className="preview-title">Your shop at a glance</div>
                <div className="preview-stats">
                  <div className="preview-stat"><span>Products</span><strong>128</strong></div>
                  <div className="preview-stat"><span>In stock</span><strong>846</strong></div>
                  <div className="preview-stat"><span>Sales today</span><strong>₹12,450</strong></div>
                </div>
                <div className="preview-chart" aria-hidden="true" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <p className="eyebrow">One place for the essentials</p>
          <h2>Less juggling, more clarity.</h2>
          <p>Bring routine shop tasks into one tool, without a complicated setup.</p>
        </div>
        <div className="card-grid">
          {modules.map((module) => (
            <article className="card" key={module.title}>
              <div className="card-icon" aria-hidden="true">{module.icon}</div>
              <h3>{module.title}</h3>
              <p>{module.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="split">
          <div className="split-copy">
            <p className="eyebrow">Offline and local by design</p>
            <h2>Your shop records stay on your device.</h2>
            <p>
              The desktop app saves its working data on the computer where it is
              installed. The product website is separate and does not receive your
              inventory, customer ledger or sales records.
            </p>
            <ul className="list-check">
              <li>Use the app without an online account</li>
              <li>Keep customer and sales records in local files</li>
              <li>Choose when and how to back up your data</li>
            </ul>
          </div>
          <div className="callout">
            <p className="eyebrow">Get started</p>
            <h2>Take a look at the product before you install.</h2>
            <p>Explore the features and setup guide, then choose a release for your computer.</p>
            <Link className="button" href="/how-to-use/">Read the quick-start guide</Link>
          </div>
        </div>
      </section>
    </>
  );
}
