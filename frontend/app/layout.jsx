import "./globals.css";

export const metadata = {
  title: "thunai — AI Support That Knows When to Act",
  description: "Evidence-grounded AI customer support agent"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}