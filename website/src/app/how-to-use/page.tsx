import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "How to use",
  description: "Install and get started with the Shop Management System desktop app.",
};

const steps = [
  ["Download the installer", "Choose the package for your operating system from the latest releases page and install it."],
  ["Open the desktop app", "Start Shop Management System from your applications list. The local service starts automatically."],
  ["Add your inventory", "Enter product names, prices, sizes, quantities and minimum stock levels. Product codes and QR labels are generated for you."],
  ["Register customers", "Add customers by name and phone number when you need to keep a ledger or record credit."],
  ["Record sales", "Add one or more products, choose the payment method and complete the sale. Stock is updated by the app."],
  ["Review and back up", "Use the dashboard and reports to review activity. Back up the local data folder regularly and before moving to another computer."],
];

export default function HowToUsePage() {
  return (
    <>
      <section className="page-hero">
        <div className="page-hero-inner">
          <p className="eyebrow">Quick start</p>
          <h1>From install to your first sale.</h1>
          <p className="lead">A short guide to setting up the app and keeping your local records safe.</p>
          <div className="actions"><Link className="button" href="/download/">Go to downloads</Link></div>
        </div>
      </section>
      <section className="section content-section">
        <div className="steps">
          {steps.map(([title, description]) => (
            <article className="step-card" key={title}>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="section">
        <div className="notice">
          Your data is stored on the computer running the app. Keep a separate
          backup of its data folder; uninstalling or losing that computer can
          otherwise make local records unavailable.
        </div>
      </section>
    </>
  );
}
