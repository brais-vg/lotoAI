import { Outlet, NavLink } from "react-router-dom";
import { MessageSquare, Upload, Search, Menu } from "lucide-react";
import { useState } from "react";
import { cn } from "../../lib/utils";
import { Button } from "../ui/Button";

export default function AppLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(true);

    const navItems = [
        { to: "/", icon: MessageSquare, label: "Chat" },
        { to: "/upload", icon: Upload, label: "Upload" },
        { to: "/search", icon: Search, label: "Search" },
    ];

    return (
        <div className="flex h-screen w-full bg-background text-foreground overflow-hidden">
            {/* Sidebar */}
            <aside
                className={cn(
                    "flex flex-col border-r bg-card transition-all duration-300",
                    sidebarOpen ? "w-64" : "w-16"
                )}
            >
                <div className="flex h-14 items-center border-b px-4 justify-between">
                    {sidebarOpen && <span className="font-bold text-lg">lotoAI</span>}
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className={!sidebarOpen ? "mx-auto" : ""}
                    >
                        <Menu className="h-5 w-5" />
                    </Button>
                </div>
                <nav className="flex-1 py-4 space-y-2 px-2">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                                cn(
                                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
                                    isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground",
                                    !sidebarOpen && "justify-center px-0"
                                )
                            }
                        >
                            <item.icon className="h-5 w-5" />
                            {sidebarOpen && <span>{item.label}</span>}
                        </NavLink>
                    ))}
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                <div className="container mx-auto p-6 max-w-5xl">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
