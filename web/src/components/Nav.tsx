import { NavLink } from "react-router-dom";
import { Icons } from "../icons";

const items = [
  { to: "/", label: "Browse", icon: Icons.search, end: true },
  { to: "/shelf", label: "Shelf", icon: Icons.shelf },
  { to: "/organize", label: "Organize", icon: Icons.organize },
  { to: "/scenes", label: "Scenes", icon: Icons.scenes },
  { to: "/layout", label: "Layout", icon: Icons.layout },
  { to: "/settings", label: "Settings", icon: Icons.settings },
];

function Links() {
  return (
    <>
      {items.map((it) => (
        <NavLink key={it.to} to={it.to} end={it.end} className={({ isActive }) => (isActive ? "active" : "")}>
          <it.icon />
          <span>{it.label}</span>
        </NavLink>
      ))}
    </>
  );
}

export function SideNav() {
  return (
    <nav className="nav-side">
      <div className="brand"><Icons.record /> recordShelf</div>
      <Links />
    </nav>
  );
}

export function TabNav() {
  return (
    <nav className="nav-tabs">
      <Links />
    </nav>
  );
}
