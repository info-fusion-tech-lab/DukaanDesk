import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About",
  description: "About the Shop Management System product.",
};

export default function AboutPage() {
  return (
    <>
      <section className="page-hero">
        <div className="page-hero-inner">
          <p className="eyebrow">About the product</p>
          <h1>Useful shop tools without a complicated setup.</h1>
          <p className="lead">
            Shop Management System brings common inventory, customer and sales
            tasks together in a desktop application for independent retailers.
          </p>
        </div>
      </section>
      <section className="section content-section">
        <div className="split">
          <div>
            <p className="eyebrow">Our approach</p>
            <h2>Practical first. Local by default.</h2>
          </div>
          <div className="split-copy">
            <p>
              The product is built around the tasks small shops handle every day:
              knowing what is in stock, keeping customer balances, recording
              transactions and checking sales history.
            </p>
            <p>
              The desktop application keeps business records on the local device.
              This means the shop owner is responsible for controlling access to
              the computer and maintaining backups.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
