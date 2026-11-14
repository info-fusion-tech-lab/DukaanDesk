import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Shop Management Features",
  description:
    "Explore DukaanDesk features for inventory management, customer ledgers, QR labels, retail sales and reports.",
};

const features = [
  ["Inventory management", "Add products with selling and cost prices, sizes, categories, current quantities and minimum stock levels."],
  ["Product codes and QR labels", "Generate product codes and QR images to help identify items in the shop."],
  ["Customer ledger", "Register customers, record money given or received, and review balance and transaction history."],
  ["Multi-item sales", "Add several products to a sale, validate stock and support cash, online, credit or split payments."],
  ["Sales history", "Review recorded sales, items, payment type, customer and notes. Filter the list by date and payment."],
  ["Dashboard summary", "See product, stock, customer, sales, receivable and low-stock totals in one place."],
];

export default function FeaturesPage() {
  return (
    <>
      <section className="page-hero">
        <div className="page-hero-inner">
          <p className="eyebrow">Features</p>
          <h1>The essentials for running a small shop.</h1>
          <p className="lead">A focused set of tools for the stock, customer and sales work you do every day.</p>
        </div>
      </section>
      <section className="section content-section">
        <div className="feature-list">
          {features.map(([title, description], index) => (
            <article className="feature-row" key={title}>
              <div className="card-icon" aria-hidden="true">{String(index + 1).padStart(2, "0")}</div>
              <div><h3>{title}</h3><p>{description}</p></div>
            </article>
          ))}
        </div>
      </section>
      <section className="section">
        <div className="notice">
          The current desktop release is designed for one computer and one local
          data store. It does not synchronize records between multiple devices.
        </div>
      </section>
    </>
  );
}
