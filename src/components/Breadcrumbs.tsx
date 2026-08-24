import { Link, useLocation } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";

export function Breadcrumbs() {
  const location = useLocation();
  const segments = location.pathname.split("/").filter(Boolean);

  const items: { label: string; href?: string; current: boolean }[] = [
    { label: "Strona główna", href: "/", current: segments.length === 0 },
  ];
  if (segments[0] === "quiz") {
    items.push({ label: "Quiz", current: true });
  }

  return (
    <nav aria-label="Breadcrumb" className="w-full border-b border-border/40 bg-background/80">
      <div className="mx-auto flex max-w-6xl items-center overflow-x-auto whitespace-nowrap px-4 py-2 sm:px-6">
        <ol className="flex items-center gap-1 text-xs text-muted-foreground">
          {items.map((item, index) => (
            <li key={index} className="flex items-center gap-1">
              {index > 0 && <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground/50" />}
              {item.current ? (
                <span className="font-medium text-foreground">{item.label}</span>
              ) : (
                <Link to={item.href!} className="transition-colors hover:text-foreground">
                  {item.label}
                </Link>
              )}
            </li>
          ))}
        </ol>
      </div>
    </nav>
  );
}
