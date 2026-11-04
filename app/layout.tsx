import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "HotspotOps — Public Wi-Fi service assurance",
  description: "Know which hotspots work. Know why the others fail. Independent public Wi-Fi service assurance concept.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
